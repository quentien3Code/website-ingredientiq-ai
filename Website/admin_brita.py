"""
Brita Filter CMS - Enhanced Admin Configuration

This admin provides a tab-based interface matching the filter stages:
- Filter 0: Pour In (Write) - raw_draft, notes_private
- Filter 1: Structured Output - body_html preview, TOC
- Filter 2: Metadata - title, slug, excerpt, takeaways (with locks)
- Filter 3: SEO Pack - meta fields, schema
- Filter 4: Social Pack - OG, social copies
- Filter 5: LLM Pack - summary, facts, sources
- Filter 6: Governance - status, review, audit
"""

from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils import timezone
from django.db.models import Count
from django import forms
from django.contrib.admin import SimpleListFilter
from simple_history.admin import SimpleHistoryAdmin
import json

from .models import (
    Stayconnected, Contact, TermsandConditions, PrivacyPolicy, 
    Blogs, Faqs, Testimonials, Aboutus, Platforms, Info, Leadership, 
    relatedposts, DownloadPDF, Video,
    BlogCategory, BlogTag, BlogAuthor
)
from .validators import BlogValidator
from foodinfo.models import DownloadRequest


# ============================================
# CUSTOM ADMIN FORMS
# ============================================

class BlogsAdminForm(forms.ModelForm):
    """Enhanced form for Blogs admin with custom widgets"""
    
    class Meta:
        model = Blogs
        fields = '__all__'
        widgets = {
            'raw_draft': forms.Textarea(attrs={
                'rows': 25,
                'class': 'vLargeTextField markdown-editor',
                'placeholder': '# Your Title Here\n\nStart writing your content in Markdown...\n\n## Section 1\n\nYour content here.\n\n## Key Takeaways\n\n- Point 1\n- Point 2\n- Point 3',
                'style': 'font-family: monospace; font-size: 14px; line-height: 1.5;',
            }),
            'notes_private': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Internal notes, research links, etc. (not published)',
            }),
            'body_html': forms.Textarea(attrs={
                'rows': 15,
                'readonly': 'readonly',
                'class': 'readonly-preview',
            }),
            'excerpt': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': 500,
            }),
            'social_copy_linkedin': forms.Textarea(attrs={
                'rows': 5,
                'maxlength': 700,
            }),
            'summary_for_llms': forms.Textarea(attrs={
                'rows': 4,
            }),
            'review_notes': forms.Textarea(attrs={
                'rows': 3,
            }),
        }


# ============================================
# CUSTOM FILTERS
# ============================================

