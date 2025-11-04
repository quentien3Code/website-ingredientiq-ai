"""
Lifecycle Notification Service
Handles all user lifecycle notifications (signup, subscription, etc.)
"""

from .firebase_service import firebase_service
from .models import User, UserSubscription, NotificationTemplate
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class LifecycleNotificationService:
    """Service for handling user lifecycle notifications"""
    
    @staticmethod
    def send_welcome_notification(user):
        """Send welcome notification when user signs up"""
        try:
            # Prepare user data for template
            user_data = {
                'full_name': user.full_name,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'email': user.email
            }
            
            # Send using template
            result = firebase_service.send_notification_from_template(
                user_id=user.id,
                template_type='welcome',
                user_data=user_data,
                custom_data={
                    'action': 'open_app',
                    'screen': 'onboarding'
                }
            )
            
            logger.info(f"Welcome notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending welcome notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_subscription_purchased_notification(user, plan_name, premium_type):
        """Send notification when user purchases subscription"""
        try:
            # Check if subscription notifications are enabled for this user
            if not user.subscription_notifications_enabled:
                logger.info(f"Subscription notifications disabled for user {user.id}, skipping subscription purchased notification")
                return {'success': False, 'error': 'Subscription notifications disabled'}
            
            # Prepare user data for template
            user_data = {
                'full_name': user.full_name,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'plan_name': plan_name,
                'premium_type': premium_type
            }
            
            # Send using template
            result = firebase_service.send_notification_from_template(
                user_id=user.id,
                template_type='subscription_purchased',
                user_data=user_data,
                custom_data={
                    'action': 'open_app',
                    'screen': 'premium_features',
                    'plan': plan_name,
                    'type': premium_type
                }
            )
            
            logger.info(f"Subscription purchased notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending subscription purchased notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_subscription_cancelled_notification(user, plan_name):
        """Send notification when user cancels subscription"""
        try:
            # Check if subscription notifications are enabled for this user
            if not user.subscription_notifications_enabled:
                logger.info(f"Subscription notifications disabled for user {user.id}, skipping subscription cancelled notification")
                return {'success': False, 'error': 'Subscription notifications disabled'}
            
            # Prepare user data for template
            user_data = {
                'full_name': user.full_name,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'plan_name': plan_name
            }
            
            # Send using template
            result = firebase_service.send_notification_from_template(
                user_id=user.id,
                template_type='subscription_cancelled',
                user_data=user_data,
                custom_data={
                    'action': 'open_app',
                    'screen': 'subscription',
                    'plan': plan_name
                }
            )
            
            logger.info(f"Subscription cancelled notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending subscription cancelled notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_subscription_upgraded_notification(user, old_plan, new_plan):
        """Send notification when user upgrades subscription"""
        try:
            # Check if subscription notifications are enabled for this user
            if not user.subscription_notifications_enabled:
                logger.info(f"Subscription notifications disabled for user {user.id}, skipping subscription upgraded notification")
                return {'success': False, 'error': 'Subscription notifications disabled'}
            
            title = f"🎉 Subscription Upgraded!"
            body = f"Hi {user.full_name}, you've successfully upgraded from {old_plan.title()} to {new_plan.title()} Plan. Enjoy your new features!"
            
            result = firebase_service.send_notification(
                user_id=user.id,
                title=title,
                body=body,
                notification_type='subscription_upgraded',
                data={
                    'action': 'open_app',
                    'screen': 'premium_features',
                    'old_plan': old_plan,
                    'new_plan': new_plan
                }
            )
            
            logger.info(f"Subscription upgraded notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending subscription upgraded notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_subscription_expiring_notification(user, days_remaining):
        """Send notification when subscription is expiring soon"""
        try:
            # Check if subscription notifications are enabled for this user
            if not user.subscription_notifications_enabled:
                logger.info(f"Subscription notifications disabled for user {user.id}, skipping subscription expiring notification")
                return {'success': False, 'error': 'Subscription notifications disabled'}
            
            # Prepare user data for template
            user_data = {
                'full_name': user.full_name,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'days_left': days_remaining,
                'plan_name': getattr(user, 'current_plan', 'Premium')
            }
            
            # Send using template
            result = firebase_service.send_notification_from_template(
                user_id=user.id,
                template_type='subscription_expiring',
                user_data=user_data,
                custom_data={
                    'action': 'open_app',
                    'screen': 'subscription',
                    'days_remaining': days_remaining
                }
            )
            
            logger.info(f"Subscription expiring notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending subscription expiring notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_subscription_expired_notification(user):
        """Send notification when subscription has expired"""
        try:
            # Check if subscription notifications are enabled for this user
            if not user.subscription_notifications_enabled:
                logger.info(f"Subscription notifications disabled for user {user.id}, skipping subscription expired notification")
                return {'success': False, 'error': 'Subscription notifications disabled'}
            
            # Prepare user data for template
            user_data = {
                'full_name': user.full_name,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', '')
            }
            
            # Send using template
            result = firebase_service.send_notification_from_template(
                user_id=user.id,
                template_type='subscription_expired',
                user_data=user_data,
                custom_data={
                    'action': 'open_app',
                    'screen': 'subscription'
                }
            )
            
            logger.info(f"Subscription expired notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending subscription expired notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_scan_limit_warning_notification(user, scans_remaining):
        """Send notification when user is approaching scan limit"""
        try:
            # Prepare user data for template
            user_data = {
                'full_name': user.full_name,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'insights_remaining': scans_remaining
            }
            
            # Send using template
            result = firebase_service.send_notification_from_template(
                user_id=user.id,
                template_type='limit_warning',
                user_data=user_data,
                custom_data={
                    'action': 'open_app',
                    'screen': 'subscription',
                    'scans_remaining': scans_remaining
                }
            )
            
            logger.info(f"Scan limit warning notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending scan limit warning notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_ai_insights_limit_warning_notification(user, insights_remaining):
        """Send notification when user is approaching AI insights limit"""
        try:
            if insights_remaining <= 2:
                title = f"🤖 Only {insights_remaining} AI Insights Left!"
                body = f"Hi {user.full_name}, you have {insights_remaining} AI insights remaining. Upgrade to Premium for unlimited AI analysis!"
            else:
                title = f"🤖 {insights_remaining} AI Insights Remaining"
                body = f"Hi {user.full_name}, you have {insights_remaining} AI insights left. Upgrade to Premium for unlimited AI analysis!"
            
            result = firebase_service.send_notification(
                user_id=user.id,
                title=title,
                body=body,
                notification_type='ai_insights_limit_warning',
                data={
                    'action': 'open_app',
                    'screen': 'subscription',
                    'insights_remaining': insights_remaining
                }
            )
            
            logger.info(f"AI insights limit warning notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending AI insights limit warning notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_app_update_notification(user, version, features):
        """Send notification about app updates"""
        try:
            title = f"🆕 New App Update Available!"
            body = f"Hi {user.full_name}, version {version} is now available with {features}. Update now for the best experience!"
            
            result = firebase_service.send_notification(
                user_id=user.id,
                title=title,
                body=body,
                notification_type='app_update',
                data={
                    'action': 'open_app_store',
                    'version': version,
                    'features': features
                }
            )
            
            logger.info(f"App update notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending app update notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_feature_reminder_notification(user, feature_name):
        """Send reminder about unused features"""
        try:
            title = f"💡 Try {feature_name}!"
            body = f"Hi {user.full_name}, discover the power of {feature_name}. It's included in your plan!"
            
            result = firebase_service.send_notification(
                user_id=user.id,
                title=title,
                body=body,
                notification_type='feature_reminder',
                data={
                    'action': 'open_app',
                    'screen': 'features',
                    'feature': feature_name
                }
            )
            
            logger.info(f"Feature reminder notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending feature reminder notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_promotional_notification(user, promo_title, promo_body, promo_code=None):
        """Send promotional notifications"""
        try:
            title = promo_title
            body = promo_body
            
            data = {
                'action': 'open_app',
                'screen': 'promotions'
            }
            
            if promo_code:
                data['promo_code'] = promo_code
            
            result = firebase_service.send_notification(
                user_id=user.id,
                title=title,
                body=body,
                notification_type='promotional',
                data=data
            )
            
            logger.info(f"Promotional notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending promotional notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_engagement_notification(user, days_inactive):
        """Send engagement notification for inactive users"""
        try:
            if days_inactive >= 30:
                title = f"👋 We Miss You!"
                body = f"Hi {user.full_name}, it's been {days_inactive} days since your last scan. Discover new ingredients today!"
            elif days_inactive >= 14:
                title = f"🔍 Ready for Another Scan?"
                body = f"Hi {user.full_name}, it's been {days_inactive} days since your last scan. What's in your food today?"
            else:
                title = f"📱 Time for a Scan!"
                body = f"Hi {user.full_name}, ready to discover what's in your food? Scan an ingredient now!"
            
            result = firebase_service.send_notification(
                user_id=user.id,
                title=title,
                body=body,
                notification_type='engagement',
                data={
                    'action': 'open_app',
                    'screen': 'scanner',
                    'days_inactive': days_inactive
                }
            )
            
            logger.info(f"Engagement notification sent to user {user.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending engagement notification to user {user.id}: {e}")
            return {'success': False, 'error': str(e)}

# Global instance
lifecycle_notifications = LifecycleNotificationService() 