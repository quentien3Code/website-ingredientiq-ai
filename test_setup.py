#!/usr/bin/env python
"""Quick test script to check Django setup"""
import sys
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodanalysis.settings')

try:
    import django
    django.setup()
    print("SUCCESS: Django setup completed")
    
    # Try to import Website models
    from Website.models import Blogs
    print("SUCCESS: Website.models.Blogs imported")
    
    # Try to import admin_brita
    from Website import admin_brita
    print("SUCCESS: Website.admin_brita imported")
    
    # Check for pending migrations
    from django.core.management import call_command
    import io
    output = io.StringIO()
    call_command('showmigrations', 'Website', '--plan', stdout=output)
    print("\n=== Website Migrations ===")
    print(output.getvalue())
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
