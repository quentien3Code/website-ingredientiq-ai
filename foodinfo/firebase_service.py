import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging
import os
from typing import List, Dict, Optional
from .models import DeviceToken, PushNotification

logger = logging.getLogger(__name__)

class FirebaseService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                # Check if credentials file exists
                cred_path = settings.FIREBASE_CREDENTIALS_PATH
                logger.info(f"Looking for Firebase credentials at: {cred_path}")
                
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized successfully")
                else:
                    # Try alternative paths
                    alt_paths = [
                        'teams-mrjw5-b4fa6002e33d.json',
                        '../teams-mrjw5-b4fa6002e33d.json',
                        os.path.join(settings.BASE_DIR, 'teams-mrjw5-b4fa6002e33d.json')
                    ]
                    
                    for alt_path in alt_paths:
                        if os.path.exists(alt_path):
                            cred = credentials.Certificate(alt_path)
                            firebase_admin.initialize_app(cred)
                            logger.info(f"Firebase initialized successfully using {alt_path}")
                            return
                    
                    logger.error(f"Firebase credentials file not found at any location")
                    logger.error(f"Tried paths: {[cred_path] + alt_paths}")
            else:
                logger.info("Firebase already initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _convert_data_to_strings(self, data: Dict) -> Dict:
        """
        Convert all values in data dictionary to strings for Firebase compatibility
        
        Args:
            data: Dictionary with mixed value types
            
        Returns:
            Dictionary with all values converted to strings
        """
        if not data:
            return {}
        
        string_data = {}
        for key, value in data.items():
            if value is None:
                string_data[key] = ''
            elif isinstance(value, (dict, list)):
                string_data[key] = str(value)
            else:
                string_data[key] = str(value)
        
        return string_data

    def send_notification(
        self, 
        user_id: int,
        title: str, 
        body: str, 
        notification_type: str = 'custom',
        data: Optional[Dict] = None,
        action_url: Optional[str] = None
    ) -> Dict:
        """
        Send push notification to all user's devices
        
        Args:
            user_id: User ID to send notification to
            title: Notification title
            body: Notification body
            notification_type: Type of notification
            data: Additional data to send
            action_url: URL to open when notification is clicked
            
        Returns:
            Dict with success status and details
        """
        try:
            # Ensure Firebase is initialized
            if not firebase_admin._apps:
                logger.warning("Firebase not initialized, attempting to initialize...")
                self._initialize_firebase()
                
            if not firebase_admin._apps:
                logger.error("Firebase initialization failed")
                return {
                    'success': False,
                    'error': 'Firebase not initialized',
                    'sent_count': 0
                }
            # Get user's active device tokens
            device_tokens = DeviceToken.objects.filter(
                user_id=user_id, 
                is_active=True
            ).values_list('token', flat=True)
            
            if not device_tokens:
                logger.warning(f"No active device tokens found for user {user_id}")
                return {
                    'success': False,
                    'error': 'No active device tokens found',
                    'sent_count': 0
                }
            
            # Prepare notification data and convert to strings
            notification_data = data or {}
            if action_url:
                notification_data['action_url'] = action_url
            notification_data['notification_type'] = notification_type
            
            # Convert all data values to strings for Firebase compatibility
            notification_data = self._convert_data_to_strings(notification_data)
            
            # Send to each token individually for better error handling
            success_count = 0
            failed_count = 0
            failed_tokens = []
            
            for token in device_tokens:
                try:
                    # Create Firebase message for single token
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=body
                        ),
                        data=notification_data,
                        token=token
                    )
                    
                    # Send notification
                    response = messaging.send(message)
                    success_count += 1
                    logger.info(f"Successfully sent notification to token: {token[:20]}...")
                    
                except Exception as e:
                    failed_count += 1
                    failed_tokens.append(token)
                    logger.error(f"Failed to send to token {token[:20]}...: {e}")
                    
                    # Check if token is invalid
                    if "InvalidRegistration" in str(e) or "NotRegistered" in str(e):
                        DeviceToken.objects.filter(token=token).update(is_active=False)
                        logger.info(f"Deactivated invalid token: {token[:20]}...")
            
            # Log notification
            notification_log = PushNotification.objects.create(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                body=body,
                status='sent' if success_count > 0 else 'failed',
                firebase_message_id=None  # Single message doesn't return message_id
            )
            
            logger.info(f"Notification sent to user {user_id}: {success_count} successful, {failed_count} failed")
            
            return {
                'success': success_count > 0,
                'sent_count': success_count,
                'failed_count': failed_count,
                'notification_id': notification_log.id
            }
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            
            # Log failed notification
            PushNotification.objects.create(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                body=body,
                status='failed',
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0
            }
    
    def send_bulk_notification(
        self,
        user_ids: List[int],
        title: str,
        body: str,
        notification_type: str = 'custom',
        data: Optional[Dict] = None,
        action_url: Optional[str] = None
    ) -> Dict:
        """
        Send notification to multiple users
        
        Args:
            user_ids: List of user IDs
            title: Notification title
            body: Notification body
            notification_type: Type of notification
            data: Additional data
            action_url: URL to open when clicked
            
        Returns:
            Dict with bulk send results
        """
        results = {
            'total_users': len(user_ids),
            'successful_users': 0,
            'failed_users': 0,
            'total_sent': 0,
            'total_failed': 0
        }
        
        for user_id in user_ids:
            result = self.send_notification(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=notification_type,
                data=data,
                action_url=action_url
            )
            
            if result['success']:
                results['successful_users'] += 1
                results['total_sent'] += result['sent_count']
            else:
                results['failed_users'] += 1
            
            results['total_failed'] += result.get('failed_count', 0)
        
        logger.info(f"Bulk notification sent: {results}")
        return results
    
    def register_device_token(self, user_id: int, token: str, platform: str) -> bool:
        """
        Register or update device token for user
        
        Args:
            user_id: User ID
            token: FCM device token
            platform: Device platform (ios, android, web)
            
        Returns:
            Boolean indicating success
        """
        try:
            device_token, created = DeviceToken.objects.update_or_create(
                user_id=user_id,
                token=token,
                defaults={
                    'platform': platform,
                    'is_active': True
                }
            )
            
            action = "registered" if created else "updated"
            logger.info(f"Device token {action} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering device token for user {user_id}: {e}")
            return False
    
    def unregister_device_token(self, user_id: int, token: str) -> bool:
        """
        Unregister device token
        
        Args:
            user_id: User ID
            token: FCM device token to remove
            
        Returns:
            Boolean indicating success
        """
        try:
            DeviceToken.objects.filter(
                user_id=user_id,
                token=token
            ).update(is_active=False)
            
            logger.info(f"Device token unregistered for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering device token for user {user_id}: {e}")
            return False

    def replace_template_placeholders(self, template_text: str, user_data: Dict) -> str:
        """
        Replace placeholders in template text with actual user data
        
        Args:
            template_text: Template text with placeholders like {user_name}
            user_data: Dictionary containing user data to replace placeholders
            
        Returns:
            Text with placeholders replaced
        """
        try:
            if not template_text or not user_data:
                return template_text
            
            # Replace common placeholders
            body = template_text
            
            # User-related placeholders
            if '{user_name}' in body:
                body = body.replace('{user_name}', user_data.get('full_name', user_data.get('first_name', 'User')))
            
            if '{first_name}' in body:
                body = body.replace('{first_name}', user_data.get('first_name', 'User'))
            
            if '{last_name}' in body:
                body = body.replace('{last_name}', user_data.get('last_name', ''))
            
            # Subscription-related placeholders
            if '{plan_name}' in body:
                body = body.replace('{plan_name}', user_data.get('plan_name', 'Premium'))
            
            if '{days_left}' in body:
                body = body.replace('{days_left}', str(user_data.get('days_left', 0)))
            
            if '{insights_remaining}' in body:
                body = body.replace('{insights_remaining}', str(user_data.get('insights_remaining', 0)))
            
            if '{subscription_end_date}' in body:
                end_date = user_data.get('subscription_end_date')
                if end_date:
                    body = body.replace('{subscription_end_date}', str(end_date))
            
            # Feature-related placeholders
            if '{feature_name}' in body:
                body = body.replace('{feature_name}', user_data.get('feature_name', 'new feature'))
            
            if '{version}' in body:
                body = body.replace('{version}', user_data.get('version', 'latest'))
            
            if '{features}' in body:
                body = body.replace('{features}', user_data.get('features', 'new features'))
            
            # Offer-related placeholders
            if '{offer_description}' in body:
                body = body.replace('{offer_description}', user_data.get('offer_description', 'special offer'))
            
            if '{discount_percent}' in body:
                body = body.replace('{discount_percent}', str(user_data.get('discount_percent', 0)))
            
            # Generic data placeholders
            for key, value in user_data.items():
                placeholder = f'{{{key}}}'
                if placeholder in body:
                    body = body.replace(placeholder, str(value))
            
            logger.debug(f"Template placeholders replaced: {template_text} -> {body}")
            return body
            
        except Exception as e:
            logger.error(f"Error replacing template placeholders: {e}")
            return template_text

    def send_notification_from_template(
        self, 
        user_id: int, 
        template_type: str, 
        user_data: Optional[Dict] = None,
        custom_data: Optional[Dict] = None
    ) -> Dict:
        """
        Send notification using a template with placeholder replacement
        
        Args:
            user_id: User ID to send notification to
            template_type: Type of notification template to use
            user_data: User data for placeholder replacement
            custom_data: Additional custom data to include
            
        Returns:
            Dict with success status and details
        """
        try:
            from .models import NotificationTemplate
            
            # Get template from database
            try:
                template = NotificationTemplate.objects.get(
                    notification_type=template_type,
                    is_active=True
                )
            except NotificationTemplate.DoesNotExist:
                logger.error(f"Template not found for type: {template_type}")
                return {
                    'success': False, 
                    'error': f'Template not found for type: {template_type}'
                }
            
            # Prepare user data if not provided
            if user_data is None:
                user_data = {}
            
            # Get user information if not provided
            if 'full_name' not in user_data or 'first_name' not in user_data:
                try:
                    from .models import User
                    user = User.objects.get(id=user_id)
                    user_data.update({
                        'full_name': getattr(user, 'full_name', f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()),
                        'first_name': getattr(user, 'first_name', 'User'),
                        'last_name': getattr(user, 'last_name', ''),
                        'email': user.email
                    })
                except User.DoesNotExist:
                    logger.error(f"User not found: {user_id}")
                    return {'success': False, 'error': 'User not found'}
            
            # Replace placeholders in title and body
            title = self.replace_template_placeholders(template.title, user_data)
            body = self.replace_template_placeholders(template.body, user_data)
            
            # Prepare notification data
            notification_data = custom_data or {}
            notification_data['template_type'] = template_type
            notification_data['notification_id'] = template.id
            
            # Add action URL if template has one
            action_url = template.action_url if hasattr(template, 'action_url') else None
            
            # Send notification
            result = self.send_notification(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=template_type,
                data=notification_data,
                action_url=action_url
            )
            
            logger.info(f"Template notification sent to user {user_id} using template {template_type}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending template notification to user {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    def send_bulk_template_notifications(
        self,
        user_ids: List[int],
        template_type: str,
        user_data_list: Optional[List[Dict]] = None,
        custom_data: Optional[Dict] = None
    ) -> Dict:
        """
        Send template-based notifications to multiple users
        
        Args:
            user_ids: List of user IDs
            template_type: Type of notification template to use
            user_data_list: List of user data dictionaries (one per user)
            custom_data: Additional custom data to include
            
        Returns:
            Dict with bulk send results
        """
        try:
            if not user_ids:
                return {'success': False, 'error': 'No user IDs provided'}
            
            # Prepare user data list
            if user_data_list is None:
                user_data_list = [{}] * len(user_ids)
            elif len(user_data_list) != len(user_ids):
                logger.warning(f"User data list length ({len(user_data_list)}) doesn't match user IDs length ({len(user_ids)})")
                # Extend or truncate to match
                if len(user_data_list) < len(user_ids):
                    user_data_list.extend([{}] * (len(user_ids) - len(user_data_list)))
                else:
                    user_data_list = user_data_list[:len(user_ids)]
            
            # Send notifications
            success_count = 0
            failed_count = 0
            results = []
            
            for i, user_id in enumerate(user_ids):
                user_data = user_data_list[i] if i < len(user_data_list) else {}
                
                result = self.send_notification_from_template(
                    user_id=user_id,
                    template_type=template_type,
                    user_data=user_data,
                    custom_data=custom_data
                )
                
                if result['success']:
                    success_count += 1
                else:
                    failed_count += 1
                
                results.append({
                    'user_id': user_id,
                    'result': result
                })
            
            logger.info(f"Bulk template notifications sent: {success_count} successful, {failed_count} failed")
            
            return {
                'success': success_count > 0,
                'total_users': len(user_ids),
                'success_count': success_count,
                'failed_count': failed_count,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error sending bulk template notifications: {e}")
            return {'success': False, 'error': str(e)}

# Singleton instance
firebase_service = FirebaseService()