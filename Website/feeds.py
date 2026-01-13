"""
RSS/Atom Feeds for IngredientIQ Blog

Provides syndication feeds for:
- Latest blog posts (RSS 2.0)
- Latest blog posts (Atom 1.0)
- Category-specific feeds
- Tag-specific feeds

Reference: https://docs.djangoproject.com/en/4.2/ref/contrib/syndication/
"""
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.urls import reverse
from django.conf import settings
from .models import Blogs, BlogCategory, BlogTag


class LatestBlogsFeed(Feed):
    """
    RSS 2.0 feed for latest blog posts.
    URL: /blog/feed/rss/
    """
    title = "IngredientIQ Blog"
    link = "/blog/"
    description = "Latest articles from IngredientIQ - Food intelligence and nutrition insights."
    
    def items(self):
        return Blogs.objects.filter(
            status='published'
        ).order_by('-publish_date')[:20]
    
    def item_title(self, item):
        return item.title
    
    def item_description(self, item):
        return item.excerpt or item.get_meta_description()
    
    def item_link(self, item):
        return f"/blog/{item.slug}/"
    
    def item_pubdate(self, item):
        return item.publish_date
    
    def item_updateddate(self, item):
        return item.last_modified or item.updated_at
    
    def item_author_name(self, item):
        if item.author_entity:
            return item.author_entity.name
        return item.author or "IngredientIQ Team"
    
    def item_categories(self, item):
        categories = []
        if item.category_new:
            categories.append(item.category_new.name)
        categories.extend([tag.name for tag in item.tags.all()])
        return categories


class LatestBlogsAtomFeed(LatestBlogsFeed):
    """
    Atom 1.0 feed for latest blog posts.
    URL: /blog/feed/atom/
    """
    feed_type = Atom1Feed
    subtitle = LatestBlogsFeed.description


class CategoryFeed(Feed):
    """
    RSS feed for posts in a specific category.
    URL: /blog/category/<slug>/feed/
    """
    
    def get_object(self, request, slug):
        return BlogCategory.objects.get(slug=slug)
    
    def title(self, obj):
        return f"IngredientIQ Blog - {obj.name}"
    
    def link(self, obj):
        return f"/blog/category/{obj.slug}/"
    
    def description(self, obj):
        return obj.description or f"Latest articles in {obj.name} from IngredientIQ."
    
    def items(self, obj):
        return Blogs.objects.filter(
            status='published',
            category_new=obj
        ).order_by('-publish_date')[:20]
    
    def item_title(self, item):
        return item.title
    
    def item_description(self, item):
        return item.excerpt or item.get_meta_description()
    
    def item_link(self, item):
        return f"/blog/{item.slug}/"
    
    def item_pubdate(self, item):
        return item.publish_date


class TagFeed(Feed):
    """
    RSS feed for posts with a specific tag.
    URL: /blog/tag/<slug>/feed/
    """
    
    def get_object(self, request, slug):
        return BlogTag.objects.get(slug=slug)
    
    def title(self, obj):
        return f"IngredientIQ Blog - #{obj.name}"
    
    def link(self, obj):
        return f"/blog/tag/{obj.slug}/"
    
    def description(self, obj):
        return f"Latest articles tagged with {obj.name} from IngredientIQ."
    
    def items(self, obj):
        return Blogs.objects.filter(
            status='published',
            tags=obj
        ).order_by('-publish_date')[:20]
    
    def item_title(self, item):
        return item.title
    
    def item_description(self, item):
        return item.excerpt or item.get_meta_description()
    
    def item_link(self, item):
        return f"/blog/{item.slug}/"
    
    def item_pubdate(self, item):
        return item.publish_date
