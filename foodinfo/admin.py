"""
Minimal admin configuration for foodinfo app.
Mobile app terminated - only essential models registered.
"""
from django.contrib import admin
from .models import (
    FAQ, AboutUS, User, privacypolicy, Termandcondition, 
    UserSubscription, AccountDeletionRequest, DownloadPDF  
)


class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'subscription_plan', 'is_active', 'date_joined']
    list_filter = ['subscription_plan', 'is_active']
    search_fields = ['email', 'full_name']
    readonly_fields = ['date_joined', 'created_at']


class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'public_plan', 'status', 'started_at']
    list_filter = ['plan_name', 'status']
    search_fields = ['user__email']

    def public_plan(self, obj):
        return getattr(obj, 'public_plan_label', None) or obj.plan_name


class AccountDeletionRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'requested_at', 'scheduled_deletion_date']
    list_filter = ['status']
    search_fields = ['user__email']


# Register models
admin.site.register(User, UserAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)
admin.site.register(AccountDeletionRequest, AccountDeletionRequestAdmin)
admin.site.register(DownloadPDF)
admin.site.register(FAQ)
admin.site.register(AboutUS)
admin.site.register(privacypolicy)
admin.site.register(Termandcondition)
