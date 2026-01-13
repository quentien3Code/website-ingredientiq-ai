"""
SEO Sitemaps for IngredientIQ Website

Provides XML sitemaps for:
- Blog posts (with images)
- Blog categories
- Blog tags
- Blog authors
- Static pages

Reference: https://docs.djangoproject.com/en/4.2/ref/contrib/sitemaps/
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Blogs, BlogCategory, BlogTag, BlogAuthor


class BlogSitemap(Sitemap):
    """
    Sitemap for published blog posts.
    Includes image information for Google Images indexing.
    """
    changefreq = "weekly"
    priority = 0.8
    protocol = "https"
    
    def items(self):
        return Blogs.objects.filter(
            status='published'
        ).order_by('-publish_date')
    
    def lastmod(self, obj):
        return obj.last_modified or obj.updated_at
    
    def location(self, obj):
        return f"/blog/{obj.slug}/"


class BlogCategorySitemap(Sitemap):
    """Sitemap for blog category pages."""
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"
    
    def items(self):
        return BlogCategory.objects.all()
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return f"/blog/category/{obj.slug}/"


class BlogTagSitemap(Sitemap):
    """Sitemap for blog tag pages."""
    changefreq = "weekly"
    priority = 0.5
    protocol = "https"
    
    def items(self):
        return BlogTag.objects.all()
    
    def location(self, obj):
        return f"/blog/tag/{obj.slug}/"


class BlogAuthorSitemap(Sitemap):
    """Sitemap for author bio pages."""
    changefreq = "monthly"
    priority = 0.6
    protocol = "https"
    
    def items(self):
        return BlogAuthor.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return f"/blog/author/{obj.slug}/"


class StaticSitemap(Sitemap):
    """Sitemap for static pages."""
    changefreq = "monthly"
    priority = 0.7
    protocol = "https"
    
    def items(self):
        return [
            '/',
            '/about/',
            '/contact/',
            '/blog/',
            '/privacy-policy/',
            '/terms-and-conditions/',
        ]
    
    def location(self, item):
        return item


# Sitemap index dictionary for URL configuration
sitemaps = {
    'blog': BlogSitemap,
    'categories': BlogCategorySitemap,
    'tags': BlogTagSitemap,
    'authors': BlogAuthorSitemap,
    'static': StaticSitemap,
}
