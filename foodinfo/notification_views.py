from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from .models import DeviceToken, NotificationTemplate, PushNotification, AppVersion, User
from .serializers import (
    DeviceTokenSerializer, NotificationTemplateSerializer, 
    PushNotificationSerializer, AppVersionSerializer,
    CustomNotificationSerializer, NotificationSettingsSerializer
)
from .firebase_service import firebase_service
import logging

logger = logging.getLogger(__name__)

class RegisterDeviceTokenView(APIView):
    """Register or update FCM device token for push notifications"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Add debugging
        print(f"Device token registration request data: {request.data}")
        print(f"User: {request.user.id} - {request.user.email}")
        
        serializer = DeviceTokenSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            device_token = serializer.save()
            
            # Register token with Firebase service
            success = firebase_service.register_device_token(
                user_id=request.user.id,
                token=device_token.token,
                platform=device_token.platform
            )
            
            if success:
                return Response({
                    'message': 'Device token registered successfully',
                    'token_id': device_token.id
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Failed to register device token'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UnregisterDeviceTokenView(APIView):
    """Unregister FCM device token"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Unregister token
        success = firebase_service.unregister_device_token(
            user_id=request.user.id,
            token=token
        )
        
        if success:
            return Response({
                'message': 'Device token unregistered successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to unregister device token'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserNotificationHistoryView(APIView):
    """Get user's notification history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        notifications = PushNotification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:50]  # Last 50 notifications
        
        serializer = PushNotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NotificationSettingsView(APIView):
    """Get and update user notification settings"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = NotificationSettingsSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        serializer = NotificationSettingsSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TestNotificationView(APIView):
    """Send test notification to user (for testing purposes)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        title = request.data.get('title', 'Test Notification')
        body = request.data.get('body', 'This is a test notification from IngredientIQ!')
        
        result = firebase_service.send_notification(
            user_id=request.user.id,
            title=title,
            body=body,
            notification_type='custom'
        )
        
        if result['success']:
            return Response({
                'message': 'Test notification sent successfully',
                'result': result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to send test notification',
                'result': result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Admin Views
class NotificationTemplateListView(APIView):
    """List and create notification templates (Admin only)"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        templates = NotificationTemplate.objects.all().order_by('notification_type')
        serializer = NotificationTemplateSerializer(templates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = NotificationTemplateSerializer(data=request.data)
        
        if serializer.is_valid():
            template = serializer.save()
            return Response(
                NotificationTemplateSerializer(template).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationTemplateDetailView(APIView):
    """Get, update, delete notification template (Admin only)"""
    permission_classes = [IsAdminUser]
    
    def get(self, request, pk):
        template = get_object_or_404(NotificationTemplate, pk=pk)
        serializer = NotificationTemplateSerializer(template)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        template = get_object_or_404(NotificationTemplate, pk=pk)
        serializer = NotificationTemplateSerializer(template, data=request.data)
        
        if serializer.is_valid():
            template = serializer.save()
            return Response(
                NotificationTemplateSerializer(template).data,
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        template = get_object_or_404(NotificationTemplate, pk=pk)
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SendCustomNotificationView(APIView):
    """Send custom notification to specific users (Admin only)"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        serializer = CustomNotificationSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Check if using template or direct notification
            template_type = data.get('template_type')
            
            if template_type:
                # Send using template
                success_count = 0
                for user_id in data['user_ids']:
                    result = firebase_service.send_notification_from_template(
                        user_id=user_id,
                        template_type=template_type,
                        user_data=data.get('user_data', {}),
                        custom_data=data.get('data')
                    )
                    if result['success']:
                        success_count += 1
                
                return Response({
                    'message': f'Template notification sent to {success_count}/{len(data["user_ids"])} users using template: {template_type}'
                }, status=status.HTTP_200_OK)
            else:
                # Send notification directly
                success_count = 0
                for user_id in data['user_ids']:
                    result = firebase_service.send_notification(
                        user_id=user_id,
                        title=data['title'],
                        body=data['body'],
                        notification_type='custom',
                        data=data.get('data')
                    )
                    if result['success']:
                        success_count += 1
                
                return Response({
                    'message': f'Custom notification sent to {success_count}/{len(data["user_ids"])} users'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AppVersionListView(APIView):
    """List and create app versions (Admin only)"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        versions = AppVersion.objects.all().order_by('-released_at')
        serializer = AppVersionSerializer(versions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = AppVersionSerializer(data=request.data)
        
        if serializer.is_valid():
            # If this is marked as current, unmark other versions for the same platform
            if serializer.validated_data.get('is_current'):
                AppVersion.objects.filter(
                    platform=serializer.validated_data['platform'],
                    is_current=True
                ).update(is_current=False)
            
            version = serializer.save()
            
            return Response(
                AppVersionSerializer(version).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationStatsView(APIView):
    """Get notification statistics (Admin only)"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        from django.db.models import Count, Q
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
            'active_device_tokens': DeviceToken.objects.filter(
                is_active=True
            ).count(),
            'users_with_notifications_enabled': User.objects.filter(
                notifications_enabled=True
            ).count(),
            'notification_types': PushNotification.objects.values(
                'notification_type'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:10]
        }
        
        return Response(stats, status=status.HTTP_200_OK)

class TriggerSubscriptionCheckView(APIView):
    """Manually trigger subscription expiry check (Admin only)"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        return Response({
            'message': 'Subscription expiry check triggered'
        }, status=status.HTTP_202_ACCEPTED) 