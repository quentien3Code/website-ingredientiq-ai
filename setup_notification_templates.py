#!/usr/bin/env python3
"""
Setup script for notification templates
Run this script to create initial notification templates in your database
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodanalysis.settings')
django.setup()

from foodinfo.models import NotificationTemplate
from django.db import transaction

def create_notification_templates():
    """Create initial notification templates"""
    
    templates_data = [
        {
            'notification_type': 'welcome',
            'title': '🎉 Welcome to FoodApp!',
            'body': 'Hi {user_name}, welcome to FoodApp! Start scanning ingredients and discover what\'s in your food.',
            'is_active': True
        },
        {
            'notification_type': 'subscription_purchased',
            'title': '🎉 Welcome to Premium!',
            'body': 'Hi {user_name}, you have successfully subscribed to {plan_name}! Enjoy unlimited access to all features.',
            'is_active': True
        },
        {
            'notification_type': 'subscription_expiring',
            'title': '⚠️ Subscription Expiring Soon',
            'body': 'Hi {user_name}, your {plan_name} subscription expires in {days_left} days. Renew now to keep enjoying premium features!',
            'is_active': True
        },
        {
            'notification_type': 'subscription_expired',
            'title': '❌ Subscription Expired',
            'body': 'Hi {user_name}, your subscription has expired. Upgrade now to continue enjoying premium features!',
            'is_active': True
        },
        {
            'notification_type': 'subscription_cancelled',
            'title': '🚫 Subscription Cancelled',
            'body': 'Hi {user_name}, your {plan_name} subscription has been cancelled. You can still use basic features.',
            'is_active': True
        },
        {
            'notification_type': 'limit_warning',
            'title': '⚠️ Scan Limit Warning',
            'body': 'Hi {user_name}, you have {insights_remaining} scans remaining this month. Upgrade to Premium for unlimited scans!',
            'is_active': True
        },
        {
            'notification_type': 'app_update',
            'title': '🆕 New App Update Available!',
            'body': 'Hi {user_name}, version {version} is now available with {features}. Update now for the best experience!',
            'is_active': True
        },
        {
            'notification_type': 'feature_reminder',
            'title': '💡 Try New Features!',
            'body': 'Hi {user_name}, you haven\'t tried our {feature_name} yet. Give it a shot!',
            'is_active': True
        },
        {
            'notification_type': 'promotional',
            'title': '🎁 Special Offer Just for You!',
            'body': 'Hi {user_name}, {offer_description}. Limited time only!',
            'is_active': True
        },
        {
            'notification_type': 'engagement',
            'title': '👋 We Miss You!',
            'body': 'Hi {user_name}, it\'s been a while since you last used FoodApp. Come back and scan some ingredients!',
            'is_active': True
        },
        {
            'notification_type': 'subscription_upgraded',
            'title': '🚀 Subscription Upgraded!',
            'body': 'Hi {user_name}, you\'ve successfully upgraded to {plan_name}! Enjoy your new features!',
            'is_active': True
        },
        {
            'notification_type': 'subscription_downgraded',
            'title': '📉 Subscription Changed',
            'body': 'Hi {user_name}, your subscription has been changed to {plan_name}. Your new plan is now active.',
            'is_active': True
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    with transaction.atomic():
        for template_data in templates_data:
            template, created = NotificationTemplate.objects.update_or_create(
                notification_type=template_data['notification_type'],
                defaults={
                    'title': template_data['title'],
                    'body': template_data['body'],
                    'is_active': template_data['is_active']
                }
            )
            
            if created:
                created_count += 1
                print(f"✅ Created template: {template.notification_type}")
            else:
                updated_count += 1
                print(f"🔄 Updated template: {template.notification_type}")
    
    print(f"\n🎯 Template setup complete!")
    print(f"📝 Created: {created_count}")
    print(f"🔄 Updated: {updated_count}")
    print(f"📊 Total templates: {NotificationTemplate.objects.count()}")

def list_existing_templates():
    """List all existing notification templates"""
    templates = NotificationTemplate.objects.all().order_by('notification_type')
    
    if not templates:
        print("❌ No notification templates found in database")
        return
    
    print("\n📋 Existing Notification Templates:")
    print("=" * 60)
    
    for template in templates:
        status = "🟢 Active" if template.is_active else "🔴 Inactive"
        print(f"{template.notification_type:25} | {status}")
        print(f"{'':25} | Title: {template.title[:50]}...")
        print(f"{'':25} | Body: {template.body[:80]}...")
        print("-" * 60)

if __name__ == '__main__':
    print("🚀 Setting up notification templates...")
    
    # List existing templates first
    list_existing_templates()
    
    print("\n" + "="*60)
    
    # Create/update templates
    create_notification_templates()
    
    print("\n" + "="*60)
    
    # List final state
    list_existing_templates()
    
    print("\n✨ Template setup script completed successfully!")
    print("💡 You can now use these templates in your admin panel and API calls.") 