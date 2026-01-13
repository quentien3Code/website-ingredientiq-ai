"""
SEO Views for IngredientIQ

Dynamic robots.txt and other SEO-related views.
"""
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET
from django.utils import timezone


@require_GET
def blog_detail_view(request, slug):
    """
    Public blog detail view with server-side rendering for SEO.
    
    This view serves the full HTML page for a blog post, enabling:
    - Search engine crawling with proper meta tags
    - Social media preview cards (Open Graph, Twitter)
    - LLM/AI crawler access to structured content
    - No-JavaScript fallback for accessibility
    
    The React app can hydrate on top of this for interactivity.
    """
    from .models import Blogs
    
    # Get the blog post
    blog = get_object_or_404(Blogs, slug=slug)
    
    # Check if published (or allow preview with token)
    preview_token = request.GET.get('preview_token')
    is_preview = str(blog.preview_token) == preview_token
    
    if blog.status != Blogs.Status.PUBLISHED and not is_preview:
        # For unpublished posts, check if scheduled and past due
        if blog.status == Blogs.Status.SCHEDULED and blog.publish_date and blog.publish_date <= timezone.now():
            # Auto-publish scheduled posts
            pass
        else:
            raise Http404("Blog post not found")
    
    # Get site URL for absolute URLs
    site_url = getattr(settings, 'SITE_URL', 'https://ingredientiq.ai')
    
    # Build context for template
    context = {
        'blog': blog,
        'is_preview': is_preview,
        'site_url': site_url,
        
        # SEO meta
        'meta_title': blog.meta_title or blog.title,
        'meta_description': blog.meta_description or blog.excerpt[:160] if blog.excerpt else '',
        'canonical_url': blog.canonical_url or f"{site_url}/blog/{blog.slug}/",
        
        # Open Graph
        'og_title': blog.og_title or blog.title,
        'og_description': blog.og_description or blog.excerpt[:200] if blog.excerpt else '',
        'og_image': blog.og_image.url if blog.og_image else (blog.get_image_url() or f"{site_url}/logo512.png"),
        'og_url': f"{site_url}/blog/{blog.slug}/",
        
        # Twitter Card
        'twitter_title': blog.twitter_title or blog.title,
        'twitter_description': blog.twitter_description or blog.excerpt[:200] if blog.excerpt else '',
        
        # Author
        'author_name': blog.author_entity.name if blog.author_entity else blog.author or 'IngredientIQ',
        'author_url': f"{site_url}/blog/author/{blog.author_entity.slug}/" if blog.author_entity else None,
        
        # Category
        'category_name': blog.category_new.name if blog.category_new else blog.category or 'Uncategorized',
        'category_url': f"{site_url}/blog/category/{blog.category_new.slug}/" if blog.category_new else None,
        
        # Dates
        'publish_date': blog.publish_date or blog.created_at,
        'modified_date': blog.last_modified or blog.updated_at,
        
        # Content
        'body_html': blog.body_html or blog.body,
        'toc': blog.toc_json or [],
        'key_takeaways': blog.key_takeaways or [],
        'sources': blog.sources_json or [],
        
        # Reading info
        'reading_time': blog.get_reading_time_display(),
        'word_count': blog.word_count or 0,
        
        # Related posts
        'related_posts': blog.related_posts.filter(status='published')[:3],
        
        # Schema.org type
        'schema_type': blog.schema_type or 'BlogPosting',
    }
    
    return render(request, 'blog_detail.html', context)


@require_GET
@cache_page(60 * 60)  # Cache for 1 hour
def robots_txt(request):
    """
    Dynamic robots.txt that adapts to environment.
    
    In production: Allow crawling with appropriate directives
    In development: Disallow all to prevent indexing dev sites
    """
    site_url = getattr(settings, 'SITE_URL', request.build_absolute_uri('/').rstrip('/'))
    
    if settings.DEBUG:
        # Development: block all crawlers
        content = """# IngredientIQ - Development Environment
# Disallow all crawlers in development

User-agent: *
Disallow: /
"""
    else:
        # Production: SEO-optimized robots.txt
        content = f"""# IngredientIQ Robots.txt
# https://ingredientiq.ai/robots.txt

# Allow all search engines
User-agent: *
Allow: /

# Disallow admin and private areas
Disallow: /admin/
Disallow: /master/
Disallow: /control-panel/
Disallow: /api/
Disallow: /accounts/

# Disallow search and filter pages (avoid duplicate content)
Disallow: /*?*
Allow: /blog/?page=

# Crawl-delay for polite crawling
Crawl-delay: 1

# Sitemaps
Sitemap: {site_url}/sitemap.xml

# LLM/AI Crawlers - Allowed with considerations
# We welcome AI crawlers to help users find our content
User-agent: GPTBot
Allow: /blog/
Allow: /
Disallow: /admin/
Disallow: /api/

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: Anthropic-AI
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Bingbot
Allow: /

# Block bad bots
User-agent: AhrefsBot
Crawl-delay: 10

User-agent: SemrushBot
Crawl-delay: 10

User-agent: MJ12bot
Disallow: /

User-agent: DotBot
Disallow: /
"""
    
    return HttpResponse(content, content_type="text/plain")


