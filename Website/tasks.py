"""
Brita Filter CMS - Celery Tasks

Async tasks for:
- OG image generation
- Link checking
- Content processing for large batches
- Sitemap regeneration
- Feed pinging
"""

import logging
import hashlib
import requests
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Note: Celery is optional. These functions can be called synchronously if Celery is not installed.
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    # Celery not installed - create a no-op decorator
    CELERY_AVAILABLE = False
    def shared_task(func):
        return func


# ============================================
# LINK CHECKING
# ============================================

@shared_task
def check_post_links(post_id: int) -> Dict:
    """
    Check all links in a blog post for validity.
    
    Returns dict with:
    - total_links: int
    - valid_links: int
    - broken_links: list of {url, status_code, error}
    - warnings: list of {url, warning}
    """
    from .models import Blogs
    import re
    
    try:
        post = Blogs.objects.get(pk=post_id)
    except Blogs.DoesNotExist:
        return {'error': 'Post not found'}
    
    body = post.body_html or post.body or ''
    
    # Extract all links
    link_pattern = r'href=["\']([^"\']+)["\']'
    urls = re.findall(link_pattern, body, re.IGNORECASE)
    
    results = {
        'total_links': len(urls),
        'valid_links': 0,
        'broken_links': [],
        'warnings': [],
        'checked_at': timezone.now().isoformat(),
    }
    
    for url in urls:
        # Skip non-HTTP links
        if url.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
            continue
        
        # Check relative links
        if url.startswith('/'):
            results['warnings'].append({
                'url': url,
                'warning': 'Relative link - cannot verify externally'
            })
            continue
        
        try:
            # Make HEAD request with timeout
            response = requests.head(
                url, 
                timeout=10, 
                allow_redirects=True,
                headers={'User-Agent': 'Brita-CMS-LinkChecker/1.0'}
            )
            
            if response.status_code < 400:
                results['valid_links'] += 1
            else:
                results['broken_links'].append({
                    'url': url,
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}'
                })
        except requests.exceptions.Timeout:
            results['broken_links'].append({
                'url': url,
                'status_code': None,
                'error': 'Timeout'
            })
        except requests.exceptions.SSLError:
            results['warnings'].append({
                'url': url,
                'warning': 'SSL certificate error'
            })
        except requests.exceptions.RequestException as e:
            results['broken_links'].append({
                'url': url,
                'status_code': None,
                'error': str(e)[:100]
            })
    
    # Update post with link check results
    # Store in a new field or in validation_warnings
    if results['broken_links']:
        warnings = list(post.validation_warnings or [])
        for broken in results['broken_links'][:5]:
            warnings.append(f"Broken link: {broken['url'][:50]} ({broken['error']})")
        post.validation_warnings = warnings
        post.save(update_fields=['validation_warnings'])
    
    logger.info(f"Link check for post {post_id}: {results['valid_links']}/{results['total_links']} valid")
    
    return results


@shared_task
def check_all_published_links() -> Dict:
    """
    Check links for all published posts.
    Run periodically to catch newly broken links.
    """
    from .models import Blogs
    
    posts = Blogs.objects.filter(status='published')
    results = {
        'total_posts': posts.count(),
        'posts_with_broken_links': 0,
        'total_broken_links': 0,
    }
    
    for post in posts:
        result = check_post_links(post.id)
        if result.get('broken_links'):
            results['posts_with_broken_links'] += 1
            results['total_broken_links'] += len(result['broken_links'])
    
    return results


# ============================================
# OG IMAGE GENERATION
# ============================================

@shared_task
def generate_og_image(post_id: int, force: bool = False) -> Optional[str]:
    """
    Generate an Open Graph image for a blog post.
    
    Uses a template to create an image with:
    - Title text
    - Brand/category color
    - Author name
    
    Returns the path to the generated image, or None if generation failed.
    
    Note: This is a placeholder. For production, integrate with:
    - Pillow for local generation
    - Cloudinary/Imgix for cloud-based generation
    - A headless browser for HTML-to-image
    """
    from .models import Blogs
    
    try:
        post = Blogs.objects.get(pk=post_id)
    except Blogs.DoesNotExist:
        logger.error(f"Post {post_id} not found for OG image generation")
        return None
    
    # Skip if already has custom OG image and not forced
    if post.og_image and not force:
        logger.info(f"Post {post_id} already has OG image, skipping")
        return post.og_image.url if hasattr(post.og_image, 'url') else None
    
    # For now, log that we would generate an image
    # In production, implement actual image generation here
    logger.info(f"Would generate OG image for post {post_id}: '{post.title}'")
    
    # Placeholder: return None to indicate no image was generated
    # In production, this would:
    # 1. Render an HTML template with post title, author, category
    # 2. Convert to image (1200x630px)
    # 3. Save to media storage
    # 4. Return the file path
    
    return None


@shared_task
def regenerate_all_og_images() -> Dict:
    """
    Regenerate OG images for all posts that don't have one.
    """
    from .models import Blogs
    
    posts = Blogs.objects.filter(og_image='').exclude(title='')
    results = {
        'total': posts.count(),
        'generated': 0,
        'failed': 0,
    }
    
    for post in posts:
        result = generate_og_image(post.id)
        if result:
            results['generated'] += 1
        else:
            results['failed'] += 1
    
    return results


