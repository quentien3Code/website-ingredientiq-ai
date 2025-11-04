"""
Lifecycle Notification API Views
API endpoints for triggering user lifecycle notifications
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from .models import User, UserSubscription
from .lifecycle_notifications import lifecycle_notifications
import logging

logger = logging.getLogger(__name__)

class TriggerWelcomeNotificationView(APIView):
    """Trigger welcome notification for new user signup"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            
            # Check if user already received welcome notification
            from .models import PushNotification
            existing_welcome = PushNotification.objects.filter(
                user=user,
                notification_type='welcome'
            ).first()
            
            if existing_welcome:
                return Response({
                    'message': 'Welcome notification already sent',
                    'notification_id': existing_welcome.id
                }, status=status.HTTP_200_OK)
            
            # Send welcome notification
            result = lifecycle_notifications.send_welcome_notification(user)
            
            if result['success']:
                return Response({
                    'message': 'Welcome notification sent successfully',
                    'result': result
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to send welcome notification',
                    'result': result
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error in TriggerWelcomeNotificationView: {e}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TriggerSubscriptionNotificationView(APIView):
    """Trigger subscription-related notifications"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            action = request.data.get('action')  # purchased, cancelled, upgraded, expiring, expired
            
            if not action:
                return Response({
                    'error': 'Action is required (purchased, cancelled, upgraded, expiring, expired)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get subscription info
            try:
                subscription = UserSubscription.objects.get(user=user)
                plan_name = subscription.plan_name
                premium_type = subscription.premium_type
            except UserSubscription.DoesNotExist:
                plan_name = 'freemium'
                premium_type = None
            
            result = None
            
            if action == 'purchased':
                result = lifecycle_notifications.send_subscription_purchased_notification(
                    user, plan_name, premium_type
                )
            elif action == 'cancelled':
                result = lifecycle_notifications.send_subscription_cancelled_notification(
                    user, plan_name
                )
            elif action == 'upgraded':
                old_plan = request.data.get('old_plan', 'freemium')
                new_plan = request.data.get('new_plan', plan_name)
                result = lifecycle_notifications.send_subscription_upgraded_notification(
                    user, old_plan, new_plan
                )
            elif action == 'expiring':
                days_remaining = request.data.get('days_remaining', 7)
                result = lifecycle_notifications.send_subscription_expiring_notification(
                    user, days_remaining
                )
            elif action == 'expired':
                result = lifecycle_notifications.send_subscription_expired_notification(user)
            else:
                return Response({
                    'error': 'Invalid action. Use: purchased, cancelled, upgraded, expiring, expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if result and result['success']:
                return Response({
                    'message': f'Subscription {action} notification sent successfully',
                    'result': result
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': f'Failed to send subscription {action} notification',
                    'result': result
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error in TriggerSubscriptionNotificationView: {e}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TriggerLimitWarningNotificationView(APIView):
    """Trigger scan limit or AI insights limit warning notifications"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            limit_type = request.data.get('limit_type')  # scan_limit, ai_insights_limit
            
            if not limit_type:
                return Response({
                    'error': 'Limit type is required (scan_limit, ai_insights_limit)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = None
            
            if limit_type == 'scan_limit':
                scans_remaining = request.data.get('scans_remaining', 5)
                result = lifecycle_notifications.send_scan_limit_warning_notification(
                    user, scans_remaining
                )
            elif limit_type == 'ai_insights_limit':
                insights_remaining = request.data.get('insights_remaining', 3)
                result = lifecycle_notifications.send_ai_insights_limit_warning_notification(
                    user, insights_remaining
                )
            else:
                return Response({
                    'error': 'Invalid limit type. Use: scan_limit, ai_insights_limit'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if result and result['success']:
                return Response({
                    'message': f'{limit_type} warning notification sent successfully',
                    'result': result
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': f'Failed to send {limit_type} warning notification',
                    'result': result
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error in TriggerLimitWarningNotificationView: {e}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TriggerAppUpdateNotificationView(APIView):
    """Trigger app update notification"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            version = request.data.get('version', '1.0.0')
            features = request.data.get('features', 'new features and improvements')
            
            result = lifecycle_notifications.send_app_update_notification(
                user, version, features
            )
            
            if result['success']:
                return Response({
                    'message': 'App update notification sent successfully',
                    'result': result
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to send app update notification',
                    'result': result
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error in TriggerAppUpdateNotificationView: {e}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TriggerFeatureReminderNotificationView(APIView):
    """Trigger feature reminder notification"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            feature_name = request.data.get('feature_name')
            
            if not feature_name:
                return Response({
                    'error': 'Feature name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = lifecycle_notifications.send_feature_reminder_notification(
                user, feature_name
            )
            
            if result['success']:
                return Response({
                    'message': 'Feature reminder notification sent successfully',
                    'result': result
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to send feature reminder notification',
                    'result': result
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error in TriggerFeatureReminderNotificationView: {e}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TriggerPromotionalNotificationView(APIView):
    """Trigger promotional notification"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            promo_title = request.data.get('title')
            promo_body = request.data.get('body')
            promo_code = request.data.get('promo_code')
            
            if not promo_title or not promo_body:
                return Response({
                    'error': 'Title and body are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = lifecycle_notifications.send_promotional_notification(
                user, promo_title, promo_body, promo_code
            )
            
            if result['success']:
                return Response({
                    'message': 'Promotional notification sent successfully',
                    'result': result
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to send promotional notification',
                    'result': result
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error in TriggerPromotionalNotificationView: {e}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TriggerEngagementNotificationView(APIView):
    """Trigger engagement notification for inactive users"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            days_inactive = request.data.get('days_inactive', 7)
            
            result = lifecycle_notifications.send_engagement_notification(
                user, days_inactive
            )
            
            if result['success']:
                return Response({
                    'message': 'Engagement notification sent successfully',
                    'result': result
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to send engagement notification',
                    'result': result
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error in TriggerEngagementNotificationView: {e}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Admin Views for Bulk Notifications
class SendBulkLifecycleNotificationView(APIView):
    """Send lifecycle notifications to multiple users (Admin only)"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        try:
            notification_type = request.data.get('notification_type')
            user_ids = request.data.get('user_ids', [])
            
            if not notification_type:
                return Response({
                    'error': 'Notification type is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not user_ids:
                return Response({
                    'error': 'User IDs are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            users = User.objects.filter(id__in=user_ids)
            results = []
            
            for user in users:
                try:
                    if notification_type == 'welcome':
                        result = lifecycle_notifications.send_welcome_notification(user)
                    elif notification_type == 'engagement':
                        days_inactive = request.data.get('days_inactive', 7)
                        result = lifecycle_notifications.send_engagement_notification(user, days_inactive)
                    elif notification_type == 'promotional':
                        promo_title = request.data.get('title')
                        promo_body = request.data.get('body')
                        promo_code = request.data.get('promo_code')
                        result = lifecycle_notifications.send_promotional_notification(
                            user, promo_title, promo_body, promo_code
                        )
                    else:
                        result = {'success': False, 'error': 'Unsupported notification type'}
                    
                    results.append({
                        'user_id': user.id,
                        'user_email': user.email,
                        'result': result
                    })
                    
                except Exception as e:
                    results.append({
                        'user_id': user.id,
                        'user_email': user.email,
                        'result': {'success': False, 'error': str(e)}
                    })
            
            success_count = sum(1 for r in results if r['result']['success'])
            
            return Response({
                'message': f'Bulk notification sent to {len(users)} users. {success_count} successful.',
                'results': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in SendBulkLifecycleNotificationView: {e}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 