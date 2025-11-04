from .models import UserSubscription, MonthlyScanUsage
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
import calendar

def get_monthly_reset_date():
    """
    Calculate the date when the monthly scan limit will reset.
    Returns the first day of the next month in both ISO and readable formats.
    """
    now = datetime.now()
    
    # Get the first day of next month
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    
    return {
        "iso_date": next_month.strftime("%Y-%m-%d"),
        "readable_date": next_month.strftime("%B %d, %Y"),
        "days_until_reset": (next_month - now).days
    }

def can_user_scan(user):
    """
    Returns (True, scan_count, remaining_scans) if user can scan.
    Returns (False, scan_count, remaining_scans) if freemium and limit reached.
    Uses MonthlyScanUsage model for monthly tracking.
    """
    try:
        subscription = UserSubscription.objects.get(user=user)
        # Only 'freemium' is limited; all other plans are unlimited
        if subscription.plan_name.strip().lower() == "freemium":
            # Get or create current month's usage record
            usage = MonthlyScanUsage.get_or_create_current_month(user)
            scan_count = usage.scan_count
            remaining_scans = usage.get_remaining_scans()
            
            if scan_count >= 20:
                return False, scan_count, remaining_scans
            return True, scan_count, remaining_scans
        # Any other plan: unlimited scans
        return True, None, None
    except UserSubscription.DoesNotExist:
        # Treat as freemium if no subscription found
        usage = MonthlyScanUsage.get_or_create_current_month(user)
        scan_count = usage.scan_count
        remaining_scans = usage.get_remaining_scans()
        
        if scan_count >= 20:
            return False, scan_count, remaining_scans
        return True, scan_count, remaining_scans

def increment_user_scan_count(user):
    """
    Increment the user's scan count for the current month.
    Returns the updated scan count and remaining scans.
    """
    try:
        usage = MonthlyScanUsage.get_or_create_current_month(user)
        old_remaining = usage.get_remaining_scans()
        usage.increment_scan()
        new_remaining = usage.get_remaining_scans()
        
        # Send notification if user is approaching limit or reached limit
        if new_remaining <= 5 and new_remaining > 1 and old_remaining > 5:
            # User has 5 or fewer scans left, send warning
            from .tasks import send_scan_limit_notification_task_celery, safe_execute_task
            safe_execute_task(send_scan_limit_notification_task_celery, user.id, new_remaining)
        elif new_remaining == 1 and old_remaining > 1:
            # User just reached the limit
            from .tasks import send_scan_limit_notification_task_celery, safe_execute_task
            safe_execute_task(send_scan_limit_notification_task_celery, user.id, 0)
        
        return usage.scan_count, usage.get_remaining_scans()
    except Exception as e:
        print(f"Error incrementing scan count: {e}")
        return 0, 0

def get_scan_limit_response(scan_count, remaining_scans):
    """
    Returns a standardized response for scan limit reached.
    """
    return Response(
        {
            "error": "Monthly scan limit reached. Please upgrade to Premium for unlimited scans.",
            "scans_used": scan_count,
            "max_scans": 20,
            "remaining_scans": remaining_scans,
            "monthly_reset_date": get_monthly_reset_date()
        },
        status=status.HTTP_402_PAYMENT_REQUIRED
    ) 