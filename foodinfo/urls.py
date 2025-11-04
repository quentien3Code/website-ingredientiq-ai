from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter
from .views import (
    FAQ, About, AboutUS, AllFlaggedIngredientsView, AWSTextractOCRView, BarcodeView, CautionIngredientsView, Details, FoodLabelNutritionView, FoodTrendsView, Frequentlyasked, GoogleSignInView, GoogleOAuth2CallbackView, GoogleSignInWithAccessTokenView, IngredientFullDataView, IngredientLLMView, LogoutView, SafeGoIngredientsView, ScanHistoryView, SettingsView,
    SignupAPIView, LoginAPIView, ForgotPasswordRequestAPIView, SubscribeUserView, SubscriptionPricesView, TrendingNewsView, changepasswordView, google_login,
    privacypolicyView, stripe_webhook_view, termsandconditionView, userprofileview, resendotpview, verifyotpview,Toggle2FAView, ProductComparisonView, SearchProductView, FeedbackView, LoveAppView, ContactSupportView, ToggleFavoriteView, AppleSignInView, DiscountEligibilityView, NotificationTestView, MobileNotificationTestView, SimpleNotificationTestView, SubscriptionManagementView, SyncScanCountsView, ExportDataView, NotificationToggleView, DownloadRequestView
)
# router = DefaultRouter()
# router.register(r'onboarding', OnboardingViewSet, basename='onboarding')

urlpatterns = [
    # User URLs
    path('signup/', SignupAPIView.as_view(), name='signup'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('login/google/', google_login, name='google_login'),
    path('accounts/google/login/callback/', GoogleOAuth2CallbackView.as_view(), name='google_oauth2_callback'),
    path('login/apple/', AppleSignInView.as_view(), name='apple_login'),
    path('forgot-password/', ForgotPasswordRequestAPIView.as_view(), name='forgot_password'),
    path('verifyotp/', verifyotpview.as_view(), name='verify_otp'),
    path('resendotp/', resendotpview.as_view(), name='resend_otp'),
    path('2fa',Toggle2FAView.as_view(),name='toggle2fa'),
    path('change-password/', changepasswordView.as_view(), name='change_password'),
    path('food-safety-check/', FoodLabelNutritionView.as_view(), name='food-safety-check'),
    path('user-profile/', userprofileview.as_view(), name='user-profile'),
    path('privacy-policy/', privacypolicyView.as_view(), name='privacy-policy'),
    path('termsandcondition/', termsandconditionView.as_view(), name='terms-and-conditions'),
    path('FAQ/', Frequentlyasked.as_view(), name='faq'),
    path('AboutUS/', About.as_view(), name='about-us'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('scan-history/', ScanHistoryView.as_view(), name='scan-history'),
    path('trending-ingredients/', FoodTrendsView.as_view(), name='trending-ingredients'),
    path('fulldata/',IngredientFullDataView.as_view(),name='IngredientFullDataView'),
    path('subscribe/', SubscribeUserView.as_view(), name='subscribe-user'),
    path('webhook/stripe/', stripe_webhook_view, name='stripe-webhook'),
    path('api/ingredient-info/', IngredientLLMView.as_view(), name='ingredient-llm-info'),
    path("settings", SettingsView.as_view()),
    path('compare-products/', ProductComparisonView.as_view(), name='compare-products'),
    path('barcode/', BarcodeView.as_view(), name='barcode'),
    path('details',Details.as_view(),name='Details'),
    path('search/', SearchProductView.as_view(), name='search-products'),
    path('feedback/', FeedbackView.as_view(), name='feedback'),
    path('love-app/', LoveAppView.as_view(), name='love-app'),
    path('contact-support/', ContactSupportView.as_view(), name='contact-support'),
    path('toggle-favorite/', ToggleFavoriteView.as_view(), name='toggle-favorite'),
    path('flaggedingredients/',AllFlaggedIngredientsView.as_view(),name='AllFlaggedIngredientsView'),
    path('Safeingredients/',SafeGoIngredientsView.as_view(),name='SafeGoIngredientsView'),
    path('cautionIngredients/',CautionIngredientsView.as_view(),name='CautionIngredientsView'),
    path('aws-ocr/',AWSTextractOCRView.as_view(),name='AWSTextractOCRView'),
    path('news/trending/', TrendingNewsView.as_view(), name='trending-news'),
    path('google-signin/', GoogleSignInView.as_view(), name='google-signin'),
    path('google-signin/access-token/', GoogleSignInWithAccessTokenView.as_view(), name='google-signin-access-token'),
    path('discount-eligibility/', DiscountEligibilityView.as_view(), name='discount-eligibility'),
    path('subscription-prices/', SubscriptionPricesView.as_view(), name='subscription-prices'),
    path('subscription-management/', SubscriptionManagementView.as_view(), name='subscription-management'),
    path('sync-scan-counts/', SyncScanCountsView.as_view(), name='sync-scan-counts'),
    
    # Push Notification URLs
    path('notifications/', include('foodinfo.notification_urls')),
    path('test-notifications/', NotificationTestView.as_view(), name='test-notifications'),
    path('test-notifications/mobile/', MobileNotificationTestView.as_view(), name='mobile-test-notifications'),
    path('test-notifications/simple/', SimpleNotificationTestView.as_view(), name='simple-test-notifications'),
    path('export-data/', ExportDataView.as_view(), name='export-data'),
    path('notification-toggle/', NotificationToggleView.as_view(), name='notification-toggle'),
    path('download-request/', DownloadRequestView.as_view(), name='download-request'),

]