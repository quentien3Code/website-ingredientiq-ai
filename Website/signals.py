"""
Brita Filter CMS - Django Signals

Provides:
1. Pre-save validation and processing
2. Post-save hooks for async tasks
3. Publish gate enforcement
4. Status change tracking
"""

import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)


# ============================================
# PRE-SAVE SIGNALS
# ============================================

@receiver(pre_save, sender='Website.Blogs')
def blogs_pre_save(sender, instance, **kwargs):
    """
    Pre-save processing for blog posts.
    
    - Enforces publish gates
    - Tracks status changes
    - Validates governance requirements
    """
    from .models import Blogs
    
    # Track if this is a new post or an update
    if instance.pk:
        try:
            old_instance = Blogs.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
            instance._was_published = old_instance.status == 'published'
        except Blogs.DoesNotExist:
            instance._old_status = None
            instance._was_published = False
    else:
        instance._old_status = None
        instance._was_published = False
    
    # ============================================
    # PUBLISH GATE ENFORCEMENT
    # ============================================
    
    if instance.status == 'published' and not instance._was_published:
        # This is a publish attempt - run validation
        can_publish, errors, warnings = instance.can_publish()
        
        if not can_publish:
            # Option 1: Raise validation error (strict mode)
            # raise ValidationError({
            #     'status': f"Cannot publish: {', '.join(errors[:3])}"
            # })
            
            # Option 2: Prevent status change (soft mode)
            logger.warning(
                f"Publish gate blocked for post '{instance.title}': {errors}"
            )
            # Keep as draft/review instead of raising error
            # Uncomment below to block publish:
            # instance.status = instance._old_status or 'draft'
            
            # For now, just update validation fields
            instance.validation_errors = errors
            instance.validation_warnings = warnings
    
    # ============================================
    # SCHEDULED POST HANDLING
    # ============================================
    
    if instance.status == 'scheduled':
        if not instance.publish_date:
            raise ValidationError({
                'publish_date': "Scheduled posts require a publish date."
            })
        if instance.publish_date <= timezone.now():
            # Past scheduled date - publish immediately
            instance.status = 'published'
    
    # ============================================
    # COMPLIANCE REVIEW ENFORCEMENT
    # ============================================
    
    if instance.requires_compliance_review:
        if instance.status == 'published' and not instance.reviewed_at:
            logger.warning(
                f"Post '{instance.title}' requires review but was published without it"
            )
            # Optionally block:
            # instance.status = 'review'


# ============================================
# POST-SAVE SIGNALS
# ============================================

@receiver(post_save, sender='Website.Blogs')
def blogs_post_save(sender, instance, created, **kwargs):
    """
    Post-save actions for blog posts.
    
    - Trigger async tasks on publish
    - Update sitemap
    - Log significant events
    """
    from .tasks import run_task_sync, check_post_links, generate_og_image, ping_search_engines
    
    # Detect if this was just published
    just_published = (
        instance.status == 'published' and 
        getattr(instance, '_old_status', None) != 'published'
    )
    
    if just_published:
        logger.info(f"Post published: '{instance.title}' (ID: {instance.pk})")
        
        # ============================================
        # POST-PUBLISH TASKS (async if Celery available)
        # ============================================
        
        # 1. Check links (non-blocking)
        try:
            run_task_sync(check_post_links, instance.pk)
        except Exception as e:
            logger.error(f"Link check failed for post {instance.pk}: {e}")
        
        # 2. Generate OG image if missing
        if not instance.og_image:
            try:
                run_task_sync(generate_og_image, instance.pk)
            except Exception as e:
                logger.error(f"OG image generation failed for post {instance.pk}: {e}")
        
        # 3. Ping search engines (optional, can be slow)
        # Uncomment for production:
        # try:
        #     run_task_sync(ping_search_engines)
        # except Exception as e:
        #     logger.error(f"Search engine ping failed: {e}")
    
    # Log new post creation
    if created:
        logger.info(f"New post created: '{instance.title}' (ID: {instance.pk})")


# ============================================
# CATEGORY/TAG SIGNALS
# ============================================

@receiver(post_save, sender='Website.BlogCategory')
def category_post_save(sender, instance, created, **kwargs):
    """Log category changes for sitemap updates"""
    if created:
        logger.info(f"New category created: '{instance.name}'")


@receiver(post_save, sender='Website.BlogTag')
def tag_post_save(sender, instance, created, **kwargs):
    """Log tag changes"""
    if created:
        logger.info(f"New tag created: '{instance.name}'")


# ============================================
# SCHEDULED PUBLISHING (for use with cron/Celery beat)
# ============================================

def publish_scheduled_posts():
    """
    Publish all posts that are scheduled and past their publish date.
    Call this from a cron job or Celery beat schedule.
    """
    from .models import Blogs
    
    now = timezone.now()
    scheduled = Blogs.objects.filter(
        status='scheduled',
        publish_date__lte=now
    )
    
    count = 0
    for post in scheduled:
        can_publish, errors, _ = post.can_publish()
        if can_publish:
            post.status = 'published'
            post.save()
            count += 1
            logger.info(f"Auto-published scheduled post: '{post.title}'")
        else:
            logger.warning(
                f"Scheduled post '{post.title}' could not be published: {errors}"
            )
    
    return count


# ============================================
# CONTENT ARCHIVING
# ============================================

def archive_old_posts(days: int = 365):
    """
    Archive posts older than specified days.
    Call from management command or Celery beat.
    """
    from .models import Blogs
    from datetime import timedelta
    
    cutoff = timezone.now() - timedelta(days=days)
    old_posts = Blogs.objects.filter(
        status='published',
        publish_date__lt=cutoff
    )
    
    count = old_posts.update(status='archived')
    logger.info(f"Archived {count} posts older than {days} days")
    
    return count
