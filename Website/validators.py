"""
Brita Filter CMS - Content Validators

Provides validation gates for content quality, SEO, accessibility,
and governance compliance.

These validators can be used:
1. On-save for immediate feedback
2. Pre-publish as hard gates
3. In admin as lint indicators
4. In Celery tasks for async validation (e.g., link checking)
"""

import re
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from django.utils.html import strip_tags
from urllib.parse import urlparse


class Severity(Enum):
    """Validation issue severity"""
    ERROR = 'error'      # Blocks publish
    WARNING = 'warning'  # Shows warning, doesn't block
    INFO = 'info'        # Informational only


@dataclass
class ValidationIssue:
    """A single validation issue"""
    code: str
    message: str
    severity: Severity
    field: Optional[str] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'message': self.message,
            'severity': self.severity.value,
            'field': self.field,
            'suggestion': self.suggestion,
        }


class ValidationResult:
    """Collection of validation issues"""
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
    
    def add(self, code: str, message: str, severity: Severity, 
            field: str = None, suggestion: str = None):
        self.issues.append(ValidationIssue(
            code=code,
            message=message,
            severity=severity,
            field=field,
            suggestion=suggestion
        ))
    
    def error(self, code: str, message: str, field: str = None, suggestion: str = None):
        self.add(code, message, Severity.ERROR, field, suggestion)
    
    def warning(self, code: str, message: str, field: str = None, suggestion: str = None):
        self.add(code, message, Severity.WARNING, field, suggestion)
    
    def info(self, code: str, message: str, field: str = None, suggestion: str = None):
        self.add(code, message, Severity.INFO, field, suggestion)
    
    @property
    def has_errors(self) -> bool:
        return any(i.severity == Severity.ERROR for i in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        return any(i.severity == Severity.WARNING for i in self.issues)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'valid': not self.has_errors,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'issues': [i.to_dict() for i in self.issues],
        }
    
    def merge(self, other: 'ValidationResult'):
        """Merge another ValidationResult into this one"""
        self.issues.extend(other.issues)


# ============================================
# SEO VALIDATORS
# ============================================

