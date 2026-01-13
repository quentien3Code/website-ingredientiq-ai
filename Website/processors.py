"""
Brita Filter CMS - Content Processing Pipeline

This module implements a multi-stage filtration pipeline that transforms
raw markdown drafts into structured, SEO-optimized, publish-ready content.

Filter 0: Raw Input (what humans write)
Filter 1: Structural Normalization (auto-parse)
Filter 2: Metadata Distillation (auto-generate with overrides)
Filter 3: SEO Pack (auto-generate)
Filter 4: SMO Pack (auto-generate)
Filter 5: LLM Surface Readiness (auto-generate)
Filter 6: Governance & Workflow (validation gates)
"""

import re
import json
import math
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from django.utils.text import slugify
from django.utils import timezone
from django.utils.html import strip_tags
import bleach


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class HeadingNode:
    """Represents a heading in the TOC"""
    level: int
    text: str
    slug: str
    children: List['HeadingNode'] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'level': self.level,
            'text': self.text,
            'slug': self.slug,
            'children': [c.to_dict() for c in self.children]
        }


@dataclass
class ExtractedSection:
    """A content section extracted from the draft"""
    heading: str
    heading_level: int
    content: str
    section_type: str  # 'intro', 'body', 'faq', 'list', 'quote', 'conclusion'


@dataclass 
class ExtractedFAQ:
    """An FAQ item extracted from content"""
    question: str
    answer: str


@dataclass
class ContentEntity:
    """Named entity extracted from content"""
    text: str
    entity_type: str  # 'person', 'org', 'location', 'concept', 'product'
    confidence: float = 1.0


@dataclass
class ProcessedContent:
    """Complete output of the content processing pipeline"""
    # Filter 1 outputs
    body_html: str = ""
    toc_json: List[Dict] = field(default_factory=list)
    key_sections_json: List[Dict] = field(default_factory=list)
    intro_text: str = ""
    
    # Filter 2 outputs
    auto_title: str = ""
    auto_slug: str = ""
    auto_excerpt: str = ""
    auto_key_takeaways: List[str] = field(default_factory=list)
    auto_reading_time: int = 1
    auto_word_count: int = 0
    entities_json: List[Dict] = field(default_factory=list)
    extracted_faqs: List[Dict] = field(default_factory=list)
    
    # Filter 3 outputs
    auto_meta_title: str = ""
    auto_meta_description: str = ""
    
    # Filter 4 outputs  
    auto_social_copy_linkedin: str = ""
    auto_social_copy_twitter: str = ""
    auto_social_hashtags: List[str] = field(default_factory=list)
    
    # Filter 5 outputs
    auto_summary_for_llms: str = ""
    auto_key_facts: List[str] = field(default_factory=list)
    auto_sources_json: List[Dict] = field(default_factory=list)  # Auto-extracted sources
    
    # Validation results
    validation_warnings: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)


# ============================================
# FILTER 0: INPUT SANITIZATION
# ============================================

