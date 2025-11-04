from django.contrib import admin
from .models import (
    FAQ, AboutUS, User, UserHealthPreference, privacypolicy, Termandcondition, 
    FoodLabelScan, StripeCustomer, UserSubscription, Feedback, DepartmentContact,
    DeviceToken, NotificationTemplate, PushNotification, AppVersion, MonthlyScanUsage,AccountDeletionRequest,DownloadPDF  
)

# Notification-related admin classes
@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'is_active', 'created_at']
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['notification_type', 'title', 'is_active', 'created_at']
    list_filter = ['notification_type', 'is_active', 'created_at']
    search_fields = ['title', 'body']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'status', 'created_at']
    list_filter = ['notification_type', 'status', 'created_at']
    search_fields = ['user__email', 'title', 'body']
    readonly_fields = ['created_at', 'sent_at', 'firebase_message_id']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ['platform', 'version', 'is_current', 'is_critical_update', 'released_at']
    list_filter = ['platform', 'is_current', 'is_critical_update', 'released_at']
    search_fields = ['version', 'release_notes']
    readonly_fields = ['released_at']
    
    def save_model(self, request, obj, form, change):
        if obj.is_current:
            AppVersion.objects.filter(
                platform=obj.platform,
                is_current=True
            ).exclude(id=obj.id).update(is_current=False)
        
        super().save_model(request, obj, form, change)
        
        if obj.is_current:
            from .tasks import send_app_update_notifications_task, safe_execute_task
            safe_execute_task(send_app_update_notifications_task, platform=obj.platform)

# Enhanced User admin with notification actions
class UserAdminWithNotifications(admin.ModelAdmin):
    actions = ['send_test_notification', 'send_welcome_notification']
    list_display = ['email', 'full_name', 'notifications_enabled', 'subscription_plan', 'date_joined']
    list_filter = ['notifications_enabled', 'subscription_plan', 'is_active']
    search_fields = ['email', 'full_name']
    
    def send_test_notification(self, request, queryset):
        from .firebase_service import firebase_service
        
        count = 0
        for user in queryset:
            result = firebase_service.send_notification(
                user_id=user.id,
                title="Test Notification",
                body=f"Hello {user.full_name}! This is a test notification.",
                notification_type='custom'
            )
            if result['success']:
                count += 1
        
        self.message_user(request, f"Test notification sent to {count} users.")
    
    def send_welcome_notification(self, request, queryset):
        from .tasks import send_welcome_notification_task_celery, safe_execute_task
        
        count = 0
        for user in queryset:
            result = safe_execute_task(send_welcome_notification_task_celery, user.id)
            if result and result.get('success'):
                count += 1
        
        self.message_user(request, f"Welcome notifications sent to {count} users.")
    
    send_test_notification.short_description = "Send test notification"
    send_welcome_notification.short_description = "Send welcome notification"

# Unregister default User admin and register enhanced version
# admin.site.unregister(User)
admin.site.register(User, UserAdminWithNotifications)
admin.site.register(DepartmentContact)

admin.site.register(Feedback)
admin.site.register(UserHealthPreference)
admin.site.register(privacypolicy)
admin.site.register(Termandcondition)
@admin.register(FoodLabelScan)
class FoodLabelScanAdmin(admin.ModelAdmin):
    list_display = ['user', 'scanned_at', 'product_name', 'scan_type']
    list_filter = ['scanned_at', 'user']
    search_fields = ['user__email', 'product_name', 'extracted_text']
    readonly_fields = ['scanned_at']
    actions = ['sync_scan_counts']
    
    def scan_type(self, obj):
        """Display the type of scan (barcode or OCR)"""
        if obj.product_name and obj.product_image_url:
            return "Barcode"
        elif obj.extracted_text and obj.image_url:
            return "OCR"
        return "Unknown"
    scan_type.short_description = "Scan Type"
    
    def sync_scan_counts(self, request, queryset):
        """Sync scan counts for users of selected scans"""
        from .models import MonthlyScanUsage
        
        synced_users = set()
        for scan in queryset:
            if scan.user not in synced_users:
                try:
                    actual_count = FoodLabelScan.objects.filter(user=scan.user).count()
                    usage = MonthlyScanUsage.get_or_create_current_month(scan.user)
                    if usage.scan_count != actual_count:
                        old_count = usage.scan_count
                        usage.scan_count = actual_count
                        usage.save()
                        synced_users.add(scan.user)
                except Exception as e:
                    self.message_user(request, f"Error syncing scan count for user {scan.user.email}: {e}")
        
        if synced_users:
            self.message_user(request, f"Successfully synced scan counts for {len(synced_users)} users")
        else:
            self.message_user(request, "No scan counts needed syncing")
    
    sync_scan_counts.short_description = "Sync scan counts for selected scan users"

@admin.register(MonthlyScanUsage)
class MonthlyScanUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'month', 'scan_count', 'premium_scans_used', 'remaining_scans', 'updated_at']
    list_filter = ['year', 'month', 'updated_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['sync_with_actual_scans']
    
    def remaining_scans(self, obj):
        """Calculate remaining scans for this month"""
        return max(0, 20 - obj.scan_count)
    remaining_scans.short_description = "Remaining Scans"
    
    def sync_with_actual_scans(self, request, queryset):
        """Sync selected MonthlyScanUsage records with actual FoodLabelScan counts"""
        synced_count = 0
        for usage in queryset:
            try:
                actual_count = FoodLabelScan.objects.filter(user=usage.user).count()
                if usage.scan_count != actual_count:
                    old_count = usage.scan_count
                    usage.scan_count = actual_count
                    usage.save()
                    synced_count += 1
            except Exception as e:
                self.message_user(request, f"Error syncing scan count for user {usage.user.email}: {e}")
        
        if synced_count:
            self.message_user(request, f"Successfully synced {synced_count} MonthlyScanUsage records")
        else:
            self.message_user(request, "No records needed syncing")
    
    sync_with_actual_scans.short_description = "Sync with actual scan counts"

admin.site.register(FAQ)
admin.site.register(AboutUS)
# admin.site.register(SuperAdmin)
admin.site.register(StripeCustomer)
admin.site.register(UserSubscription)
admin.site.register(AccountDeletionRequest)
admin.site.register(DownloadPDF)
# admin.site.register(OTP)