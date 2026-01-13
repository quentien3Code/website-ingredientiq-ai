"""
JSON-LD Structured Data Template Tags

Provides template tags for generating JSON-LD structured data for:
- Article/BlogPosting schema
- Author (Person) schema
- Organization (Publisher) schema
- FAQPage schema
- Breadcrumb schema

Usage in templates:
    {% load jsonld_tags %}
    {% article_jsonld blog_post %}
    {% organization_jsonld %}
    {% breadcrumb_jsonld breadcrumbs %}

Reference: https://schema.org/
Google: https://developers.google.com/search/docs/appearance/structured-data
"""
import json
from django import template
from django.utils.safestring import mark_safe
from django.conf import settings
from django.utils import timezone

register = template.Library()


def get_site_url():
    """Get the site's base URL from settings or default."""
    return getattr(settings, 'SITE_URL', 'https://ingredientiq.ai')


def get_site_name():
    """Get the site name."""
    return getattr(settings, 'SITE_NAME', 'IngredientIQ')


def get_site_logo():
    """Get the site logo URL."""
    return getattr(settings, 'SITE_LOGO', f"{get_site_url()}/static/logo512.png")


@register.simple_tag
def article_jsonld(blog_post):
    """
    Generate Article/BlogPosting JSON-LD for a blog post.
    
    Usage: {% article_jsonld post %}
    """
    site_url = get_site_url()
    
    # Build author object
    author_data = {
        "@type": "Person",
        "name": blog_post.author_entity.name if blog_post.author_entity else (blog_post.author or "IngredientIQ Team"),
    }
    
    if blog_post.author_entity:
        author = blog_post.author_entity
        author_data["url"] = f"{site_url}/blog/author/{author.slug}/"
        if author.job_title:
            author_data["jobTitle"] = author.job_title
        if author.bio:
            author_data["description"] = author.bio[:200]
        # Add social profiles as sameAs
        same_as = []
        if author.twitter:
            same_as.append(author.twitter)
        if author.linkedin:
            same_as.append(author.linkedin)
        if author.website:
            same_as.append(author.website)
        if same_as:
            author_data["sameAs"] = same_as
    
    # Build image object
    image_data = None
    if blog_post.image:
        image_data = {
            "@type": "ImageObject",
            "url": f"{site_url}{blog_post.image.url}",
        }
        if blog_post.image_caption:
            image_data["caption"] = blog_post.image_caption
        if blog_post.image_credit:
            image_data["creditText"] = blog_post.image_credit
    
    # Build the main schema
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": blog_post.get_meta_title(),
        "description": blog_post.get_meta_description(),
        "url": f"{site_url}/blog/{blog_post.slug}/",
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"{site_url}/blog/{blog_post.slug}/"
        },
        "author": author_data,
        "publisher": {
            "@type": "Organization",
            "name": get_site_name(),
            "logo": {
                "@type": "ImageObject",
                "url": get_site_logo()
            }
        },
        "datePublished": blog_post.publish_date.isoformat() if blog_post.publish_date else blog_post.created_at.isoformat(),
        "dateModified": (blog_post.last_modified or blog_post.updated_at).isoformat(),
    }
    
    if image_data:
        schema["image"] = image_data
    
    if blog_post.reading_time_minutes:
        schema["timeRequired"] = f"PT{blog_post.reading_time_minutes}M"
    
    # Use category_new FK, fallback to legacy category string
    if blog_post.category_new:
        schema["articleSection"] = blog_post.category_new.name
    elif blog_post.category:
        schema["articleSection"] = blog_post.category  # Legacy string field
    
    # Add keywords from tags
    if blog_post.tags.exists():
        schema["keywords"] = ", ".join([tag.name for tag in blog_post.tags.all()])
    
    # Word count estimate from reading time (200 wpm)
    if blog_post.reading_time_minutes:
        schema["wordCount"] = blog_post.reading_time_minutes * 200
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema, indent=2)}</script>')


@register.simple_tag
def organization_jsonld():
    """
    Generate Organization JSON-LD for the site.
    
    Usage: {% organization_jsonld %}
    """
    site_url = get_site_url()
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": get_site_name(),
        "url": site_url,
        "logo": get_site_logo(),
        "description": "IngredientIQ provides AI-powered food intelligence and nutrition analysis.",
        "sameAs": [
            # Add your social profiles here
            # "https://twitter.com/ingredientiq",
            # "https://linkedin.com/company/ingredientiq",
        ]
    }
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema, indent=2)}</script>')


@register.simple_tag
def author_jsonld(author):
    """
    Generate Person JSON-LD for an author page.
    
    Usage: {% author_jsonld author %}
    """
    site_url = get_site_url()
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": author.name,
        "url": f"{site_url}/blog/author/{author.slug}/",
    }
    
    if author.job_title:
        schema["jobTitle"] = author.job_title
    
    if author.bio:
        schema["description"] = author.bio
    
    if author.avatar:
        schema["image"] = f"{site_url}{author.avatar.url}"
    
    # Social profiles
    same_as = []
    if author.twitter:
        same_as.append(author.twitter)
    if author.linkedin:
        same_as.append(author.linkedin)
    if author.instagram:
        same_as.append(author.instagram)
    if author.website:
        same_as.append(author.website)
    if same_as:
        schema["sameAs"] = same_as
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema, indent=2)}</script>')


@register.simple_tag
def breadcrumb_jsonld(breadcrumbs):
    """
    Generate BreadcrumbList JSON-LD.
    
    Usage: 
        {% breadcrumb_jsonld breadcrumbs %}
    
    Where breadcrumbs is a list of tuples: [(name, url), ...]
    Example: [('Home', '/'), ('Blog', '/blog/'), ('Article Title', None)]
    """
    site_url = get_site_url()
    
    items = []
    for i, (name, url) in enumerate(breadcrumbs, 1):
        item = {
            "@type": "ListItem",
            "position": i,
            "name": name,
        }
        if url:
            item["item"] = f"{site_url}{url}"
        items.append(item)
    
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items
    }
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema, indent=2)}</script>')


@register.simple_tag
def faq_jsonld(faqs):
    """
    Generate FAQPage JSON-LD for FAQ content.
    
    Usage: {% faq_jsonld faq_list %}
    
    Where faqs is a list of objects with 'question' and 'answer' attributes.
    """
    items = []
    for faq in faqs:
        items.append({
            "@type": "Question",
            "name": getattr(faq, 'question', str(faq)),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": getattr(faq, 'answer', '')
            }
        })
    
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": items
    }
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema, indent=2)}</script>')


@register.simple_tag
def website_jsonld():
    """
    Generate WebSite JSON-LD with search action.
    
    Usage: {% website_jsonld %}
    """
    site_url = get_site_url()
    
    schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": get_site_name(),
        "url": site_url,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{site_url}/blog/?search={{search_term_string}}"
            },
            "query-input": "required name=search_term_string"
        }
    }
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema, indent=2)}</script>')
