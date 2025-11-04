"""
Notification Tasks
Background tasks for notifications (optional - works without Celery)
"""

from django.utils import timezone
from datetime import timedelta
from .notification_utils import notification_manager
from .models import User, UserSubscription, AppVersion
import logging

logger = logging.getLogger(__name__)

# Try to import Celery, but don't fail if it's not available
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Create a dummy decorator for when Celery is not available
    def shared_task(func):
        return func

def check_subscription_expiry():
    """
    Check for expiring subscriptions and send notifications
    """
    try:
        logger.info("Starting subscription expiry check task")
        
        # Check for subscriptions expiring in 3 days
        result_3_days = notification_manager.check_expiring_subscriptions(days_ahead=3)
        
        # Check for subscriptions expiring in 1 day
        result_1_day = notification_manager.check_expiring_subscriptions(days_ahead=1)
        
        # Check for expired subscriptions (0 days)
        result_expired = notification_manager.check_expiring_subscriptions(days_ahead=0)
        
        # Send expired notifications with different template
        if result_expired.get('total_expiring', 0) > 0:
            expired_subscriptions = UserSubscription.objects.filter(
                plan_name='premium',
                status='active'
            )
            
            for subscription in expired_subscriptions:
                try:
                    # For now, we'll just send the notification directly
                    # In a real implementation, you'd check actual expiry dates
                    notification_manager.send_subscription_notification(
                        user_id=subscription.user.id,
                        notification_type='subscription_expired',
                        plan_type=subscription.premium_type
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing expired subscription {subscription.id}: {e}")
        
        total_results = {
            'expiring_3_days': result_3_days,
            'expiring_1_day': result_1_day,
            'expired': result_expired
        }
        
        logger.info(f"Subscription expiry check completed: {total_results}")
        return total_results
        
    except Exception as e:
        logger.error(f"Error in subscription expiry check task: {e}")
        return {'error': str(e)}

def send_app_update_notifications(platform=None):
    """
    Send app update notifications
    """
    try:
        logger.info(f"Starting app update notification task for platform: {platform}")
        
        result = notification_manager.send_app_update_notification(platform=platform)
        
        logger.info(f"App update notification task completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in app update notification task: {e}")
        return {'error': str(e)}

def send_welcome_notification_task(user_id):
    """
    Send welcome notification to new user
    """
    try:
        logger.info(f"Sending welcome notification to user {user_id}")
        
        result = notification_manager.send_welcome_notification(user_id)
        
        logger.info(f"Welcome notification sent to user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending welcome notification to user {user_id}: {e}")
        return {'error': str(e)}

def send_subscription_notification_task(user_id, notification_type, **kwargs):
    """
    Send subscription-related notifications
    """
    try:
        logger.info(f"Sending {notification_type} notification to user {user_id}")
        
        result = notification_manager.send_subscription_notification(
            user_id=user_id,
            notification_type=notification_type,
            **kwargs
        )
        
        logger.info(f"Subscription notification sent to user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending subscription notification to user {user_id}: {e}")
        return {'error': str(e)}

def send_scan_limit_notification_task(user_id, remaining_scans=0):
    """
    Send scan limit notification
    """
    try:
        logger.info(f"Sending scan limit notification to user {user_id}")
        
        result = notification_manager.send_scan_limit_notification(
            user_id=user_id,
            remaining_scans=remaining_scans
        )
        
        logger.info(f"Scan limit notification sent to user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending scan limit notification to user {user_id}: {e}")
        return {'error': str(e)}

def send_bulk_custom_notification(user_ids, title, body, data=None, action_url=None):
    """
    Send custom notifications to multiple users
    """
    try:
        logger.info(f"Sending custom notification to {len(user_ids)} users")
        
        result = notification_manager.send_custom_notification(
            user_ids=user_ids,
            title=title,
            body=body,
            data=data,
            action_url=action_url
        )
        
        logger.info(f"Custom notification sent: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending custom notification: {e}")
        return {'error': str(e)}

def cleanup_old_notifications():
    """
    Cleanup old notification logs
    """
    try:
        logger.info("Starting notification cleanup task")
        
        # Delete notifications older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        
        from .models import PushNotification
        deleted_count = PushNotification.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return {'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f"Error in notification cleanup task: {e}")
        return {'error': str(e)}

def cleanup_inactive_device_tokens():
    """
    Cleanup inactive device tokens
    """
    try:
        logger.info("Starting device token cleanup task")
        
        # Delete inactive tokens older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        
        from .models import DeviceToken
        deleted_count = DeviceToken.objects.filter(
            is_active=False,
            updated_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} inactive device tokens")
        return {'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f"Error in device token cleanup task: {e}")
        return {'error': str(e)}

# If Celery is available, create the shared_task versions
if CELERY_AVAILABLE:
    @shared_task
    def check_subscription_expiry_task():
        return check_subscription_expiry()
    
    @shared_task
    def send_app_update_notifications_task(platform=None):
        return send_app_update_notifications(platform)
    
    @shared_task
    def send_welcome_notification_task_celery(user_id):
        return send_welcome_notification_task(user_id)
    
    @shared_task
    def send_subscription_notification_task_celery(user_id, notification_type, **kwargs):
        return send_subscription_notification_task(user_id, notification_type, **kwargs)
    
    @shared_task
    def send_scan_limit_notification_task_celery(user_id, remaining_scans=0):
        return send_scan_limit_notification_task(user_id, remaining_scans)
    
    @shared_task
    def send_bulk_custom_notification_task(user_ids, title, body, data=None, action_url=None):
        return send_bulk_custom_notification(user_ids, title, body, data, action_url)
    
    @shared_task
    def cleanup_old_notifications_task():
        return cleanup_old_notifications()
    
    @shared_task
    def cleanup_inactive_device_tokens_task():
        return cleanup_inactive_device_tokens()
else:
    logger.info("Celery not available - using direct function calls for notifications")

def safe_execute_task(task_func, *args, **kwargs):
    """
    Safely execute a task with fallback to direct function call if Celery fails.
    
    Args:
        task_func: The Celery task function to execute
        *args: Arguments to pass to the task
        **kwargs: Keyword arguments to pass to the task
    
    Returns:
        The result of the task execution
    """
    try:
        # Try to execute as Celery task
        if hasattr(task_func, 'delay'):
            result = task_func.delay(*args, **kwargs)
            logger.info(f"Task {task_func.__name__} queued successfully")
            return result
        else:
            # Fallback to direct execution
            logger.warning(f"Task {task_func.__name__} has no delay method, executing directly")
            return task_func(*args, **kwargs)
    except Exception as e:
        # If Celery task fails, try direct execution
        logger.warning(f"Celery task {task_func.__name__} failed: {e}. Falling back to direct execution.")
        try:
            # Get the underlying function if it's a Celery task
            if hasattr(task_func, 'func'):
                actual_func = task_func.func
            else:
                actual_func = task_func
            
            result = actual_func(*args, **kwargs)
            logger.info(f"Direct execution of {task_func.__name__} completed successfully")
            return result
        except Exception as direct_error:
            logger.error(f"Direct execution of {task_func.__name__} also failed: {direct_error}")
            return {'error': str(direct_error)}