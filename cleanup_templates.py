#!/usr/bin/env python3
"""
Cleanup script for notification templates
Remove duplicate and unnecessary templates
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

def cleanup_templates():
    """Remove duplicate and unnecessary templates"""
    
    # Templates to keep (these are the ones your code actually uses)
    keep_templates = [
        'welcome',
        'subscription_purchased',
        'subscription_expiring',
        'subscription_expired',
        'subscription_cancelled',
        'subscription_upgraded',
        'subscription_downgraded',
        'limit_warning',
        'app_update',
        'feature_reminder',
        'promotional',
        'engagement'
    ]
    
    # Get all templates
    all_templates = NotificationTemplate.objects.all()
    
    # Find templates to delete
    templates_to_delete = []
    for template in all_templates:
        if template.notification_type not in keep_templates:
            templates_to_delete.append(template)
    
    # Delete unnecessary templates
    deleted_count = 0
    for template in templates_to_delete:
        print(f"🗑️  Deleting template: {template.notification_type}")
        template.delete()
        deleted_count += 1
    
    print(f"\n🧹 Cleanup complete!")
    print(f"🗑️  Deleted: {deleted_count}")
    print(f"📊 Remaining templates: {NotificationTemplate.objects.count()}")
    
    # List remaining templates
    remaining = NotificationTemplate.objects.all().order_by('notification_type')
    print(f"\n📋 Remaining Templates:")
    print("=" * 50)
    for template in remaining:
        print(f"✅ {template.notification_type}")

if __name__ == '__main__':
    print("🧹 Cleaning up notification templates...")
    cleanup_templates()
    print("\n✨ Template cleanup completed successfully!") 