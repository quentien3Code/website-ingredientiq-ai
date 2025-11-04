from django.urls import path
from .notification_views import (
    RegisterDeviceTokenView, UnregisterDeviceTokenView,
    UserNotificationHistoryView, NotificationSettingsView,
    TestNotificationView, NotificationTemplateListView,
    NotificationTemplateDetailView, SendCustomNotificationView,
    AppVersionListView, NotificationStatsView,
    TriggerSubscriptionCheckView
)
from .lifecycle_notification_views import (
    TriggerWelcomeNotificationView, TriggerSubscriptionNotificationView,
    TriggerLimitWarningNotificationView, TriggerAppUpdateNotificationView,
    TriggerFeatureReminderNotificationView, TriggerPromotionalNotificationView,
    TriggerEngagementNotificationView, SendBulkLifecycleNotificationView
)

urlpatterns = [
    # User endpoints
    path('device-token/register/', RegisterDeviceTokenView.as_view(), name='register-device-token'),
    path('device-token/unregister/', UnregisterDeviceTokenView.as_view(), name='unregister-device-token'),
    path('history/', UserNotificationHistoryView.as_view(), name='notification-history'),
    path('settings/', NotificationSettingsView.as_view(), name='notification-settings'),
    path('test/', TestNotificationView.as_view(), name='test-notification'),
    
    # Lifecycle notification endpoints
    path('lifecycle/welcome/', TriggerWelcomeNotificationView.as_view(), name='trigger-welcome-notification'),
    path('lifecycle/subscription/', TriggerSubscriptionNotificationView.as_view(), name='trigger-subscription-notification'),
    path('lifecycle/limit-warning/', TriggerLimitWarningNotificationView.as_view(), name='trigger-limit-warning-notification'),
    path('lifecycle/app-update/', TriggerAppUpdateNotificationView.as_view(), name='trigger-app-update-notification'),
    path('lifecycle/feature-reminder/', TriggerFeatureReminderNotificationView.as_view(), name='trigger-feature-reminder-notification'),
    path('lifecycle/promotional/', TriggerPromotionalNotificationView.as_view(), name='trigger-promotional-notification'),
    path('lifecycle/engagement/', TriggerEngagementNotificationView.as_view(), name='trigger-engagement-notification'),
    
    # Admin endpoints
    path('admin/templates/', NotificationTemplateListView.as_view(), name='notification-templates'),
    path('admin/templates/<int:pk>/', NotificationTemplateDetailView.as_view(), name='notification-template-detail'),
    path('admin/send-custom/', SendCustomNotificationView.as_view(), name='send-custom-notification'),
    path('admin/app-versions/', AppVersionListView.as_view(), name='app-versions'),
    path('admin/stats/', NotificationStatsView.as_view(), name='notification-stats'),
    path('admin/trigger-subscription-check/', TriggerSubscriptionCheckView.as_view(), name='trigger-subscription-check'),
    path('admin/bulk-lifecycle/', SendBulkLifecycleNotificationView.as_view(), name='send-bulk-lifecycle-notification'),
] 