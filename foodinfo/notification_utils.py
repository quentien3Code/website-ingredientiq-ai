"""
Notification Utilities
Helper functions for notification management
"""

from .firebase_service import firebase_service
from .lifecycle_notifications import lifecycle_notifications
from .models import User, PushNotification, UserSubscription
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manager class for handling notification operations"""
    
    def __init__(self):
        self.firebase_service = firebase_service
    
    def send_notification(self, user_id, title, body, notification_type='custom', data=None):
        """Send notification to a specific user"""
        try:
            result = self.firebase_service.send_notification(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=notification_type,
                data=data
            )
            return result
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_bulk_notifications(self, user_ids, title, body, notification_type='custom', data=None):
        """Send notification to multiple users"""
        results = []
        for user_id in user_ids:
            result = self.send_notification(user_id, title, body, notification_type, data)
            results.append({
                'user_id': user_id,
                'result': result
            })
        return results
    
    def get_user_notifications(self, user_id, limit=50):
        """Get notification history for a user"""
        try:
            notifications = PushNotification.objects.filter(
                user_id=user_id
            ).order_by('-created_at')[:limit]
            return notifications
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {e}")
            return []
    
    def get_notification_stats(self):
        """Get notification statistics"""
        try:
            from django.db.models import Count
            from datetime import datetime, timedelta
            
            # Get stats for last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            stats = {
                'total_notifications': PushNotification.objects.count(),
                'notifications_last_30_days': PushNotification.objects.filter(
                    created_at__gte=thirty_days_ago
                ).count(),
                'successful_notifications': PushNotification.objects.filter(
                    status='sent'
                ).count(),
                'failed_notifications': PushNotification.objects.filter(
                    status='failed'
                ).count(),
                'notification_types': PushNotification.objects.values(
                    'notification_type'
                ).annotate(
                    count=Count('id')
                ).order_by('-count')[:10]
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            return {}
    
    def cleanup_old_notifications(self, days_old=90):
        """Clean up old notifications"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            deleted_count = PushNotification.objects.filter(
                created_at__lt=cutoff_date
            ).delete()[0]
            
            logger.info(f"Cleaned up {deleted_count} old notifications")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old notifications: {e}")
            return 0
    
    # Lifecycle notification methods
    def send_welcome_notification(self, user_id):
        """Send welcome notification to user"""
        try:
            user = User.objects.get(id=user_id)
            return lifecycle_notifications.send_welcome_notification(user)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found for welcome notification")
            return {'success': False, 'error': 'User not found'}
        except Exception as e:
            logger.error(f"Error sending welcome notification to user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_subscription_notification(self, user_id, notification_type, **kwargs):
        """Send subscription notification to user"""
        try:
            user = User.objects.get(id=user_id)
            
            if notification_type == 'subscription_purchased':
                plan_name = kwargs.get('plan_name', 'premium')
                premium_type = kwargs.get('premium_type')
                return lifecycle_notifications.send_subscription_purchased_notification(
                    user, plan_name, premium_type
                )
            elif notification_type == 'subscription_cancelled':
                plan_name = kwargs.get('plan_name', 'premium')
                return lifecycle_notifications.send_subscription_cancelled_notification(
                    user, plan_name
                )
            elif notification_type == 'subscription_upgraded':
                old_plan = kwargs.get('old_plan', 'freemium')
                new_plan = kwargs.get('new_plan', 'premium')
                return lifecycle_notifications.send_subscription_upgraded_notification(
                    user, old_plan, new_plan
                )
            elif notification_type == 'subscription_expiring':
                days_remaining = kwargs.get('days_remaining', 7)
                return lifecycle_notifications.send_subscription_expiring_notification(
                    user, days_remaining
                )
            elif notification_type == 'subscription_expired':
                return lifecycle_notifications.send_subscription_expired_notification(user)
            else:
                logger.error(f"Unknown subscription notification type: {notification_type}")
                return {'success': False, 'error': 'Unknown notification type'}
                
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found for subscription notification")
            return {'success': False, 'error': 'User not found'}
        except Exception as e:
            logger.error(f"Error sending subscription notification to user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_scan_limit_notification(self, user_id, remaining_scans=0):
        """Send scan limit notification to user"""
        try:
            user = User.objects.get(id=user_id)
            return lifecycle_notifications.send_scan_limit_warning_notification(
                user, remaining_scans
            )
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found for scan limit notification")
            return {'success': False, 'error': 'User not found'}
        except Exception as e:
            logger.error(f"Error sending scan limit notification to user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_custom_notification(self, user_ids, title, body, data=None, action_url=None):
        """Send custom notification to multiple users"""
        try:
            results = []
            for user_id in user_ids:
                result = self.send_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type='custom',
                    data=data
                )
                results.append({
                    'user_id': user_id,
                    'result': result
                })
            return results
        except Exception as e:
            logger.error(f"Error sending custom notification: {e}")
            return {'error': str(e)}
    
    def send_app_update_notification(self, platform=None):
        """Send app update notification to users"""
        try:
            # Get current app version for the platform
            from .models import AppVersion
            try:
                app_version = AppVersion.objects.filter(
                    platform=platform,
                    is_current=True
                ).first()
                
                if app_version:
                    # Send to all users or specific platform users
                    users = User.objects.filter(notifications_enabled=True)
                    
                    results = []
                    for user in users:
                        result = lifecycle_notifications.send_app_update_notification(
                            user, 
                            app_version.version, 
                            app_version.release_notes
                        )
                        results.append({
                            'user_id': user.id,
                            'result': result
                        })
                    
                    return {
                        'success': True,
                        'sent_count': len(results),
                        'results': results
                    }
                else:
                    logger.warning(f"No current app version found for platform: {platform}")
                    return {'success': False, 'error': 'No current app version found'}
                    
            except AppVersion.DoesNotExist:
                logger.warning(f"No app version found for platform: {platform}")
                return {'success': False, 'error': 'No app version found'}
                
        except Exception as e:
            logger.error(f"Error sending app update notification: {e}")
            return {'error': str(e)}
    
    def check_expiring_subscriptions(self, days_ahead=7):
        """Check for subscriptions expiring in specified days"""
        try:
            from datetime import datetime, timedelta
            
            # Calculate expiry date
            expiry_date = datetime.now() + timedelta(days=days_ahead)
            
            # Get subscriptions expiring around that date
            expiring_subscriptions = UserSubscription.objects.filter(
                plan_name='premium',
                status='active'
            )
            
            total_expiring = 0
            notifications_sent = 0
            
            for subscription in expiring_subscriptions:
                try:
                    # For now, we'll send notifications to all premium users
                    # In a real implementation, you'd check actual expiry dates
                    result = lifecycle_notifications.send_subscription_expiring_notification(
                        subscription.user, days_ahead
                    )
                    
                    if result['success']:
                        notifications_sent += 1
                    
                    total_expiring += 1
                    
                except Exception as e:
                    logger.error(f"Error processing expiring subscription {subscription.id}: {e}")
            
            return {
                'total_expiring': total_expiring,
                'notifications_sent': notifications_sent,
                'days_ahead': days_ahead
            }
            
        except Exception as e:
            logger.error(f"Error checking expiring subscriptions: {e}")
            return {'error': str(e)}

# Global instance
notification_manager = NotificationManager() 