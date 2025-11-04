from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter
from .views import AboutUsView, AdminChangePasswordAPIView, AdminForgotPasswordAPIView, AdminLoginAPIView, AdminProfileView, AdminSignupAPIView, AdminUserManagementView, FAQView, OnboardingAnswerAPIView, OnboardingQuestionAPIView, OnboardingChoiceAPIView, OnboardingCategoryAPIView, PrivacyPolicyView, TermsAndConditionsView, passwordreset


urlpatterns = [
    # Admin URLs with CSRF exempt
    path('signup/',AdminSignupAPIView.as_view(), name='admin-signup'),
    path('login/',AdminLoginAPIView.as_view(), name='admin-login'),
    path('users/',AdminUserManagementView.as_view(), name='admin-users-list'),
    # path('users/<int:user_id>/',AdminUserManagementView.as_view(), name='admin-users-detail'),
    path('forgotpassword/',AdminForgotPasswordAPIView.as_view(),name='admin-forgotpassword'),
    path('changepassword/',AdminChangePasswordAPIView.as_view(),name='admin-changepassword'),
    path('profileview',AdminProfileView.as_view(),name='admin-profileview'),
    path('privacypolicy',PrivacyPolicyView.as_view(),name='admin-privacypolicy'),
    path('Termsandcondition',TermsAndConditionsView.as_view(),name='admin-termsandcondition'),
    path('FAQ',FAQView.as_view(),name='admin-FAQ'),
    path('Aboutus',AboutUsView.as_view(),name='admin-aboutus'),
    path('passwordreset/',passwordreset.as_view()),
    path('onboarding/questions/', OnboardingQuestionAPIView.as_view(), name='onboarding-question-create'),
    path('onboarding/questions/<int:pk>/choices/', OnboardingQuestionAPIView.as_view(), name='onboarding-question-choices'),
    path('onboarding/answers/',OnboardingAnswerAPIView.as_view(),name='OnboardingAnswerAPIView'),
    path('onboarding/choices/', OnboardingChoiceAPIView.as_view(), name='onboarding-choice-management'),
    path('onboarding/categories/', OnboardingCategoryAPIView.as_view(), name='onboarding-categories')
]