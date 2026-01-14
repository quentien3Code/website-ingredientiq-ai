from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from simple_history.models import HistoricalRecords
import math
import re
import uuid

# Create your models here.

# ============================================
# BLOG TAXONOMY & AUTHOR MODELS
# ============================================

class BlogCategory(models.Model):
    """Category for blog posts - single category per post"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Category description for SEO")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Blog Categories"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogTag(models.Model):
    """Tags for blog posts - multiple tags per post"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogAuthor(models.Model):
    """Rich author model for blog posts"""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    email = models.EmailField(blank=True)
    bio = models.TextField(blank=True, help_text="Author biography")
    avatar = models.ImageField(upload_to='website/authors/', blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True)
    
    # Social links
    website = models.URLField(blank=True)
    twitter = models.URLField(blank=True, help_text="Twitter/X profile URL")
    linkedin = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return None


class Stayconnected(models.Model):
    name = models.CharField(max_length=100,null=True,blank=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
    
class Contact(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    # name = models.CharField(max_length=255)   
    phone_number = models.CharField(max_length=255)
    enquiry_type = models.CharField(max_length=255,choices=[('support','Support'),('feedback','Feedback'),('partnership','Partnership'),('press','Press'),('security','Security')])
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    agreed_to_terms = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name
    
class TermsandConditions(models.Model):
    terms_and_conditions = models.TextField(null=True,blank=True)
    heading = models.CharField(max_length=255,null=True,blank=True)
    subheading = models.CharField(max_length=255,null=True,blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content
    
class PrivacyPolicy(models.Model):
    privacy_policy = models.TextField(null=True,blank=True)
    heading = models.CharField(max_length=255,null=True,blank=True)
    subheading = models.CharField(max_length=255,null=True,blank=True)
    content = models.TextField(max_length=10000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content
    
class Blogs(models.Model):
    """
    Brita Filter CMS - Modern blog post model with multi-stage content processing.
    
    Writers pour in raw markdown (raw_draft), and the system automatically produces:
    - Filter 1: Structured HTML, TOC, sections
    - Filter 2: Title, excerpt, key takeaways, entities
    - Filter 3: SEO metadata pack
    - Filter 4: Social media optimization pack
    - Filter 5: LLM-ready summaries and facts
    - Filter 6: Governance validation and workflow
    
    All auto-generated fields have override toggles so humans can lock their edits.
    """
    
    # ============================================
    # PUBLISHING STATUS CHOICES (Extended for governance)
    # ============================================
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        REVIEW = 'review', 'In Review'  # NEW: Requires editorial review
        SCHEDULED = 'scheduled', 'Scheduled'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'
    
    # ============================================
    # FILTER 0: RAW INPUT (What humans touch)
    # ============================================
    raw_draft = models.TextField(
        blank=True,
        default='',
        help_text="Markdown content - the ONLY required writing field. Pour in your raw narrative here."
    )
    notes_private = models.TextField(
        blank=True,
        default='',
        help_text="Private notes (never published). For internal communication, research notes, etc."
    )
    
    # ============================================
    # FILTER 1: STRUCTURAL OUTPUT (Auto-generated)
    # ============================================
    body_html = models.TextField(
        blank=True,
        default='',
        help_text="Auto-generated sanitized HTML from raw_draft. DO NOT EDIT directly."
    )
    toc_json = models.JSONField(
        blank=True,
        default=list,
        help_text="Auto-generated table of contents as JSON"
    )
    key_sections_json = models.JSONField(
        blank=True,
        default=list,
        help_text="Auto-extracted content sections for reuse"
    )
    extracted_faqs_json = models.JSONField(
        blank=True,
        default=list,
        help_text="Auto-extracted FAQ items from content"
    )
    
    # ============================================
    # CORE CONTENT FIELDS (with override toggles)
    # ============================================
    title = models.CharField(max_length=255, blank=True, help_text="Auto-generated from first H1. Override to customize.")
    title_locked = models.BooleanField(default=False, help_text="Lock to prevent auto-update")
    
    slug = models.SlugField(max_length=255, unique=True, blank=True, help_text="Auto-generated from title. Override to customize.")
    slug_locked = models.BooleanField(default=False, help_text="Lock to prevent auto-update")
    
    excerpt = models.TextField(max_length=500, blank=True, default='', help_text="Auto-generated 155-180 char summary. Override to customize.")
    excerpt_locked = models.BooleanField(default=False, help_text="Lock to prevent auto-update")
    
    # Legacy body field - now auto-populated from body_html
    body = models.TextField(blank=True, default='', help_text="DEPRECATED: Use raw_draft instead. Auto-synced from body_html.")
    
    # Optional content blocks
    pull_quote = models.TextField(blank=True, null=True, help_text="Optional highlighted quote to display prominently")
    
    # Legacy fields (deprecated - kept for migration compatibility)
    description_1 = models.TextField(max_length=10000, blank=True, null=True, help_text="DEPRECATED: Use 'body' field instead")
    description_2 = models.TextField(max_length=10000, blank=True, null=True, help_text="DEPRECATED: Use 'body' field instead")
    quote = models.TextField(max_length=10000, blank=True, null=True, help_text="DEPRECATED: Use 'pull_quote' field instead")
    
    # ============================================
    # FEATURED IMAGE WITH ACCESSIBILITY
    # ============================================
    image = models.ImageField(upload_to='website/blogs/', blank=True, null=True, help_text="Featured image for the blog post")
    image_alt_text = models.CharField(max_length=255, blank=True, default='', help_text="Alt text for accessibility (recommended for SEO and screen readers)")
    image_caption = models.CharField(max_length=500, blank=True, help_text="Optional caption displayed below the image")
    image_credit = models.CharField(max_length=255, blank=True, help_text="Photo credit / source attribution")
    
    # ============================================
    # PUBLISHING WORKFLOW
    # ============================================
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Publishing status of the post"
    )
    publish_date = models.DateTimeField(
        blank=True, 
        null=True, 
        help_text="When the post should be published (timezone-aware)"
    )
    last_modified = models.DateTimeField(auto_now=True, help_text="Automatically updated on save")
    
    # Preview functionality
    preview_token = models.UUIDField(default=uuid.uuid4, editable=False, help_text="Token for shareable preview links")
    
    # Legacy date field (deprecated)
    date = models.DateField(blank=True, null=True, help_text="DEPRECATED: Use 'publish_date' instead")
    
    # ============================================
    # AUTHOR & TAXONOMY
    # ============================================
    author_entity = models.ForeignKey(
        BlogAuthor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='blog_posts',
        help_text="Select from registered authors"
    )
    author = models.CharField(max_length=255, blank=True, help_text="DEPRECATED: Use 'author_entity' instead")
    
    category_new = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts',
        help_text="Primary category for this post"
    )
    category = models.CharField(max_length=255, blank=True, help_text="DEPRECATED: Use 'category_new' FK instead")
    
    tags = models.ManyToManyField(
        BlogTag,
        blank=True,
        related_name='blog_posts',
        help_text="Add multiple tags for better discoverability"
    )
    
    # ============================================
    # FILTER 2: METADATA DISTILLATION (Auto-generated with overrides)
    # ============================================
    reading_time_minutes = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        help_text="Auto-calculated from body content (200 wpm). Set manually to override."
    )
    reading_time_locked = models.BooleanField(
        default=False, 
        help_text="Lock to prevent auto-recalculation of reading time"
    )
    word_count = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Auto-calculated word count"
    )
    
    # Key takeaways (3-7 bullets)
    key_takeaways = models.JSONField(
        blank=True,
        default=list,
        help_text="Auto-extracted key points. Edit to customize."
    )
    key_takeaways_locked = models.BooleanField(default=False, help_text="Lock to prevent auto-update")
    
    # Entity extraction for internal linking
    entities_json = models.JSONField(
        blank=True,
        default=list,
        help_text="Auto-extracted entities (people, orgs, concepts) for internal linking"
    )
    
    time_to_read = models.CharField(max_length=255, blank=True, help_text="DEPRECATED: Use 'reading_time_minutes' instead")
    
    # ============================================
    # FILTER 3: SEO PACK (Auto-generated with overrides)
    # ============================================
    meta_title = models.CharField(
        max_length=70, 
        blank=True, 
        help_text="Auto-generated SEO title (<= 60 chars). Override to customize."
    )
    meta_title_locked = models.BooleanField(default=False, help_text="Lock to prevent auto-update")
    
    meta_description = models.CharField(
        max_length=160, 
        blank=True, 
        help_text="Auto-generated SEO description (<= 160 chars). Override to customize."
    )
    meta_description_locked = models.BooleanField(default=False, help_text="Lock to prevent auto-update")
    
    canonical_url = models.URLField(
        blank=True, 
        help_text="Canonical URL. Defaults to current URL if blank."
    )
    robots_indexable = models.BooleanField(
        default=True, 
        help_text="Allow search engines to index this page"
    )
    robots_followable = models.BooleanField(
        default=True,
        help_text="Allow search engines to follow links on this page"
    )
    schema_type = models.CharField(
        max_length=50,
        blank=True,
        default='BlogPosting',
        help_text="Schema.org type (Article, BlogPosting, NewsArticle, etc.)"
    )
    
    # Open Graph / Social
    og_title = models.CharField(max_length=95, blank=True, help_text="Open Graph title for social sharing (max 95 chars)")
    og_description = models.CharField(max_length=200, blank=True, help_text="Open Graph description (max 200 chars)")
    og_image = models.ImageField(
        upload_to='website/blogs/og/', 
        blank=True, 
        null=True, 
        help_text="Custom image for social sharing (1200x630px recommended). Uses featured image if blank."
    )
    
    # Twitter/X specific
    twitter_title = models.CharField(max_length=70, blank=True, help_text="Twitter card title (optional)")
    twitter_description = models.CharField(max_length=200, blank=True, help_text="Twitter card description (optional)")
    
    # ============================================
    # FILTER 4: SMO PACK (Social Media Optimization)
    # ============================================
    social_copy_linkedin = models.TextField(
        blank=True,
        default='',
        help_text="Auto-generated LinkedIn post copy. Override to customize."
    )
    social_copy_linkedin_locked = models.BooleanField(default=False, help_text="Lock to prevent auto-update")
    
    social_copy_twitter = models.CharField(
        max_length=280,
        blank=True,
        default='',
        help_text="Auto-generated Twitter/X post copy (<= 280 chars). Override to customize."
    )
    social_copy_twitter_locked = models.BooleanField(default=False, help_text="Lock to prevent auto-update")
    
    social_hashtags = models.JSONField(
        blank=True,
        default=list,
        help_text="Auto-generated hashtags (3-8). Override to customize."
    )
    social_hashtags_locked = models.BooleanField(default=False, help_text="Lock to prevent auto-update")
    
    # ============================================
    # FILTER 5: LLM SURFACE READINESS
    # ============================================
    summary_for_llms = models.TextField(
        blank=True,
        default='',
        help_text="Auto-generated tight, factual summary (80-120 words) for LLM consumption."
    )
    summary_for_llms_locked = models.BooleanField(default=False, help_text="Lock to prevent auto-update")
    
    key_facts = models.JSONField(
        blank=True,
        default=list,
        help_text="Auto-extracted verifiable claims/facts for high-risk content validation."
    )
    
    sources_json = models.JSONField(
        blank=True,
        default=list,
        help_text="Citations and sources referenced in this post [{url, label, accessed_date}]"
    )
    
    # ============================================
    # FILTER 6: GOVERNANCE & WORKFLOW
    # ============================================
    requires_compliance_review = models.BooleanField(
        default=False,
        help_text="Flag for content requiring legal/compliance review before publish"
    )
    reviewer = models.ForeignKey(
        'foodinfo.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_posts',
        help_text="Reviewer who approved this post"
    )
    reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the post was reviewed/approved"
    )
    review_notes = models.TextField(
        blank=True,
        default='',
        help_text="Reviewer notes and feedback"
    )
    
    # Validation tracking
    validation_errors = models.JSONField(
        blank=True,
        default=list,
        help_text="Current publish-blocking errors"
    )
    validation_warnings = models.JSONField(
        blank=True,
        default=list,
        help_text="Current publish warnings (non-blocking)"
    )
    last_processed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the Brita pipeline last processed this post"
    )
    content_hash = models.CharField(
        max_length=64,
        blank=True,
        default='',
        help_text="Hash of raw_draft to detect changes"
    )
    
    # ============================================
    # ORGANIZATION & FEATURING
    # ============================================
    is_featured = models.BooleanField(default=False, help_text="Feature this post on homepage/listings")
    is_pinned = models.BooleanField(default=False, help_text="Pin to top of blog listing")
    related_posts = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False,
        help_text="Manually select related posts"
    )
    
    # ============================================
    # TIMESTAMPS
    # ============================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ============================================
    # REVISION HISTORY
    # ============================================
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ['-publish_date', '-created_at']
    
    def __str__(self):
        return self.title or "Untitled Post"
    
    def _compute_content_hash(self) -> str:
        """Compute hash of raw_draft to detect changes"""
        import hashlib
        content = (self.raw_draft or '').encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    def process_through_brita_pipeline(self, force: bool = False):
        """
        Run the Brita Filter pipeline on raw_draft.
        Only processes if content has changed (based on hash) unless force=True.
        """
        from .processors import BritaFilterPipeline
        
        current_hash = self._compute_content_hash()
        
        # Skip if content hasn't changed and not forced
        if not force and self.content_hash == current_hash and self.body_html:
            return
        
        # Run the pipeline
        result = BritaFilterPipeline.process_draft(
            self.raw_draft,
            existing_data={
                'title': self.title if self.title_locked else None,
                'slug': self.slug if self.slug_locked else None,
                'excerpt': self.excerpt if self.excerpt_locked else None,
                'author_entity': self.author_entity_id,
                'category_new': self.category_new_id,
                'image': self.image,
                'image_alt_text': self.image_alt_text,
                'meta_title': self.meta_title if self.meta_title_locked else None,
                'meta_description': self.meta_description if self.meta_description_locked else None,
                'canonical_url': self.canonical_url,
            }
        )
        
        # Filter 1: Structural output (always update)
        self.body_html = result.body_html
        self.body = result.body_html  # Sync legacy field
        self.toc_json = result.toc_json
        self.key_sections_json = result.key_sections_json
        self.extracted_faqs_json = result.extracted_faqs
        
        # Filter 2: Metadata (respect locks)
        if not self.title_locked and result.auto_title:
            self.title = result.auto_title
        if not self.slug_locked and result.auto_slug:
            # Ensure unique slug
            base_slug = result.auto_slug
            slug = base_slug
            counter = 1
            while Blogs.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if not self.excerpt_locked and result.auto_excerpt:
            self.excerpt = result.auto_excerpt
        if not self.key_takeaways_locked:
            self.key_takeaways = result.auto_key_takeaways
        
        # Reading time (respect lock)
        if not self.reading_time_locked:
            self.reading_time_minutes = result.auto_reading_time
        self.word_count = result.auto_word_count  # Always update word count
        self.entities_json = result.entities_json
        
        # Filter 3: SEO (respect locks)
        if not self.meta_title_locked and result.auto_meta_title:
            self.meta_title = result.auto_meta_title
        if not self.meta_description_locked and result.auto_meta_description:
            self.meta_description = result.auto_meta_description
        
        # Filter 4: SMO (respect locks)
        if not self.social_copy_linkedin_locked:
            self.social_copy_linkedin = result.auto_social_copy_linkedin
        if not self.social_copy_twitter_locked:
            self.social_copy_twitter = result.auto_social_copy_twitter
        if not self.social_hashtags_locked:
            self.social_hashtags = result.auto_social_hashtags
        
        # Filter 5: LLM Readiness (respect locks)
        if not self.summary_for_llms_locked:
            self.summary_for_llms = result.auto_summary_for_llms
        self.key_facts = result.auto_key_facts
        
        # Auto-populate sources_json if empty (always update from extracted sources)
        if not self.sources_json or self.sources_json == []:
            self.sources_json = result.auto_sources_json
        
        # Filter 6: Validation
        self.validation_errors = result.validation_errors
        self.validation_warnings = result.validation_warnings
        
        # Update tracking
        self.content_hash = current_hash
        self.last_processed_at = timezone.now()
    
    def save(self, *args, **kwargs):
        # Process through Brita pipeline if raw_draft exists
        if self.raw_draft:
            self.process_through_brita_pipeline()
        elif self.body and not self.body_html:
            # Legacy: if body exists but body_html doesn't, copy it
            self.body_html = self.body
        
        # Ensure slug exists (fallback)
        if not self.slug and self.title:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Blogs.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Auto-generate canonical URL if not set (based on domain + slug)
        if not self.canonical_url and self.slug:
            self.canonical_url = self.get_full_url()
        
        # Fallback reading time calculation
        if not self.reading_time_minutes and (self.body_html or self.body):
            text = re.sub(r'<[^>]+>', '', self.body_html or self.body)
            word_count = len(text.split())
            self.reading_time_minutes = max(1, math.ceil(word_count / 200))
        
        # Set publish_date when status changes to published
        if self.status == self.Status.PUBLISHED and not self.publish_date:
            self.publish_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def can_publish(self) -> tuple:
        """
        Check if post can be published.
        Returns (can_publish: bool, errors: list, warnings: list)
        """
        errors = list(self.validation_errors or [])
        warnings = list(self.validation_warnings or [])
        
        # Additional checks
        if not self.title:
            errors.append("Title is required")
        if not self.slug:
            errors.append("Slug is required")
        if not self.body_html and not self.body:
            errors.append("Content is required")
        if not self.author_entity_id:
            errors.append("Author is required")
        if not self.category_new_id:
            errors.append("Category is required")
        if self.image and not self.image_alt_text:
            errors.append("Featured image requires alt text")
        if self.requires_compliance_review and not self.reviewed_at:
            errors.append("Post requires compliance review before publishing")
        
        return len(errors) == 0, errors, warnings
    
    def get_absolute_url(self):
        return f"/blog/{self.slug}/"
    
    def get_full_url(self):
        """Get the full URL including domain for canonical/sharing purposes"""
        from django.conf import settings
        site_url = getattr(settings, 'SITE_URL', 'https://ingredientiq.ai')
        return f"{site_url}/blog/{self.slug}/"
    
    def get_canonical_url(self):
        """Get canonical URL - uses saved value or auto-generates from domain + slug"""
        if self.canonical_url:
            return self.canonical_url
        return self.get_full_url()
    
    def get_preview_url(self):
        """Generate preview URL that opens the actual blog post"""
        return self.get_absolute_url()
    
    def get_reading_time_display(self):
        """Return formatted reading time"""
        minutes = self.reading_time_minutes or 1
        return f"{minutes} min read"
    
    def get_meta_title(self):
        """Return meta title or fallback to post title"""
        return self.meta_title or self.title
    
    def get_meta_description(self):
        """Return meta description or fallback to excerpt"""
        return self.meta_description or self.excerpt[:160]
    
    def get_og_title(self):
        """Return OG title with fallbacks"""
        return self.og_title or self.meta_title or self.title
    
    def get_og_description(self):
        """Return OG description with fallbacks"""
        return self.og_description or self.meta_description or self.excerpt[:200]
    
    def get_og_image_url(self):
        """Return OG image URL or fallback to featured image"""
        if self.og_image and hasattr(self.og_image, 'url'):
            return self.og_image.url
        return self.get_image_url()
    
    def is_published(self):
        """Check if post is currently published and visible"""
        if self.status != self.Status.PUBLISHED:
            return False
        if self.publish_date and self.publish_date > timezone.now():
            return False
        return True
    is_published.boolean = True
    
    def get_image_url(self):
        """Get the URL for the image"""
        if self.image:
            if hasattr(self.image, 'url'):
                url = self.image.url
                # Fix malformed URLs with double https://
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
            elif isinstance(self.image, str):
                url = self.image
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
        return None
    
    # Legacy compatibility methods
    def get_description_1_html(self):
        """Get description_1 as safe HTML - DEPRECATED"""
        from django.utils.safestring import mark_safe
        return mark_safe(self.description_1 or self.body or '')
    
    def get_description_2_html(self):
        """Get description_2 as safe HTML - DEPRECATED"""
        from django.utils.safestring import mark_safe
        return mark_safe(self.description_2 or '')
    
    def get_quote_html(self):
        """Get quote as safe HTML - DEPRECATED"""
        from django.utils.safestring import mark_safe
        return mark_safe(self.quote or self.pull_quote or '')