class SEOValidator:
    """SEO validation rules"""
    
    TITLE_MIN = 30
    TITLE_MAX = 60
    TITLE_OPTIMAL_MIN = 50
    TITLE_OPTIMAL_MAX = 60
    
    DESC_MIN = 120
    DESC_MAX = 160
    DESC_OPTIMAL_MIN = 150
    DESC_OPTIMAL_MAX = 160
    
    SLUG_MAX = 75
    
    @classmethod
    def validate_title(cls, title: str, result: ValidationResult):
        """Validate meta title for SEO"""
        if not title:
            result.error('seo_title_missing', 'Meta title is required', 
                        field='meta_title',
                        suggestion='Add a compelling title that includes your main keyword')
            return
        
        length = len(title)
        
        if length < cls.TITLE_MIN:
            result.warning('seo_title_short', 
                          f'Meta title is too short ({length} chars, recommend {cls.TITLE_OPTIMAL_MIN}-{cls.TITLE_OPTIMAL_MAX})',
                          field='meta_title',
                          suggestion='Expand with descriptive keywords')
        elif length > cls.TITLE_MAX:
            result.warning('seo_title_long',
                          f'Meta title may be truncated ({length} chars, max {cls.TITLE_MAX})',
                          field='meta_title',
                          suggestion=f'Shorten to under {cls.TITLE_MAX} characters')
        elif length < cls.TITLE_OPTIMAL_MIN:
            result.info('seo_title_suboptimal',
                       f'Meta title could be longer ({length} chars, optimal {cls.TITLE_OPTIMAL_MIN}-{cls.TITLE_OPTIMAL_MAX})',
                       field='meta_title')
        
        # Check for brand/site name at end (common best practice)
        if ' | ' not in title and ' - ' not in title:
            result.info('seo_title_no_brand',
                       'Consider adding site name to title (e.g., "Title | Brand")',
                       field='meta_title')
    
    @classmethod
    def validate_description(cls, description: str, result: ValidationResult):
        """Validate meta description for SEO"""
        if not description:
            result.error('seo_desc_missing', 'Meta description is required',
                        field='meta_description',
                        suggestion='Write a compelling summary that includes your main keywords')
            return
        
        length = len(description)
        
        if length < cls.DESC_MIN:
            result.warning('seo_desc_short',
                          f'Meta description is too short ({length} chars, recommend {cls.DESC_OPTIMAL_MIN}-{cls.DESC_OPTIMAL_MAX})',
                          field='meta_description',
                          suggestion='Expand to provide more context for search users')
        elif length > cls.DESC_MAX:
            result.warning('seo_desc_long',
                          f'Meta description will be truncated ({length} chars, max {cls.DESC_MAX})',
                          field='meta_description',
                          suggestion=f'Shorten to under {cls.DESC_MAX} characters')
        elif length < cls.DESC_OPTIMAL_MIN:
            result.info('seo_desc_suboptimal',
                       f'Meta description could be longer ({length} chars, optimal {cls.DESC_OPTIMAL_MIN}-{cls.DESC_OPTIMAL_MAX})',
                       field='meta_description')
        
        # Check for call-to-action
        cta_words = ['learn', 'discover', 'find out', 'read', 'get', 'explore']
        if not any(word in description.lower() for word in cta_words):
            result.info('seo_desc_no_cta',
                       'Consider adding a call-to-action to the description',
                       field='meta_description')
    
    @classmethod
    def validate_slug(cls, slug: str, result: ValidationResult):
        """Validate URL slug for SEO"""
        if not slug:
            result.error('seo_slug_missing', 'URL slug is required',
                        field='slug')
            return
        
        if len(slug) > cls.SLUG_MAX:
            result.warning('seo_slug_long',
                          f'URL slug is long ({len(slug)} chars, recommend under {cls.SLUG_MAX})',
                          field='slug',
                          suggestion='Use shorter, keyword-focused slugs')
        
        # Check for stop words
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of']
        slug_words = slug.split('-')
        if any(word in stop_words for word in slug_words):
            result.info('seo_slug_stopwords',
                       'URL contains common stop words that could be removed',
                       field='slug')
        
        # Check for numbers (often indicates date, which can age content)
        if re.search(r'\d{4}', slug):
            result.info('seo_slug_year',
                       'URL contains year - this may make content appear dated',
                       field='slug')
    
    @classmethod
    def validate_canonical(cls, canonical_url: str, current_url: str, result: ValidationResult):
        """Validate canonical URL"""
        if canonical_url:
            # Validate URL format
            try:
                parsed = urlparse(canonical_url)
                if not parsed.scheme or not parsed.netloc:
                    result.error('seo_canonical_invalid',
                                'Canonical URL is not a valid absolute URL',
                                field='canonical_url')
            except Exception:
                result.error('seo_canonical_invalid',
                            'Canonical URL is not valid',
                            field='canonical_url')
        else:
            result.info('seo_canonical_missing',
                       'No canonical URL set (will default to current URL)',
                       field='canonical_url')
    
    @classmethod
    def validate_heading_structure(cls, body_html: str, result: ValidationResult):
        """Validate heading hierarchy"""
        if not body_html:
            return
        
        # Find all headings
        headings = re.findall(r'<h([1-6])[^>]*>.*?</h\1>', body_html, re.IGNORECASE | re.DOTALL)
        
        if not headings:
            result.warning('seo_no_headings',
                          'Content has no headings - add structure for better SEO',
                          field='body_html',
                          suggestion='Use H2 and H3 headings to break up content')
            return
        
        # Count H1s
        h1_count = headings.count('1')
        if h1_count == 0:
            result.info('seo_no_h1', 'No H1 heading in content (title is used instead)')
        elif h1_count > 1:
            result.warning('seo_multiple_h1',
                          f'Multiple H1 headings found ({h1_count}) - use only one',
                          field='body_html',
                          suggestion='Change extra H1s to H2')
        
        # Check for level skipping
        levels = [int(h) for h in headings]
        for i in range(len(levels) - 1):
            if levels[i + 1] > levels[i] + 1:
                result.warning('seo_heading_skip',
                              f'Heading level skipped (H{levels[i]} to H{levels[i + 1]})',
                              field='body_html',
                              suggestion='Maintain proper heading hierarchy')
                break
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> ValidationResult:
        """Run all SEO validations"""
        result = ValidationResult()
        
        cls.validate_title(data.get('meta_title', '') or data.get('title', ''), result)
        cls.validate_description(data.get('meta_description', '') or data.get('excerpt', ''), result)
        cls.validate_slug(data.get('slug', ''), result)
        cls.validate_canonical(data.get('canonical_url', ''), data.get('current_url', ''), result)
        cls.validate_heading_structure(data.get('body_html', ''), result)
        
        return result


