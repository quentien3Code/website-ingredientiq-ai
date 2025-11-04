#!/usr/bin/env python3
"""
Check admin template access
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
from django.contrib import admin

def check_admin_templates():
    """Check admin template access"""
    
    print("🔍 Checking Notification Templates in Admin...")
    print("=" * 60)
    
    # Check if templates exist in database
    templates = NotificationTemplate.objects.all()
    print(f"📊 Total templates in database: {templates.count()}")
    
    if templates.count() > 0:
        print("\n📋 Available Templates:")
        print("-" * 40)
        for template in templates:
            status = "🟢 Active" if template.is_active else "🔴 Inactive"
            print(f"✅ {template.notification_type:25} | {status}")
            print(f"    Title: {template.title}")
            print(f"    Body: {template.body[:80]}...")
            print("-" * 40)
    
    # Check admin registration
    print(f"\n🔧 Admin Registration Check:")
    print("-" * 40)
    
    try:
        # Check if NotificationTemplate is registered
        if NotificationTemplate in admin.site._registry:
            print("✅ NotificationTemplate is registered in admin")
            
            # Get admin class
            admin_class = admin.site._registry[NotificationTemplate]
            print(f"✅ Admin class: {admin_class.__class__.__name__}")
            print(f"✅ List display: {admin_class.list_display}")
            print(f"✅ List filter: {admin_class.list_filter}")
            print(f"✅ Search fields: {admin_class.search_fields}")
            
        else:
            print("❌ NotificationTemplate is NOT registered in admin")
            
    except Exception as e:
        print(f"❌ Error checking admin registration: {e}")
    
    # Check admin URLs
    print(f"\n🌐 Admin URL Information:")
    print("-" * 40)
    print("Main admin: http://127.0.0.1:8000/admin/")
    print("Notification templates: http://127.0.0.1:8000/admin/foodinfo/notificationtemplate/")
    print("Add template: http://127.0.0.1:8000/admin/foodinfo/notificationtemplate/add/")

if __name__ == '__main__':
    check_admin_templates()
    print("\n✨ Admin template check completed!") 