class PublishReadyFilter(SimpleListFilter):
    """Filter posts by publish readiness"""
    title = 'Publish Ready'
    parameter_name = 'publish_ready'
    
    def lookups(self, request, model_admin):
        return [
            ('ready', '✅ Ready to Publish'),
            ('blocked', '❌ Has Errors'),
            ('warnings', '⚠️ Has Warnings'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'ready':
            return queryset.filter(validation_errors=[])
        elif self.value() == 'blocked':
            return queryset.exclude(validation_errors=[])
        elif self.value() == 'warnings':
            return queryset.filter(validation_errors=[]).exclude(validation_warnings=[])


class HasContentFilter(SimpleListFilter):
    """Filter by content type"""
    title = 'Content Status'
    parameter_name = 'content_status'
    
    def lookups(self, request, model_admin):
        return [
            ('brita', '🔄 Brita Processed'),
            ('legacy', '📜 Legacy Content'),
            ('empty', '📝 Needs Content'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'brita':
            return queryset.exclude(raw_draft='')
        elif self.value() == 'legacy':
            return queryset.filter(raw_draft='').exclude(body='')
        elif self.value() == 'empty':
            return queryset.filter(raw_draft='', body='')


# ============================================
# BLOG TAXONOMY ADMIN
# ============================================

@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'order', 'created_at']
    list_editable = ['order']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    
    def post_count(self, obj):
        return obj.blog_posts.count()
    post_count.short_description = 'Posts'


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    def post_count(self, obj):
        return obj.blog_posts.count()
    post_count.short_description = 'Posts'


@admin.register(BlogAuthor)
class BlogAuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'job_title', 'email', 'is_active', 'post_count', 'avatar_preview']
    list_filter = ['is_active']
    search_fields = ['name', 'email', 'bio']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'email', 'job_title', 'avatar', 'bio')
        }),
        ('Social Links', {
            'fields': ('website', 'twitter', 'linkedin', 'instagram'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def post_count(self, obj):
        return obj.blog_posts.count()
    post_count.short_description = 'Posts'
    
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />', obj.avatar.url)
        return "-"
    avatar_preview.short_description = 'Avatar'


# ============================================
# MAIN BLOG POST ADMIN - BRITA FILTER CMS
# ============================================

@admin.register(Blogs)
class BlogsAdmin(SimpleHistoryAdmin):
    """
    Brita Filter CMS Admin
    
    Organized as filter stages:
    - Filter 0: Pour In (Write)
    - Filter 1: Structured Output
    - Filter 2: Metadata Distillation
    - Filter 3: SEO Pack
    - Filter 4: Social Pack
    - Filter 5: LLM Pack
    - Filter 6: Governance
    """
    
    form = BlogsAdminForm
    
    # ============================================
    # LIST CONFIGURATION
    # ============================================
    list_display = [
        'title', 'status_badge', 'quality_score', 'author_entity', 'category_new', 
        'word_count_display', 'reading_time_display',
        'publish_date_display', 'is_featured', 'is_pinned', 'is_published'
    ]
    list_filter = [
        'status', PublishReadyFilter, HasContentFilter,
        'is_featured', 'is_pinned', 'requires_compliance_review',
        'category_new', 'author_entity', 'robots_indexable',
        'created_at', 'publish_date'
    ]
    list_editable = ['is_featured', 'is_pinned']
    search_fields = ['title', 'slug', 'excerpt', 'raw_draft', 'meta_title', 'meta_description']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'
    ordering = ['-created_at']
    filter_horizontal = ['tags', 'related_posts']
    autocomplete_fields = ['author_entity', 'category_new', 'reviewer']
    
    # Readonly fields
    readonly_fields = [
        'body_html_preview', 'toc_preview', 'sections_preview', 'faqs_preview',
        'entities_preview', 'key_facts_preview',
        'validation_status', 'lint_report',
        'preview_token', 'preview_link', 
        'word_count_display_detail',
        'last_processed_at', 'content_hash',
        'last_modified', 'created_at', 'updated_at'
    ]
    
    # ============================================
    # FIELDSETS - ORGANIZED BY FILTER STAGE
    # ============================================
    fieldsets = (
        # FILTER 0: POUR IN (WRITE)
        ('🖊️ Filter 0: Pour In (Write)', {
            'fields': ('raw_draft', 'notes_private'),
            'description': '''
                <div style="background: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>✨ Just write here!</strong> Use Markdown format. Everything else is auto-generated.
                    <br>Supported: # Headings, **bold**, *italic*, - lists, > quotes, [links](url), ![images](url)
                </div>
            '''
        }),
        
        # FILTER 1: STRUCTURAL OUTPUT (READ-ONLY)
        ('📄 Filter 1: Structured Output (Auto)', {
            'fields': ('body_html_preview', 'toc_preview', 'sections_preview', 'faqs_preview'),
            'classes': ('collapse',),
            'description': 'Auto-generated from your markdown. Read-only.'
        }),
        
        # FILTER 2: METADATA (WITH LOCKS)
        ('📊 Filter 2: Metadata', {
            'fields': (
                ('title', 'title_locked'),
                ('slug', 'slug_locked'),
                ('excerpt', 'excerpt_locked'),
                ('key_takeaways', 'key_takeaways_locked'),
                ('author_entity', 'category_new'),
                'tags',
                ('reading_time_minutes', 'reading_time_locked'),
                'word_count_display_detail',
                'entities_preview',
            ),
            'description': 'Auto-generated with override toggles. Lock fields to prevent auto-update.'
        }),
        
        # FILTER 3: SEO PACK
        ('🔍 Filter 3: SEO Pack', {
            'fields': (
                ('meta_title', 'meta_title_locked'),
                ('meta_description', 'meta_description_locked'),
                'canonical_url',
                ('robots_indexable', 'robots_followable'),
                'schema_type',
            ),
            'classes': ('collapse',),
            'description': 'Search engine optimization. Auto-generated with locks.'
        }),
        
        # FILTER 4: SOCIAL PACK
        ('📱 Filter 4: Social Pack', {
            'fields': (
                'og_title', 'og_description', 'og_image',
                'twitter_title', 'twitter_description',
                ('social_copy_linkedin', 'social_copy_linkedin_locked'),
                ('social_copy_twitter', 'social_copy_twitter_locked'),
                ('social_hashtags', 'social_hashtags_locked'),
            ),
            'classes': ('collapse',),
            'description': 'Social media previews and copy. Auto-generated with locks.'
        }),
        
        # FILTER 5: LLM PACK
        ('🤖 Filter 5: LLM Readiness', {
            'fields': (
                ('summary_for_llms', 'summary_for_llms_locked'),
                'key_facts_preview',
                'sources_json',
            ),
            'classes': ('collapse',),
            'description': 'LLM-optimized content for AI discovery.'
        }),
        
        # FILTER 6: GOVERNANCE
        ('⚙️ Filter 6: Governance & Workflow', {
            'fields': (
                'validation_status',
                'lint_report',
                ('status', 'publish_date'),
                ('is_featured', 'is_pinned'),
                'preview_link',
                ('requires_compliance_review', 'reviewer', 'reviewed_at'),
                'review_notes',
                'related_posts',
            ),
            'description': 'Publishing workflow and quality gates.'
        }),
        
        # FEATURED IMAGE
        ('🖼️ Featured Image', {
            'fields': ('image', 'image_alt_text', 'image_caption', 'image_credit'),
            'description': 'Featured image with required alt text for accessibility.'
        }),
        
        # SYSTEM INFO
        ('📋 System Info', {
            'fields': ('preview_token', 'content_hash', 'last_processed_at', 'created_at', 'updated_at', 'last_modified'),
            'classes': ('collapse',),
        }),
        
        # LEGACY (DEPRECATED)
        ('🗄️ Legacy Fields (Deprecated)', {
            'fields': ('body', 'description_1', 'description_2', 'quote', 'author', 'date', 'category', 'time_to_read'),
            'classes': ('collapse',),
            'description': '⚠️ Deprecated fields kept for backward compatibility. Use new fields instead.'
        }),
    )
    
    # ============================================
    # CUSTOM DISPLAY METHODS
    # ============================================
    
    def body_html_preview(self, obj):
        """Preview of generated HTML"""
        if not obj.body_html:
            return format_html('<em style="color: #999;">No content generated yet. Write in raw_draft above.</em>')
        
        preview = obj.body_html[:2000]
        if len(obj.body_html) > 2000:
            preview += '...'
        
        return format_html(
            '<div style="max-height: 400px; overflow-y: auto; padding: 10px; background: #fafafa; border: 1px solid #ddd; border-radius: 4px;">{}</div>',
            mark_safe(preview)
        )
    body_html_preview.short_description = 'Generated HTML Preview'
    
    def toc_preview(self, obj):
        """Preview of table of contents"""
        if not obj.toc_json:
            return format_html('<em style="color: #999;">No headings detected.</em>')
        
        def render_toc(items, depth=0):
            html = '<ul style="margin-left: {}px; list-style: none;">'.format(depth * 20)
            for item in items:
                html += '<li>→ {}</li>'.format(item.get('text', ''))
                if item.get('children'):
                    html += render_toc(item['children'], depth + 1)
            html += '</ul>'
            return html
        
        return format_html(
            '<div style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{}</div>',
            mark_safe(render_toc(obj.toc_json))
        )
    toc_preview.short_description = 'Table of Contents'
    
    def sections_preview(self, obj):
        """Preview of extracted sections"""
        if not obj.key_sections_json:
            return format_html('<em style="color: #999;">No sections extracted.</em>')
        
        html = '<ol>'
        for section in obj.key_sections_json[:10]:
            html += '<li><strong>{}</strong> ({})</li>'.format(
                section.get('heading', 'Untitled'),
                section.get('type', 'body')
            )
        html += '</ol>'
        return format_html(html)
    sections_preview.short_description = 'Content Sections'
    
    def faqs_preview(self, obj):
        """Preview of extracted FAQs"""
        if not obj.extracted_faqs_json:
            return format_html('<em style="color: #999;">No FAQs detected. Add Q&A sections to your content.</em>')
        
        html = '<dl style="background: #fff9e6; padding: 10px; border-radius: 4px;">'
        for faq in obj.extracted_faqs_json[:5]:
            html += '<dt style="font-weight: bold;">❓ {}</dt>'.format(faq.get('question', ''))
            html += '<dd style="margin-left: 20px; margin-bottom: 10px;">{}</dd>'.format(faq.get('answer', '')[:200])
        html += '</dl>'
        return format_html(html)
    faqs_preview.short_description = 'Extracted FAQs'
    
    def entities_preview(self, obj):
        """Preview of extracted entities"""
        if not obj.entities_json:
            return format_html('<em style="color: #999;">No entities detected.</em>')
        
        type_colors = {
            'person': '#e3f2fd',
            'org': '#f3e5f5',
            'location': '#e8f5e9',
            'concept': '#fff3e0',
            'product': '#fce4ec',
        }
        
        html = ''
        for entity in obj.entities_json[:15]:
            color = type_colors.get(entity.get('type', ''), '#f5f5f5')
            html += '<span style="background: {}; padding: 2px 8px; margin: 2px; border-radius: 3px; display: inline-block;">{} <small>({})</small></span>'.format(
                color, entity.get('text', ''), entity.get('type', 'unknown')
            )
        
        if len(obj.entities_json) > 15:
            html += '<br><small>...and {} more</small>'.format(len(obj.entities_json) - 15)
        
        return format_html(html)
    entities_preview.short_description = 'Extracted Entities'
    
    def key_facts_preview(self, obj):
        """Preview of key facts"""
        if not obj.key_facts:
            return format_html('<em style="color: #999;">No key facts extracted.</em>')
        
        html = '<ul style="background: #e8f5e9; padding: 10px; border-radius: 4px;">'
        for fact in obj.key_facts[:5]:
            html += '<li>✓ {}</li>'.format(fact[:150])
        html += '</ul>'
        return format_html(html)
    key_facts_preview.short_description = 'Key Facts (LLM)'
    
    def validation_status(self, obj):
        """Show validation status with errors/warnings"""
        errors = obj.validation_errors or []
        warnings = obj.validation_warnings or []
        
        if not errors and not warnings:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 5px 15px; border-radius: 4px; font-weight: bold;">✅ Ready to Publish</span>'
            )
        elif errors:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 5px 15px; border-radius: 4px; font-weight: bold;">❌ {} Error(s), {} Warning(s)</span>',
                len(errors), len(warnings)
            )
        else:
            return format_html(
                '<span style="background: #ffc107; color: black; padding: 5px 15px; border-radius: 4px; font-weight: bold;">⚠️ {} Warning(s)</span>',
                len(warnings)
            )
    validation_status.short_description = 'Publish Status'
    
    def lint_report(self, obj):
        """Detailed lint report"""
        errors = obj.validation_errors or []
        warnings = obj.validation_warnings or []
        
        if not errors and not warnings:
            return format_html('<em style="color: #28a745;">All checks passed! 🎉</em>')
        
        html = '<div style="font-size: 12px;">'
        
        if errors:
            html += '<div style="background: #f8d7da; padding: 8px; border-radius: 4px; margin-bottom: 5px;">'
            html += '<strong style="color: #721c24;">Errors (must fix):</strong><ul style="margin: 5px 0 0 0;">'
            for err in errors[:5]:
                html += '<li>{}</li>'.format(err)
            html += '</ul></div>'
        
        if warnings:
            html += '<div style="background: #fff3cd; padding: 8px; border-radius: 4px;">'
            html += '<strong style="color: #856404;">Warnings:</strong><ul style="margin: 5px 0 0 0;">'
            for warn in warnings[:5]:
                html += '<li>{}</li>'.format(warn)
            html += '</ul></div>'
        
        html += '</div>'
        return format_html(html)
    lint_report.short_description = 'Quality Report'
    
    def quality_score(self, obj):
        """Show quality score as badge"""
        # Quick calculation based on validation state
        errors = len(obj.validation_errors or [])
        warnings = len(obj.validation_warnings or [])
        
        score = 100 - (errors * 15) - (warnings * 5)
        score = max(0, min(100, score))
        
        if score >= 90:
            color = '#28a745'
        elif score >= 70:
            color = '#ffc107'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">{}</span>',
            color, score
        )
    quality_score.short_description = 'Score'
    
    def status_badge(self, obj):
        """Colored status badge"""
        colors = {
            'draft': '#6c757d',
            'review': '#17a2b8',
            'scheduled': '#ffc107',
            'published': '#28a745',
            'archived': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def publish_date_display(self, obj):
        """Display publish date with scheduled indicator"""
        if obj.publish_date:
            now = timezone.now()
            if obj.publish_date > now:
                return format_html('<span style="color: #ffc107;">📅 {}</span>', obj.publish_date.strftime('%Y-%m-%d %H:%M'))
            return obj.publish_date.strftime('%Y-%m-%d %H:%M')
        return "-"
    publish_date_display.short_description = 'Publish Date'
    publish_date_display.admin_order_field = 'publish_date'
    
    def reading_time_display(self, obj):
        """Display reading time"""
        if obj.reading_time_minutes:
            return f"{obj.reading_time_minutes} min"
        return "-"
    reading_time_display.short_description = 'Time'
    
    def word_count_display(self, obj):
        """Display word count"""
        if obj.word_count:
            return f"{obj.word_count:,}"
        return "-"
    word_count_display.short_description = 'Words'
    
    def word_count_display_detail(self, obj):
        """Detailed word count for form"""
        if obj.word_count and obj.reading_time_minutes:
            return format_html(
                '<span style="color: #666;">{:,} words • {} min read @ 200 wpm</span>',
                obj.word_count, obj.reading_time_minutes
            )
        return "Calculate by saving"
    word_count_display_detail.short_description = 'Content Stats'
    
    def reading_time_calculated(self, obj):
        """Calculated reading time display"""
        return self.word_count_display_detail(obj)
    reading_time_calculated.short_description = 'Reading Time'
    
    def preview_link(self, obj):
        """Preview link - opens the actual blog post on the public site"""
        if obj.slug:
            # Get the full URL including domain for public blogs
            from django.conf import settings
            site_url = getattr(settings, 'SITE_URL', 'https://ingredientiq.ai')
            public_url = f"{site_url}/blog/{obj.slug}/"
            
            if obj.status == 'published':
                return format_html(
                    '<a href="{}" target="_blank" style="text-decoration: none; background: #28a745; color: white; padding: 5px 10px; border-radius: 4px;">🌐 View Live Post</a>',
                    public_url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank" style="text-decoration: none; background: #6c757d; color: white; padding: 5px 10px; border-radius: 4px;">👁️ Preview Draft</a>',
                    public_url
                )
        return format_html('<span style="color: #999;">Save post to generate preview link</span>')
    preview_link.short_description = 'View Post'
    
    # ============================================
    # ADMIN ACTIONS
    # ============================================
    actions = [
        'publish_selected', 'unpublish_selected', 
        'send_to_review', 'approve_selected',
        'reprocess_pipeline', 'feature_selected', 'unfeature_selected'
    ]
    
    @admin.action(description='✅ Publish selected posts')
    def publish_selected(self, request, queryset):
        published = 0
        blocked = 0
        
        for post in queryset:
            can_publish, errors, _ = post.can_publish()
            if can_publish:
                post.status = 'published'
                if not post.publish_date:
                    post.publish_date = timezone.now()
                post.save()
                published += 1
            else:
                blocked += 1
        
        if blocked:
            self.message_user(request, f'{published} post(s) published, {blocked} blocked due to errors.', level='warning')
        else:
            self.message_user(request, f'{published} post(s) published.')
    
    @admin.action(description='📝 Unpublish (set to draft)')
    def unpublish_selected(self, request, queryset):
        count = queryset.update(status='draft')
        self.message_user(request, f'{count} post(s) set to draft.')
    
    @admin.action(description='👀 Send to Review')
    def send_to_review(self, request, queryset):
        count = queryset.update(status='review')
        self.message_user(request, f'{count} post(s) sent to review.')
    
    @admin.action(description='✓ Approve & Ready')
    def approve_selected(self, request, queryset):
        count = queryset.update(
            reviewed_at=timezone.now(),
            reviewer=request.user
        )
        self.message_user(request, f'{count} post(s) approved.')
    
    @admin.action(description='🔄 Reprocess through Pipeline')
    def reprocess_pipeline(self, request, queryset):
        count = 0
        for post in queryset:
            if post.raw_draft:
                post.process_through_brita_pipeline(force=True)
                post.save()
                count += 1
        self.message_user(request, f'{count} post(s) reprocessed.')
    
    @admin.action(description='⭐ Feature selected posts')
    def feature_selected(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f'{count} post(s) featured.')
    
    @admin.action(description='Remove from featured')
    def unfeature_selected(self, request, queryset):
        count = queryset.update(is_featured=False)
        self.message_user(request, f'{count} post(s) unfeatured.')
    
    # ============================================
    # SAVE HOOKS
    # ============================================
    
    def save_model(self, request, obj, form, change):
        """Run validation before save"""
        # The model's save() method handles pipeline processing
        super().save_model(request, obj, form, change)
        
        # Show warnings in admin
        if obj.validation_warnings:
            from django.contrib import messages
            for warning in obj.validation_warnings[:3]:
                messages.warning(request, f"⚠️ {warning}")
    
    class Media:
        css = {
            'all': ('admin/css/brita_admin.css',)
        }
        js = ('admin/js/brita_admin.js',)


# ============================================
# OTHER MODEL ADMINS (existing, unchanged)
# ============================================

@admin.register(Leadership)
class LeadershipAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'is_active', 'order', 'profile_preview']
    list_filter = ['is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['name', 'position', 'bio']
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'position', 'experience', 'profile_picture', 'bio')
        }),
        ('Social Links', {
            'fields': ('instagram_link', 'facebook_link'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order')
        }),
    )
    
    def profile_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />', obj.profile_picture.url)
        return "-"
    profile_preview.short_description = 'Photo'


# Simple registrations for other models
admin.site.register(Stayconnected)
admin.site.register(Contact)
admin.site.register(TermsandConditions)
admin.site.register(PrivacyPolicy)
admin.site.register(Faqs)
admin.site.register(Testimonials)
admin.site.register(Aboutus)
admin.site.register(Platforms)
admin.site.register(Info)
admin.site.register(relatedposts)
admin.site.register(DownloadPDF)
admin.site.register(Video)
admin.site.register(DownloadRequest)