# ============================================
# ACCESSIBILITY VALIDATORS
# ============================================

class AccessibilityValidator:
    """WCAG-aligned accessibility validation"""
    
    @classmethod
    def validate_images(cls, body_html: str, featured_image: Any, featured_alt: str, result: ValidationResult):
        """Validate image accessibility"""
        # Featured image
        if featured_image and not featured_alt:
            result.error('a11y_featured_alt_missing',
                        'Featured image is missing alt text',
                        field='image_alt_text',
                        suggestion='Describe the image content for screen reader users')
        elif featured_image and featured_alt:
            if len(featured_alt) < 10:
                result.warning('a11y_featured_alt_short',
                              'Featured image alt text is very short',
                              field='image_alt_text',
                              suggestion='Provide a more descriptive alt text')
            if featured_alt.lower().startswith(('image of', 'picture of', 'photo of')):
                result.info('a11y_featured_alt_redundant',
                           'Alt text starts with "image of" - this is redundant',
                           field='image_alt_text')
        
        # Inline images
        if body_html:
            img_pattern = r'<img[^>]*>'
            images = re.findall(img_pattern, body_html, re.IGNORECASE)
            
            for i, img in enumerate(images):
                # Check for alt attribute
                if 'alt=' not in img.lower():
                    result.error('a11y_inline_alt_missing',
                                f'Image #{i + 1} in content is missing alt attribute',
                                field='body_html')
                elif 'alt=""' in img or "alt=''" in img:
                    # Empty alt is valid for decorative images, but flag it
                    result.info('a11y_inline_alt_empty',
                               f'Image #{i + 1} has empty alt (OK for decorative images)',
                               field='body_html')
    
    @classmethod
    def validate_links(cls, body_html: str, result: ValidationResult):
        """Validate link accessibility"""
        if not body_html:
            return
        
        # Find all links
        link_pattern = r'<a[^>]*>(.*?)</a>'
        links = re.findall(link_pattern, body_html, re.IGNORECASE | re.DOTALL)
        
        for i, link_text in enumerate(links):
            text = strip_tags(link_text).strip()
            
            if not text:
                result.error('a11y_empty_link',
                            f'Empty link found in content',
                            field='body_html',
                            suggestion='Add descriptive link text')
            elif text.lower() in ('click here', 'here', 'read more', 'more', 'link'):
                result.warning('a11y_generic_link',
                              f'Generic link text "{text}" is not descriptive',
                              field='body_html',
                              suggestion='Use descriptive link text that explains the destination')
        
        # Check for JavaScript links
        js_links = re.findall(r'href=["\']javascript:', body_html, re.IGNORECASE)
        if js_links:
            result.error('a11y_js_link',
                        f'{len(js_links)} JavaScript link(s) found',
                        field='body_html',
                        suggestion='Replace JavaScript links with proper URLs or buttons')
    
    @classmethod
    def validate_color_contrast(cls, body_html: str, result: ValidationResult):
        """Check for potential color contrast issues"""
        if not body_html:
            return
        
        # Look for inline color styles
        color_pattern = r'style=["\'][^"\']*color:\s*([^;"\')]+)'
        colors = re.findall(color_pattern, body_html, re.IGNORECASE)
        
        if colors:
            result.info('a11y_inline_colors',
                       f'{len(colors)} inline color style(s) found - verify contrast',
                       field='body_html',
                       suggestion='Ensure sufficient contrast ratio (4.5:1 for normal text)')
    
    @classmethod
    def validate_tables(cls, body_html: str, result: ValidationResult):
        """Validate table accessibility"""
        if not body_html:
            return
        
        # Find tables
        tables = re.findall(r'<table[^>]*>.*?</table>', body_html, re.IGNORECASE | re.DOTALL)
        
        for i, table in enumerate(tables):
            # Check for headers
            if '<th' not in table.lower():
                result.warning('a11y_table_no_headers',
                              f'Table #{i + 1} has no header cells (<th>)',
                              field='body_html',
                              suggestion='Add <th> elements for column/row headers')
            
            # Check for scope attribute on th
            if '<th' in table.lower() and 'scope=' not in table.lower():
                result.info('a11y_table_no_scope',
                           f'Table #{i + 1} headers missing scope attribute',
                           field='body_html')
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> ValidationResult:
        """Run all accessibility validations"""
        result = ValidationResult()
        
        cls.validate_images(
            data.get('body_html', ''),
            data.get('image'),
            data.get('image_alt_text', ''),
            result
        )
        cls.validate_links(data.get('body_html', ''), result)
        cls.validate_color_contrast(data.get('body_html', ''), result)
        cls.validate_tables(data.get('body_html', ''), result)
        
        return result