class Filter0RawInput:
    """
    Filter 0 - Raw Input Sanitization
    Cleans and normalizes the raw markdown input.
    """
    
    # Allowed HTML tags after markdown conversion
    ALLOWED_TAGS = [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'strong', 'em', 'b', 'i', 'u', 's', 'del', 'ins',
        'a', 'img', 'br', 'hr',
        'ul', 'ol', 'li',
        'blockquote', 'pre', 'code',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'figure', 'figcaption',
        'div', 'span',
        'sup', 'sub',
    ]
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title', 'rel', 'target'],
        'img': ['src', 'alt', 'title', 'width', 'height', 'loading'],
        'td': ['colspan', 'rowspan'],
        'th': ['colspan', 'rowspan', 'scope'],
        '*': ['class', 'id'],
    }
    
    @classmethod
    def normalize_whitespace(cls, text: str) -> str:
        """Normalize whitespace and line endings"""
        # Normalize line endings to Unix style
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Remove trailing whitespace from lines
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        # Collapse multiple blank lines to max 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    @classmethod
    def normalize_punctuation(cls, text: str) -> str:
        """Normalize typography and punctuation"""
        # Smart quotes to straight
        replacements = [
            ('"', '"'), ('"', '"'),
            (''', "'"), (''', "'"),
            ('–', '-'), ('—', '-'),
            ('…', '...'),
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text
    
    @classmethod
    def sanitize_html(cls, html: str) -> str:
        """Sanitize HTML output using bleach"""
        return bleach.clean(
            html,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @classmethod
    def process(cls, raw_draft: str) -> str:
        """Main entry point for Filter 0"""
        if not raw_draft:
            return ""
        text = cls.normalize_whitespace(raw_draft)
        text = cls.normalize_punctuation(text)
        return text


# ============================================
# FILTER 1: STRUCTURAL NORMALIZATION
# ============================================

class Filter1StructuralNormalization:
    """
    Filter 1 - Structural Normalization
    Parses markdown and extracts document structure.
    """
    
    @classmethod
    def markdown_to_html(cls, markdown_text: str) -> str:
        """
        Convert markdown to HTML.
        Uses a simple regex-based approach for portability.
        For production, consider using markdown or mistune library.
        """
        html = markdown_text
        
        # Escape HTML entities first (but preserve markdown syntax)
        # Only escape < and > that aren't part of existing HTML or markdown
        
        # Headers (must be at line start)
        html = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
        html = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Bold and italic (order matters)
        html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'___(.+?)___', r'<strong><em>\1</em></strong>', html)
        html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
        html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)
        
        # Strikethrough
        html = re.sub(r'~~(.+?)~~', r'<del>\1</del>', html)
        
        # Inline code
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        # Links and images
        html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" loading="lazy">', html)
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Blockquotes (handle multi-line)
        lines = html.split('\n')
        in_blockquote = False
        result_lines = []
        for line in lines:
            if line.startswith('> '):
                if not in_blockquote:
                    result_lines.append('<blockquote>')
                    in_blockquote = True
                result_lines.append(line[2:])
            else:
                if in_blockquote:
                    result_lines.append('</blockquote>')
                    in_blockquote = False
                result_lines.append(line)
        if in_blockquote:
            result_lines.append('</blockquote>')
        html = '\n'.join(result_lines)
        
        # Unordered lists
        html = re.sub(r'^[\*\-\+] (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.+</li>\n?)+', lambda m: '<ul>\n' + m.group(0) + '</ul>\n', html)
        
        # Ordered lists
        html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        # Horizontal rules
        html = re.sub(r'^---+$', r'<hr>', html, flags=re.MULTILINE)
        html = re.sub(r'^\*\*\*+$', r'<hr>', html, flags=re.MULTILINE)
        
        # Paragraphs - wrap non-tag lines
        lines = html.split('\n\n')
        wrapped = []
        block_tags = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 
                      'blockquote', 'pre', 'hr', 'table', 'div', 'figure')
        for block in lines:
            block = block.strip()
            if block and not any(block.startswith(f'<{tag}') for tag in block_tags):
                if not block.startswith('<'):
                    block = f'<p>{block}</p>'
            wrapped.append(block)
        html = '\n\n'.join(wrapped)
        
        # Clean up extra newlines within paragraphs
        html = re.sub(r'<p>(.+?)\n(.+?)</p>', r'<p>\1 \2</p>', html, flags=re.DOTALL)
        
        return html
    
    @classmethod
    def extract_headings(cls, html: str) -> List[HeadingNode]:
        """Extract heading structure for TOC generation"""
        pattern = r'<h([1-6])(?:\s[^>]*)?>(.*?)</h\1>'
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
        
        headings = []
        for level_str, text in matches:
            level = int(level_str)
            text = strip_tags(text).strip()
            slug = slugify(text)
            headings.append(HeadingNode(level=level, text=text, slug=slug))
        
        return headings
    
    @classmethod
    def build_toc_tree(cls, headings: List[HeadingNode]) -> List[HeadingNode]:
        """Build hierarchical TOC from flat heading list"""
        if not headings:
            return []
        
        root = []
        stack = [(0, root)]  # (level, children_list)
        
        for heading in headings:
            # Pop stack until we find a parent with lower level
            while stack and stack[-1][0] >= heading.level:
                stack.pop()
            
            if stack:
                stack[-1][1].append(heading)
            else:
                root.append(heading)
            
            stack.append((heading.level, heading.children))
        
        return root
    
    @classmethod
    def enforce_heading_hierarchy(cls, html: str) -> str:
        """
        Enforce proper heading hierarchy:
        - Only one H1 (demote extras to H2)
        - No skipped levels (H1 -> H3 becomes H1 -> H2)
        """
        pattern = r'<h([1-6])(\s[^>]*)?>(.*?)</h\1>'
        matches = list(re.finditer(pattern, html, re.IGNORECASE | re.DOTALL))
        
        if not matches:
            return html
        
        h1_count = 0
        last_level = 0
        replacements = []
        
        for match in matches:
            original_level = int(match.group(1))
            attrs = match.group(2) or ''
            content = match.group(3)
            
            new_level = original_level
            
            # Only one H1 allowed
            if original_level == 1:
                h1_count += 1
                if h1_count > 1:
                    new_level = 2
            
            # Don't skip levels (max +1 from last)
            if last_level > 0 and new_level > last_level + 1:
                new_level = last_level + 1
            
            last_level = new_level
            
            if new_level != original_level:
                old = match.group(0)
                new = f'<h{new_level}{attrs}>{content}</h{new_level}>'
                replacements.append((old, new))
        
        for old, new in replacements:
            html = html.replace(old, new, 1)
        
        return html
    
    @classmethod
    def extract_intro(cls, html: str) -> str:
        """Extract intro text (content before first H2)"""
        # Find first H2 or H3
        match = re.search(r'<h[23][^>]*>', html, re.IGNORECASE)
        if match:
            intro_html = html[:match.start()]
        else:
            # No subheadings, take first paragraph
            match = re.search(r'<p>(.*?)</p>', html, re.DOTALL)
            intro_html = match.group(1) if match else html[:500]
        
        return strip_tags(intro_html).strip()
    
    @classmethod
    def extract_pull_quotes(cls, html: str) -> List[str]:
        """Extract blockquote content as pull quotes"""
        pattern = r'<blockquote>(.*?)</blockquote>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        return [strip_tags(q).strip() for q in matches if strip_tags(q).strip()]
    
    @classmethod
    def extract_sections(cls, html: str) -> List[ExtractedSection]:
        """Extract content sections based on headings"""
        # Split by headings
        pattern = r'(<h([1-6])[^>]*>(.*?)</h\2>)'
        parts = re.split(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        
        sections = []
        current_heading = "Introduction"
        current_level = 1
        current_content = []
        
        i = 0
        while i < len(parts):
            part = parts[i]
            
            # Check if this is a heading match
            if re.match(r'<h[1-6]', part, re.IGNORECASE):
                # Ensure we have enough parts for heading (need i+1 for level, i+2 for text)
                if i + 2 >= len(parts):
                    # Not enough parts, treat as content
                    current_content.append(part)
                    i += 1
                    continue
                
                # Save previous section
                if current_content or not sections:
                    section_type = 'intro' if not sections else 'body'
                    content = ''.join(current_content).strip()
                    if content:
                        sections.append(ExtractedSection(
                            heading=current_heading,
                            heading_level=current_level,
                            content=content,
                            section_type=section_type
                        ))
                
                # Parse new heading - verify we have valid level
                try:
                    level = int(parts[i + 1])
                except (ValueError, TypeError):
                    # Invalid level, skip this heading
                    current_content.append(part)
                    i += 1
                    continue
                    
                heading_text = strip_tags(parts[i + 2]).strip()
                current_heading = heading_text
                current_level = level
                current_content = []
                i += 4  # Skip heading parts
            else:
                current_content.append(part)
                i += 1
        
        # Add final section
        if current_content:
            content = ''.join(current_content).strip()
            if content:
                sections.append(ExtractedSection(
                    heading=current_heading,
                    heading_level=current_level,
                    content=content,
                    section_type='body'
                ))
        
        return sections
    
    @classmethod
    def extract_faqs(cls, html: str, sections: List[ExtractedSection]) -> List[ExtractedFAQ]:
        """
        Extract FAQ items from content.
        Detects FAQ sections and Q&A patterns.
        """
        faqs = []
        
        # Look for FAQ sections
        faq_section = None
        for section in sections:
            heading_lower = section.heading.lower()
            if any(term in heading_lower for term in ['faq', 'frequently asked', 'questions']):
                faq_section = section
                break
        
        if faq_section:
            # Extract Q&A from FAQ section
            # Pattern: **Q:** text or ### Question format
            content = faq_section.content
            
            # Pattern 1: Bold Q&A
            qa_pattern = r'\*\*(?:Q:|Question:?)\*\*\s*(.+?)(?:\*\*(?:A:|Answer:?)\*\*\s*(.+?))?(?=\*\*(?:Q:|Question:?)\*\*|$)'
            matches = re.findall(qa_pattern, content, re.DOTALL | re.IGNORECASE)
            for q, a in matches:
                if q.strip():
                    faqs.append(ExtractedFAQ(
                        question=strip_tags(q).strip(),
                        answer=strip_tags(a).strip() if a else ""
                    ))
        
        # Also look for any content with question marks followed by answers
        question_pattern = r'(?:^|\n)\s*(?:\*\*)?([^*\n]+\?)\s*(?:\*\*)?\s*\n+([^\n*#]+(?:\n(?![#*\-\d])[^\n]+)*)'
        matches = re.findall(question_pattern, html, re.MULTILINE)
        for q, a in matches:
            q = strip_tags(q).strip()
            a = strip_tags(a).strip()
            if q and a and len(q) < 200 and len(a) > 20:
                # Check not already added
                if not any(faq.question == q for faq in faqs):
                    faqs.append(ExtractedFAQ(question=q, answer=a))
        
        return faqs[:10]  # Max 10 FAQs
    
    @classmethod
    def add_heading_ids(cls, html: str) -> str:
        """Add id attributes to headings for anchor links"""
        def replace_heading(match):
            full = match.group(0)
            level = match.group(1)
            attrs = match.group(2) or ''
            content = match.group(3)
            
            # Check if id already exists
            if 'id=' in attrs:
                return full
            
            slug = slugify(strip_tags(content))
            return f'<h{level} id="{slug}"{attrs}>{content}</h{level}>'
        
        pattern = r'<h([1-6])(\s[^>]*)?>(.*?)</h\1>'
        return re.sub(pattern, replace_heading, html, flags=re.IGNORECASE | re.DOTALL)
    
    @classmethod
    def process(cls, sanitized_text: str) -> Tuple[str, List[Dict], List[Dict], str, List[ExtractedFAQ]]:
        """
        Main entry point for Filter 1.
        Returns: (body_html, toc_json, key_sections_json, intro_text, faqs)
        """
        if not sanitized_text:
            return "", [], [], "", []
        
        # Convert markdown to HTML
        html = cls.markdown_to_html(sanitized_text)
        
        # Enforce heading hierarchy
        html = cls.enforce_heading_hierarchy(html)
        
        # Add heading IDs for anchor links
        html = cls.add_heading_ids(html)
        
        # Extract structure
        headings = cls.extract_headings(html)
        toc_tree = cls.build_toc_tree(headings)
        toc_json = [h.to_dict() for h in toc_tree]
        
        # Extract sections
        sections = cls.extract_sections(html)
        sections_json = [
            {
                'heading': s.heading,
                'level': s.heading_level,
                'type': s.section_type,
                'preview': strip_tags(s.content)[:200]
            }
            for s in sections
        ]
        
        # Extract intro
        intro = cls.extract_intro(html)
        
        # Extract FAQs
        faqs = cls.extract_faqs(html, sections)
        
        # Sanitize final output
        html = Filter0RawInput.sanitize_html(html)
        
        return html, toc_json, sections_json, intro, faqs


# ============================================
# FILTER 2: METADATA DISTILLATION
# ============================================

class Filter2MetadataDistillation:
    """
    Filter 2 - Metadata Distillation
    Auto-generates high-signal summaries and entities from content.
    """
    
    EXCERPT_TARGET_LENGTH = 160  # 155-180 chars
    TAKEAWAYS_MIN = 3
    TAKEAWAYS_MAX = 7
    
    @classmethod
    def generate_title(cls, html: str, raw_text: str) -> str:
        """Generate title from first H1 or first sentence"""
        # Try H1 first
        match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return strip_tags(match.group(1)).strip()[:255]
        
        # Fallback to first sentence
        text = strip_tags(raw_text).strip()
        sentences = re.split(r'[.!?]', text)
        if sentences:
            return sentences[0].strip()[:255]
        
        return text[:100]
    
    @classmethod
    def generate_slug(cls, title: str) -> str:
        """Generate URL-safe slug from title"""
        return slugify(title)[:255]
    
    @classmethod
    def generate_excerpt(cls, intro: str, body_html: str) -> str:
        """Generate excerpt targeting 155-180 chars"""
        # Use intro if available
        text = intro or strip_tags(body_html)
        text = text.strip()
        
        if len(text) <= cls.EXCERPT_TARGET_LENGTH:
            return text
        
        # Truncate at sentence boundary near target length
        sentences = re.split(r'([.!?])', text)
        excerpt = ""
        for i in range(0, len(sentences) - 1, 2):
            candidate = excerpt + sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
            if len(candidate) > cls.EXCERPT_TARGET_LENGTH + 20:
                break
            excerpt = candidate
        
        if not excerpt or len(excerpt) < 50:
            # Fallback: truncate at word boundary
            excerpt = text[:cls.EXCERPT_TARGET_LENGTH]
            last_space = excerpt.rfind(' ')
            if last_space > 100:
                excerpt = excerpt[:last_space] + "..."
        
        return excerpt.strip()
    
    @classmethod
    def extract_key_takeaways(cls, sections: List[Dict], body_html: str) -> List[str]:
        """
        Extract key takeaways from content.
        Looks for bullet points, numbered lists, and conclusion sections.
        """
        takeaways = []
        text = strip_tags(body_html)
        
        # Look for explicit takeaways/summary section
        for section in sections:
            heading = section.get('heading', '').lower()
            if any(term in heading for term in ['takeaway', 'summary', 'conclusion', 'key point', 'tl;dr']):
                # Extract list items from this section
                preview = section.get('preview', '')
                # Try to parse as list
                items = re.findall(r'(?:^|\n)\s*[\-\*•]\s*(.+?)(?=\n|$)', preview)
                takeaways.extend(items[:cls.TAKEAWAYS_MAX])
        
        # If not enough, extract from bullet lists anywhere
        if len(takeaways) < cls.TAKEAWAYS_MIN:
            list_items = re.findall(r'<li>(.*?)</li>', body_html, re.IGNORECASE | re.DOTALL)
            for item in list_items:
                item_text = strip_tags(item).strip()
                if 20 < len(item_text) < 200 and item_text not in takeaways:
                    takeaways.append(item_text)
                    if len(takeaways) >= cls.TAKEAWAYS_MAX:
                        break
        
        # If still not enough, extract key sentences
        if len(takeaways) < cls.TAKEAWAYS_MIN:
            sentences = re.split(r'[.!?]', text)
            # Prefer sentences with signal words
            signal_words = ['important', 'key', 'essential', 'must', 'should', 'recommend', 
                           'benefit', 'advantage', 'critical', 'significant']
            scored = []
            for sent in sentences:
                sent = sent.strip()
                if 30 < len(sent) < 200:
                    score = sum(1 for word in signal_words if word in sent.lower())
                    scored.append((score, sent))
            scored.sort(reverse=True)
            for score, sent in scored:
                if sent not in takeaways:
                    takeaways.append(sent)
                    if len(takeaways) >= cls.TAKEAWAYS_MAX:
                        break
        
        return takeaways[:cls.TAKEAWAYS_MAX]
    
    @classmethod
    def calculate_reading_time(cls, text: str) -> Tuple[int, int]:
        """Calculate reading time and word count (200 wpm average)"""
        words = text.split()
        word_count = len(words)
        minutes = max(1, math.ceil(word_count / 200))
        return minutes, word_count
    
    @classmethod
    def extract_entities(cls, text: str) -> List[ContentEntity]:
        """
        Extract named entities from content.
        Uses pattern-based extraction (no ML required).
        """
        entities = []
        
        # Capitalized phrases (potential names/orgs)
        cap_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        for match in re.finditer(cap_pattern, text):
            entity_text = match.group(1)
            # Guess type based on context
            if any(title in entity_text for title in ['Dr.', 'Mr.', 'Ms.', 'Prof.']):
                entity_type = 'person'
            elif any(suffix in entity_text for suffix in ['Inc', 'Corp', 'LLC', 'Ltd', 'Company']):
                entity_type = 'org'
            else:
                entity_type = 'concept'
            entities.append(ContentEntity(text=entity_text, entity_type=entity_type))
        
        # Location patterns
        location_pattern = r'\b(?:in|at|from|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        for match in re.finditer(location_pattern, text):
            entities.append(ContentEntity(text=match.group(1), entity_type='location'))
        
        # Product/brand patterns (words in quotes or with ®™)
        product_pattern = r'"([^"]+)"|\b(\w+[®™])'
        for match in re.finditer(product_pattern, text):
            product = match.group(1) or match.group(2)
            entities.append(ContentEntity(text=product, entity_type='product'))
        
        # Deduplicate
        seen = set()
        unique = []
        for e in entities:
            key = (e.text.lower(), e.entity_type)
            if key not in seen:
                seen.add(key)
                unique.append(e)
        
        return unique[:50]  # Max 50 entities
    
    @classmethod
    def suggest_tags(cls, text: str, entities: List[ContentEntity]) -> List[str]:
        """Suggest tags based on content analysis"""
        tags = set()
        text_lower = text.lower()
        
        # Add entity-based tags (concepts and products)
        for entity in entities:
            if entity.entity_type in ('concept', 'product'):
                tag = slugify(entity.text)
                if 3 <= len(tag) <= 30:
                    tags.add(entity.text)
        
        # Common topic detection
        topic_keywords = {
            'nutrition': ['nutrition', 'nutrient', 'vitamin', 'mineral', 'diet', 'calorie'],
            'health': ['health', 'healthy', 'wellness', 'medical', 'doctor'],
            'food': ['food', 'ingredient', 'recipe', 'cooking', 'meal'],
            'safety': ['safety', 'safe', 'dangerous', 'risk', 'warning'],
            'science': ['research', 'study', 'scientist', 'evidence', 'clinical'],
            'tips': ['tip', 'advice', 'guide', 'how to', 'step'],
            'review': ['review', 'comparison', 'best', 'top', 'recommend'],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                tags.add(topic)
        
        return list(tags)[:8]  # Max 8 tags
    
    @classmethod
    def process(cls, body_html: str, intro: str, sections: List[Dict], raw_text: str) -> Dict[str, Any]:
        """Main entry point for Filter 2"""
        plain_text = strip_tags(body_html)
        
        title = cls.generate_title(body_html, raw_text)
        excerpt = cls.generate_excerpt(intro, body_html)
        takeaways = cls.extract_key_takeaways(sections, body_html)
        reading_time, word_count = cls.calculate_reading_time(plain_text)
        entities = cls.extract_entities(plain_text)
        tags = cls.suggest_tags(plain_text, entities)
        
        return {
            'auto_title': title,
            'auto_slug': cls.generate_slug(title),
            'auto_excerpt': excerpt,
            'auto_key_takeaways': takeaways,
            'auto_reading_time': reading_time,
            'auto_word_count': word_count,
            'entities_json': [{'text': e.text, 'type': e.entity_type} for e in entities],
            'suggested_tags': tags,
        }


# ============================================
# FILTER 3: SEO PACK
# ============================================

class Filter3SEOPack:
    """
    Filter 3 - SEO/Discoverability Pack
    Generates publisher metadata suite.
    """
    
    META_TITLE_MAX = 60
    META_DESC_MAX = 160
    
    @classmethod
    def generate_meta_title(cls, title: str, site_name: str = "") -> str:
        """Generate SEO title (<= 60 chars)"""
        if len(title) <= cls.META_TITLE_MAX:
            return title
        
        # Truncate at word boundary
        truncated = title[:cls.META_TITLE_MAX - 3]
        last_space = truncated.rfind(' ')
        if last_space > 30:
            truncated = truncated[:last_space]
        
        return truncated.strip() + "..."
    
    @classmethod
    def generate_meta_description(cls, excerpt: str) -> str:
        """Generate meta description (<= 160 chars)"""
        if len(excerpt) <= cls.META_DESC_MAX:
            return excerpt
        
        truncated = excerpt[:cls.META_DESC_MAX - 3]
        last_space = truncated.rfind(' ')
        if last_space > 100:
            truncated = truncated[:last_space]
        
        return truncated.strip() + "..."
    
    @classmethod
    def validate_seo(cls, data: Dict) -> List[str]:
        """Run SEO validation checks"""
        warnings = []
        
        title = data.get('meta_title', '') or data.get('title', '')
        desc = data.get('meta_description', '') or data.get('excerpt', '')
        
        if len(title) < 30:
            warnings.append(f"Meta title too short ({len(title)} chars, recommend 50-60)")
        elif len(title) > 60:
            warnings.append(f"Meta title too long ({len(title)} chars, max 60)")
        
        if len(desc) < 100:
            warnings.append(f"Meta description too short ({len(desc)} chars, recommend 150-160)")
        elif len(desc) > 160:
            warnings.append(f"Meta description too long ({len(desc)} chars, max 160)")
        
        if not data.get('canonical_url'):
            warnings.append("Missing canonical URL (will default to current URL)")
        
        return warnings
    
    @classmethod
    def process(cls, title: str, excerpt: str, site_name: str = "") -> Dict[str, str]:
        """Main entry point for Filter 3"""
        return {
            'auto_meta_title': cls.generate_meta_title(title, site_name),
            'auto_meta_description': cls.generate_meta_description(excerpt),
        }


# ============================================
# FILTER 4: SMO (SOCIAL MEDIA OPTIMIZATION) PACK
# ============================================

class Filter4SMOPack:
    """
    Filter 4 - Social Media Optimization Pack
    Generates social-ready content and previews.
    """
    
    LINKEDIN_MAX = 700
    TWITTER_MAX = 280
    
    @classmethod
    def generate_linkedin_copy(cls, title: str, excerpt: str, takeaways: List[str]) -> str:
        """Generate LinkedIn post copy (1-2 paragraphs)"""
        parts = [f"📝 {title}", ""]
        
        if excerpt:
            parts.append(excerpt)
            parts.append("")
        
        if takeaways:
            parts.append("Key insights:")
            for i, takeaway in enumerate(takeaways[:3], 1):
                parts.append(f"→ {takeaway}")
        
        copy = "\n".join(parts)
        if len(copy) > cls.LINKEDIN_MAX:
            copy = copy[:cls.LINKEDIN_MAX - 3] + "..."
        
        return copy
    
    @classmethod
    def generate_twitter_copy(cls, title: str, excerpt: str) -> str:
        """Generate Twitter/X post copy (<= 280 chars)"""
        # Leave room for link (~23 chars) and hashtags
        max_text = cls.TWITTER_MAX - 30
        
        copy = title
        if len(copy) < max_text - 50 and excerpt:
            remaining = max_text - len(copy) - 3
            if remaining > 30:
                excerpt_short = excerpt[:remaining]
                last_space = excerpt_short.rfind(' ')
                if last_space > 20:
                    excerpt_short = excerpt_short[:last_space]
                copy = f"{copy} — {excerpt_short}"
        
        if len(copy) > max_text:
            copy = copy[:max_text - 3] + "..."
        
        return copy
    
    @classmethod
    def generate_hashtags(cls, tags: List[str], title: str) -> List[str]:
        """Generate 3-8 hashtags from tags and title"""
        hashtags = []
        
        # Convert tags to hashtags
        for tag in tags[:5]:
            hashtag = re.sub(r'[^a-zA-Z0-9]', '', tag.title())
            if 3 <= len(hashtag) <= 20:
                hashtags.append(f"#{hashtag}")
        
        # Add generic hashtags if needed
        if len(hashtags) < 3:
            generic = ['#ContentMarketing', '#BlogPost', '#MustRead', '#Insights']
            for g in generic:
                if g not in hashtags:
                    hashtags.append(g)
                    if len(hashtags) >= 5:
                        break
        
        return hashtags[:8]
    
    @classmethod
    def process(cls, title: str, excerpt: str, takeaways: List[str], tags: List[str]) -> Dict[str, Any]:
        """Main entry point for Filter 4"""
        return {
            'auto_social_copy_linkedin': cls.generate_linkedin_copy(title, excerpt, takeaways),
            'auto_social_copy_twitter': cls.generate_twitter_copy(title, excerpt),
            'auto_social_hashtags': cls.generate_hashtags(tags, title),
        }


# ============================================
# FILTER 5: LLM SURFACE READINESS
# ============================================

class Filter5LLMReadiness:
    """
    Filter 5 - LLM Surface Readiness
    Makes content easy to ingest, cite, and trust by LLMs.
    Auto-extracts sources, generates summaries, and key facts.
    """
    
    SUMMARY_MIN = 80
    SUMMARY_MAX = 120
    SITE_URL = 'https://ingredientiq.ai'
    SITE_NAME = 'IngredientIQ'
    
    @classmethod
    def generate_summary_for_llms(cls, title: str, excerpt: str, takeaways: List[str]) -> str:
        """
        Generate tight, factual summary (80-120 words) optimized for LLM consumption.
        """
        parts = [f"This article about '{title}' explains:"]
        
        if takeaways:
            for takeaway in takeaways[:4]:
                parts.append(f"- {takeaway}")
        elif excerpt:
            parts.append(excerpt)
        
        summary = " ".join(parts)
        words = summary.split()
        
        if len(words) > cls.SUMMARY_MAX:
            summary = " ".join(words[:cls.SUMMARY_MAX])
            if not summary.endswith('.'):
                summary += "."
        
        return summary
    
    @classmethod
    def extract_key_facts(cls, body_html: str, entities: List[Dict]) -> List[str]:
        """
        Extract verifiable facts/claims from content.
        Useful for high-risk or policy content.
        """
        facts = []
        text = strip_tags(body_html)
        
        # Look for sentences with numbers/statistics
        stat_pattern = r'[^.!?]*\b\d+(?:\.\d+)?(?:\s*(?:%|percent|million|billion|thousand))?[^.!?]*[.!?]'
        matches = re.findall(stat_pattern, text, re.IGNORECASE)
        for match in matches[:5]:
            fact = match.strip()
            if 20 < len(fact) < 200:
                facts.append(fact)
        
        # Look for definitive statements
        definitive_patterns = [
            r'[^.!?]*\b(?:is|are|was|were)\s+(?:the|a)\s+[^.!?]+[.!?]',
            r'[^.!?]*\b(?:studies?\s+show|research\s+(?:indicates?|shows?)|according\s+to)[^.!?]+[.!?]',
        ]
        for pattern in definitive_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:3]:
                fact = match.strip()
                if 20 < len(fact) < 200 and fact not in facts:
                    facts.append(fact)
        
        return facts[:10]
    
    @classmethod
    def extract_sources_from_content(
        cls, 
        body_html: str, 
        title: str, 
        slug: str,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """
        Auto-extract sources/links from blog content.
        Also adds:
        - Link to this blog post itself
        - Link to IngredientIQ homepage
        - Category of the blog
        
        Returns list of source dicts: {url, label, type, accessed_date, category}
        """
        from datetime import date
        sources = []
        seen_urls = set()
        today = date.today().isoformat()
        
        # Extract all links from HTML content
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        matches = re.findall(link_pattern, body_html, re.IGNORECASE)
        
        for url, label in matches:
            # Skip internal anchors and javascript
            if url.startswith('#') or url.startswith('javascript:'):
                continue
            # Skip empty labels
            if not label.strip():
                label = url
            
            # Normalize URL
            url = url.strip()
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Determine source type
            source_type = 'external'
            if 'ingredientiq' in url.lower():
                source_type = 'internal'
            elif any(domain in url.lower() for domain in ['pubmed', 'ncbi', 'nih.gov', 'scholar.google']):
                source_type = 'academic'
            elif any(domain in url.lower() for domain in ['wikipedia', 'britannica']):
                source_type = 'reference'
            elif any(domain in url.lower() for domain in ['fda.gov', 'usda.gov', 'cdc.gov', 'who.int']):
                source_type = 'government'
            
            sources.append({
                'url': url,
                'label': label.strip()[:100],  # Truncate long labels
                'type': source_type,
                'accessed_date': today,
            })
        
        # Also extract markdown-style links from content [text](url)
        md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        md_matches = re.findall(md_link_pattern, strip_tags(body_html))
        for label, url in md_matches:
            if url.startswith('#') or url.startswith('javascript:'):
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            sources.append({
                'url': url,
                'label': label.strip()[:100],
                'type': 'external',
                'accessed_date': today,
            })
        
        # Add this blog post as a source (self-reference for citation)
        blog_url = f"{cls.SITE_URL}/blog/{slug}/" if slug else None
        if blog_url and blog_url not in seen_urls:
            sources.insert(0, {
                'url': blog_url,
                'label': f"This article: {title[:80]}",
                'type': 'self',
                'accessed_date': today,
                'category': category or 'Uncategorized',
            })
        
        # Add IngredientIQ homepage as a source
        if cls.SITE_URL not in seen_urls:
            sources.append({
                'url': cls.SITE_URL,
                'label': f"{cls.SITE_NAME} - AI-Powered Food Intelligence",
                'type': 'publisher',
                'accessed_date': today,
            })
        
        return sources[:20]  # Limit to 20 sources
    
    @classmethod
    def process(
        cls, 
        title: str, 
        excerpt: str, 
        takeaways: List[str], 
        body_html: str, 
        entities: List[Dict],
        slug: str = '',
        category: str = None
    ) -> Dict[str, Any]:
        """Main entry point for Filter 5"""
        return {
            'auto_summary_for_llms': cls.generate_summary_for_llms(title, excerpt, takeaways),
            'auto_key_facts': cls.extract_key_facts(body_html, entities),
            'auto_sources_json': cls.extract_sources_from_content(body_html, title, slug, category),
        }


# ============================================
# FILTER 6: GOVERNANCE & WORKFLOW VALIDATION
# ============================================

class Filter6Governance:
    """
    Filter 6 - Governance & Workflow
    Enforces quality gates and validation rules.
    """
    
    REQUIRED_FOR_PUBLISH = [
        'title',
        'slug', 
        'excerpt',
        'body_html',
        'author_entity',
        'category_new',
        'image',
        'image_alt_text',
        'meta_title',
        'meta_description',
    ]
    
    @classmethod
    def validate_title_length(cls, title: str) -> Optional[str]:
        """Validate title length and format"""
        if not title:
            return "Title is required"
        if len(title) < 10:
            return f"Title too short ({len(title)} chars, min 10)"
        if len(title) > 200:
            return f"Title too long ({len(title)} chars, max 200)"
        return None
    
    @classmethod
    def validate_heading_structure(cls, toc: List[Dict]) -> List[str]:
        """Validate heading hierarchy"""
        warnings = []
        if not toc:
            warnings.append("No headings found - consider adding structure")
        elif len(toc) < 2:
            warnings.append("Only one heading - consider adding more sections")
        return warnings
    
    @classmethod
    def validate_accessibility(cls, body_html: str, image: Any, image_alt: str) -> List[str]:
        """Validate accessibility requirements"""
        errors = []
        
        # Check image alt text
        if image and not image_alt:
            errors.append("Featured image missing alt text (required for accessibility)")
        
        # Check inline images
        img_pattern = r'<img[^>]+>'
        for img in re.findall(img_pattern, body_html, re.IGNORECASE):
            if 'alt=""' in img or 'alt=' not in img:
                errors.append("Content contains image(s) without alt text")
                break
        
        # Check for empty links
        empty_link_pattern = r'<a[^>]*>\s*</a>'
        if re.search(empty_link_pattern, body_html, re.IGNORECASE):
            errors.append("Content contains empty link(s)")
        
        return errors
    
    @classmethod
    def validate_links(cls, body_html: str) -> List[str]:
        """Check for broken or problematic links"""
        warnings = []
        
        # Find all links
        link_pattern = r'href=["\']([^"\']+)["\']'
        links = re.findall(link_pattern, body_html)
        
        for link in links:
            if link.startswith('javascript:'):
                warnings.append(f"JavaScript link found: {link[:50]}")
            elif link == '#':
                warnings.append("Empty anchor link (#) found")
            # Note: Actual HTTP checking would be async/Celery task
        
        return warnings
    
    @classmethod
    def check_publish_readiness(cls, data: Dict) -> Tuple[List[str], List[str]]:
        """
        Check if post is ready for publication.
        Returns (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check required fields
        for field in cls.REQUIRED_FOR_PUBLISH:
            value = data.get(field)
            if not value:
                errors.append(f"Required field missing: {field}")
        
        # Validate title
        title_error = cls.validate_title_length(data.get('title', ''))
        if title_error:
            errors.append(title_error)
        
        # Validate heading structure
        warnings.extend(cls.validate_heading_structure(data.get('toc_json', [])))
        
        # Validate accessibility
        errors.extend(cls.validate_accessibility(
            data.get('body_html', ''),
            data.get('image'),
            data.get('image_alt_text', '')
        ))
        
        # Validate links
        warnings.extend(cls.validate_links(data.get('body_html', '')))
        
        # SEO warnings
        meta_title = data.get('meta_title', '') or data.get('title', '')
        meta_desc = data.get('meta_description', '') or data.get('excerpt', '')
        warnings.extend(Filter3SEOPack.validate_seo({
            'meta_title': meta_title,
            'meta_description': meta_desc,
            'canonical_url': data.get('canonical_url'),
        }))
        
        return errors, warnings
    
    @classmethod
    def process(cls, data: Dict) -> Tuple[List[str], List[str]]:
        """Main entry point for Filter 6"""
        return cls.check_publish_readiness(data)


# ============================================
# MAIN PIPELINE PROCESSOR
# ============================================

class BritaFilterPipeline:
    """
    Main orchestrator for the Brita Filter CMS pipeline.
    Processes raw markdown drafts through all filters.
    """
    
    @classmethod
    def process_draft(cls, raw_draft: str, existing_data: Optional[Dict] = None) -> ProcessedContent:
        """
        Process a raw draft through all filters.
        
        Args:
            raw_draft: Raw markdown content from writer
            existing_data: Optional existing post data for validation
            
        Returns:
            ProcessedContent with all auto-generated fields
        """
        result = ProcessedContent()
        existing_data = existing_data or {}
        
        if not raw_draft:
            result.validation_errors.append("No content provided")
            return result
        
        # Filter 0: Sanitize input
        sanitized = Filter0RawInput.process(raw_draft)
        
        # Filter 1: Structural normalization
        (
            result.body_html,
            result.toc_json,
            result.key_sections_json,
            result.intro_text,
            faqs
        ) = Filter1StructuralNormalization.process(sanitized)
        
        result.extracted_faqs = [{'question': f.question, 'answer': f.answer} for f in faqs]
        
        # Filter 2: Metadata distillation
        meta = Filter2MetadataDistillation.process(
            result.body_html,
            result.intro_text,
            result.key_sections_json,
            sanitized
        )
        result.auto_title = meta['auto_title']
        result.auto_slug = meta['auto_slug']
        result.auto_excerpt = meta['auto_excerpt']
        result.auto_key_takeaways = meta['auto_key_takeaways']
        result.auto_reading_time = meta['auto_reading_time']
        result.auto_word_count = meta['auto_word_count']
        result.entities_json = meta['entities_json']
        suggested_tags = meta['suggested_tags']
        
        # Filter 3: SEO pack
        seo = Filter3SEOPack.process(result.auto_title, result.auto_excerpt)
        result.auto_meta_title = seo['auto_meta_title']
        result.auto_meta_description = seo['auto_meta_description']
        
        # Filter 4: SMO pack
        smo = Filter4SMOPack.process(
            result.auto_title,
            result.auto_excerpt,
            result.auto_key_takeaways,
            suggested_tags
        )
        result.auto_social_copy_linkedin = smo['auto_social_copy_linkedin']
        result.auto_social_copy_twitter = smo['auto_social_copy_twitter']
        result.auto_social_hashtags = smo['auto_social_hashtags']
        
        # Filter 5: LLM readiness (now includes sources extraction)
        # Get slug and category for source self-reference
        current_slug = existing_data.get('slug') or result.auto_slug
        current_category = None
        if existing_data.get('category_new'):
            # Try to get category name if it's an ID
            try:
                from .models import BlogCategory
                cat = BlogCategory.objects.filter(id=existing_data.get('category_new')).first()
                if cat:
                    current_category = cat.name
            except:
                pass
        
        llm = Filter5LLMReadiness.process(
            result.auto_title,
            result.auto_excerpt,
            result.auto_key_takeaways,
            result.body_html,
            result.entities_json,
            slug=current_slug,
            category=current_category
        )
        result.auto_summary_for_llms = llm['auto_summary_for_llms']
        result.auto_key_facts = llm['auto_key_facts']
        result.auto_sources_json = llm.get('auto_sources_json', [])
        
        # Filter 6: Governance validation
        validation_data = {
            'title': existing_data.get('title') or result.auto_title,
            'slug': existing_data.get('slug') or result.auto_slug,
            'excerpt': existing_data.get('excerpt') or result.auto_excerpt,
            'body_html': result.body_html,
            'author_entity': existing_data.get('author_entity'),
            'category_new': existing_data.get('category_new'),
            'image': existing_data.get('image'),
            'image_alt_text': existing_data.get('image_alt_text'),
            'meta_title': existing_data.get('meta_title') or result.auto_meta_title,
            'meta_description': existing_data.get('meta_description') or result.auto_meta_description,
            'canonical_url': existing_data.get('canonical_url'),
            'toc_json': result.toc_json,
        }
        errors, warnings = Filter6Governance.process(validation_data)
        result.validation_errors = errors
        result.validation_warnings = warnings
        
        return result
    
    @classmethod
    def to_dict(cls, processed: ProcessedContent) -> Dict[str, Any]:
        """Convert ProcessedContent to dictionary"""
        return asdict(processed)