# ============================================
# CONTENT PROCESSING
# ============================================

@shared_task
def reprocess_post_pipeline(post_id: int) -> Dict:
    """
    Reprocess a single post through the Brita pipeline.
    Useful for batch updates after pipeline improvements.
    """
    from .models import Blogs
    
    try:
        post = Blogs.objects.get(pk=post_id)
    except Blogs.DoesNotExist:
        return {'error': 'Post not found'}
    
    if not post.raw_draft:
        return {'error': 'No raw_draft to process'}
    
    # Force reprocess
    post.process_through_brita_pipeline(force=True)
    post.save()
    
    return {
        'success': True,
        'post_id': post_id,
        'title': post.title,
        'word_count': post.word_count,
        'errors': len(post.validation_errors or []),
        'warnings': len(post.validation_warnings or []),
    }


@shared_task
def reprocess_all_posts() -> Dict:
    """
    Reprocess all posts with raw_draft through the pipeline.
    """
    from .models import Blogs
    
    posts = Blogs.objects.exclude(raw_draft='')
    results = {
        'total': posts.count(),
        'processed': 0,
        'failed': 0,
    }
    
    for post in posts:
        try:
            result = reprocess_post_pipeline(post.id)
            if result.get('success'):
                results['processed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            logger.error(f"Failed to reprocess post {post.id}: {e}")
            results['failed'] += 1
    
    return results


# ============================================
# SITEMAP & FEED PINGING
# ============================================

PING_ENDPOINTS = [
    ('Google', 'https://www.google.com/ping?sitemap='),
    ('Bing', 'https://www.bing.com/indexnow'),
    # Add more as needed
]


@shared_task
def ping_search_engines(sitemap_url: str = None) -> Dict:
    """
    Ping search engines to notify them of sitemap updates.
    """
    if not sitemap_url:
        sitemap_url = getattr(settings, 'SITE_URL', '') + '/sitemap.xml'
    
    if not sitemap_url.startswith('http'):
        return {'error': 'Invalid sitemap URL'}
    
    results = {
        'sitemap': sitemap_url,
        'pings': []
    }
    
    for name, endpoint in PING_ENDPOINTS:
        try:
            if 'sitemap=' in endpoint:
                url = endpoint + sitemap_url
            else:
                url = endpoint
            
            response = requests.get(url, timeout=10)
            results['pings'].append({
                'service': name,
                'status': response.status_code,
                'success': response.status_code < 400
            })
        except requests.RequestException as e:
            results['pings'].append({
                'service': name,
                'status': None,
                'success': False,
                'error': str(e)[:100]
            })
    
    return results


@shared_task
def on_post_publish(post_id: int) -> Dict:
    """
    Tasks to run when a post is published:
    1. Check links
    2. Generate OG image if needed
    3. Ping search engines
    """
    results = {
        'post_id': post_id,
        'tasks': {}
    }
    
    # Link check
    link_result = check_post_links(post_id)
    results['tasks']['link_check'] = {
        'broken_links': len(link_result.get('broken_links', []))
    }
    
    # OG image
    og_result = generate_og_image(post_id)
    results['tasks']['og_image'] = {
        'generated': og_result is not None
    }
    
    # Ping search engines
    ping_result = ping_search_engines()
    results['tasks']['ping'] = {
        'success': all(p.get('success') for p in ping_result.get('pings', []))
    }
    
    return results


# ============================================
# ANALYTICS & REPORTING
# ============================================

@shared_task
def generate_content_report() -> Dict:
    """
    Generate a content health report.
    """
    from .models import Blogs
    from django.db.models import Avg, Count, Q
    
    total = Blogs.objects.count()
    published = Blogs.objects.filter(status='published').count()
    draft = Blogs.objects.filter(status='draft').count()
    
    with_errors = Blogs.objects.exclude(validation_errors=[]).count()
    with_warnings = Blogs.objects.exclude(validation_warnings=[]).count()
    
    # Content stats
    stats = Blogs.objects.aggregate(
        avg_word_count=Avg('word_count'),
        avg_reading_time=Avg('reading_time_minutes'),
    )
    
    # Posts by category
    by_category = list(
        Blogs.objects.values('category_new__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    # Posts by author
    by_author = list(
        Blogs.objects.values('author_entity__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    return {
        'generated_at': timezone.now().isoformat(),
        'counts': {
            'total': total,
            'published': published,
            'draft': draft,
            'with_errors': with_errors,
            'with_warnings': with_warnings,
        },
        'averages': {
            'word_count': round(stats['avg_word_count'] or 0),
            'reading_time': round(stats['avg_reading_time'] or 0),
        },
        'by_category': by_category,
        'by_author': by_author,
    }


# ============================================
# HELPER: RUN SYNCHRONOUSLY IF NO CELERY
# ============================================

def run_task_sync(task_func, *args, **kwargs):
    """
    Run a task synchronously if Celery is not available.
    Use this for development or when you don't want to set up Celery.
    """
    if CELERY_AVAILABLE and hasattr(task_func, 'delay'):
        return task_func.delay(*args, **kwargs)
    else:
        return task_func(*args, **kwargs)