# ============================================
# CONTENT QUALITY VALIDATORS
# ============================================

class ContentQualityValidator:
    """Content quality validation"""
    
    MIN_WORD_COUNT = 300
    OPTIMAL_WORD_COUNT = 1000
    MAX_WORD_COUNT = 5000
    
    @classmethod
    def validate_length(cls, body_html: str, result: ValidationResult):
        """Validate content length"""
        if not body_html:
            result.error('content_empty', 'Content is empty',
                        field='body_html')
            return
        
        text = strip_tags(body_html)
        word_count = len(text.split())
        
        if word_count < cls.MIN_WORD_COUNT:
            result.warning('content_short',
                          f'Content is short ({word_count} words, recommend {cls.MIN_WORD_COUNT}+)',
                          field='body_html',
                          suggestion='Add more depth and detail to improve value')
        elif word_count > cls.MAX_WORD_COUNT:
            result.info('content_long',
                       f'Content is very long ({word_count} words)',
                       field='body_html',
                       suggestion='Consider breaking into multiple posts')
        elif word_count < cls.OPTIMAL_WORD_COUNT:
            result.info('content_suboptimal',
                       f'Content length is OK but could be expanded ({word_count} words)',
                       field='body_html')
    
    @classmethod
    def validate_structure(cls, toc_json: list, result: ValidationResult):
        """Validate content structure"""
        if not toc_json:
            result.warning('content_no_structure',
                          'Content has no heading structure',
                          suggestion='Add H2/H3 headings to organize content')
        elif len(toc_json) < 2:
            result.info('content_minimal_structure',
                       'Content has minimal structure (only 1 section)',
                       suggestion='Consider adding more sections')
    
    @classmethod
    def validate_excerpt(cls, excerpt: str, result: ValidationResult):
        """Validate excerpt"""
        if not excerpt:
            result.error('content_no_excerpt', 'Excerpt is required',
                        field='excerpt',
                        suggestion='Write a compelling summary for listings and social shares')
        elif len(excerpt) < 100:
            result.warning('content_excerpt_short',
                          f'Excerpt is short ({len(excerpt)} chars)',
                          field='excerpt',
                          suggestion='Expand to 150-200 characters for optimal display')
    
    @classmethod
    def validate_takeaways(cls, takeaways: list, result: ValidationResult):
        """Validate key takeaways"""
        if not takeaways:
            result.info('content_no_takeaways',
                       'No key takeaways extracted',
                       field='key_takeaways',
                       suggestion='Add a "Key Takeaways" section or bullet points')
        elif len(takeaways) < 3:
            result.info('content_few_takeaways',
                       f'Only {len(takeaways)} takeaway(s) - recommend 3-7',
                       field='key_takeaways')
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> ValidationResult:
        """Run all content quality validations"""
        result = ValidationResult()
        
        cls.validate_length(data.get('body_html', ''), result)
        cls.validate_structure(data.get('toc_json', []), result)
        cls.validate_excerpt(data.get('excerpt', ''), result)
        cls.validate_takeaways(data.get('key_takeaways', []), result)
        
        return result


# ============================================
# GOVERNANCE VALIDATORS
# ============================================

