from django.contrib import admin
from .models import (
    FAQ, AboutUS, User, UserHealthPreference, privacypolicy, Termandcondition, 
    FoodLabelScan, StripeCustomer, UserSubscription, Feedback, DepartmentContact,
    MonthlyScanUsage, AccountDeletionRequest, DownloadPDF  
)

# Simple User admin (mobile notification features removed)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'notifications_enabled', 'subscription_plan', 'date_joined']
    list_filter = ['notifications_enabled', 'subscription_plan', 'is_active']
    search_fields = ['email', 'full_name']

admin.site.register(User, UserAdmin)
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