@require_GET
@cache_page(60 * 60 * 24)  # Cache for 24 hours
def llms_txt(request):
    """
    llms.txt - Machine-readable site documentation for LLMs and AI crawlers.
    
    Emerging standard for helping AI systems understand your site.
    Reference: https://llmstxt.org/
    """
    site_url = getattr(settings, 'SITE_URL', 'https://ingredientiq.ai')
    
    content = f"""# IngredientIQ - llms.txt
# Machine-readable documentation for AI systems
# Last updated: 2026-01-12

## About This Site

IngredientIQ is an AI-powered food intelligence and nutrition analysis platform. We provide:
- Food ingredient analysis and safety information
- Nutrition insights and dietary guidance
- Educational content about food science
- Blog articles about health, nutrition, and food technology

## Content Guidelines

Our content is factual, research-based, and designed to help users make informed decisions about food and nutrition. We cite sources where applicable and update content regularly.

## Canonical Domain

The canonical domain for all content is: {site_url}

Please attribute content to IngredientIQ ({site_url}) when referencing our articles.

## Content Locations

- Blog: {site_url}/blog/
- RSS Feed: {site_url}/blog/feed/rss/
- Atom Feed: {site_url}/blog/feed/atom/
- Sitemap: {site_url}/sitemap.xml
- API (if applicable): {site_url}/api/

## Preferred Citation Format

When citing our content, please use:
"[Article Title]" by [Author Name], IngredientIQ, [Date]. {site_url}/blog/[slug]/

## Topics We Cover

- Food ingredients and additives
- Nutritional information and analysis
- Dietary restrictions and allergies
- Food safety and regulations
- Health and wellness related to food
- Food technology and innovation

## Content Freshness

- Blog posts are dated with publish and last-modified dates
- We update evergreen content periodically
- Check the "Last Updated" date on articles for freshness

## Contact

For corrections, feedback, or partnership inquiries:
- Website: {site_url}/contact/
- General inquiries: hello@ingredientiq.ai

## Licensing

Our blog content is copyrighted. Please link back rather than republishing in full.
API access may be available for partners - contact us for details.

## Technical Notes

- Our site uses server-side rendering (Django templates)
- Content is available without JavaScript for accessibility
- We provide structured data (JSON-LD) for rich results
- Mobile-responsive design

## Crawling Notes

- We welcome ethical AI crawling
- Please respect robots.txt directives
- Rate limit requests to avoid server load
- Our sitemap is updated regularly

---
Generated by IngredientIQ
{site_url}
"""
    
    return HttpResponse(content, content_type="text/plain; charset=utf-8")


@require_GET
@cache_page(60 * 60 * 24)  # Cache for 24 hours  
def humans_txt(request):
    """
    humans.txt - Information about the team behind the site.
    Reference: https://humanstxt.org/
    """
    content = """/* TEAM */
    
Name: IngredientIQ Team
Site: https://ingredientiq.ai
Location: Global

/* SITE */

Last update: 2026-01-12
Language: English
Doctype: HTML5
IDE: Visual Studio Code
Standards: HTML5, CSS3, ES6+

/* TECHNOLOGY */

Backend: Django 4.2, Python 3.12
Frontend: React
Database: PostgreSQL
Hosting: Railway
CDN: Cloudflare

/* THANKS */

Django Community
Python Software Foundation
Open Source Contributors
"""
    
    return HttpResponse(content, content_type="text/plain")


@require_GET
def security_txt(request):
    """
    security.txt - Security policy disclosure.
    Reference: https://securitytxt.org/
    """
    content = """# IngredientIQ Security Policy
# https://ingredientiq.ai/.well-known/security.txt

Contact: mailto:security@ingredientiq.ai
Preferred-Languages: en
Canonical: https://ingredientiq.ai/.well-known/security.txt
Expires: 2027-01-12T00:00:00.000Z

# We appreciate responsible disclosure of security vulnerabilities.
# Please do not publicly disclose issues until we've had a chance to address them.
"""
    
    return HttpResponse(content, content_type="text/plain")