class GovernanceValidator:
    """Governance and compliance validation"""
    
    REQUIRED_FIELDS = [
        ('title', 'Title'),
        ('slug', 'URL Slug'),
        ('body_html', 'Content'),
        ('excerpt', 'Excerpt'),
        ('author_entity', 'Author'),
        ('category_new', 'Category'),
    ]
    
    @classmethod
    def validate_required_fields(cls, data: Dict[str, Any], result: ValidationResult):
        """Check required fields for publishing"""
        for field_name, display_name in cls.REQUIRED_FIELDS:
            if not data.get(field_name):
                result.error(f'gov_missing_{field_name}',
                            f'{display_name} is required for publishing',
                            field=field_name)
    
    @classmethod
    def validate_featured_image(cls, image: Any, alt_text: str, result: ValidationResult):
        """Validate featured image requirements"""
        if not image:
            result.warning('gov_no_image',
                          'No featured image set',
                          field='image',
                          suggestion='Add a featured image for better social sharing')
        elif not alt_text:
            result.error('gov_image_no_alt',
                        'Featured image requires alt text',
                        field='image_alt_text')
    
    @classmethod
    def validate_compliance(cls, requires_review: bool, reviewed_at: Any, reviewer: Any, result: ValidationResult):
        """Validate compliance requirements"""
        if requires_review:
            if not reviewed_at or not reviewer:
                result.error('gov_needs_review',
                            'This post requires compliance review before publishing',
                            field='requires_compliance_review',
                            suggestion='Submit for review before publishing')
    
    @classmethod
    def validate_dates(cls, publish_date: Any, status: str, result: ValidationResult):
        """Validate date logic"""
        from django.utils import timezone
        
        if status == 'scheduled' and not publish_date:
            result.error('gov_scheduled_no_date',
                        'Scheduled posts require a publish date',
                        field='publish_date')
        elif status == 'scheduled' and publish_date:
            if publish_date <= timezone.now():
                result.warning('gov_scheduled_past',
                              'Scheduled date is in the past',
                              field='publish_date',
                              suggestion='Update to a future date or change status to Published')
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> ValidationResult:
        """Run all governance validations"""
        result = ValidationResult()
        
        cls.validate_required_fields(data, result)
        cls.validate_featured_image(data.get('image'), data.get('image_alt_text', ''), result)
        cls.validate_compliance(
            data.get('requires_compliance_review', False),
            data.get('reviewed_at'),
            data.get('reviewer'),
            result
        )
        cls.validate_dates(data.get('publish_date'), data.get('status', ''), result)
        
        return result


# ============================================
# MASTER VALIDATOR
# ============================================

class BlogValidator:
    """
    Master validator that runs all validation checks.
    """
    
    @classmethod
    def validate_for_save(cls, data: Dict[str, Any]) -> ValidationResult:
        """Run validations appropriate for save (non-blocking)"""
        result = ValidationResult()
        
        # Run all validators but demote errors to warnings for save
        seo = SEOValidator.validate(data)
        a11y = AccessibilityValidator.validate(data)
        content = ContentQualityValidator.validate(data)
        
        result.merge(seo)
        result.merge(a11y)
        result.merge(content)
        
        return result
    
    @classmethod
    def validate_for_publish(cls, data: Dict[str, Any]) -> ValidationResult:
        """Run all validations for publish (blocking)"""
        result = ValidationResult()
        
        # Run all validators
        seo = SEOValidator.validate(data)
        a11y = AccessibilityValidator.validate(data)
        content = ContentQualityValidator.validate(data)
        governance = GovernanceValidator.validate(data)
        
        result.merge(seo)
        result.merge(a11y)
        result.merge(content)
        result.merge(governance)
        
        return result
    
    @classmethod
    def get_lint_summary(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary for admin display"""
        result = cls.validate_for_save(data)
        
        return {
            'valid': not result.has_errors,
            'score': cls._calculate_score(result),
            'error_count': len(result.errors),
            'warning_count': len(result.warnings),
            'top_issues': [i.to_dict() for i in result.issues[:5]],
        }
    
    @classmethod
    def _calculate_score(cls, result: ValidationResult) -> int:
        """Calculate a simple quality score 0-100"""
        score = 100
        
        for issue in result.issues:
            if issue.severity == Severity.ERROR:
                score -= 15
            elif issue.severity == Severity.WARNING:
                score -= 5
            elif issue.severity == Severity.INFO:
                score -= 1
        
        return max(0, min(100, score))