class Faqs(models.Model):
    category = models.CharField(max_length=255,null=True,blank=True)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question
    
class Testimonials(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    image = models.ImageField(upload_to='website/testimonials/')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - Rating: {self.rating}"
    
    def get_image_url(self):
        """Get the S3 URL for the image"""
        if self.image:
            # Ensure we're getting a clean URL
            if hasattr(self.image, 'url'):
                url = self.image.url
                # Fix malformed URLs with double https://
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
            elif isinstance(self.image, str):
                # If it's already a string, fix malformed URLs
                url = self.image
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
        return None
    
class Aboutus(models.Model):
    title = models.CharField(max_length=255,null=True,blank=True)
    image = models.ImageField(upload_to='website/aboutus/',null=True,blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def get_image_url(self):
        """Get the S3 URL for the image"""
        if self.image:
            # Ensure we're getting a clean URL
            if hasattr(self.image, 'url'):
                url = self.image.url
                # Fix malformed URLs with double https://
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
            elif isinstance(self.image, str):
                # If it's already a string, fix malformed URLs
                url = self.image
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
        return None
    
class Platforms(models.Model):
    # name = models.CharField(max_length=255)
    content = models.TextField()
    TikTok = models.URLField(null=True,blank=True)
    Instagram = models.URLField(null=True,blank=True)
    Facebook = models.URLField(null=True,blank=True)
    LinkedIn = models.URLField(null=True,blank=True)
    # image = models.ImageField(upload_to='platforms/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content
    
class Info(models.Model):
    office_address = models.TextField()
    call_us = models.CharField(max_length=255)
    working_hours = models.CharField(max_length=255)
    partnership_and_support = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.office_address
    
class Leadership(models.Model):
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    experience = models.CharField(max_length=255, blank=True, null=True, help_text="Years of experience or experience description")
    instagram_link = models.URLField(blank=True, null=True, help_text="Instagram profile URL")
    facebook_link = models.URLField(blank=True, null=True, help_text="Facebook profile URL")
    profile_picture = models.ImageField(upload_to='leadership/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True, help_text="Brief biography")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of display")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Leadership"

    def __str__(self):
        return f"{self.name} - {self.position}"
    
class relatedposts(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='relatedposts/')
    description_1 = models.TextField(max_length=10000)
    description_2 = models.TextField(max_length=10000,null=True,blank=True)
    quote = models.TextField(max_length=10000)
    author = models.CharField(max_length=255,null=True,blank=True)
    date = models.DateField(null=True,blank=True)
    time_to_read = models.CharField(max_length=255,null=True,blank=True)
    category = models.CharField(max_length=255,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def get_image_url(self):
        """Get the S3 URL for the image"""
        if self.image:
            # Ensure we're getting a clean URL
            if hasattr(self.image, 'url'):
                url = self.image.url
                # Fix malformed URLs with double https://
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
            elif isinstance(self.image, str):
                # If it's already a string, fix malformed URLs
                url = self.image
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
        return None
    
class DownloadPDF(models.Model):
    email = models.EmailField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    pdf = models.FileField(upload_to='website/pdfs/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or self.email or f"DownloadPDF #{self.pk}"
    
class Video(models.Model):
    title = models.CharField(max_length=255)
    video = models.FileField(upload_to='website/videos/',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    