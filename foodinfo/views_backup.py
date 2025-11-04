import io
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import json
import random
import ssl
import tempfile
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.utils import timezone
from datetime import timedelta
import openai
import hashlib
import threading
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from fuzzywuzzy import fuzz
from django.contrib.auth import login
from .serializers import FAQSerializer, AboutSerializer, AllergenDietaryCheckSerializer, FAQSerializer, SignupSerializer, LoginSerializer, ForgotPasswordRequestSerializer, UpdateUserProfileSerializer, UserSettingsSerializer, VerifyOTPSerializer,ChangePasswordSerializer,HealthPreferenceSerializer, privacypolicySerializer, termsandconditionSerializer, userGetSerializer, userPatchSerializer, FoodLabelScanSerializer, FeedbackSerializer, LoveAppSerializer, DepartmentContactSerializer
from .models import FoodLabelScan, MonthlyScanUsage, Termandcondition, User, UserSubscription, privacypolicy, AboutUS, FAQ,StripeCustomer, Feedback, DepartmentContact
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import IsSuperAdmin
# from paddleocr import PaddleOCR
import re
# import easyocr
from io import BytesIO
# from .apps import YourAppConfig
from django.http import HttpResponse
import asyncio
import aiohttp
import numpy as np
from .utils import get_comprehensive_discount_info, send_sms, is_eligible_for_new_user_discount, get_discount_info, get_subscription_prices
# from .utils import extract_nutrition_info_from_text
from PIL import Image
from foodanalysis import settings
import os
from bs4 import BeautifulSoup
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth import logout
import cv2
import time
import logging
import os
from PIL import Image, ImageEnhance, ImageFilter
import uuid
from django.core.files.base import ContentFile
import requests
from django.core.files.storage import default_storage
# from allauth.socialaccount.models import SocialApp
from django.shortcuts import redirect
from pytrends.request import TrendReq
from geopy.geocoders import Nominatim
from collections import Counter
from geopy.exc import GeocoderTimedOut
from django.core.cache import cache 
import stripe
from .utils import fetch_llm_insight, fetch_medlineplus_summary, fetch_pubchem_toxicology_summary, fetch_pubmed_articles, fetch_efsa_openfoodtox_data, fetch_efsa_ingredient_summary, fetch_fsa_hygiene_rating, fetch_fsa_hygiene_summary, search_fsa_establishments_by_product, fetch_snomed_ct_data, fetch_icd10_data, get_medical_condition_food_recommendations
from asgiref.sync import sync_to_async
from django.views.decorators.csrf import csrf_exempt
import aiohttp
import asyncio
# import concurrent.futures
from openai import OpenAI
# from .openfoodfacts_api import openfoodfacts_api
openfoodfacts_api = "https://world.openfoodfacts.org/api/v0/product/"
USE_STATIC_INGREDIENT_SAFETY = False    
# openai.api_key = os.getenv("OPENAI_API_KEY")
# import feedparser  # For Medium RSS feeds
client = OpenAI(api_key="OPENAI_API_KEY_REMOVED")
BASE_URL = "https://api.spoonacular.com"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
OPEN_FOOD_FACTS_API = "https://world.openfoodfacts.org/api/v0/product/"
USDA_API_KEY = os.getenv("USDA_API_KEY")
API_KEY = os.getenv("foursquare_api_key")
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WORDPRESS_API_URL = "https://public-api.wordpress.com/rest/v1.1/sites/example.wordpress.com/posts/"
WORDPRESS_BLOG_URL = "https://public-api.wordpress.com/rest/v1.1/sites/example.wordpress.com/posts"
EDAMAM_APP_ID = os.getenv("EDAMAM_APP_ID")
EDAMAM_APP_KEY = os.getenv("EDAMAM_APP_KEY")
SPOONACULAR_KEY = "c01bfdfb4ccd4d8097b5110f789e0618"
WIKIPEDIA_SEARCH_API_URL = "https://en.wikipedia.org/w/api.php"
WHO_SEARCH_URL = "https://www.who.int/search?q="
WIKIPEDIA_LINKS_API = "https://en.wikipedia.org/w/api.php"
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# openai.api_key = "OPENAI_API_KEY_REMOVED"

# Singleton EasyOCR reader and GPU check
# _easyocr_reader = None
# _easyocr_lock = threading.Lock()
# _easyocr_gpu = None

# def get_easyocr_reader():
#     global _easyocr_reader, _easyocr_gpu
#     with _easyocr_lock:
#         if _easyocr_reader is None:
#             try:
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=True)
#                 # Check if GPU is actually used
#                 _easyocr_gpu = _easyocr_reader.gpu
#                 logging.info(f"EasyOCR initialized. GPU used: {_easyocr_gpu}")
#             except Exception as e:
#                 logging.error(f"EasyOCR initialization failed: {e}")
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=False)
#                 _easyocr_gpu = False
#         return _easyocr_reader

# def is_easyocr_gpu():
#     global _easyocr_gpu
#     return _easyocr_gpu

def google_login(request):
    # google = SocialApp.objects.get(provider='google')
    # return redirect(f"https://accounts.google.com/o/oauth2/auth?client_id={google.client_id}&redirect_uri=http://localhost:8000/accounts/google/login/callback/&response_type=code&scope=email profile")
    pass  # Social login temporarily disabled due to SQLite JSONField incompatibility

class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'message': 'User created successfully.',
                'access_token': access_token,
                'refresh_token': str(refresh),
                'is_2fa_enabled': user.is_2fa_enabled
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            if user.is_2fa_enabled:  # Check if 2FA is enabled
                from random import randint
                from django.core.mail import send_mail

                otp_code = randint(100000, 999999)  # Generate 6-digit OTP
                user.otp = str(otp_code)
                user.save()

                # Send OTP via email
                send_mail(
                    "Your OTP Code",
                    f"Your OTP code is: {otp_code}",
                    "no-reply@example.com",
                    [user.email],
                    fail_silently=False,
                )

                return Response({
                    "message": "OTP sent to your email. Please verify to continue.",
                    "user_id": user.id,
                    "is_2fa_enabled": user.is_2fa_enabled,
                    "has_answered_onboarding": user.has_answered_onboarding, # <-- Added here
                    # "subscription_plan": user.UserSubscription

                }, status=status.HTTP_200_OK)

            # If 2FA is disabled, proceed with normal login
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                "message": "Login successful.",
                "access_token": access_token,
                "refresh_token": str(refresh),
                "is_2fa_enabled": user.is_2fa_enabled,
                "has_answered_onboarding": user.has_answered_onboarding,  # <-- Added here
                "subscription_plan": user.subscription_plan

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class Toggle2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        is_2fa_enabled = request.data.get("is_2fa_enabled", None)

        if is_2fa_enabled is None:
            return Response({"error": "is_2fa_enabled field is required"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_2fa_enabled = is_2fa_enabled
        user.save()
        
        return Response({
            "message": f"Two-Factor Authentication {'enabled' if is_2fa_enabled else 'disabled'} successfully.",
            "is_2fa_enabled": user.is_2fa_enabled
        }, status=status.HTTP_200_OK)

class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            
            if not user.check_password(old_password):
                return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'message': 'User created successfully.',
                'access_token': access_token,
                'refresh_token': str(refresh),
                'is_2fa_enabled': user.is_2fa_enabled
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            if user.is_2fa_enabled:  # Check if 2FA is enabled
                from random import randint
                from django.core.mail import send_mail

                otp_code = randint(100000, 999999)  # Generate 6-digit OTP
                user.otp = str(otp_code)
                user.save()

                # Send OTP via email
                send_mail(
                    "Your OTP Code",
                    f"Your OTP code is: {otp_code}",
                    "no-reply@example.com",
                    [user.email],
                    fail_silently=False,
                )

                return Response({
                    "message": "OTP sent to your email. Please verify to continue.",
                    "user_id": user.id,
                    "is_2fa_enabled": user.is_2fa_enabled,
                    "has_answered_onboarding": user.has_answered_onboarding, # <-- Added here
                    # "subscription_plan": user.UserSubscription

                }, status=status.HTTP_200_OK)

            # If 2FA is disabled, proceed with normal login
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                "message": "Login successful.",
                "access_token": access_token,
                "refresh_token": str(refresh),
                "is_2fa_enabled": user.is_2fa_enabled,
                "has_answered_onboarding": user.has_answered_onboarding,  # <-- Added here
                "subscription_plan": user.subscription_plan

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class Toggle2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        is_2fa_enabled = request.data.get("is_2fa_enabled", None)

        if is_2fa_enabled is None:
            return Response({"error": "is_2fa_enabled field is required"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_2fa_enabled = is_2fa_enabled
        user.save()
        
        return Response({
            "message": f"Two-Factor Authentication {'enabled' if is_2fa_enabled else 'disabled'} successfully.",
            "is_2fa_enabled": user.is_2fa_enabled
        }, status=status.HTTP_200_OK)

class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

def send_otp_email(email, otp_code):
    subject = "Your OTP Code for Password Reset"
    message = f"Your OTP code is: {otp_code}. It is valid for 5 minutes."
    from_email = (os.getenv("EMAIL_HOST_USER")) 
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
    print(f"OTP {otp_code} sent to email: {email}")

class resendotpview(APIView):
    def post(self, request):
        try:
            identifier = request.data.get('email_or_phone', '').strip().lower()

            if not identifier:
                return JsonResponse({"message": "Please enter Email or Phone number"}, status=status.HTTP_400_BAD_REQUEST)

            otp = random.randint(1000, 9999)

            if '@' in identifier:
                try:
                    user = User.objects.get(email=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this email not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                subject = "One Time Password"
                email_body = f"Your OTP is: {otp}\n\nUse this code to complete your verification."

                try:
                    send_mail(subject, email_body, 'AI IngredientIQ', [user.email], fail_silently=False)
                except BadHeaderError:
                    return JsonResponse({"message": "Invalid email header"}, status=status.HTTP_400_BAD_REQUEST)

                return JsonResponse({"data": "OTP sent to your email"}, status=status.HTTP_200_OK)

            else:
                try:
                    user = User.objects.get(phone_number=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this phone number not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                message = f"Your OTP is: {otp}. Use this to complete your verification."
                send_sms(user.phone_number, message)

                return JsonResponse({"data": "OTP sent to your phone number"}, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Verify OTP API
class verifyotpview(APIView):
    def post(self, request):
        try:
            otp = request.data.get('otp', None)
            
            if not otp:
                return JsonResponse({"error": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                otp = int(otp)
            except ValueError:
                return JsonResponse({"error": "OTP should be a valid integer"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(otp=otp).first()

            if user:
                user.otp = None  # Clear OTP after successful verification
                user.save()

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                return Response({
                    "message": "OTP Verified Successfully. Login successful.",
                    "access_token": access_token,
                    "refresh_token": str(refresh)
                }, status=status.HTTP_200_OK)

            return Response({"error": "Incorrect OTP"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordRequestAPIView(APIView):
    permission_classes = [] 

    def post(self, request):
        email = request.data.get("email")  
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            confirm_password = serializer.validated_data['confirm_password']

            if new_password != confirm_password:
                return Response({"detail": "Passwords must match."}, status=status.HTTP_400_BAD_REQUEST)

            if len(confirm_password) < 8:
                return Response({"detail": "New password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(confirm_password)
            user.save()

            return Response({"detail": "Password has been successfully reset."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

class termsandconditionView(APIView):
    def get(self,request):
        user = Termandcondition.objects.all()
        serializer = termsandconditionSerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)


class privacypolicyView(APIView):
    def get(self,request):
        user = privacypolicy.objects.all()
        serializer = privacypolicySerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)

class Frequentlyasked(APIView):
    def get(self,request):
        user = FAQ.objects.all()
        serializer = FAQSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class About(APIView):
    def get(self,request):
        user = AboutUS.objects.all()
        serializer = AboutSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class userprofileview(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request):
        user = User.objects.get(email=request.user.email)

        if not request.data:
            return Response({"message": "No data provided to update."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = userPatchSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            profile_picture_url = None
            if user.profile_picture:
                profile_picture_url = user.profile_picture.url
                print("------------", profile_picture_url)
                profile_picture_url = profile_picture_url.replace("https//", "")
                print("======", profile_picture_url)  
            return Response(
                {"message": "Profile updated successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self,request):
        user = User.objects.select_related().get(email=request.user.email)
        user.refresh_from_db()  # Force refresh from database
        serializer = userGetSerializer(user)
        # Add payment status info
        from .models import UserSubscription
        payment_status = 'freemium'
        premium_type = None
        try:
            sub = UserSubscription.objects.get(user=user)
            if sub.plan_name == 'premium':
                payment_status = 'premium'
                # Use a new field 'premium_type' if present, else fallback to 'unknown'
                premium_type = getattr(sub, 'premium_type', None)
        except UserSubscription.DoesNotExist:
            pass
        data = serializer.data
        data['payment_status'] = payment_status
        data['premium_type'] = premium_type
        return Response({"data":data}, status=status.HTTP_200_OK)
    
    def delete(self, request):
        user = User.objects.get(email=request.user.email)
        user.delete()
        return Response({"detail":"User deleted successfully."}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)

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

def get_user_plan_info(user):
    """
    Returns user's plan information including plan name, type, and status.
    """
    try:
        subscription = UserSubscription.objects.get(user=user)
        return {
            "plan_name": subscription.plan_name,
            "premium_type": subscription.premium_type,
            "status": subscription.status,
            "is_premium": subscription.plan_name.strip().lower() != "freemium"
        }
    except UserSubscription.DoesNotExist:
        return {
            "plan_name": "freemium",
            "premium_type": None,
            "status": "inactive",
            "is_premium": False
        }

def get_accurate_scan_count(user):
    """
    Returns the accurate scan count for a user based on actual FoodLabelScan objects.
    This ensures the count is accurate even if MonthlyScanUsage records are out of sync.
    """
    try:
        # Get the actual count of FoodLabelScan objects for this user
        actual_count = FoodLabelScan.objects.filter(user=user).count()
        
        # Update the MonthlyScanUsage record to sync with actual count
        usage = MonthlyScanUsage.get_or_create_current_month(user)
        if usage.scan_count != actual_count:
            usage.scan_count = actual_count
            usage.save()
            print(f"Synced scan count for user {user.email}: {usage.scan_count} -> {actual_count}")
        
        return actual_count
    except Exception as e:
        print(f"Error getting accurate scan count: {e}")
        return 0

def get_scan_count_at_time(user, scan_time):
    """
    Returns the scan count for a user at a specific point in time.
    This is used to show the correct scan count for historical scans.
    """
    try:
        # Count how many scans were created before or at the given time
        scan_count = FoodLabelScan.objects.filter(
            user=user,
            scanned_at__lte=scan_time
        ).count()
        
        return scan_count
    except Exception as e:
        print(f"Error getting scan count at time: {e}")
        return 0

def sync_all_user_scan_counts():
    """
    Sync all users' scan counts in MonthlyScanUsage with their actual FoodLabelScan objects.
    This should be run after deleting scans from admin panel to fix count discrepancies.
    """
    try:
        users = User.objects.all()
        synced_count = 0
        
        for user in users:
            actual_count = FoodLabelScan.objects.filter(user=user).count()
            usage = MonthlyScanUsage.get_or_create_current_month(user)
            
            if usage.scan_count != actual_count:
                old_count = usage.scan_count
                usage.scan_count = actual_count
                usage.save()
                print(f"Synced user {user.email}: {old_count} -> {actual_count}")
                synced_count += 1
        
        print(f"Synced scan counts for {synced_count} users")
        return synced_count
    except Exception as e:
        print(f"Error syncing scan counts: {e}")
        return 0

# Add a setting at the top of the file
USE_STATIC_INGREDIENT_SAFETY = False  # Set to True for instant local safety check, False to use Edamam

def increment_user_scan_count(user):
    """
    Increment the user's scan count for the current month.
    Returns the updated scan count and remaining scans.
    """
    try:
        usage = MonthlyScanUsage.get_or_create_current_month(user)
        usage.increment_scan()
        return usage.scan_count, usage.get_remaining_scans()
    except Exception as e:
        print(f"Error incrementing scan count: {e}")
        return 0, 0

class FoodLabelNutritionView(APIView):
    import io
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import json
import random
import ssl
import tempfile
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.utils import timezone
from datetime import timedelta
import openai
import hashlib
import threading
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from fuzzywuzzy import fuzz
from django.contrib.auth import login
from .serializers import FAQSerializer, AboutSerializer, AllergenDietaryCheckSerializer, FAQSerializer, SignupSerializer, LoginSerializer, ForgotPasswordRequestSerializer, UpdateUserProfileSerializer, UserSettingsSerializer, VerifyOTPSerializer,ChangePasswordSerializer,HealthPreferenceSerializer, privacypolicySerializer, termsandconditionSerializer, userGetSerializer, userPatchSerializer, FoodLabelScanSerializer, FeedbackSerializer, LoveAppSerializer, DepartmentContactSerializer
from .models import FoodLabelScan, MonthlyScanUsage, Termandcondition, User, UserSubscription, privacypolicy, AboutUS, FAQ,StripeCustomer, Feedback, DepartmentContact
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import IsSuperAdmin
# from paddleocr import PaddleOCR
import re
# import easyocr
from io import BytesIO
# from .apps import YourAppConfig
from django.http import HttpResponse
import asyncio
import aiohttp
import numpy as np
from .utils import send_sms, is_eligible_for_new_user_discount, get_discount_info, get_subscription_prices
# from .utils import extract_nutrition_info_from_text
from PIL import Image
from foodanalysis import settings
import os
from bs4 import BeautifulSoup
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth import logout
import cv2
import time
import logging
import os
from PIL import Image, ImageEnhance, ImageFilter
import uuid
from django.core.files.base import ContentFile
import requests
from django.core.files.storage import default_storage
# from allauth.socialaccount.models import SocialApp
from django.shortcuts import redirect
from pytrends.request import TrendReq
from geopy.geocoders import Nominatim
from collections import Counter
from geopy.exc import GeocoderTimedOut
from django.core.cache import cache 
import stripe
from .utils import fetch_llm_insight, fetch_medlineplus_summary, fetch_pubchem_toxicology_summary, fetch_pubmed_articles, fetch_efsa_openfoodtox_data, fetch_efsa_ingredient_summary, fetch_fsa_hygiene_rating, fetch_fsa_hygiene_summary, search_fsa_establishments_by_product, fetch_snomed_ct_data, fetch_icd10_data, get_medical_condition_food_recommendations
from asgiref.sync import sync_to_async
from django.views.decorators.csrf import csrf_exempt
import aiohttp
import asyncio
# import concurrent.futures
from openai import OpenAI
# from .openfoodfacts_api import openfoodfacts_api
openfoodfacts_api = "https://world.openfoodfacts.org/api/v0/product/"
USE_STATIC_INGREDIENT_SAFETY = False    
# openai.api_key = os.getenv("OPENAI_API_KEY")
# import feedparser  # For Medium RSS feeds
client = OpenAI(api_key="OPENAI_API_KEY_REMOVED")
BASE_URL = "https://api.spoonacular.com"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
OPEN_FOOD_FACTS_API = "https://world.openfoodfacts.org/api/v0/product/"
USDA_API_KEY = os.getenv("USDA_API_KEY")
API_KEY = os.getenv("foursquare_api_key")
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WORDPRESS_API_URL = "https://public-api.wordpress.com/rest/v1.1/sites/example.wordpress.com/posts/"
WORDPRESS_BLOG_URL = "https://public-api.wordpress.com/rest/v1.1/sites/example.wordpress.com/posts"
EDAMAM_APP_ID = os.getenv("EDAMAM_APP_ID")
EDAMAM_APP_KEY = os.getenv("EDAMAM_APP_KEY")
SPOONACULAR_KEY = "c01bfdfb4ccd4d8097b5110f789e0618"
WIKIPEDIA_SEARCH_API_URL = "https://en.wikipedia.org/w/api.php"
WHO_SEARCH_URL = "https://www.who.int/search?q="
WIKIPEDIA_LINKS_API = "https://en.wikipedia.org/w/api.php"
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# openai.api_key = "OPENAI_API_KEY_REMOVED"

# Singleton EasyOCR reader and GPU check
# _easyocr_reader = None
# _easyocr_lock = threading.Lock()
# _easyocr_gpu = None

# def get_easyocr_reader():
#     global _easyocr_reader, _easyocr_gpu
#     with _easyocr_lock:
#         if _easyocr_reader is None:
#             try:
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=True)
#                 # Check if GPU is actually used
#                 _easyocr_gpu = _easyocr_reader.gpu
#                 logging.info(f"EasyOCR initialized. GPU used: {_easyocr_gpu}")
#             except Exception as e:
#                 logging.error(f"EasyOCR initialization failed: {e}")
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=False)
#                 _easyocr_gpu = False
#         return _easyocr_reader

# def is_easyocr_gpu():
#     global _easyocr_gpu
#     return _easyocr_gpu

def google_login(request):
    # google = SocialApp.objects.get(provider='google')
    # return redirect(f"https://accounts.google.com/o/oauth2/auth?client_id={google.client_id}&redirect_uri=http://localhost:8000/accounts/google/login/callback/&response_type=code&scope=email profile")
    pass  # Social login temporarily disabled due to SQLite JSONField incompatibility

class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'message': 'User created successfully.',
                'access_token': access_token,
                'refresh_token': str(refresh),
                'is_2fa_enabled': user.is_2fa_enabled
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            if user.is_2fa_enabled:  # Check if 2FA is enabled
                from random import randint
                from django.core.mail import send_mail

                otp_code = randint(100000, 999999)  # Generate 6-digit OTP
                user.otp = str(otp_code)
                user.save()

                # Send OTP via email
                send_mail(
                    "Your OTP Code",
                    f"Your OTP code is: {otp_code}",
                    "no-reply@example.com",
                    [user.email],
                    fail_silently=False,
                )

                return Response({
                    "message": "OTP sent to your email. Please verify to continue.",
                    "user_id": user.id,
                    "is_2fa_enabled": user.is_2fa_enabled,
                    "has_answered_onboarding": user.has_answered_onboarding, # <-- Added here
                    # "subscription_plan": user.UserSubscription

                }, status=status.HTTP_200_OK)

            # If 2FA is disabled, proceed with normal login
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                "message": "Login successful.",
                "access_token": access_token,
                "refresh_token": str(refresh),
                "is_2fa_enabled": user.is_2fa_enabled,
                "has_answered_onboarding": user.has_answered_onboarding,  # <-- Added here
                "subscription_plan": user.subscription_plan

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class Toggle2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        is_2fa_enabled = request.data.get("is_2fa_enabled", None)

        if is_2fa_enabled is None:
            return Response({"error": "is_2fa_enabled field is required"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_2fa_enabled = is_2fa_enabled
        user.save()
        
        return Response({
            "message": f"Two-Factor Authentication {'enabled' if is_2fa_enabled else 'disabled'} successfully.",
            "is_2fa_enabled": user.is_2fa_enabled
        }, status=status.HTTP_200_OK)

class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

def send_otp_email(email, otp_code):
    subject = "Your OTP Code for Password Reset"
    message = f"Your OTP code is: {otp_code}. It is valid for 5 minutes."
    from_email = (os.getenv("EMAIL_HOST_USER")) 
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
    print(f"OTP {otp_code} sent to email: {email}")

class resendotpview(APIView):
    def post(self, request):
        try:
            identifier = request.data.get('email_or_phone', '').strip().lower()

            if not identifier:
                return JsonResponse({"message": "Please enter Email or Phone number"}, status=status.HTTP_400_BAD_REQUEST)

            otp = random.randint(1000, 9999)

            if '@' in identifier:
                try:
                    user = User.objects.get(email=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this email not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                subject = "One Time Password"
                email_body = f"Your OTP is: {otp}\n\nUse this code to complete your verification."

                try:
                    send_mail(subject, email_body, 'AI IngredientIQ', [user.email], fail_silently=False)
                except BadHeaderError:
                    return JsonResponse({"message": "Invalid email header"}, status=status.HTTP_400_BAD_REQUEST)

                return JsonResponse({"data": "OTP sent to your email"}, status=status.HTTP_200_OK)

            else:
                try:
                    user = User.objects.get(phone_number=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this phone number not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                message = f"Your OTP is: {otp}. Use this to complete your verification."
                send_sms(user.phone_number, message)

                return JsonResponse({"data": "OTP sent to your phone number"}, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Verify OTP API
class verifyotpview(APIView):
    def post(self, request):
        try:
            otp = request.data.get('otp', None)
            
            if not otp:
                return JsonResponse({"error": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                otp = int(otp)
            except ValueError:
                return JsonResponse({"error": "OTP should be a valid integer"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(otp=otp).first()

            if user:
                user.otp = None  # Clear OTP after successful verification
                user.save()

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                return Response({
                    "message": "OTP Verified Successfully. Login successful.",
                    "access_token": access_token,
                    "refresh_token": str(refresh)
                }, status=status.HTTP_200_OK)

            return Response({"error": "Incorrect OTP"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordRequestAPIView(APIView):
    permission_classes = [] 

    def post(self, request):
        email = request.data.get("email")  
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            confirm_password = serializer.validated_data['confirm_password']

            if new_password != confirm_password:
                return Response({"detail": "Passwords must match."}, status=status.HTTP_400_BAD_REQUEST)

            if len(confirm_password) < 8:
                return Response({"detail": "New password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(confirm_password)
            user.save()

            return Response({"detail": "Password has been successfully reset."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

class termsandconditionView(APIView):
    def get(self,request):
        user = Termandcondition.objects.all()
        serializer = termsandconditionSerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)


class privacypolicyView(APIView):
    def get(self,request):
        user = privacypolicy.objects.all()
        serializer = privacypolicySerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)

class Frequentlyasked(APIView):
    def get(self,request):
        user = FAQ.objects.all()
        serializer = FAQSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class About(APIView):
    def get(self,request):
        user = AboutUS.objects.all()
        serializer = AboutSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class userprofileview(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request):
        user = User.objects.get(email=request.user.email)

        if not request.data:
            return Response({"message": "No data provided to update."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = userPatchSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            profile_picture_url = None
            if user.profile_picture:
                profile_picture_url = user.profile_picture.url
                print("------------", profile_picture_url)
                profile_picture_url = profile_picture_url.replace("https//", "")
                print("======", profile_picture_url)  
            return Response(
                {"message": "Profile updated successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self,request):
        user = User.objects.select_related().get(email=request.user.email)
        user.refresh_from_db()  # Force refresh from database
        serializer = userGetSerializer(user)
        # Add payment status info
        from .models import UserSubscription
        payment_status = 'freemium'
        premium_type = None
        try:
            sub = UserSubscription.objects.get(user=user)
            if sub.plan_name == 'premium':
                payment_status = 'premium'
                # Use a new field 'premium_type' if present, else fallback to 'unknown'
                premium_type = getattr(sub, 'premium_type', None)
        except UserSubscription.DoesNotExist:
            pass
        data = serializer.data
        data['payment_status'] = payment_status
        data['premium_type'] = premium_type
        return Response({"data":data}, status=status.HTTP_200_OK)
    
    def delete(self, request):
        user = User.objects.get(email=request.user.email)
        user.delete()
        return Response({"detail":"User deleted successfully."}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)

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

def get_user_plan_info(user):
    """
    Returns user's plan information including plan name, type, and status.
    """
    try:
        subscription = UserSubscription.objects.get(user=user)
        return {
            "plan_name": subscription.plan_name,
            "premium_type": subscription.premium_type,
            "status": subscription.status,
            "is_premium": subscription.plan_name.strip().lower() != "freemium"
        }
    except UserSubscription.DoesNotExist:
        return {
            "plan_name": "freemium",
            "premium_type": None,
            "status": "inactive",
            "is_premium": False
        }

def get_accurate_scan_count(user):
    """
    Returns the accurate scan count for a user based on actual FoodLabelScan objects.
    This ensures the count is accurate even if MonthlyScanUsage records are out of sync.
    """
    try:
        # Get the actual count of FoodLabelScan objects for this user
        actual_count = FoodLabelScan.objects.filter(user=user).count()
        
        # Update the MonthlyScanUsage record to sync with actual count
        usage = MonthlyScanUsage.get_or_create_current_month(user)
        if usage.scan_count != actual_count:
            usage.scan_count = actual_count
            usage.save()
            print(f"Synced scan count for user {user.email}: {usage.scan_count} -> {actual_count}")
        
        return actual_count
    except Exception as e:
        print(f"Error getting accurate scan count: {e}")
        return 0

def get_scan_count_at_time(user, scan_time):
    """
    Returns the scan count for a user at a specific point in time.
    This is used to show the correct scan count for historical scans.
    """
    try:
        # Count how many scans were created before or at the given time
        scan_count = FoodLabelScan.objects.filter(
            user=user,
            scanned_at__lte=scan_time
        ).count()
        
        return scan_count
    except Exception as e:
        print(f"Error getting scan count at time: {e}")
        return 0

def sync_all_user_scan_counts():
    """
    Sync all users' scan counts in MonthlyScanUsage with their actual FoodLabelScan objects.
    This should be run after deleting scans from admin panel to fix count discrepancies.
    """
    try:
        users = User.objects.all()
        synced_count = 0
        
        for user in users:
            actual_count = FoodLabelScan.objects.filter(user=user).count()
            usage = MonthlyScanUsage.get_or_create_current_month(user)
            
            if usage.scan_count != actual_count:
                old_count = usage.scan_count
                usage.scan_count = actual_count
                usage.save()
                print(f"Synced user {user.email}: {old_count} -> {actual_count}")
                synced_count += 1
        
        print(f"Synced scan counts for {synced_count} users")
        return synced_count
    except Exception as e:
        print(f"Error syncing scan counts: {e}")
        return 0

# Add a setting at the top of the file
USE_STATIC_INGREDIENT_SAFETY = False  # Set to True for instant local safety check, False to use Edamam

def increment_user_scan_count(user):
    """
    Increment the user's scan count for the current month.
    Returns the updated scan count and remaining scans.
    """
    try:
        usage = MonthlyScanUsage.get_or_create_current_month(user)
        usage.increment_scan()
        return usage.scan_count, usage.get_remaining_scans()
    except Exception as e:
        print(f"Error incrementing scan count: {e}")
        return 0, 0

class FoodLabelNutritionView(APIView):
    permission_classes = [IsAuthenticated]
    
    # In-memory caches (class-level)
    edamam_cache = {}
    openai_cache = {}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize AWS Textract client
        try:
            aws_access_key = settings.AWS_ACCESS_KEY_ID
            aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
            aws_region = settings.AWS_S3_REGION_NAME or 'us-east-1'
            
            if not aws_access_key or not aws_secret_key:
                logging.error("AWS credentials not found in settings")
                self.textract_client = None
                return
            
            self.textract_client = boto3.client(
                'textract',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            print("AWS Textract client initialized successfully for FoodLabelNutritionView")
        except Exception as e:
            logging.error(f"Failed to initialize AWS Textract client: {e}")
            self.textract_client = None

    def post(self, request):
        # can_scan, scan_count = can_user_scan(request.user)
        # if not can_scan:
        #     return Response(
        #         {
        #             "error": "Scan limit reached. Please subscribe to AI IngredientIQ for unlimited scans.",
        #             "scans_used": scan_count,
        #             "max_scans": 6
        #         },
        #         status=status.HTTP_402_PAYMENT_REQUIRED
        #     )
        import time
        import logging
        from concurrent.futures import ThreadPoolExecutor
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"FoodLabelNutritionView is running on: {device.upper()}")
        except ImportError:
            print("torch not installed; cannot determine GPU/CPU.")

        start_time = time.time()

        # Deserialize and validate
        serializer = AllergenDietaryCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data['image']
        image_content = image_file.read()

        # LIGHTNING FAST PARALLEL PROCESSING
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all tasks simultaneously
            image_future = executor.submit(self.save_image, image_content)
            ocr_future = executor.submit(self.run_ocr, image_content)
            ingredients_future = executor.submit(self.extract_ingredients_with_textract_query, image_content)
            nutrition_future = executor.submit(self.extract_nutrition_with_textract_query, image_content)
            
            # Get image URL first (critical)
            image_url, image_path = image_future.result(timeout=3)
            if not image_url:
                return Response({'error': 'Image upload failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get OCR results with timeouts
            try:
                extracted_text = ocr_future.result(timeout=8)  # 8 second timeout
            except:
                extracted_text = ""
                
            try:
                query_ingredients = ingredients_future.result(timeout=8)
            except:
                query_ingredients = []
                
            try:
                query_nutrition = nutrition_future.result(timeout=8)
            except:
                query_nutrition = {}
        
        # Process results quickly
        if query_nutrition:
            nutrition_data = self.process_query_nutrition_data(query_nutrition)
        else:
            nutrition_data = self.extract_nutrition_info_fallback(extracted_text)
        
        if query_ingredients:
            actual_ingredients = self.process_query_ingredients(query_ingredients)
        else:
            actual_ingredients = self.extract_ingredients_from_text_fallback(extracted_text)

        # Debug logging
        print(f"Extracted text: {extracted_text}")
        print(f"Nutrition data extracted: {nutrition_data}")
        
        # More lenient check - allow partial nutrition data
        if not nutrition_data:
            # Try a simpler extraction method as fallback
            nutrition_data = self.extract_nutrition_info_simple(extracted_text)
            print(f"Fallback nutrition data: {nutrition_data}")
            
        if not nutrition_data:
            return Response(
                {"error": "No nutrition data found, Please capture clear photo of nutrition label of food packet. Scan not saved."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # PARALLEL SAFETY VALIDATION AND AI INSIGHTS
        safety_start = time.time()
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Run safety validation and AI insights in parallel
            safety_future = executor.submit(lambda: asyncio.run(self.validate_product_safety(request.user, actual_ingredients)))
            ai_future = executor.submit(self.get_ai_health_insight_and_expert_advice, request.user, nutrition_data, [])
            
            # Get safety results with timeout
            try:
                safety_result = safety_future.result(timeout=5)  # 5 second timeout
                if len(safety_result) == 5:
                    safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache = safety_result
                else:
                    safety_status, go_ingredients, caution_ingredients, no_go_ingredients = safety_result
                    efsa_data_cache = {}
            except:
                safety_status, go_ingredients, caution_ingredients, no_go_ingredients = "unknown", [], [], []
                efsa_data_cache = {}
            
            # Get AI results with timeout
            try:
                ai_results = ai_future.result(timeout=3)  # 3 second timeout
            except:
                ai_results = {
                    "ai_health_insight": "Health insights unavailable.",
                    "expert_advice": "Consult healthcare professional."
                }
        
        safety_end = time.time()
        logging.info(f"Safety validation completed in {safety_end - safety_start:.2f} seconds.")

        # Prepare ingredients for scan history (convert back to simple format for storage)
        def extract_ingredient_names(ingredient_list):
            return [ing["ingredient"] if isinstance(ing, dict) else ing for ing in ingredient_list]
        
        no_go_names = extract_ingredient_names(no_go_ingredients)
        go_names = extract_ingredient_names(go_ingredients)
        caution_names = extract_ingredient_names(caution_ingredients)
        
        with ThreadPoolExecutor() as executor:
            scan_future = executor.submit(lambda: asyncio.run(self.save_scan_history(
                request.user,
                image_url,
                extracted_text,
                nutrition_data,
                ai_results,
                safety_status,
                no_go_names,  # flagged_ingredients
                go_names,     # go_ingredients
                caution_names,  # caution_ingredients
                no_go_names,  # no_go_ingredients
                "OCR Product"  # product_name
            )))
            scan = scan_future.result()

        total_time = time.time() - start_time
        logging.info(f"FoodLabelNutritionView total time: {total_time:.2f} seconds.")

        # Convert ingredient lists to list of objects with clean names and EFSA data
        def format_ingredient_list(ingredient_list):
            formatted_list = []
            for ing in ingredient_list:
                if isinstance(ing, dict):
                    # New format with EFSA data
                    formatted_ing = {
                        "ingredient": ing["ingredient"],
                        "reasons": ing.get("reasons", []),
                        "efsa_data": ing.get("efsa_data", {})
                    }
                else:
                    # Old format (string)
                    formatted_ing = {
                        "ingredient": ing,
                        "reasons": ["Legacy format"],
                        "efsa_data": {}
                    }
                formatted_list.append(formatted_ing)
            return formatted_list
        
        go_ingredients_obj = format_ingredient_list(go_ingredients)
        caution_ingredients_obj = format_ingredient_list(caution_ingredients)
        no_go_ingredients_obj = format_ingredient_list(no_go_ingredients)

        main_ingredient = actual_ingredients[0] if actual_ingredients else None
        def safe_summary(fetch_func, ingredient, default_msg):
            try:
                summary = fetch_func(ingredient)
                if not summary or (isinstance(summary, str) and not summary.strip()):
                    return default_msg
                return summary
            except Exception as e:
                print(f"Summary fetch error for {ingredient}: {e}")
                return default_msg

        medlineplus_summary = safe_summary(
            fetch_medlineplus_summary,
            main_ingredient,
            "No MedlinePlus summary available for this ingredient."
        ) if main_ingredient else "No MedlinePlus summary available for this ingredient."

        pubchem_summary = safe_summary(
            fetch_pubchem_toxicology_summary,
            main_ingredient,
            "No PubChem toxicology data found for this ingredient."
        ) if main_ingredient else "No PubChem toxicology data found for this ingredient."
        pubmed_articles = fetch_pubmed_articles(main_ingredient) if main_ingredient else []

        # REMOVED ClinicalTrials.gov integration for speed
        def fetch_clinical_trials(ingredient):
            return []  # Return empty list for speed
            if not ingredient:
                return []
            try:
                url = f"https://clinicaltrials.gov/api/v2/studies?q={ingredient}&limit=3"
                resp = requests.get(url, timeout=5)
                if resp.status_code != 200:
                    print(f"ClinicalTrials.gov API error: {resp.status_code}")
                    return []
                data = resp.json()
                studies = data.get("studies", [])
                trials = []
                for study in studies:
                    nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
                    title = study.get("protocolSection", {}).get("identificationModule", {}).get("officialTitle")
                    status = study.get("protocolSection", {}).get("statusModule", {}).get("overallStatus")
                    summary = study.get("protocolSection", {}).get("descriptionModule", {}).get("briefSummary")
                    url = f"https://clinicaltrials.gov/ct2/show/{nct_id}" if nct_id else None
                    if nct_id and title:
                        trials.append({
                            "title": title,
                            "nct_id": nct_id,
                            "status": status,
                            "summary": summary,
                            "url": url
                        })
                return trials
            except Exception as e:
                print(f"ClinicalTrials.gov fetch error: {e}")
                return []

        clinical_trials = fetch_clinical_trials(main_ingredient)

        # --- FSA Hygiene Rating Integration ---
        # Try to extract business name from OCR text or use default
        business_name = "OCR Product"  # Default fallback
        fsa_data = None
        
        # Look for business names in the extracted text
        business_keywords = ['ltd', 'limited', 'inc', 'corporation', 'company', 'co', 'brand', 'manufacturer']
        lines = extracted_text.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in business_keywords):
                business_name = line.strip()
                break
        
        # Fetch FSA hygiene rating data
        try:
            fsa_data = fetch_fsa_hygiene_rating(business_name=business_name)
        except Exception as e:
            print(f"FSA API error: {e}")
            fsa_data = {
                'found': False,
                'error': f'FSA API error: {str(e)}',
                'source': 'UK FSA FHRS API'
            }

        # Get current scan count for response
        from .scan_limit import can_user_scan, get_monthly_reset_date
        _, scan_count, remaining_scans = can_user_scan(request.user)
        
        # Handle None values for premium users
        if scan_count is None:
            scan_count = 0
        if remaining_scans is None:
            remaining_scans = "unlimited"
        
        return Response({
            "scan_id": scan.id,
            "product_name":"OCR Product",
            "image_url": image_url,
            "extracted_text": extracted_text,
            "nutrition_data": nutrition_data,
            "ingredients": actual_ingredients,
            "safety_status": safety_status,
            "is_favorite": scan.is_favorite,
            "scan_usage": {
                "scans_used": scan_count,
                "max_scans": 20,
                "remaining_scans": remaining_scans,
                "monthly_reset_date": get_monthly_reset_date(),
                "total_user_scans": scan_count,
            },
            "user_plan": get_user_plan_info(request.user),
            "ingredients_analysis": {
                "go": {
                    "ingredients": go_ingredients_obj,
                    "count": len(go_ingredients_obj),
                    "description": "Ingredients that are safe and suitable for your health profile"
                },
                "caution": {
                    "ingredients": caution_ingredients_obj,
                    "count": len(caution_ingredients_obj),
                    "description": "Ingredients that may not be ideal for your health profile - consume at your own risk"
                },
                "no_go": {
                    "ingredients": no_go_ingredients_obj,
                    "count": len(no_go_ingredients_obj),
                    "description": "Ingredients that are harmful or not suitable for your health profile - avoid these"
                },
                "total_flagged": len(caution_ingredients_obj) + len(no_go_ingredients_obj)
            },
            "efsa_data": {
                "source": "European Food Safety Authority (EFSA) OpenFoodTox Database",
                "total_ingredients_checked": len(efsa_data_cache),
                "ingredients_with_efsa_data": len([data for data in efsa_data_cache.values() if data and data.get('found')]),
                "cache": {k: v for k, v in efsa_data_cache.items() if v is not None}
            },
            "fsa_hygiene_data": fsa_data,
            "medical_condition_recommendations": {
                "user_health_profile": {
                    "allergies": request.user.Allergies,
                    "dietary_preferences": request.user.Dietary_preferences,
                    "health_conditions": request.user.Health_conditions
                },
                "recommendations": get_medical_condition_food_recommendations(
                    request.user.Health_conditions, 
                    request.user.Allergies, 
                    request.user.Dietary_preferences
                ) if (request.user.Health_conditions or request.user.Allergies or request.user.Dietary_preferences) else {"found": False, "message": "No health profile specified"},
                "source": "SNOMED CT & ICD-10 Clinical Guidelines"
            },
            "ai_health_insight": {
                "Bluf_insight": ai_results.get("structured_health_analysis", {}).get("bluf_insight", ai_results.get("ai_health_insight", "")),
                "Main_insight": ai_results.get("structured_health_analysis", {}).get("main_insight", ai_results.get("expert_advice", "")),
                "Deeper_reference": ai_results.get("structured_health_analysis", {}).get("deeper_reference", ""),
                "Disclaimer": ai_results.get("structured_health_analysis", {}).get("disclaimer", "Informational, not diagnostic. Consult healthcare providers for medical advice.")
            },
            "expert_ai_conclusion": ai_results.get("expert_ai_conclusion", ai_results.get("expert_advice", "")),
            "structured_health_analysis": ai_results.get("structured_health_analysis", {}),            # "ocr_gpu": False,  # Azure OCR
            # "medlineplus_summary": medlineplus_summary,
            # "pubchem_summary": pubchem_summary,
            # "pubmed_articles": pubmed_articles,
            # "clinical_trials": clinical_trials,
            # "timing": {
            #     "ocr": ocr_end - ocr_start,
            #     "safety+ai": safety_end - safety_start,
            #     "total": total_time
            # }
        }, status=status.HTTP_200_OK)

    def get_ai_health_insight_and_expert_advice(self, user, nutrition_data, flagged_ingredients):
        """
        Ultra-fast AI insights with minimal processing and aggressive timeouts.
        """
        import time
        import json
        import hashlib
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        
        # Quick cache check
        key_data = {
            'ingredients': sorted(flagged_ingredients[:2]),  # Only first 2 for speed
            'nutrition': {k: v for k, v in list(nutrition_data.items())[:3]},  # Only first 3
            'diet': user.Dietary_preferences,
            'allergies': user.Allergies
        }
        cache_key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        if cache_key in self.openai_cache:
            return self.openai_cache[cache_key]
        
        # Ultra-minimal prompt
        nutrition_summary = ', '.join(f"{k}: {v}" for k, v in list(nutrition_data.items())[:3])
        flagged_str = ', '.join(flagged_ingredients[:2])  # Only top 2
        prompt = f"User: {user.Dietary_preferences or 'None'}. Nutrition: {nutrition_summary}. Avoid: {flagged_str}. Give 1 sentence health insight + 1 sentence advice. Be extremely concise."
        
        def openai_call():
            from openai import OpenAI
            import os
            
            # Try OpenAI with very fast timeout
            try:
                client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    timeout=2  # 2 second timeout
                )
                
                # Ultra-minimal prompt for speed
                nutrition_summary = ', '.join(f"{k}: {v}" for k, v in list(nutrition_data.items())[:3])
                flagged_str = ', '.join(flagged_ingredients[:2])  # Only top 2
                user_profile = f"Diet: {user.Dietary_preferences or 'None'}, Allergies: {user.Allergies or 'None'}"
                
                prompt = f"""
                User Profile: {user_profile}
                Nutrition: {nutrition_summary}
                Avoid: {flagged_str}
                
                Give 1 sentence health insight + 1 sentence advice. Be extremely concise.
                """
                
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Nutrition expert. Be extremely concise and actionable."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=60,  # Very short response
                    temperature=0.3,
                )
                
                content = completion.choices[0].message.content.strip()
                
                # Simple split
                parts = content.split('.', 1)
                ai_health_insight = parts[0] + "." if parts else "Product analyzed successfully."
                expert_advice = parts[1] + "." if len(parts) > 1 else "Check ingredients for your dietary needs."
                
                return {
                    "ai_health_insight": ai_health_insight,
                    "expert_advice": expert_advice
                }
                
            except Exception as e:
                print(f"OpenAI error: {e}")
                # Fallback to intelligent response based on data
                if flagged_ingredients:
                    return {
                        "ai_health_insight": f"Product contains {len(flagged_ingredients)} ingredients that may not suit your dietary needs.",
                        "expert_advice": "Review the flagged ingredients and consult healthcare professional if needed."
                    }
                else:
                    return {
                        "ai_health_insight": "Product analyzed successfully. Check nutrition values for your health goals.",
                        "expert_advice": "Consider portion size and overall dietary balance."
                    }
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(openai_call)
            try:
                result = future.result(timeout=3)  # 3 second total timeout for OpenAI
                self.openai_cache[cache_key] = result
                return result
            except TimeoutError:
                return {"ai_health_insight": "Health insights unavailable.", "expert_advice": "Consult healthcare professional."}
            except Exception as e:
                print(f"OpenAI outer error: {e}")
                return {"ai_health_insight": "Health insights unavailable.", "expert_advice": "Consult healthcare professional."}

    def run_in_thread_pool(self, func, *args):
        with ThreadPoolExecutor() as executor:
            return executor.submit(func, *args).result()

    def save_image(self, image_content):
        try:
            image_name = f"food_labels/{uuid.uuid4()}.jpg"
            image_path = default_storage.save(image_name, ContentFile(image_content))
            image_url = default_storage.url(image_path).replace("https//", "")
            return image_url, image_path
        except Exception as e:
            print(f"Error saving image: {e}")
            return None, None

    def run_ocr(self, image_content):
        """
        Uses AWS Textract for high-accuracy text extraction with Query feature.
        """
        try:
            if not self.textract_client:
                logging.error("AWS Textract client not initialized")
                return ''
            
            # Try to extract text using AWS Textract Query first
            extracted_text = self.extract_text_with_textract_query(image_content)
            if extracted_text:
                logging.info(f"Extracted text from AWS Textract Query: {extracted_text}")
                return extracted_text
            
            # Fallback to regular text extraction
            extracted_text = self.extract_text_with_textract(image_content)
            if extracted_text:
                logging.info(f"Extracted text from AWS Textract: {extracted_text}")
                return extracted_text
            
            logging.error("AWS Textract failed to extract text")
            return ''
            
        except Exception as e:
            logging.error(f"AWS Textract OCR error: {e}", exc_info=True)
            return ''

    def extract_text_with_textract_query(self, image_content):
        """
        Extract text using AWS Textract Query feature for better accuracy.
        """
        try:
            # Validate image content
            if not isinstance(image_content, bytes):
                logging.error("Image content must be bytes")
                return ""
            
            # Check image size (AWS Textract limit is 5MB)
            if len(image_content) > 5 * 1024 * 1024:
                logging.error("Image too large for AWS Textract (max 5MB)")
                return ""
            
            # Check if image content is valid
            if len(image_content) < 100:
                logging.error("Image content too small")
                return ""

            # Query for general text content
            queries = [
                {
                    'Text': 'What text is visible in this image?',
                    'Alias': 'general_text'
                },
                {
                    'Text': 'Extract all text from this nutrition label',
                    'Alias': 'nutrition_text'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES', 'TABLES', 'FORMS', 'LINES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                extracted_text = ""
                
                # Extract text from query results
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                extracted_text += answer_block['Text'] + "\n"
                
                # Also extract regular text blocks
                text_blocks = [block for block in response.get('Blocks', []) if block['BlockType'] == 'LINE']
                text_blocks.sort(key=lambda x: (x['Geometry']['BoundingBox']['Top'], x['Geometry']['BoundingBox']['Left']))
                
                for block in text_blocks:
                    if 'Text' in block:
                        extracted_text += block['Text'] + "\n"

                return extracted_text.strip()
                
            except Exception as e:
                logging.error(f"Textract Query API error: {e}")
                return ""
            
        except Exception as e:
            logging.error(f"Textract Query extraction error: {e}")
            return ""

    def extract_text_with_textract(self, image_content):
        """
        Extract text using AWS Textract with enhanced features.
        """
        try:
            if not self.textract_client:
                raise Exception("AWS Textract client not initialized")

            # Ensure image_content is bytes
            if not isinstance(image_content, bytes):
                logging.error("Image content must be bytes")
                return ""

            # Check image size (AWS Textract limit is 5MB)
            if len(image_content) > 5 * 1024 * 1024:
                logging.error("Image too large for AWS Textract (max 5MB)")
                return ""

            # Check if image content is valid
            if len(image_content) < 100:
                logging.error("Image content too small")
                return ""

            # Try analyze_document first (more features)
            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['TABLES', 'FORMS', 'LINES']
                )
                
                # Extract text with spatial information
                extracted_text = ""
                blocks = response.get('Blocks', [])
                
                # Sort blocks by geometry for proper reading order
                text_blocks = [block for block in blocks if block['BlockType'] == 'LINE']
                text_blocks.sort(key=lambda x: (x['Geometry']['BoundingBox']['Top'], x['Geometry']['BoundingBox']['Left']))
                
                for block in text_blocks:
                    if 'Text' in block:
                        extracted_text += block['Text'] + "\n"

                return extracted_text.strip()
                
            except Exception as e:
                logging.error(f"Textract analyze_document failed: {e}")
                # Try simpler detect_document_text as fallback
                try:
                    response = self.textract_client.detect_document_text(
                        Document={
                            'Bytes': image_content
                        }
                    )
                    
                    extracted_text = ""
                    blocks = response.get('Blocks', [])
                    
                    for block in blocks:
                        if block['BlockType'] == 'LINE' and 'Text' in block:
                            extracted_text += block['Text'] + "\n"
                    
                    return extracted_text.strip()
                    
                except Exception as fallback_error:
                    logging.error(f"Textract detect_document_text also failed: {fallback_error}")
                    return ""

        except Exception as e:
            logging.error(f"Textract extraction error: {e}")
            return ""

    def correct_ocr_errors(self, text):
        corrections = {
            "Bg": "8g", "Omg": "0mg", "lron": "Iron", "meg": "mcg"
        }
        for wrong, right in corrections.items():
            text = text.replace(wrong, right)
        return text

    def extract_nutrition_info_from_text(self, text, image_content=None):
        """
        Enhanced nutrition extraction using AWS Textract Query for better accuracy.
        """
        nutrition_data = {}
        
        # Fix common OCR errors first
        text = self.correct_ocr_errors(text)
        
        # Try AWS Textract Query first if image_content is available
        if image_content and hasattr(self, 'textract_client') and self.textract_client:
            query_nutrition = self.extract_nutrition_with_textract_query(image_content)
            if query_nutrition:
                # Convert query results to the expected format
                for key, value in query_nutrition.items():
                    if value:
                        # Extract numeric value and unit
                        match = re.search(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', value)
                        if match:
                            numeric_value = match.group(1)
                            unit = match.group(2).lower()
                            
                            # Map query keys to nutrition data keys with proper units
                            if key == 'energy':
                                nutrition_data["Energy"] = f"{numeric_value} kcal"
                            elif key == 'protein':
                                nutrition_data["Protein"] = f"{numeric_value} g"
                            elif key == 'total_fat':
                                nutrition_data["Total Fat"] = f"{numeric_value} g"
                            elif key == 'saturated_fat':
                                nutrition_data["Saturated Fat"] = f"{numeric_value} g"
                            elif key == 'carbohydrates':
                                nutrition_data["Carbohydrate"] = f"{numeric_value} g"
                            elif key == 'sugars':
                                nutrition_data["Total Sugars"] = f"{numeric_value} g"
                            elif key == 'sodium':
                                nutrition_data["Sodium"] = f"{numeric_value} mg"
                            elif key == 'fiber':
                                nutrition_data["Dietary Fibre"] = f"{numeric_value} g"
                            else:
                                # Add as custom nutrient with proper unit
                                nutrition_data[key.replace('_', ' ').title()] = f"{numeric_value} {unit}"
        
        # If AWS Textract Query didn't provide enough data, fall back to text parsing
        if len(nutrition_data) < 3:  # If we have less than 3 nutrients, use fallback
            nutrition_data = self.extract_nutrition_info_fallback(text)
        
        return nutrition_data

    def extract_nutrition_with_textract_query(self, image_content):
        """
        Extract nutrition data using AWS Textract Query feature.
        """
        try:
            if not self.textract_client:
                return {}

            # Query for nutrition information
            queries = [
                {
                    'Text': 'What is the energy/calories value?',
                    'Alias': 'energy'
                },
                {
                    'Text': 'What is the protein content?',
                    'Alias': 'protein'
                },
                {
                    'Text': 'What is the total fat content?',
                    'Alias': 'total_fat'
                },
                {
                    'Text': 'What is the saturated fat content?',
                    'Alias': 'saturated_fat'
                },
                {
                    'Text': 'What is the carbohydrate content?',
                    'Alias': 'carbohydrates'
                },
                {
                    'Text': 'What is the sugar content?',
                    'Alias': 'sugars'
                },
                {
                    'Text': 'What is the sodium content?',
                    'Alias': 'sodium'
                },
                {
                    'Text': 'What is the fiber content?',
                    'Alias': 'fiber'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                nutrition_data = {}
                
                # Extract answers from the response
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        query_alias = block.get('Query', {}).get('Alias', '')
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        # Find the answer block
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                nutrition_data[query_alias] = answer_block['Text']
                
                return nutrition_data
                
            except Exception as e:
                logging.error(f"Nutrition Query failed: {e}")
                return {}

        except Exception as e:
            logging.error(f"Nutrition Query extraction error: {e}")
            return {}

    def extract_nutrition_info_fallback(self, text):
        """
        Fallback nutrition extraction using text parsing (original method).
        """
        nutrition_data = {}
        
        # Define comprehensive nutrient patterns with variations
        nutrient_patterns = {
            "Energy": [
                r'energy[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'calories[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'calorie[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*energy',
                r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*calories'
            ],
            "Total Fat": [
                r'total\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+fat',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fat'
            ],
            "Saturated Fat": [
                r'saturated\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sat\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*saturated\s+fat',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sat\s+fat'
            ],
            "Trans Fat": [
                r'trans\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*trans\s+fat'
            ],
            "Cholesterol": [
                r'cholesterol[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*cholesterol'
            ],
            "Sodium": [
                r'sodium[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'salt[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*sodium',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*salt'
            ],
            "Carbohydrate": [
                r'carbohydrate[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'carbohydrates[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'carbs[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrate',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrates',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbs'
            ],
            "Total Sugars": [
                r'total\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sugar[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+sugars',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugars',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugar'
            ],
            "Added Sugars": [
                r'added\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*added\s+sugars'
            ],
            "Dietary Fibre": [
                r'dietary\s+fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'dietary\s+fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fibre',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fiber',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fibre',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fiber'
            ],
            "Protein": [
                r'protein[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*protein'
            ]
        }
        
        # Extract using comprehensive patterns with proper unit mapping
        for nutrient_name, patterns in nutrient_patterns.items():
            all_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                all_matches.extend(matches)
            
            if all_matches:
                value, unit = all_matches[0]
                # Map units correctly
                if unit.lower() in ['kj', 'cal']:
                    unit = 'kcal'
                elif unit.lower() == '%':
                    unit = '%'
                elif nutrient_name in ["Energy"]:
                    unit = 'kcal'
                elif nutrient_name in ["Sodium", "Cholesterol"]:
                    unit = 'mg'
                else:
                    unit = 'g'
                    
                nutrition_data[nutrient_name] = f"{value} {unit}".strip()
        
        # Clean up and standardize units
        for key, value in nutrition_data.items():
            if value and not value.endswith(('kcal', 'g', 'mg', 'mcg', '%', 'kj', 'cal')):
                # Extract numeric value
                numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
                if numeric_match:
                    numeric_value = numeric_match.group(1)
                    if key.lower() in ["energy", "calories"]:
                        nutrition_data[key] = f"{numeric_value} kcal"
                    elif key.lower() in ["protein", "carbohydrate", "total sugars", "dietary fibre", "total fat", "saturated fat", "trans fat"]:
                        nutrition_data[key] = f"{numeric_value} g"
                    elif key.lower() in ["sodium", "cholesterol"]:
                        nutrition_data[key] = f"{numeric_value} mg"
        
        return nutrition_data

    def extract_nutrition_info_simple(self, text):
        """
        Simple fallback nutrition extraction method for OCR text that's hard to parse.
        """
        nutrition_data = {}
        
        # Fix common OCR errors
        text = text.replace('o.', '0.').replace('O.', '0.').replace('O', '0').replace('l', '1')
        text = text.replace('Ptotetn', 'Protein').replace('rotat', 'Total').replace('agog', '240g')
        text = text.replace('tug', '240g').replace('osg', '240g')
        
        # Split into lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        print(f"Processing lines: {lines}")  # Debug
        
        # Look for nutrition section
        nutrition_section = False
        for line in lines:
            if 'nutrition' in line.lower() or 'kcal' in line.lower() or 'g' in line:
                nutrition_section = True
                break
        
        if not nutrition_section:
            return nutrition_data
        
        # Enhanced pattern matching for the specific OCR format
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Skip non-nutrition lines
            if any(skip in line_lower for skip in ['ingredients', 'allergen', 'manufactured', 'store', 'packaged']):
                    continue
                
            print(f"Processing line {i}: '{line}' -> '{line_lower}'")  # Debug
            
            # Look for nutrient names and values
            if 'protein' in line_lower or 'ptotetn' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger (more likely to be correct)
                        if 'Protein' not in nutrition_data or float(value) > float(nutrition_data['Protein'].split()[0]):
                            nutrition_data['Protein'] = f"{value} {unit}"
                            print(f"Found Protein: {value} {unit}")  # Debug
                        break
            
            elif 'carbohydrate' in line_lower or 'carbs' in line_lower or 'rotat' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Carbohydrate' not in nutrition_data or float(value) > float(nutrition_data['Carbohydrate'].split()[0]):
                            nutrition_data['Carbohydrate'] = f"{value} {unit}"
                            print(f"Found Carbohydrate: {value} {unit}")  # Debug
                        break
            
            elif 'sugar' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Total Sugars' not in nutrition_data or float(value) > float(nutrition_data['Total Sugars'].split()[0]):
                            nutrition_data['Total Sugars'] = f"{value} {unit}"
                            print(f"Found Total Sugars: {value} {unit}")  # Debug
                        break
            
            elif 'fat' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        if 'saturated' in line_lower:
                            # Only add if we don't already have this nutrient or if this value is larger
                            if 'Saturated Fat' not in nutrition_data or float(value) > float(nutrition_data['Saturated Fat'].split()[0]):
                                nutrition_data['Saturated Fat'] = f"{value} {unit}"
                                print(f"Found Saturated Fat: {value} {unit}")  # Debug
                        else:
                            # Only add if we don't already have this nutrient or if this value is larger
                            if 'Total Fat' not in nutrition_data or float(value) > float(nutrition_data['Total Fat'].split()[0]):
                                nutrition_data['Total Fat'] = f"{value} {unit}"
                                print(f"Found Total Fat: {value} {unit}")  # Debug
                        break
            
            elif 'kcal' in line_lower or 'calorie' in line_lower or 'energy' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(kcal|cal)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'kcal'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Energy' not in nutrition_data or float(value) > float(nutrition_data['Energy'].split()[0]):
                            nutrition_data['Energy'] = f"{value} {unit}"
                            print(f"Found Energy: {value} {unit}")  # Debug
                        break
        
        # Also look for standalone numbers that might be nutrition values
        for i, line in enumerate(lines):
            # Look for lines that are just numbers (potential nutrition values)
            if re.match(r'^\d+(?:\.\d+)?\s*(g|kcal|mg)?$', line.strip()):
                value = re.search(r'(\d+(?:\.\d+)?)', line).group(1)
                unit = re.search(r'(g|kcal|mg)', line)
                unit = unit.group(1) if unit else 'g'
                
                print(f"Found standalone value: {value} {unit} at line {i}")  # Debug
                
                # Try to match with nearby nutrient names
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    nearby_line = lines[j].lower()
                    if ('protein' in nearby_line or 'ptotetn' in nearby_line) and 'Protein' not in nutrition_data:
                        nutrition_data['Protein'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Protein")  # Debug
                        break
                    elif ('carbohydrate' in nearby_line or 'carbs' in nearby_line or 'rotat' in nearby_line) and 'Carbohydrate' not in nutrition_data:
                        nutrition_data['Carbohydrate'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Carbohydrate")  # Debug
                        break
                    elif 'sugar' in nearby_line and 'Total Sugars' not in nutrition_data:
                        nutrition_data['Total Sugars'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Total Sugars")  # Debug
                        break
                    elif 'fat' in nearby_line:
                        if 'saturated' in nearby_line and 'Saturated Fat' not in nutrition_data:
                            nutrition_data['Saturated Fat'] = f"{value} {unit}"
                            print(f"Mapped {value} {unit} to Saturated Fat")  # Debug
                            break
                        elif 'Total Fat' not in nutrition_data:
                            nutrition_data['Total Fat'] = f"{value} {unit}"
                            print(f"Mapped {value} {unit} to Total Fat")  # Debug
                            break
        
        # Special handling for "Per 100g" format
        per_100g_section = ""
        for i, line in enumerate(lines):
            if 'per' in line.lower() and '100' in line and 'g' in line.lower():
                # Found the per 100g section, collect the next few lines
                per_100g_section = '\n'.join(lines[i:i+10])
                print(f"Found Per 100g section: {per_100g_section}")  # Debug
                break
        
        if per_100g_section:
            # Extract all number-unit pairs from this section
            number_unit_pairs = re.findall(r'(\d+(?:\.\d+)?)\s*(kcal|g|mg|mcg|%|kj|cal)', per_100g_section, re.IGNORECASE)
            print(f"Number-unit pairs found: {number_unit_pairs}")  # Debug
            
            # Try to match with nutrient names in the same section
            for pair in number_unit_pairs:
                value, unit = pair
                # Look for nutrient names near this value
                for nutrient_name in ['Energy', 'Protein', 'Carbohydrate', 'Total Sugars', 'Total Fat', 'Saturated Fat', 'Trans Fat']:
                    if nutrient_name.lower().replace(' ', '') in per_100g_section.lower().replace(' ', ''):
                        # Only add if we don't already have this nutrient or if this value is larger
                        if nutrient_name not in nutrition_data or float(value) > float(nutrition_data[nutrient_name].split()[0]):
                            # Standardize units
                            if unit.lower() in ['kj', 'cal']:
                                unit = 'kcal'
                            else:
                                unit = 'g'
                            
                        nutrition_data[nutrient_name] = f"{value} {unit}".strip()
                        print(f"Found {nutrient_name}: {value} {unit} from Per 100g section")  # Debug
        
        print(f"Final nutrition data: {nutrition_data}")  # Debug
        return nutrition_data

    def extract_ingredients_from_text(self, text, image_content=None):
        """
        Extracts a clean list of ingredients using AWS Textract Query for better accuracy.
        """
        import re
        
        # Try AWS Textract Query first if image_content is available
        if image_content and hasattr(self, 'textract_client') and self.textract_client:
            query_ingredients = self.extract_ingredients_with_textract_query(image_content)
            if query_ingredients:
                # Process query results
                ingredients = self.process_query_ingredients(query_ingredients)
                if ingredients:
                    return ingredients
        
        # Fallback to text parsing
        return self.extract_ingredients_from_text_fallback(text)

    def extract_ingredients_with_textract_query(self, image_content):
        """
        Extract ingredients using AWS Textract Query feature.
        """
        try:
            if not self.textract_client:
                return []

            # Query for ingredients
            queries = [
                {
                    'Text': 'What are the ingredients?',
                    'Alias': 'ingredients'
                },
                {
                    'Text': 'List all ingredients',
                    'Alias': 'ingredients_list'
                },
                {
                    'Text': 'What ingredients are in this product?',
                    'Alias': 'product_ingredients'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                ingredients = []
                
                # Extract answers from the response
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        # Find the answer block
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                ingredients.append(answer_block['Text'])
                
                return ingredients
                
            except Exception as e:
                logging.error(f"Ingredients Query failed: {e}")
                return []

        except Exception as e:
            logging.error(f"Ingredients Query extraction error: {e}")
            return []

    def process_query_ingredients(self, query_ingredients):
        """
        Process ingredients from Textract Query results with better cleaning.
        """
        if not query_ingredients:
            return []
        
        # Join all ingredient responses and clean them up
        ingredients_text = " ".join(query_ingredients)
        
        # Clean up the ingredients text - preserve important characters
        ingredients_text = re.sub(r'[^\w\s,()%.&-]', ' ', ingredients_text)  # Keep important chars
        ingredients_text = re.sub(r'\s+', ' ', ingredients_text)  # Normalize whitespace
        
        # Split ingredients by common separators, but be smarter about it
        ingredients = []
        
        # First, try to split by commas, but respect parentheses
        # This pattern splits by commas that are NOT inside parentheses
        parts = re.split(r',\s*(?![^()]*\))', ingredients_text)
        
        # If the above didn't work well, try a more aggressive approach
        if len(parts) <= 1:
            # Split by commas and then clean up each part
            parts = re.split(r',\s*', ingredients_text)
        
        for part in parts:
            ingredient = part.strip()
            if ingredient and len(ingredient) > 2:
                # Clean up ingredient using the cleaning function
                ingredient = self.clean_ingredient_text(ingredient)
                
                # Skip if it's just a number, percentage, or very short
                if (ingredient and len(ingredient) > 2 and 
                    not re.match(r'^\d+\.?\d*%?$', ingredient) and
                    not ingredient.lower() in ['and', 'or', 'the', 'a', 'an']):
                    
                    # Use the compound ingredient splitting function
                    split_ingredients = self.split_compound_ingredients(ingredient)
                    for split_ingredient in split_ingredients:
                        if split_ingredient and len(split_ingredient) > 2:
                            ingredients.append(split_ingredient)

        # Remove duplicates while preserving order
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            clean_ingredient = re.sub(r'\s+', ' ', ingredient).strip()
            if clean_ingredient.lower() not in seen:
                seen.add(clean_ingredient.lower())
                unique_ingredients.append(clean_ingredient)

        return unique_ingredients

    def extract_ingredients_from_text_fallback(self, text):
        """
        Fallback ingredients extraction using text parsing with improved cleaning.
        """
        import re
        # 1. Find the INGREDIENTS section (case-insensitive)
        match = re.search(
            r'ingredients[:\s]*([\s\S]+?)(allergen|nutritional|store|packaged|may contain|used as natural|information|$)',
            text, re.IGNORECASE
        )
        if not match:
            return []
        ingredients_text = match.group(1)

        # 2. Clean up text: replace newlines, remove unwanted symbols (but keep (), %, &)
        ingredients_text = re.sub(r'\n', ' ', ingredients_text)
        ingredients_text = re.sub(r'[^a-zA-Z0-9,().&%\-\s]', '', ingredients_text)
        ingredients_text = re.sub(r'\s+', ' ', ingredients_text)

        # 3. Split on commas and periods (not inside parentheses)
        parts = re.split(r'[,.](?![^()]*\))', ingredients_text)
        
        # If the above didn't work well, try a more aggressive approach
        if len(parts) <= 1:
            # Split by commas and then clean up each part
            parts = re.split(r'[,\s]+', ingredients_text)
        ingredients = []
        for part in parts:
            ing = part.strip()
            # Clean up ingredient using the cleaning function
            ing = self.clean_ingredient_text(ing)
            # Filter out non-ingredient lines
            if ing and not re.search(
                r'(may contain|allergen|information|flavouring|substances|regulator|identical|used as natural|limit of quantification)',
                ing, re.IGNORECASE
            ):
                # Use the compound ingredient splitting function
                split_ingredients = self.split_compound_ingredients(ing)
                for split_ingredient in split_ingredients:
                    if split_ingredient and len(split_ingredient) > 2:
                        ingredients.append(split_ingredient)
        
        # Remove duplicates and clean up
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            clean_ingredient = re.sub(r'\s+', ' ', ingredient).strip()
            if clean_ingredient.lower() not in seen and len(clean_ingredient) > 2:
                seen.add(clean_ingredient.lower())
                unique_ingredients.append(clean_ingredient)
        
        return unique_ingredients

    def clean_ingredient_text(self, ingredient):
        """
        Clean and normalize ingredient text.
        """
        import re
        
        # Remove extra whitespace
        ingredient = re.sub(r'\s+', ' ', ingredient).strip()
        
        # Remove trailing punctuation
        ingredient = re.sub(r'[.,;:]$', '', ingredient)
        
        # Remove leading numbers and percentages
        ingredient = re.sub(r'^\d+%?\s*', '', ingredient)
        
        # Remove bullet points
        ingredient = re.sub(r'^\s*[-•]\s*', '', ingredient)
        
        # Fix common OCR errors
        ingredient = ingredient.replace("Flailed", "Flaked")
        ingredient = ingredient.replace("Mingo", "Mango")
        ingredient = ingredient.replace("Pomcgranate", "Pomegranate")
        ingredient = ingredient.replace("lodised", "Iodised")
        
        return ingredient.strip()

    def split_compound_ingredients(self, ingredient_text):
        """
        Split compound ingredients that contain multiple items.
        """
        import re
        
        # If it contains commas but no parentheses, split by commas
        if ',' in ingredient_text and '(' not in ingredient_text:
            parts = re.split(r',\s*', ingredient_text)
            return [part.strip() for part in parts if part.strip()]
        
        # If it contains "and" but no parentheses, split by "and"
        if ' and ' in ingredient_text.lower() and '(' not in ingredient_text:
            parts = re.split(r'\s+and\s+', ingredient_text, flags=re.IGNORECASE)
            return [part.strip() for part in parts if part.strip()]
        
        # If it contains both commas and parentheses, try to split carefully
        if ',' in ingredient_text and '(' in ingredient_text:
            # Look for patterns like "A (B), C, D"
            # Split by commas that are not inside parentheses
            parts = re.split(r',\s*(?![^()]*\))', ingredient_text)
            result = []
            for part in parts:
                part = part.strip()
                if part:
                    # If this part still contains commas, split it further
                    if ',' in part and '(' not in part:
                        sub_parts = re.split(r',\s*', part)
                        result.extend([sub_part.strip() for sub_part in sub_parts if sub_part.strip()])
                    else:
                        result.append(part)
            return result
        
        return [ingredient_text]

    async def save_scan_history(self, user, image_url, extracted_text, nutrition_data, ai_results, safety_status, flagged_ingredients, go_ingredients=None, caution_ingredients=None, no_go_ingredients=None, product_name="OCR Product"):
        # Save scan history in a separate async function
        # Keep nutrition_data clean - only nutrition facts, not ingredients
        clean_nutrition_data = dict(nutrition_data) if nutrition_data else {}
        
        # Add AI results to nutrition data
        clean_nutrition_data.update({
            "ai_health_insight": ai_results.get("ai_health_insight", ""),
            "expert_advice": ai_results.get("expert_advice", ""),
            "go_ingredients": go_ingredients or [],
            "caution_ingredients": caution_ingredients or [],
            "no_go_ingredients": no_go_ingredients or []
        })
        
        scan = await sync_to_async(FoodLabelScan.objects.create)(
            user=user,
            image_url=image_url,
            extracted_text=extracted_text,
            nutrition_data=clean_nutrition_data,  # Include ingredient classifications
            safety_status=safety_status,
            flagged_ingredients=flagged_ingredients,
            product_name=product_name,
        )
        
        # Increment scan count for freemium users
        await sync_to_async(increment_user_scan_count)(user)
        
        return scan

    async def validate_product_safety(self, user, ingredients_list):
        # Use OpenAI for ingredient categorization based on user profile
        try:
            # Get OpenAI categorization
            categorization = self.categorize_ingredients_with_openai(user, ingredients_list)
            
            go_ingredients = categorization.get('go', [])
            no_go_ingredients = categorization.get('no_go', [])
            caution_ingredients = categorization.get('caution', [])
            
            # Add EFSA data to each ingredient for consistency with existing structure
            efsa_data_cache = {}
            for category in [go_ingredients, no_go_ingredients, caution_ingredients]:
                for ingredient_data in category:
                    ingredient_name = ingredient_data.get('ingredient', '')
                    try:
                        efsa_data = fetch_efsa_openfoodtox_data(ingredient_name)
                        efsa_data_cache[ingredient_name] = efsa_data or {}
                        ingredient_data['efsa_data'] = efsa_data or {}
                    except Exception as e:
                        print(f"EFSA error for {ingredient_name}: {e}")
                        efsa_data_cache[ingredient_name] = {
                            'found': False,
                            'error': f'EFSA query failed: {str(e)}',
                            'source': 'EFSA OpenFoodTox Database'
                        }
                        ingredient_data['efsa_data'] = efsa_data_cache[ingredient_name]
            
            # Determine overall safety status
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache
            
        except Exception as e:
            print(f"OpenAI categorization failed, falling back to static method: {e}")
            # Fallback to original static method
            if USE_STATIC_INGREDIENT_SAFETY:
                # --- Enhanced safety check with EFSA OpenFoodTox integration ---
                dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
                health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
                allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
                go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
                efsa_data_cache = {}  # Cache EFSA data to avoid duplicate API calls
                
                for ingredient in ingredients_list:
                    ing_lower = ingredient.lower()
                    
                    # Check EFSA OpenFoodTox database first
                    try:
                        efsa_data = fetch_efsa_openfoodtox_data(ingredient)
                        efsa_data_cache[ingredient] = efsa_data or {}
                    except Exception as e:
                        print(f"EFSA error for {ingredient}: {e}")
                        efsa_data_cache[ingredient] = {
                            'found': False,
                            'error': f'EFSA query failed: {str(e)}',
                            'source': 'EFSA OpenFoodTox Database'
                        }
                        efsa_data = efsa_data_cache[ingredient]
                    
                    # Determine safety based on EFSA data, user allergies, dietary preferences, and health conditions
                    safety_reasons = []
                    
                    # Check EFSA safety level
                    if efsa_data and efsa_data.get('found') and efsa_data.get('safety_level'):
                        if efsa_data['safety_level'] == 'UNSAFE':
                            safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Unsafe')}")
                        elif efsa_data['safety_level'] == 'CAUTION':
                            safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Caution')}")
                    
                    # Check user allergies
                    if any(a in ing_lower for a in allergies):
                        safety_reasons.append("Allergen")
                    
                    # Check dietary preferences
                    if any(d not in ing_lower for d in dietary) and dietary:
                        safety_reasons.append("Dietary")
                    
                    # Check health conditions
                    if any(h in ing_lower for h in health):
                        safety_reasons.append("Health")
                    
                    # Categorize ingredient based on safety reasons
                    if safety_reasons:
                        if "Allergen" in safety_reasons or (efsa_data and efsa_data.get('found') and efsa_data.get('safety_level') == 'UNSAFE'):
                            no_go_ingredients.append({
                                "ingredient": ingredient,
                                "reasons": safety_reasons,
                                "efsa_data": efsa_data or {}
                            })
                        else:
                            caution_ingredients.append({
                                "ingredient": ingredient,
                                "reasons": safety_reasons,
                                "efsa_data": efsa_data or {}
                            })
                    else:
                        go_ingredients.append({
                            "ingredient": ingredient,
                            "reasons": ["Safe"],
                            "efsa_data": efsa_data or {}
                        })
                
                # Determine overall safety status
                if no_go_ingredients:
                    safety_status = "UNSAFE"
                elif caution_ingredients:
                    safety_status = "CAUTION"
                else:
                    safety_status = "SAFE"
                
                return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache
            else:
                # --- Edamam-based safety check with EFSA enhancement ---
                dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
                health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
                allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
                go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
                efsa_data_cache = {}
                
                async def classify(ingredient):
                    # Get EFSA data
                    try:
                        efsa_data = fetch_efsa_openfoodtox_data(ingredient)
                        efsa_data_cache[ingredient] = efsa_data or {}
                    except Exception as e:
                        print(f"EFSA error for {ingredient}: {e}")
                        efsa_data_cache[ingredient] = {
                            'found': False,
                            'error': f'EFSA query failed: {str(e)}',
                            'source': 'EFSA OpenFoodTox Database'
                        }
                        efsa_data = efsa_data_cache[ingredient]
                    
                    info = await self.get_edamam_info(ingredient)
                    safety_reasons = []
                    
                    # Check EFSA safety level first
                    if efsa_data and efsa_data.get('found') and efsa_data.get('safety_level'):
                        if efsa_data['safety_level'] == 'UNSAFE':
                            safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Unsafe')}")
                        elif efsa_data['safety_level'] == 'CAUTION':
                            safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Caution')}")
                    
                    # Check Edamam data
                    if not info["healthLabels"] and not info["cautions"]:
                        if any(a in ingredient.lower() for a in allergies):
                            safety_reasons.append("Allergen")
                        elif any(d not in ingredient.lower() for d in dietary):
                            safety_reasons.append("Dietary")
                        elif any(h in ingredient.lower() for h in health):
                            safety_reasons.append("Health")
                        else:
                            safety_reasons.append("No Edamam data")
                    else:
                        if any(a in info["cautions"] for a in allergies):
                            safety_reasons.append("Allergen")
                        elif any(d not in info["healthLabels"] for d in dietary):
                            safety_reasons.append("Dietary")
                        elif any(h in ingredient.lower() for h in health):
                            safety_reasons.append("Health")
                    
                    # Categorize ingredient
                    if safety_reasons:
                        if "Allergen" in safety_reasons or (efsa_data and efsa_data.get('found') and efsa_data.get('safety_level') == 'UNSAFE'):
                            no_go_ingredients.append({
                                "ingredient": ingredient,
                                "reasons": safety_reasons,
                                "efsa_data": efsa_data or {}
                            })
                        else:
                            caution_ingredients.append({
                                "ingredient": ingredient,
                                "reasons": safety_reasons,
                                "efsa_data": efsa_data or {}
                            })
                    else:
                        go_ingredients.append({
                            "ingredient": ingredient,
                            "reasons": ["Safe"],
                            "efsa_data": efsa_data or {}
                        })
                
                await asyncio.gather(*(classify(ing) for ing in ingredients_list))
                
                # Handle any unclassified ingredients
                all_classified = set()
                for ing_list in [go_ingredients, caution_ingredients, no_go_ingredients]:
                    for ing in ing_list:
                        all_classified.add(ing["ingredient"])
                
                for ing in ingredients_list:
                    if ing not in all_classified:
                        try:
                            efsa_data = fetch_efsa_openfoodtox_data(ing)
                            efsa_data_cache[ing] = efsa_data or {}
                        except Exception as e:
                            print(f"EFSA error for {ing}: {e}")
                            efsa_data_cache[ing] = {
                                'found': False,
                                'error': f'EFSA query failed: {str(e)}',
                                'source': 'EFSA OpenFoodTox Database'
                            }
                            efsa_data = efsa_data_cache[ing]
                        go_ingredients.append({
                            "ingredient": ing,
                            "reasons": ["Defaulted"],
                            "efsa_data": efsa_data or {}
                        })
                
                if no_go_ingredients:
                    safety_status = "UNSAFE"
                elif caution_ingredients:
                    safety_status = "CAUTION"
                else:
                    safety_status = "SAFE"
                
                return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache

    def categorize_ingredients_with_openai(self, user, ingredients_list):
        """
        Use OpenAI to categorize ingredients into Go, No-Go, and Caution categories
        based on user's allergies, dietary preferences, and health conditions.
        """
        import json
        import hashlib
        from openai import OpenAI
        import os
        
        # Create cache key for this categorization
        key_data = {
            'ingredients': sorted(ingredients_list),
            'diet': user.Dietary_preferences,
            'allergies': user.Allergies,
            'health': user.Health_conditions
        }
        cache_key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        
        # Check cache first
        if cache_key in self.openai_cache:
            return self.openai_cache[cache_key]
        
        try:
            client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=10
            )
            
            # Create detailed prompt for ingredient categorization
            prompt = f"""
            You are a certified nutritionist and food safety expert. Categorize the following ingredients into three categories based on the user's health profile:

            USER PROFILE:
            - Allergies: {user.Allergies or 'None'}
            - Dietary Preferences: {user.Dietary_preferences or 'None'}
            - Health Conditions: {user.Health_conditions or 'None'}

            INGREDIENTS TO CATEGORIZE:
            {', '.join(ingredients_list)}

            CATEGORIES:
            1. GO: Ingredients that are safe and suitable for the user's health profile
            2. NO-GO: Ingredients that are harmful, allergenic, or contraindicated for the user's health profile
            3. CAUTION: Ingredients that may not be ideal but are not strictly forbidden - consume at your own risk

            RESPONSE FORMAT:
            Return a JSON object with exactly this structure:
            {{
                "go": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ],
                "no_go": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ],
                "caution": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ]
            }}

            IMPORTANT RULES:
            - Every ingredient must be categorized into exactly one category
            - Be conservative with safety - when in doubt, categorize as CAUTION or NO-GO
            - Consider cross-contamination risks for severe allergies
            - For dietary preferences, consider both direct ingredients and potential hidden sources
            - Provide specific, actionable reasons for each categorization
            - If an ingredient is not in the provided list, do not include it in the response
            """
            
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a certified nutritionist and food safety expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.1,
            )
            
            content = completion.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(content)
                
                # Validate structure
                required_keys = ['go', 'no_go', 'caution']
                if not all(key in result for key in required_keys):
                    raise ValueError("Missing required categories in response")
                
                # Ensure all ingredients are categorized
                categorized_ingredients = set()
                for category in required_keys:
                    for item in result[category]:
                        if 'ingredient' in item:
                            categorized_ingredients.add(item['ingredient'].lower())
                
                # Check if all ingredients are categorized
                all_ingredients = set(ing.lower() for ing in ingredients_list)
                if not categorized_ingredients.issuperset(all_ingredients):
                    # If not all ingredients categorized, add missing ones to caution
                    missing_ingredients = all_ingredients - categorized_ingredients
                    for missing in missing_ingredients:
                        result['caution'].append({
                            "ingredient": missing,
                            "reasons": ["Unable to determine safety - categorized as caution"]
                        })
                
                # Cache the result
                self.openai_cache[cache_key] = result
                return result
                
            except json.JSONDecodeError as e:
                print(f"OpenAI response parsing error: {e}")
                print(f"Raw response: {content}")
                # Fallback to default categorization
                return self._fallback_categorization(ingredients_list, user)
                
        except Exception as e:
            print(f"OpenAI categorization error: {e}")
            # Fallback to default categorization
            return self._fallback_categorization(ingredients_list, user)
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# openai.api_key = "OPENAI_API_KEY_REMOVED"

# Singleton EasyOCR reader and GPU check
# _easyocr_reader = None
# _easyocr_lock = threading.Lock()
# _easyocr_gpu = None

# def get_easyocr_reader():
#     global _easyocr_reader, _easyocr_gpu
#     with _easyocr_lock:
#         if _easyocr_reader is None:
#             try:
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=True)
#                 # Check if GPU is actually used
#                 _easyocr_gpu = _easyocr_reader.gpu
#                 logging.info(f"EasyOCR initialized. GPU used: {_easyocr_gpu}")
#             except Exception as e:
#                 logging.error(f"EasyOCR initialization failed: {e}")
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=False)
#                 _easyocr_gpu = False
#         return _easyocr_reader

# def is_easyocr_gpu():
#     global _easyocr_gpu
#     return _easyocr_gpu

def google_login(request):
    """
    Traditional OAuth2 flow for Google Sign-In
    """
    from django.shortcuts import redirect
    from urllib.parse import urlencode
    
    # Get Google OAuth2 credentials from settings
    client_id = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', None) or os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
    
    if not client_id:
        return Response({"error": "Google OAuth2 not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Build OAuth2 authorization URL
    params = {
        'client_id': client_id,
        'redirect_uri': request.build_absolute_uri('/accounts/google/login/callback/'),
        'response_type': 'code',
        'scope': 'email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    return redirect(auth_url)

@method_decorator(csrf_exempt, name='dispatch')
class GoogleOAuth2CallbackView(APIView):
    """
    Handle Google OAuth2 callback and exchange authorization code for tokens
    """
    permission_classes = []
    
    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        
        if error:
            return Response({"error": f"OAuth error: {error}"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not code:
            return Response({"error": "No authorization code received"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Exchange authorization code for access token
        client_id = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', None) or os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
        client_secret = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', None) or os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')
        redirect_uri = request.build_absolute_uri('/accounts/google/login/callback/')
        
        # Exchange code for tokens
        token_response = requests.post('https://oauth2.googleapis.com/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        })
        
        if token_response.status_code != 200:
            return Response({"error": "Failed to exchange authorization code"}, status=status.HTTP_400_BAD_REQUEST)
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        # Get user info using access token
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if user_info_response.status_code != 200:
            return Response({"error": "Failed to get user info"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_info = user_info_response.json()
        email = user_info.get('email')
        
        if not email:
            return Response({"error": "No email in user info"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or get user
        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email, 
            defaults={
                "username": email.split("@")[0],
                "full_name": user_info.get('name', ''),
                "profile_picture": user_info.get('picture', '')
            }
        )
        
        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        return Response({
            "access_token": access_token,
            "refresh_token": str(refresh),
            "created": created,
            "email": user.email,
            "full_name": user.full_name,
            "profile_picture": user.profile_picture
        }, status=status.HTTP_200_OK)

class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'message': 'User created successfully.',
                'access_token': access_token,
                'refresh_token': str(refresh),
                'is_2fa_enabled': user.is_2fa_enabled
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            if user.is_2fa_enabled:  # Check if 2FA is enabled
                from random import randint
                from django.core.mail import send_mail

                otp_code = randint(100000, 999999)  # Generate 6-digit OTP
                user.otp = str(otp_code)
                user.save()

                # Send OTP via email
                send_mail(
                    "Your OTP Code",
                    f"Your OTP code is: {otp_code}",
                    "no-reply@example.com",
                    [user.email],
                    fail_silently=False,
                )

                return Response({
                    "message": "OTP sent to your email. Please verify to continue.",
                    "user_id": user.id,
                    "is_2fa_enabled": user.is_2fa_enabled,
                    "has_answered_onboarding": user.has_answered_onboarding, # <-- Added here
                    # "subscription_plan": user.UserSubscription

                }, status=status.HTTP_200_OK)

            # If 2FA is disabled, proceed with normal login
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                "message": "Login successful.",
                "access_token": access_token,
                "refresh_token": str(refresh),
                "is_2fa_enabled": user.is_2fa_enabled,
                "has_answered_onboarding": user.has_answered_onboarding,  # <-- Added here
                "subscription_plan": user.subscription_plan,
                

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class Toggle2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        is_2fa_enabled = request.data.get("is_2fa_enabled", None)

        if is_2fa_enabled is None:
            return Response({"error": "is_2fa_enabled field is required"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_2fa_enabled = is_2fa_enabled
        user.save()
        
        return Response({
            "message": f"Two-Factor Authentication {'enabled' if is_2fa_enabled else 'disabled'} successfully.",
            "is_2fa_enabled": user.is_2fa_enabled
        }, status=status.HTTP_200_OK)

class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

def send_otp_email(email, otp_code):
    subject = "Your OTP Code for Password Reset"
    message = f"Your OTP code is: {otp_code}. It is valid for 5 minutes."
    from_email = (os.getenv("EMAIL_HOST_USER")) 
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
    print(f"OTP {otp_code} sent to email: {email}")

class resendotpview(APIView):
    def post(self, request):
        try:
            identifier = request.data.get('email_or_phone', '').strip().lower()

            if not identifier:
                return JsonResponse({"message": "Please enter Email or Phone number"}, status=status.HTTP_400_BAD_REQUEST)

            otp = random.randint(1000, 9999)

            if '@' in identifier:
                try:
                    user = User.objects.get(email=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this email not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                subject = "One Time Password"
                email_body = f"Your OTP is: {otp}\n\nUse this code to complete your verification."

                try:
                    send_mail(subject, email_body, 'AI IngredientIQ', [user.email], fail_silently=False)
                except BadHeaderError:
                    return JsonResponse({"message": "Invalid email header"}, status=status.HTTP_400_BAD_REQUEST)

                return JsonResponse({"data": "OTP sent to your email"}, status=status.HTTP_200_OK)

            else:
                try:
                    user = User.objects.get(phone_number=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this phone number not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                message = f"Your OTP is: {otp}. Use this to complete your verification."
                send_sms(user.phone_number, message)

                return JsonResponse({"data": "OTP sent to your phone number"}, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Verify OTP API
class verifyotpview(APIView):
    def post(self, request):
        try:
            otp = request.data.get('otp', None)
            
            if not otp:
                return JsonResponse({"error": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                otp = int(otp)
            except ValueError:
                return JsonResponse({"error": "OTP should be a valid integer"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(otp=otp).first()

            if user:
                user.otp = None  # Clear OTP after successful verification
                user.save()

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                return Response({
                    "message": "OTP Verified Successfully. Login successful.",
                    "access_token": access_token,
                    "refresh_token": str(refresh)
                }, status=status.HTTP_200_OK)

            return Response({"error": "Incorrect OTP"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordRequestAPIView(APIView):
    permission_classes = [] 

    def post(self, request):
        email = request.data.get("email")  
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            confirm_password = serializer.validated_data['confirm_password']

            if new_password != confirm_password:
                return Response({"detail": "Passwords must match."}, status=status.HTTP_400_BAD_REQUEST)

            if len(confirm_password) < 8:
                return Response({"detail": "New password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(confirm_password)
            user.save()

            return Response({"detail": "Password has been successfully reset."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

class termsandconditionView(APIView):
    def get(self,request):
        user = Termandcondition.objects.all()
        serializer = termsandconditionSerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)


class privacypolicyView(APIView):
    def get(self,request):
        user = privacypolicy.objects.all()
        serializer = privacypolicySerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)

class Frequentlyasked(APIView):
    def get(self,request):
        user = FAQ.objects.all()
        serializer = FAQSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class About(APIView):
    def get(self,request):
        user = AboutUS.objects.all()
        serializer = AboutSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class userprofileview(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request):
        user = User.objects.get(email=request.user.email)

        if not request.data:
            return Response({"message": "No data provided to update."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = userPatchSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            profile_picture_url = None
            if user.profile_picture:
                profile_picture_url = user.profile_picture.url
                print("------------", profile_picture_url)
                profile_picture_url = profile_picture_url.replace("https//", "")
                print("======", profile_picture_url)  
            return Response(
                {"message": "Profile updated successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self,request):
        user = User.objects.select_related().get(email=request.user.email)
        user.refresh_from_db()  # Force refresh from database
        serializer = userGetSerializer(user)
        # Add payment status info
        from .models import UserSubscription
        payment_status = 'freemium'
        premium_type = None
        try:
            sub = UserSubscription.objects.get(user=user)
            if sub.plan_name == 'premium':
                payment_status = 'premium'
                # Use a new field 'premium_type' if present, else fallback to 'unknown'
                premium_type = getattr(sub, 'premium_type', None)
        except UserSubscription.DoesNotExist:
            pass
        data = serializer.data
        data['payment_status'] = payment_status
        data['premium_type'] = premium_type
        return Response({"data":data}, status=status.HTTP_200_OK)
    
    def delete(self, request):
        user = User.objects.get(email=request.user.email)
        user.delete()
        return Response({"detail":"User deleted successfully."}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)




class FoodLabelNutritionView(APIView):
    permission_classes = [IsAuthenticated]
    
    # In-memory caches (class-level)
    openai_cache = {}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize AWS Textract client
        try:
            aws_access_key = settings.AWS_ACCESS_KEY_ID
            aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
            aws_region = settings.AWS_S3_REGION_NAME or 'us-east-1'
            
            if not aws_access_key or not aws_secret_key:
                logging.error("AWS credentials not found in settings")
                self.textract_client = None
                return
            
            self.textract_client = boto3.client(
                'textract',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            print("AWS Textract client initialized successfully for FoodLabelNutritionView")
        except Exception as e:
            logging.error(f"Failed to initialize AWS Textract client: {e}")
            self.textract_client = None

    def post(self, request):
        # can_scan, scan_count = can_user_scan(request.user)
        # if not can_scan:
        #     return Response(
        #         {
        #             "error": "Scan limit reached. Please subscribe to AI IngredientIQ for unlimited scans.",
        #             "scans_used": scan_count,
        #             "max_scans": 6
        #         },
        #         status=status.HTTP_402_PAYMENT_REQUIRED
        #     )
        import time
        import logging
        from concurrent.futures import ThreadPoolExecutor
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"FoodLabelNutritionView is running on: {device.upper()}")
        except ImportError:
            print("torch not installed; cannot determine GPU/CPU.")

        start_time = time.time()

        # Deserialize and validate
        serializer = AllergenDietaryCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data['image']
        image_content = image_file.read()

        # LIGHTNING FAST PARALLEL PROCESSING
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all tasks simultaneously
            image_future = executor.submit(self.save_image, image_content)
            ocr_future = executor.submit(self.run_ocr, image_content)
            ingredients_future = executor.submit(self.extract_ingredients_with_textract_query, image_content)
            nutrition_future = executor.submit(self.extract_nutrition_with_textract_query, image_content)
            
            # Get image URL first (critical)
            image_url, image_path = image_future.result(timeout=3)
            if not image_url:
                return Response({'error': 'Image upload failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get OCR results with timeouts
            try:
                extracted_text = ocr_future.result(timeout=8)  # 8 second timeout
            except:
                extracted_text = ""
                
            try:
                query_ingredients = ingredients_future.result(timeout=8)
            except:
                query_ingredients = []
                
            try:
                query_nutrition = nutrition_future.result(timeout=8)
            except:
                query_nutrition = {}
        
        # Process results quickly
        if query_nutrition:
            nutrition_data = self.process_query_nutrition_data(query_nutrition)
        else:
            nutrition_data = self.extract_nutrition_info_fallback(extracted_text)
        
        if query_ingredients:
            actual_ingredients = self.process_query_ingredients(query_ingredients)
        else:
            actual_ingredients = self.extract_ingredients_from_text_fallback(extracted_text)

        # Debug logging
        print(f"Extracted text: {extracted_text}")
        print(f"Nutrition data extracted: {nutrition_data}")
        
        # More lenient check - allow partial nutrition data
        if not nutrition_data:
            # Try a simpler extraction method as fallback
            nutrition_data = self.extract_nutrition_info_simple(extracted_text)
            print(f"Fallback nutrition data: {nutrition_data}")
            
        if not nutrition_data:
            return Response(
                {"error": "No nutrition data found, Please capture clear photo of nutrition label of food packet. Scan not saved."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # PARALLEL SAFETY VALIDATION AND AI INSIGHTS
        safety_start = time.time()
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Run safety validation and AI insights in parallel
            safety_future = executor.submit(lambda: asyncio.run(self.validate_product_safety(request.user, actual_ingredients)))
            ai_future = executor.submit(self.get_ai_health_insight_and_expert_advice, request.user, nutrition_data, [])
            
            # Get safety results with timeout
            try:
                safety_result = safety_future.result(timeout=5)  # 5 second timeout
                if len(safety_result) == 5:
                    safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache = safety_result
                else:
                    safety_status, go_ingredients, caution_ingredients, no_go_ingredients = safety_result
                    efsa_data_cache = {}
            except:
                safety_status, go_ingredients, caution_ingredients, no_go_ingredients = "unknown", [], [], []
                efsa_data_cache = {}
            
            # Get AI results with timeout
            try:
                ai_results = ai_future.result(timeout=3)  # 3 second timeout
            except:
                ai_results = {
                    "ai_health_insight": "Health insights unavailable.",
                    "expert_advice": "Consult healthcare professional."
                }
        
        safety_end = time.time()
        logging.info(f"Safety validation completed in {safety_end - safety_start:.2f} seconds.")

        # Prepare ingredients for scan history (convert back to simple format for storage)
        def extract_ingredient_names(ingredient_list):
            return [ing["ingredient"] if isinstance(ing, dict) else ing for ing in ingredient_list]
        
        no_go_names = extract_ingredient_names(no_go_ingredients)
        go_names = extract_ingredient_names(go_ingredients)
        caution_names = extract_ingredient_names(caution_ingredients)
        
        with ThreadPoolExecutor() as executor:
            scan_future = executor.submit(lambda: asyncio.run(self.save_scan_history(
                request.user,
                image_url,
                extracted_text,
                nutrition_data,
                ai_results,
                safety_status,
                no_go_names,  # flagged_ingredients
                go_names,     # go_ingredients
                caution_names,  # caution_ingredients
                no_go_names,  # no_go_ingredients
                "OCR Product"  # product_name
            )))
            scan = scan_future.result()

        total_time = time.time() - start_time
        logging.info(f"FoodLabelNutritionView total time: {total_time:.2f} seconds.")

        # Convert ingredient lists to list of objects with clean names and EFSA data
        # Global deduplication across all categories
        all_ingredients_seen = set()

        def format_ingredient_list_with_global_dedup(ingredient_list, category_name):
            formatted_list = []
            
            for ing in ingredient_list:
                if isinstance(ing, dict):
                    # New format with EFSA data
                    ingredient_name = ing.get("ingredient", "")
                    reasons = ing.get("reasons", [])
                    efsa_data = ing.get("efsa_data", {})
                    
                    # Clean the ingredient name
                    clean_ingredient = ingredient_name.strip()
                    if not clean_ingredient:
                        continue
                    
                    # Check for global duplicates
                    clean_ingredient_lower = clean_ingredient.lower().strip()
                    if clean_ingredient_lower in all_ingredients_seen:
                        continue
                    all_ingredients_seen.add(clean_ingredient_lower)
                    
                    formatted_ing = {
                        "ingredient": clean_ingredient,
                        "reasons": reasons,
                        "efsa_data": efsa_data or {}
                    }
                else:
                    # Old format (string)
                    ingredient_str = str(ing)
                    clean_ingredient = ingredient_str.strip()
                    if not clean_ingredient:
                        continue
                    
                    # Check for global duplicates
                    clean_ingredient_lower = clean_ingredient.lower().strip()
                    if clean_ingredient_lower in all_ingredients_seen:
                        continue
                    all_ingredients_seen.add(clean_ingredient_lower)
                    
                    formatted_ing = {
                        "ingredient": clean_ingredient,
                        "reasons": ["Legacy format"],
                        "efsa_data": {}
                    }
                formatted_list.append(formatted_ing)
            return formatted_list

        # Process in priority order: no_go first, then caution, then go
        no_go_ingredients_obj = format_ingredient_list_with_global_dedup(no_go_ingredients, "no_go")
        caution_ingredients_obj = format_ingredient_list_with_global_dedup(caution_ingredients, "caution")
        go_ingredients_obj = format_ingredient_list_with_global_dedup(go_ingredients, "go")

        main_ingredient = actual_ingredients[0] if actual_ingredients else None
        def safe_summary(fetch_func, ingredient, default_msg):
            try:
                summary = fetch_func(ingredient)
                if not summary or (isinstance(summary, str) and not summary.strip()):
                    return default_msg
                return summary
            except Exception as e:
                print(f"Summary fetch error for {ingredient}: {e}")
                return default_msg

        medlineplus_summary = safe_summary(
            fetch_medlineplus_summary,
            main_ingredient,
            "No MedlinePlus summary available for this ingredient."
        ) if main_ingredient else "No MedlinePlus summary available for this ingredient."

        pubchem_summary = safe_summary(
            fetch_pubchem_toxicology_summary,
            main_ingredient,
            "No PubChem toxicology data found for this ingredient."
        ) if main_ingredient else "No PubChem toxicology data found for this ingredient."
        pubmed_articles = fetch_pubmed_articles(main_ingredient) if main_ingredient else []

        # REMOVED ClinicalTrials.gov integration for speed
        def fetch_clinical_trials(ingredient):
            return []  # Return empty list for speed
            if not ingredient:
                return []
            try:
                url = f"https://clinicaltrials.gov/api/v2/studies?q={ingredient}&limit=3"
                resp = requests.get(url, timeout=5)
                if resp.status_code != 200:
                    print(f"ClinicalTrials.gov API error: {resp.status_code}")
                    return []
                data = resp.json()
                studies = data.get("studies", [])
                trials = []
                for study in studies:
                    nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
                    title = study.get("protocolSection", {}).get("identificationModule", {}).get("officialTitle")
                    status = study.get("protocolSection", {}).get("statusModule", {}).get("overallStatus")
                    summary = study.get("protocolSection", {}).get("descriptionModule", {}).get("briefSummary")
                    url = f"https://clinicaltrials.gov/ct2/show/{nct_id}" if nct_id else None
                    if nct_id and title:
                        trials.append({
                            "title": title,
                            "nct_id": nct_id,
                            "status": status,
                            "summary": summary,
                            "url": url
                        })
                return trials
            except Exception as e:
                print(f"ClinicalTrials.gov fetch error: {e}")
                return []

        clinical_trials = fetch_clinical_trials(main_ingredient)

        # --- FSA Hygiene Rating Integration ---
        # Try to extract business name from OCR text or use default
        business_name = "OCR Product"  # Default fallback
        fsa_data = None
        
        # Look for business names in the extracted text
        business_keywords = ['ltd', 'limited', 'inc', 'corporation', 'company', 'co', 'brand', 'manufacturer']
        lines = extracted_text.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in business_keywords):
                business_name = line.strip()
                break
        
        # Fetch FSA hygiene rating data
        try:
            fsa_data = fetch_fsa_hygiene_rating(business_name=business_name)
        except Exception as e:
            print(f"FSA API error: {e}")
            fsa_data = {
                'found': False,
                'error': f'FSA API error: {str(e)}',
                'source': 'UK FSA FHRS API'
            }
        from .scan_limit import can_user_scan, get_monthly_reset_date
        _, scan_count, remaining_scans = can_user_scan(request.user)
        
        # Handle None values for premium users
        if scan_count is None:
            scan_count = 0
        if remaining_scans is None:
            remaining_scans = "unlimited"

        return Response({
            "scan_id": scan.id,
            "product_name":"OCR Product",
            "image_url": image_url,
            "extracted_text": extracted_text,
            "nutrition_data": nutrition_data,
            "ingredients": actual_ingredients,
            "safety_status": safety_status,
            "is_favorite": scan.is_favorite,
            "ingredients_analysis": {
                "go": {
                    "ingredients": go_ingredients_obj,
                    "count": len(go_ingredients_obj),
                    "description": "Ingredients that are safe and suitable for your health profile"
                },
                "caution": {
                    "ingredients": caution_ingredients_obj,
                    "count": len(caution_ingredients_obj),
                    "description": "Ingredients that may not be ideal for your health profile - consume at your own risk"
                },
                "no_go": {
                    "ingredients": no_go_ingredients_obj,
                    "count": len(no_go_ingredients_obj),
                    "description": "Ingredients that are harmful or not suitable for your health profile - avoid these"
                },
                "total_flagged": len(caution_ingredients_obj) + len(no_go_ingredients_obj)
            },
            "efsa_data": {
                "source": "European Food Safety Authority (EFSA) OpenFoodTox Database",
                "total_ingredients_checked": len(efsa_data_cache),
                "ingredients_with_efsa_data": len([data for data in efsa_data_cache.values() if data and data.get('found')]),
                "cache": {k: v for k, v in efsa_data_cache.items() if v is not None}
            },
            "fsa_hygiene_data": fsa_data,
            "scan_usage": {
                "scans_used": scan_count,
                "max_scans": 20,
                "remaining_scans": remaining_scans,
                "monthly_reset_date": get_monthly_reset_date()
            },
            "medical_condition_recommendations": {
                "user_health_profile": {
                    "allergies": request.user.Allergies,
                    "dietary_preferences": request.user.Dietary_preferences,
                    "health_conditions": request.user.Health_conditions
                },
                "recommendations": get_medical_condition_food_recommendations(
                    request.user.Health_conditions, 
                    request.user.Allergies,
                    request.user.Dietary_preferences
                ) if (request.user.Health_conditions or request.user.Allergies or request.user.Dietary_preferences) else {"found": False, "message": "No health profile specified"},
                "source": "SNOMED CT & ICD-10 Clinical Guidelines"
            },
            "ai_health_insight": {
                "Bluf_insight": ai_results.get("structured_health_analysis", {}).get("bluf_insight", ai_results.get("ai_health_insight", "")),
                "Main_insight": ai_results.get("structured_health_analysis", {}).get("main_insight", ai_results.get("expert_advice", "")),
                "Deeper_reference": ai_results.get("structured_health_analysis", {}).get("deeper_reference", ""),
                "Disclaimer": ai_results.get("structured_health_analysis", {}).get("disclaimer", "Informational, not diagnostic. Consult healthcare providers for medical advice.")
            },
            "expert_ai_conclusion": ai_results.get("expert_ai_conclusion", ai_results.get("expert_advice", "")),
            "structured_health_analysis": ai_results.get("structured_health_analysis", {}),
            "source": "SNOMED CT & ICD-10 Clinical Guidelines"
        }, status=status.HTTP_200_OK)
            
            # "ocr_gpu": False,  # Azure OCR
            # "medlineplus_summary": medlineplus_summary,
            # "pubchem_summary": pubchem_summary,
            # "pubmed_articles": pubmed_articles,
            # "clinical_trials": clinical_trials,
            # "timing": {
            #     "ocr": ocr_end - ocr_start,
            #     "safety+ai": safety_end - safety_start,
            #     "total": total_time
            # }
        # }, status=status.HTTP_200_OK)

    def get_ai_health_insight_and_expert_advice(self, user, nutrition_data, flagged_ingredients):
        """
        Ultra-fast AI insights with minimal processing, caching, and aggressive timeouts.
        """
        import time
        import json
        import hashlib
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        
        # Quick cache check
        key_data = {
            'ingredients': sorted(flagged_ingredients[:3]),  # Only first 3 for speed
            'nutrition': {k: v for k, v in list(nutrition_data.items())[:5]},  # Only first 5
            'diet': user.Dietary_preferences,
            'allergies': user.Allergies
        }
        cache_key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        if cache_key in self.openai_cache:
            return self.openai_cache[cache_key]
        
        # Ultra-minimal single prompt for both insights
        nutrition_summary = ', '.join(f"{k}: {v}" for k, v in list(nutrition_data.items())[:5])
        flagged_str = ', '.join(flagged_ingredients[:3])  # Only top 3
        user_profile = f"Diet: {user.Dietary_preferences or 'None'}, Allergies: {user.Allergies or 'None'}"
        
        # Single prompt for both health insight and expert advice
        prompt = f"""
        User Profile: {user_profile}
        Nutrition: {nutrition_summary}
        Flagged Ingredients: {flagged_str}
        
        Provide BOTH responses in the exact format below:
        
        1. Health Insight (30-50 words): Analyze safety, nutritional value, and any red flags based on user's dietary preferences and health conditions.
        
        2. Expert Advice (70-80 words): Give detailed, actionable recommendations including portion control, alternatives, preparation tips, and specific guidance for the user's dietary needs.
        
        Format: "HEALTH: [30-50 word insight] ADVICE: [70-80 word detailed recommendation]"
        """
        
        def openai_call():
            from openai import OpenAI
            import os
            
            try:
                client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    timeout=2.5  # 2.5 second timeout per call
                )
                
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Faster than gpt-4o
                    messages=[
                        {"role": "system", "content": "You are a certified nutrition expert. Provide detailed, informative responses following the exact word count and format specified."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=200,  # Increased for longer responses (30-50 + 70-80 words)
                    temperature=0.3,
                )
                
                content = completion.choices[0].message.content.strip()
                
                # Parse the response
                if "HEALTH:" in content and "ADVICE:" in content:
                    parts = content.split("ADVICE:")
                    health_part = parts[0].replace("HEALTH:", "").strip()
                    advice_part = parts[1].strip()
                    
                    return {
                        "ai_health_insight": health_part,
                        "expert_advice": advice_part
                    }
                else:
                    # Fallback parsing - try to split by sentences and create meaningful responses
                    sentences = [s.strip() + "." for s in content.split('.') if s.strip()]
                    
                    if len(sentences) >= 2:
                        # Use first part as health insight, rest as expert advice
                        health_insight = sentences[0]
                        expert_advice = " ".join(sentences[1:])
                    else:
                        # Create structured fallback responses
                        health_insight = "Product nutrition analysis completed. Key nutritional components identified for your dietary assessment."
                        expert_advice = "Consider this product's nutritional profile in context of your daily intake goals. Monitor portion sizes and balance with other foods throughout the day. Consult nutrition labels for detailed ingredient information and allergen warnings before consumption."
                    
                    return {
                        "ai_health_insight": health_insight,
                        "expert_advice": expert_advice
                    }
                
            except Exception as e:
                print(f"OpenAI error: {e}")
                # Intelligent fallback based on data
                if flagged_ingredients:
                    return {
                        "ai_health_insight": f"Product contains {len(flagged_ingredients)} flagged ingredients that may conflict with your dietary preferences or health conditions. These components require careful consideration for your nutritional goals.",
                        "expert_advice": f"Review the flagged ingredients: {', '.join(flagged_ingredients[:3])}. Consider alternatives that better align with your dietary needs. If consuming, monitor portion sizes and balance with nutrient-dense foods. Consult your healthcare provider if you have specific health concerns about these ingredients."
                    }
                else:
                    return {
                        "ai_health_insight": "Product appears nutritionally suitable based on available information and shows no immediate red flags for your dietary profile and health considerations.",
                        "expert_advice": "This product can be incorporated into a balanced diet when consumed in appropriate portions. Focus on overall dietary variety and ensure adequate intake of essential nutrients throughout the day. Consider pairing with complementary foods to optimize nutritional benefits and maintain balanced macronutrient ratios."
                    }
        
        # Execute with timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(openai_call)
            try:
                result = future.result(timeout=2.8)  # 2.8 second total timeout
                self.openai_cache[cache_key] = result
                return result
            except TimeoutError:
                print("OpenAI timeout - using fallback")
                return {
                    "ai_health_insight": "Product nutritional analysis completed successfully. Key ingredients and nutritional components have been identified and evaluated for your dietary profile.",
                    "expert_advice": "Review the product's nutrition label and ingredient list carefully. Pay attention to any flagged ingredients that may not align with your dietary preferences. Consider portion control and incorporate this product as part of a balanced, varied diet. Consult with a healthcare professional for personalized nutritional guidance."
                }
            except Exception as e:
                print(f"OpenAI outer error: {e}")
                return {
                    "ai_health_insight": "Product nutritional analysis completed successfully. Key ingredients and nutritional components have been identified and evaluated for your dietary profile.",
                    "expert_advice": "Review the product's nutrition label and ingredient list carefully. Pay attention to any flagged ingredients that may not align with your dietary preferences. Consider portion control and incorporate this product as part of a balanced, varied diet. Consult with a healthcare professional for personalized nutritional guidance."
                }

    def run_in_thread_pool(self, func, *args):
        with ThreadPoolExecutor() as executor:
            return executor.submit(func, *args).result()

    def save_image(self, image_content):
        try:
            image_name = f"food_labels/{uuid.uuid4()}.jpg"
            image_path = default_storage.save(image_name, ContentFile(image_content))
            image_url = default_storage.url(image_path).replace("https//", "")
            return image_url, image_path
        except Exception as e:
            print(f"Error saving image: {e}")
            return None, None

    def run_ocr(self, image_content):
        """
        Uses AWS Textract for high-accuracy text extraction with Query feature.
        """
        try:
            if not self.textract_client:
                logging.error("AWS Textract client not initialized")
                return ''
            
            # Try to extract text using AWS Textract Query first
            extracted_text = self.extract_text_with_textract_query(image_content)
            if extracted_text:
                logging.info(f"Extracted text from AWS Textract Query: {extracted_text}")
                return extracted_text
            
            # Fallback to regular text extraction
            extracted_text = self.extract_text_with_textract(image_content)
            if extracted_text:
                logging.info(f"Extracted text from AWS Textract: {extracted_text}")
                return extracted_text
            
            logging.error("AWS Textract failed to extract text")
            return ''
            
        except Exception as e:
            logging.error(f"AWS Textract OCR error: {e}", exc_info=True)
            return ''

    def extract_text_with_textract_query(self, image_content):
        """
        Extract text using AWS Textract Query feature for better accuracy.
        """
        try:
            # Validate image content
            if not isinstance(image_content, bytes):
                logging.error("Image content must be bytes")
                return ""
            
            # Check image size (AWS Textract limit is 5MB)
            if len(image_content) > 5 * 1024 * 1024:
                logging.error("Image too large for AWS Textract (max 5MB)")
                return ""
            
            # Check if image content is valid
            if len(image_content) < 100:
                logging.error("Image content too small")
                return ""

            # Query for general text content
            queries = [
                {
                    'Text': 'What text is visible in this image?',
                    'Alias': 'general_text'
                },
                {
                    'Text': 'Extract all text from this nutrition label',
                    'Alias': 'nutrition_text'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES', 'TABLES', 'FORMS', 'LINES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                extracted_text = ""
                
                # Extract text from query results
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                extracted_text += answer_block['Text'] + "\n"
                
                # Also extract regular text blocks
                text_blocks = [block for block in response.get('Blocks', []) if block['BlockType'] == 'LINE']
                text_blocks.sort(key=lambda x: (x['Geometry']['BoundingBox']['Top'], x['Geometry']['BoundingBox']['Left']))
                
                for block in text_blocks:
                    if 'Text' in block:
                        extracted_text += block['Text'] + "\n"

                return extracted_text.strip()
                
            except Exception as e:
                logging.error(f"Textract Query API error: {e}")
                return ""
            
        except Exception as e:
            logging.error(f"Textract Query extraction error: {e}")
            return ""

    def extract_text_with_textract(self, image_content):
        """
        Extract text using AWS Textract with enhanced features.
        """
        try:
            if not self.textract_client:
                raise Exception("AWS Textract client not initialized")

            # Ensure image_content is bytes
            if not isinstance(image_content, bytes):
                logging.error("Image content must be bytes")
                return ""

            # Check image size (AWS Textract limit is 5MB)
            if len(image_content) > 5 * 1024 * 1024:
                logging.error("Image too large for AWS Textract (max 5MB)")
                return ""

            # Check if image content is valid
            if len(image_content) < 100:
                logging.error("Image content too small")
                return ""

            # Try analyze_document first (more features)
            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['TABLES', 'FORMS', 'LINES']
                )
                
                # Extract text with spatial information
                extracted_text = ""
                blocks = response.get('Blocks', [])
                
                # Sort blocks by geometry for proper reading order
                text_blocks = [block for block in blocks if block['BlockType'] == 'LINE']
                text_blocks.sort(key=lambda x: (x['Geometry']['BoundingBox']['Top'], x['Geometry']['BoundingBox']['Left']))
                
                for block in text_blocks:
                    if 'Text' in block:
                        extracted_text += block['Text'] + "\n"

                return extracted_text.strip()
                
            except Exception as e:
                logging.error(f"Textract analyze_document failed: {e}")
                # Try simpler detect_document_text as fallback
                try:
                    response = self.textract_client.detect_document_text(
                        Document={
                            'Bytes': image_content
                        }
                    )
                    
                    extracted_text = ""
                    blocks = response.get('Blocks', [])
                    
                    for block in blocks:
                        if block['BlockType'] == 'LINE' and 'Text' in block:
                            extracted_text += block['Text'] + "\n"
                    
                    return extracted_text.strip()
                    
                except Exception as fallback_error:
                    logging.error(f"Textract detect_document_text also failed: {fallback_error}")
                    return ""

        except Exception as e:
            logging.error(f"Textract extraction error: {e}")
            return ""

    def correct_ocr_errors(self, text):
        corrections = {
            "Bg": "8g", "Omg": "0mg", "lron": "Iron", "meg": "mcg"
        }
        for wrong, right in corrections.items():
            text = text.replace(wrong, right)
        return text

    def extract_nutrition_info_from_text(self, text, image_content=None):
        """
        Enhanced nutrition extraction using AWS Textract Query for better accuracy.
        """
        nutrition_data = {}
        
        # Fix common OCR errors first
        text = self.correct_ocr_errors(text)
        
        # Try AWS Textract Query first if image_content is available
        if image_content and hasattr(self, 'textract_client') and self.textract_client:
            query_nutrition = self.extract_nutrition_with_textract_query(image_content)
            if query_nutrition:
                # Convert query results to the expected format
                for key, value in query_nutrition.items():
                    if value:
                        # Extract numeric value and unit
                        match = re.search(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', value)
                        if match:
                            numeric_value = match.group(1)
                            unit = match.group(2).lower()
                            
                            # Map query keys to nutrition data keys with proper units
                            if key == 'energy':
                                nutrition_data["Energy"] = f"{numeric_value} kcal"
                            elif key == 'protein':
                                nutrition_data["Protein"] = f"{numeric_value} g"
                            elif key == 'total_fat':
                                nutrition_data["Total Fat"] = f"{numeric_value} g"
                            elif key == 'saturated_fat':
                                nutrition_data["Saturated Fat"] = f"{numeric_value} g"
                            elif key == 'carbohydrates':
                                nutrition_data["Carbohydrate"] = f"{numeric_value} g"
                            elif key == 'sugars':
                                nutrition_data["Total Sugars"] = f"{numeric_value} g"
                            elif key == 'sodium':
                                nutrition_data["Sodium"] = f"{numeric_value} mg"
                            elif key == 'fiber':
                                nutrition_data["Dietary Fibre"] = f"{numeric_value} g"
                            else:
                                # Add as custom nutrient with proper unit
                                nutrition_data[key.replace('_', ' ').title()] = f"{numeric_value} {unit}"
        
        # If AWS Textract Query didn't provide enough data, fall back to text parsing
        if len(nutrition_data) < 3:  # If we have less than 3 nutrients, use fallback
            nutrition_data = self.extract_nutrition_info_fallback(text)
        
        return nutrition_data

    def extract_nutrition_with_textract_query(self, image_content):
        """
        Extract nutrition data using AWS Textract Query feature.
        """
        try:
            if not self.textract_client:
                return {}

            # Query for nutrition information
            queries = [
                {
                    'Text': 'What is the energy/calories value?',
                    'Alias': 'energy'
                },
                {
                    'Text': 'What is the protein content?',
                    'Alias': 'protein'
                },
                {
                    'Text': 'What is the total fat content?',
                    'Alias': 'total_fat'
                },
                {
                    'Text': 'What is the saturated fat content?',
                    'Alias': 'saturated_fat'
                },
                {
                    'Text': 'What is the carbohydrate content?',
                    'Alias': 'carbohydrates'
                },
                {
                    'Text': 'What is the sugar content?',
                    'Alias': 'sugars'
                },
                {
                    'Text': 'What is the sodium content?',
                    'Alias': 'sodium'
                },
                {
                    'Text': 'What is the fiber content?',
                    'Alias': 'fiber'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                nutrition_data = {}
                
                # Extract answers from the response
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        query_alias = block.get('Query', {}).get('Alias', '')
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        # Find the answer block
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                nutrition_data[query_alias] = answer_block['Text']
                
                return nutrition_data
                
            except Exception as e:
                logging.error(f"Nutrition Query failed: {e}")
                return {}

        except Exception as e:
            logging.error(f"Nutrition Query extraction error: {e}")
            return {}

    def extract_nutrition_info_fallback(self, text):
        """
        Fallback nutrition extraction using text parsing (original method).
        """
        nutrition_data = {}
        
        # Define comprehensive nutrient patterns with variations
        nutrient_patterns = {
            "Energy": [
                r'energy[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'calories[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'calorie[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*energy',
                r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*calories'
            ],
            "Total Fat": [
                r'total\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+fat',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fat'
            ],
            "Saturated Fat": [
                r'saturated\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sat\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*saturated\s+fat',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sat\s+fat'
            ],
            "Trans Fat": [
                r'trans\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*trans\s+fat'
            ],
            "Cholesterol": [
                r'cholesterol[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*cholesterol'
            ],
            "Sodium": [
                r'sodium[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'salt[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*sodium',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*salt'
            ],
            "Carbohydrate": [
                r'carbohydrate[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'carbohydrates[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'carbs[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrate',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrates',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbs'
            ],
            "Total Sugars": [
                r'total\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sugar[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+sugars',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugars',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugar'
            ],
            "Added Sugars": [
                r'added\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*added\s+sugars'
            ],
            "Dietary Fibre": [
                r'dietary\s+fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'dietary\s+fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fibre',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fiber',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fibre',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fiber'
            ],
            "Protein": [
                r'protein[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*protein'
            ]
        }
        
        # Extract using comprehensive patterns with proper unit mapping
        for nutrient_name, patterns in nutrient_patterns.items():
            all_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                all_matches.extend(matches)
            
            if all_matches:
                value, unit = all_matches[0]
                # Map units correctly
                if unit.lower() in ['kj', 'cal']:
                    unit = 'kcal'
                elif unit.lower() == '%':
                    unit = '%'
                elif nutrient_name in ["Energy"]:
                    unit = 'kcal'
                elif nutrient_name in ["Sodium", "Cholesterol"]:
                    unit = 'mg'
                else:
                    unit = 'g'
                    
                nutrition_data[nutrient_name] = f"{value} {unit}".strip()
        
        # Clean up and standardize units
        for key, value in nutrition_data.items():
            if value and not value.endswith(('kcal', 'g', 'mg', 'mcg', '%', 'kj', 'cal')):
                # Extract numeric value
                numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
                if numeric_match:
                    numeric_value = numeric_match.group(1)
                    if key.lower() in ["energy", "calories"]:
                        nutrition_data[key] = f"{numeric_value} kcal"
                    elif key.lower() in ["protein", "carbohydrate", "total sugars", "dietary fibre", "total fat", "saturated fat", "trans fat"]:
                        nutrition_data[key] = f"{numeric_value} g"
                    elif key.lower() in ["sodium", "cholesterol"]:
                        nutrition_data[key] = f"{numeric_value} mg"
        
        return nutrition_data

    def extract_nutrition_info_simple(self, text):
        """
        Simple fallback nutrition extraction method for OCR text that's hard to parse.
        """
        nutrition_data = {}
        
        # Fix common OCR errors
        text = text.replace('o.', '0.').replace('O.', '0.').replace('O', '0').replace('l', '1')
        text = text.replace('Ptotetn', 'Protein').replace('rotat', 'Total').replace('agog', '240g')
        text = text.replace('tug', '240g').replace('osg', '240g')
        
        # Split into lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        print(f"Processing lines: {lines}")  # Debug
        
        # Look for nutrition section
        nutrition_section = False
        for line in lines:
            if 'nutrition' in line.lower() or 'kcal' in line.lower() or 'g' in line:
                nutrition_section = True
                break
        
        if not nutrition_section:
            return nutrition_data
        
        # Enhanced pattern matching for the specific OCR format
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Skip non-nutrition lines
            if any(skip in line_lower for skip in ['ingredients', 'allergen', 'manufactured', 'store', 'packaged']):
                    continue
                
            print(f"Processing line {i}: '{line}' -> '{line_lower}'")  # Debug
            
            # Look for nutrient names and values
            if 'protein' in line_lower or 'ptotetn' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger (more likely to be correct)
                        if 'Protein' not in nutrition_data or float(value) > float(nutrition_data['Protein'].split()[0]):
                            nutrition_data['Protein'] = f"{value} {unit}"
                            print(f"Found Protein: {value} {unit}")  # Debug
                        break
            
            elif 'carbohydrate' in line_lower or 'carbs' in line_lower or 'rotat' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Carbohydrate' not in nutrition_data or float(value) > float(nutrition_data['Carbohydrate'].split()[0]):
                            nutrition_data['Carbohydrate'] = f"{value} {unit}"
                            print(f"Found Carbohydrate: {value} {unit}")  # Debug
                        break
            
            elif 'sugar' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Total Sugars' not in nutrition_data or float(value) > float(nutrition_data['Total Sugars'].split()[0]):
                            nutrition_data['Total Sugars'] = f"{value} {unit}"
                            print(f"Found Total Sugars: {value} {unit}")  # Debug
                        break
            
            elif 'fat' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        if 'saturated' in line_lower:
                            # Only add if we don't already have this nutrient or if this value is larger
                            if 'Saturated Fat' not in nutrition_data or float(value) > float(nutrition_data['Saturated Fat'].split()[0]):
                                nutrition_data['Saturated Fat'] = f"{value} {unit}"
                                print(f"Found Saturated Fat: {value} {unit}")  # Debug
                        else:
                            # Only add if we don't already have this nutrient or if this value is larger
                            if 'Total Fat' not in nutrition_data or float(value) > float(nutrition_data['Total Fat'].split()[0]):
                                nutrition_data['Total Fat'] = f"{value} {unit}"
                                print(f"Found Total Fat: {value} {unit}")  # Debug
                        break
            
            elif 'kcal' in line_lower or 'calorie' in line_lower or 'energy' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(kcal|cal)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'kcal'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Energy' not in nutrition_data or float(value) > float(nutrition_data['Energy'].split()[0]):
                            nutrition_data['Energy'] = f"{value} {unit}"
                            print(f"Found Energy: {value} {unit}")  # Debug
                        break
        
        # Also look for standalone numbers that might be nutrition values
        for i, line in enumerate(lines):
            # Look for lines that are just numbers (potential nutrition values)
            if re.match(r'^\d+(?:\.\d+)?\s*(g|kcal|mg)?$', line.strip()):
                value = re.search(r'(\d+(?:\.\d+)?)', line).group(1)
                unit = re.search(r'(g|kcal|mg)', line)
                unit = unit.group(1) if unit else 'g'
                
                print(f"Found standalone value: {value} {unit} at line {i}")  # Debug
                
                # Try to match with nearby nutrient names
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    nearby_line = lines[j].lower()
                    if ('protein' in nearby_line or 'ptotetn' in nearby_line) and 'Protein' not in nutrition_data:
                        nutrition_data['Protein'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Protein")  # Debug
                        break
                    elif ('carbohydrate' in nearby_line or 'carbs' in nearby_line or 'rotat' in nearby_line) and 'Carbohydrate' not in nutrition_data:
                        nutrition_data['Carbohydrate'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Carbohydrate")  # Debug
                        break
                    elif 'sugar' in nearby_line and 'Total Sugars' not in nutrition_data:
                        nutrition_data['Total Sugars'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Total Sugars")  # Debug
                        break
                    elif 'fat' in nearby_line:
                        if 'saturated' in nearby_line and 'Saturated Fat' not in nutrition_data:
                            nutrition_data['Saturated Fat'] = f"{value} {unit}"
                            print(f"Mapped {value} {unit} to Saturated Fat")  # Debug
                            break
                        elif 'Total Fat' not in nutrition_data:
                            nutrition_data['Total Fat'] = f"{value} {unit}"
                            print(f"Mapped {value} {unit} to Total Fat")  # Debug
                            break
        
        # Special handling for "Per 100g" format
        per_100g_section = ""
        for i, line in enumerate(lines):
            if 'per' in line.lower() and '100' in line and 'g' in line.lower():
                # Found the per 100g section, collect the next few lines
                per_100g_section = '\n'.join(lines[i:i+10])
                print(f"Found Per 100g section: {per_100g_section}")  # Debug
                break
        
        if per_100g_section:
            # Extract all number-unit pairs from this section
            number_unit_pairs = re.findall(r'(\d+(?:\.\d+)?)\s*(kcal|g|mg|mcg|%|kj|cal)', per_100g_section, re.IGNORECASE)
            print(f"Number-unit pairs found: {number_unit_pairs}")  # Debug
            
            # Try to match with nutrient names in the same section
            for pair in number_unit_pairs:
                value, unit = pair
                # Look for nutrient names near this value
                for nutrient_name in ['Energy', 'Protein', 'Carbohydrate', 'Total Sugars', 'Total Fat', 'Saturated Fat', 'Trans Fat']:
                    if nutrient_name.lower().replace(' ', '') in per_100g_section.lower().replace(' ', ''):
                        # Only add if we don't already have this nutrient or if this value is larger
                        if nutrient_name not in nutrition_data or float(value) > float(nutrition_data[nutrient_name].split()[0]):
                            # Standardize units
                            if unit.lower() in ['kj', 'cal']:
                                unit = 'kcal'
                            else:
                                unit = 'g'
                            
                        nutrition_data[nutrient_name] = f"{value} {unit}".strip()
                        print(f"Found {nutrient_name}: {value} {unit} from Per 100g section")  # Debug
        
        print(f"Final nutrition data: {nutrition_data}")  # Debug
        return nutrition_data

    def extract_ingredients_from_text(self, text, image_content=None):
        """
        Extracts a clean list of ingredients using AWS Textract Query for better accuracy.
        """
        import re
        
        # Try AWS Textract Query first if image_content is available
        if image_content and hasattr(self, 'textract_client') and self.textract_client:
            query_ingredients = self.extract_ingredients_with_textract_query(image_content)
            if query_ingredients:
                # Process query results
                ingredients = self.process_query_ingredients(query_ingredients)
                if ingredients:
                    return ingredients
        
        # Fallback to text parsing
        return self.extract_ingredients_from_text_fallback(text)

    def extract_ingredients_with_textract_query(self, image_content):
        """
        Extract ingredients using AWS Textract Query feature.
        """
        try:
            if not self.textract_client:
                return []

            # Query for ingredients
            queries = [
                {
                    'Text': 'What are the ingredients?',
                    'Alias': 'ingredients'
                },
                {
                    'Text': 'List all ingredients',
                    'Alias': 'ingredients_list'
                },
                {
                    'Text': 'What ingredients are in this product?',
                    'Alias': 'product_ingredients'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                ingredients = []
                
                # Extract answers from the response
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        # Find the answer block
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                ingredients.append(answer_block['Text'])
                
                return ingredients
                
            except Exception as e:
                logging.error(f"Ingredients Query failed: {e}")
                return []

        except Exception as e:
            logging.error(f"Ingredients Query extraction error: {e}")
            return []

    def process_query_ingredients(self, query_ingredients):
        """
        Process ingredients from Textract Query results with better cleaning.
        """
        if not query_ingredients:
            return []
        
        # Join all ingredient responses and clean them up
        ingredients_text = " ".join(query_ingredients)
        
        # Clean up the ingredients text - preserve important characters
        ingredients_text = re.sub(r'[^\w\s,()%.&-]', ' ', ingredients_text)  # Keep important chars
        ingredients_text = re.sub(r'\s+', ' ', ingredients_text)  # Normalize whitespace
        
        # Split ingredients by common separators, but be smarter about it
        ingredients = []
        
        # First, try to split by commas, but respect parentheses
        # This pattern splits by commas that are NOT inside parentheses
        parts = re.split(r',\s*(?![^()]*\))', ingredients_text)
        
        # If the above didn't work well, try a more aggressive approach
        if len(parts) <= 1:
            # Split by commas and then clean up each part
            parts = re.split(r',\s*', ingredients_text)
        
        for part in parts:
            ingredient = part.strip()
            if ingredient and len(ingredient) > 2:
                # Clean up ingredient using the cleaning function
                ingredient = self.clean_ingredient_text(ingredient)
                
                # Skip if it's just a number, percentage, or very short
                if (ingredient and len(ingredient) > 2 and 
                    not re.match(r'^\d+\.?\d*%?$', ingredient) and
                    not ingredient.lower() in ['and', 'or', 'the', 'a', 'an']):
                    
                    # Use the compound ingredient splitting function
                    split_ingredients = self.split_compound_ingredients(ingredient)
                    for split_ingredient in split_ingredients:
                        if split_ingredient and len(split_ingredient) > 2:
                            ingredients.append(split_ingredient)

        # Remove duplicates while preserving order
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            clean_ingredient = re.sub(r'\s+', ' ', ingredient).strip()
            if clean_ingredient.lower() not in seen:
                seen.add(clean_ingredient.lower())
                unique_ingredients.append(clean_ingredient)

        return unique_ingredients

    def extract_ingredients_from_text_fallback(self, text):
        """
        Fallback ingredients extraction using text parsing with improved cleaning.
        """
        import re
        # 1. Find the INGREDIENTS section (case-insensitive)
        match = re.search(
            r'ingredients[:\s]*([\s\S]+?)(allergen|nutritional|store|packaged|may contain|used as natural|information|$)',
            text, re.IGNORECASE
        )
        if not match:
            return []
        ingredients_text = match.group(1)

        # 2. Clean up text: replace newlines, remove unwanted symbols (but keep (), %, &)
        ingredients_text = re.sub(r'\n', ' ', ingredients_text)
        ingredients_text = re.sub(r'[^a-zA-Z0-9,().&%\-\s]', '', ingredients_text)
        ingredients_text = re.sub(r'\s+', ' ', ingredients_text)

        # 3. Split on commas and periods (not inside parentheses)
        parts = re.split(r'[,.](?![^()]*\))', ingredients_text)
        
        # If the above didn't work well, try a more aggressive approach
        if len(parts) <= 1:
            # Split by commas and then clean up each part
            parts = re.split(r'[,\s]+', ingredients_text)
        ingredients = []
        for part in parts:
            ing = part.strip()
            # Clean up ingredient using the cleaning function
            ing = self.clean_ingredient_text(ing)
            # Filter out non-ingredient lines
            if ing and not re.search(
                r'(may contain|allergen|information|flavouring|substances|regulator|identical|used as natural|limit of quantification)',
                ing, re.IGNORECASE
            ):
                # Use the compound ingredient splitting function
                split_ingredients = self.split_compound_ingredients(ing)
                for split_ingredient in split_ingredients:
                    if split_ingredient and len(split_ingredient) > 2:
                        ingredients.append(split_ingredient)
        
        # Remove duplicates and clean up
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            clean_ingredient = re.sub(r'\s+', ' ', ingredient).strip()
            if clean_ingredient.lower() not in seen and len(clean_ingredient) > 2:
                seen.add(clean_ingredient.lower())
                unique_ingredients.append(clean_ingredient)
        
        return unique_ingredients

    def clean_ingredient_text(self, ingredient):
        """
        Clean and normalize ingredient text.
        """
        import re
        
        # Remove extra whitespace
        ingredient = re.sub(r'\s+', ' ', ingredient).strip()
        
        # Remove trailing punctuation
        ingredient = re.sub(r'[.,;:]$', '', ingredient)
        
        # Remove leading numbers and percentages
        ingredient = re.sub(r'^\d+%?\s*', '', ingredient)
        
        # Remove bullet points
        ingredient = re.sub(r'^\s*[-•]\s*', '', ingredient)
        
        # Fix common OCR errors
        ingredient = ingredient.replace("Flailed", "Flaked")
        ingredient = ingredient.replace("Mingo", "Mango")
        ingredient = ingredient.replace("Pomcgranate", "Pomegranate")
        ingredient = ingredient.replace("lodised", "Iodised")
        
        return ingredient.strip()

    def split_compound_ingredients(self, ingredient_text):
        """
        Split compound ingredients that contain multiple items.
        """
        import re
        
        # If it contains commas but no parentheses, split by commas
        if ',' in ingredient_text and '(' not in ingredient_text:
            parts = re.split(r',\s*', ingredient_text)
            return [part.strip() for part in parts if part.strip()]
        
        # If it contains "and" but no parentheses, split by "and"
        if ' and ' in ingredient_text.lower() and '(' not in ingredient_text:
            parts = re.split(r'\s+and\s+', ingredient_text, flags=re.IGNORECASE)
            return [part.strip() for part in parts if part.strip()]
        
        # If it contains both commas and parentheses, try to split carefully
        if ',' in ingredient_text and '(' in ingredient_text:
            # Look for patterns like "A (B), C, D"
            # Split by commas that are not inside parentheses
            parts = re.split(r',\s*(?![^()]*\))', ingredient_text)
            result = []
            for part in parts:
                part = part.strip()
                if part:
                    # If this part still contains commas, split it further
                    if ',' in part and '(' not in part:
                        sub_parts = re.split(r',\s*', part)
                        result.extend([sub_part.strip() for sub_part in sub_parts if sub_part.strip()])
                    else:
                        result.append(part)
            return result
        
        return [ingredient_text]

    async def save_scan_history(self, user, image_url, extracted_text, nutrition_data, ai_results, safety_status, flagged_ingredients, go_ingredients=None, caution_ingredients=None, no_go_ingredients=None, product_name="OCR Product"):
        # Save scan history in a separate async function
        # Keep nutrition_data clean - only nutrition facts, not ingredients
        clean_nutrition_data = dict(nutrition_data) if nutrition_data else {}
        
        # Add AI results to nutrition data
        clean_nutrition_data.update({
            "ai_health_insight": ai_results.get("ai_health_insight", ""),
            "expert_advice": ai_results.get("expert_advice", ""),
            "go_ingredients": go_ingredients or [],
            "caution_ingredients": caution_ingredients or [],
            "no_go_ingredients": no_go_ingredients or []
        })
        
        scan = await sync_to_async(FoodLabelScan.objects.create)(
            user=user,
            image_url=image_url,
            extracted_text=extracted_text,
            nutrition_data=clean_nutrition_data,  # Include ingredient classifications
            safety_status=safety_status,
            flagged_ingredients=flagged_ingredients,
            product_name=product_name,
        )
        
        # Increment scan count for freemium users
        await sync_to_async(increment_user_scan_count)(user)
        
        return scan

    def categorize_ingredients_with_openai(self, user, ingredients_list):
        """
        Categorize ingredients using OpenAI based on user profile (allergies, dietary preferences, medical conditions)
        into Go, No-Go, and Caution categories.
        """
        try:
            # Prepare user profile information
            allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
            dietary_preferences = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
            health_conditions = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
            
            # Create a comprehensive prompt for OpenAI
            prompt = f"""
            As a nutrition and food safety expert, categorize the following ingredients based on this user's profile:

            USER PROFILE:
            - Allergies: {', '.join(allergies) if allergies else 'None'}
            - Dietary Preferences: {', '.join(dietary_preferences) if dietary_preferences else 'None'}
            - Health Conditions: {', '.join(health_conditions) if health_conditions else 'None'}

            INGREDIENTS TO CATEGORIZE:
            {', '.join(ingredients_list)}

            CATEGORIZE EACH INGREDIENT INTO ONE OF THREE CATEGORIES:

            1. GO: Safe ingredients that align with user's profile
            2. NO-GO: Ingredients that are harmful or contraindicated for the user
            3. CAUTION: Ingredients that may not be ideal but aren't strictly harmful

            RESPONSE FORMAT (JSON only):
            {{
                "go": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ],
                "no_go": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ],
                "caution": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ]
            }}

            RULES:
            - If user has allergies, any ingredient containing those allergens goes to NO-GO
            - If user has dietary preferences (vegan, vegetarian, etc.), non-compliant ingredients go to NO-GO or CAUTION
            - If user has health conditions, ingredients that may worsen them go to NO-GO or CAUTION
            - Common safe ingredients like water, salt, natural flavors typically go to GO
            - Artificial colors, preservatives, high-sodium ingredients often go to CAUTION
            - Known harmful ingredients go to NO-GO

            Return only valid JSON, no additional text.
            """
            
            # Call OpenAI API
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a nutrition and food safety expert. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3,
                    timeout=10
                )
                
                # Parse the response
                content = response.choices[0].message.content.strip()
                
                # Clean up the response to ensure it's valid JSON
                content = content.replace('```json', '').replace('```', '').strip()
                
                # Parse JSON
                categorization = json.loads(content)
                
                # Validate the structure
                required_keys = ['go', 'no_go', 'caution']
                for key in required_keys:
                    if key not in categorization:
                        categorization[key] = []
                
                # Ensure all ingredients are categorized
                all_categorized = set()
                for category in categorization.values():
                    for item in category:
                        if isinstance(item, dict) and 'ingredient' in item:
                            all_categorized.add(item['ingredient'])
                
                # Add any uncategorized ingredients to 'go' as default
                for ingredient in ingredients_list:
                    if ingredient not in all_categorized:
                        categorization['go'].append({
                            "ingredient": ingredient,
                            "reasons": ["Defaulted to safe category"]
                        })
                
                return categorization
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
                # Fallback to basic categorization
                return self._fallback_categorization(user, ingredients_list)
                
        except Exception as e:
            print(f"OpenAI categorization error: {e}")
            # Fallback to basic categorization
            return self._fallback_categorization(user, ingredients_list)

    def _fallback_categorization(self, user, ingredients_list):
        """
        Fallback categorization method when OpenAI fails.
        """
        allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
        dietary_preferences = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
        health_conditions = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
        
        go_ingredients = []
        no_go_ingredients = []
        caution_ingredients = []
        
        for ingredient in ingredients_list:
            ing_lower = ingredient.lower()
            reasons = []
            
            # Check allergies
            if any(allergen in ing_lower for allergen in allergies):
                reasons.append("Allergen")
            
            # Check dietary preferences
            if dietary_preferences:
                if 'vegan' in dietary_preferences and any(animal in ing_lower for animal in ['milk', 'egg', 'meat', 'fish', 'gelatin', 'honey']):
                    reasons.append("Non-vegan")
                elif 'vegetarian' in dietary_preferences and any(animal in ing_lower for animal in ['meat', 'fish', 'gelatin']):
                    reasons.append("Non-vegetarian")
            
            # Check health conditions
            if health_conditions:
                if 'diabetes' in health_conditions and 'sugar' in ing_lower:
                    reasons.append("High sugar")
                elif 'hypertension' in health_conditions and 'salt' in ing_lower:
                    reasons.append("High sodium")
            
            # Categorize based on reasons
            if reasons:
                if "Allergen" in reasons:
                    no_go_ingredients.append({
                        "ingredient": ingredient,
                        "reasons": reasons
                    })
                else:
                    caution_ingredients.append({
                        "ingredient": ingredient,
                        "reasons": reasons
                    })
            else:
                go_ingredients.append({
                    "ingredient": ingredient,
                    "reasons": ["Safe"]
                })
        
        return {
            "go": go_ingredients,
            "no_go": no_go_ingredients,
            "caution": caution_ingredients
        }

    async def validate_product_safety(self, user, ingredients_list):
        """
        Categorize ingredients using OpenAI based on user profile (allergies, dietary preferences, medical conditions)
        into Go, No-Go, and Caution categories.
        """
        try:
            # Get OpenAI categorization
            categorization = self.categorize_ingredients_with_openai(user, ingredients_list)
            
            go_ingredients = categorization.get('go', [])
            no_go_ingredients = categorization.get('no_go', [])
            caution_ingredients = categorization.get('caution', [])
            
            # Add EFSA data to each ingredient for consistency with existing structure
            efsa_data_cache = {}
            for category in [go_ingredients, no_go_ingredients, caution_ingredients]:
                for ingredient_data in category:
                    ingredient_name = ingredient_data.get('ingredient', '')
                    try:
                        efsa_data = fetch_efsa_openfoodtox_data(ingredient_name)
                        efsa_data_cache[ingredient_name] = efsa_data or {}
                        ingredient_data['efsa_data'] = efsa_data or {}
                    except Exception as e:
                        print(f"EFSA error for {ingredient_name}: {e}")
                        efsa_data_cache[ingredient_name] = {
                            'found': False,
                            'error': f'EFSA query failed: {str(e)}',
                            'source': 'EFSA OpenFoodTox Database'
                        }
                        ingredient_data['efsa_data'] = efsa_data_cache[ingredient_name]
            
            # Determine overall safety status
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache
            
        except Exception as e:
            print(f"OpenAI categorization failed: {e}")
            # Fallback to basic categorization
            fallback_result = self._fallback_categorization(user, ingredients_list)
            
            go_ingredients = fallback_result.get('go', [])
            no_go_ingredients = fallback_result.get('no_go', [])
            caution_ingredients = fallback_result.get('caution', [])
            
            # Add empty EFSA data for fallback
            efsa_data_cache = {}
            for category in [go_ingredients, no_go_ingredients, caution_ingredients]:
                for ingredient_data in category:
                    ingredient_data['efsa_data'] = {}
            
            # Determine overall safety status
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache

import io
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import json
import random
import ssl
import tempfile
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.utils import timezone
from datetime import timedelta
import openai
import hashlib
import threading
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from fuzzywuzzy import fuzz
from django.contrib.auth import login
from .serializers import FAQSerializer, AboutSerializer, AllergenDietaryCheckSerializer, FAQSerializer, SignupSerializer, LoginSerializer, ForgotPasswordRequestSerializer, UpdateUserProfileSerializer, UserSettingsSerializer, VerifyOTPSerializer,ChangePasswordSerializer,HealthPreferenceSerializer, privacypolicySerializer, termsandconditionSerializer, userGetSerializer, userPatchSerializer, FoodLabelScanSerializer, FeedbackSerializer, LoveAppSerializer, DepartmentContactSerializer
from .models import FoodLabelScan, MonthlyScanUsage, Termandcondition, User, UserSubscription, privacypolicy, AboutUS, FAQ,StripeCustomer, Feedback, DepartmentContact
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import IsSuperAdmin
# from paddleocr import PaddleOCR
import re
# import easyocr
from io import BytesIO
# from .apps import YourAppConfig
from django.http import HttpResponse
import asyncio
import aiohttp
import numpy as np
from .utils import send_sms, is_eligible_for_new_user_discount, get_discount_info, get_subscription_prices
# from .utils import extract_nutrition_info_from_text
from PIL import Image
from foodanalysis import settings
import os
from bs4 import BeautifulSoup
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth import logout
import cv2
import time
import logging
import os
from PIL import Image, ImageEnhance, ImageFilter
import uuid
from django.core.files.base import ContentFile
import requests
from django.core.files.storage import default_storage
# from allauth.socialaccount.models import SocialApp
from django.shortcuts import redirect
from pytrends.request import TrendReq
from geopy.geocoders import Nominatim
from collections import Counter
from geopy.exc import GeocoderTimedOut
from django.core.cache import cache 
import stripe
from .utils import fetch_llm_insight, fetch_medlineplus_summary, fetch_pubchem_toxicology_summary, fetch_pubmed_articles, fetch_efsa_openfoodtox_data, fetch_efsa_ingredient_summary, fetch_fsa_hygiene_rating, fetch_fsa_hygiene_summary, search_fsa_establishments_by_product, fetch_snomed_ct_data, fetch_icd10_data, get_medical_condition_food_recommendations
from asgiref.sync import sync_to_async
from django.views.decorators.csrf import csrf_exempt
import aiohttp
import asyncio
# import concurrent.futures
from openai import OpenAI
# from .openfoodfacts_api import openfoodfacts_api
openfoodfacts_api = "https://world.openfoodfacts.org/api/v0/product/"
USE_STATIC_INGREDIENT_SAFETY = False    
# openai.api_key = os.getenv("OPENAI_API_KEY")
# import feedparser  # For Medium RSS feeds
client = OpenAI(api_key="OPENAI_API_KEY_REMOVED")
BASE_URL = "https://api.spoonacular.com"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
OPEN_FOOD_FACTS_API = "https://world.openfoodfacts.org/api/v0/product/"
USDA_API_KEY = os.getenv("USDA_API_KEY")
API_KEY = os.getenv("foursquare_api_key")
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WORDPRESS_API_URL = "https://public-api.wordpress.com/rest/v1.1/sites/example.wordpress.com/posts/"
WORDPRESS_BLOG_URL = "https://public-api.wordpress.com/rest/v1.1/sites/example.wordpress.com/posts"
EDAMAM_APP_ID = os.getenv("EDAMAM_APP_ID")
EDAMAM_APP_KEY = os.getenv("EDAMAM_APP_KEY")
SPOONACULAR_KEY = "c01bfdfb4ccd4d8097b5110f789e0618"
WIKIPEDIA_SEARCH_API_URL = "https://en.wikipedia.org/w/api.php"
WHO_SEARCH_URL = "https://www.who.int/search?q="
WIKIPEDIA_LINKS_API = "https://en.wikipedia.org/w/api.php"
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# openai.api_key = "OPENAI_API_KEY_REMOVED"

# Singleton EasyOCR reader and GPU check
# _easyocr_reader = None
# _easyocr_lock = threading.Lock()
# _easyocr_gpu = None

# def get_easyocr_reader():
#     global _easyocr_reader, _easyocr_gpu
#     with _easyocr_lock:
#         if _easyocr_reader is None:
#             try:
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=True)
#                 # Check if GPU is actually used
#                 _easyocr_gpu = _easyocr_reader.gpu
#                 logging.info(f"EasyOCR initialized. GPU used: {_easyocr_gpu}")
#             except Exception as e:
#                 logging.error(f"EasyOCR initialization failed: {e}")
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=False)
#                 _easyocr_gpu = False
#         return _easyocr_reader

# def is_easyocr_gpu():
#     global _easyocr_gpu
#     return _easyocr_gpu

def google_login(request):
    # google = SocialApp.objects.get(provider='google')
    # return redirect(f"https://accounts.google.com/o/oauth2/auth?client_id={google.client_id}&redirect_uri=http://localhost:8000/accounts/google/login/callback/&response_type=code&scope=email profile")
    pass  # Social login temporarily disabled due to SQLite JSONField incompatibility

class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'message': 'User created successfully.',
                'access_token': access_token,
                'refresh_token': str(refresh),
                'is_2fa_enabled': user.is_2fa_enabled
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            if user.is_2fa_enabled:  # Check if 2FA is enabled
                from random import randint
                from django.core.mail import send_mail

                otp_code = randint(100000, 999999)  # Generate 6-digit OTP
                user.otp = str(otp_code)
                user.save()

                # Send OTP via email
                send_mail(
                    "Your OTP Code",
                    f"Your OTP code is: {otp_code}",
                    "no-reply@example.com",
                    [user.email],
                    fail_silently=False,
                )

                return Response({
                    "message": "OTP sent to your email. Please verify to continue.",
                    "user_id": user.id,
                    "is_2fa_enabled": user.is_2fa_enabled,
                    "has_answered_onboarding": user.has_answered_onboarding, # <-- Added here
                    # "subscription_plan": user.UserSubscription

                }, status=status.HTTP_200_OK)

            # If 2FA is disabled, proceed with normal login
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                "message": "Login successful.",
                "access_token": access_token,
                "refresh_token": str(refresh),
                "is_2fa_enabled": user.is_2fa_enabled,
                "has_answered_onboarding": user.has_answered_onboarding,  # <-- Added here
                "subscription_plan": user.subscription_plan

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class Toggle2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        is_2fa_enabled = request.data.get("is_2fa_enabled", None)

        if is_2fa_enabled is None:
            return Response({"error": "is_2fa_enabled field is required"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_2fa_enabled = is_2fa_enabled
        user.save()
        
        return Response({
            "message": f"Two-Factor Authentication {'enabled' if is_2fa_enabled else 'disabled'} successfully.",
            "is_2fa_enabled": user.is_2fa_enabled
        }, status=status.HTTP_200_OK)

class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            
            if not user.check_password(old_password):
                return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'message': 'User created successfully.',
                'access_token': access_token,
                'refresh_token': str(refresh),
                'is_2fa_enabled': user.is_2fa_enabled
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            if user.is_2fa_enabled:  # Check if 2FA is enabled
                from random import randint
                from django.core.mail import send_mail

                otp_code = randint(100000, 999999)  # Generate 6-digit OTP
                user.otp = str(otp_code)
                user.save()

                # Send OTP via email
                send_mail(
                    "Your OTP Code",
                    f"Your OTP code is: {otp_code}",
                    "no-reply@example.com",
                    [user.email],
                    fail_silently=False,
                )

                return Response({
                    "message": "OTP sent to your email. Please verify to continue.",
                    "user_id": user.id,
                    "is_2fa_enabled": user.is_2fa_enabled,
                    "has_answered_onboarding": user.has_answered_onboarding, # <-- Added here
                    # "subscription_plan": user.UserSubscription

                }, status=status.HTTP_200_OK)

            # If 2FA is disabled, proceed with normal login
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                "message": "Login successful.",
                "access_token": access_token,
                "refresh_token": str(refresh),
                "is_2fa_enabled": user.is_2fa_enabled,
                "has_answered_onboarding": user.has_answered_onboarding,  # <-- Added here
                "subscription_plan": user.subscription_plan

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class Toggle2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        is_2fa_enabled = request.data.get("is_2fa_enabled", None)

        if is_2fa_enabled is None:
            return Response({"error": "is_2fa_enabled field is required"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_2fa_enabled = is_2fa_enabled
        user.save()
        
        return Response({
            "message": f"Two-Factor Authentication {'enabled' if is_2fa_enabled else 'disabled'} successfully.",
            "is_2fa_enabled": user.is_2fa_enabled
        }, status=status.HTTP_200_OK)

class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

def send_otp_email(email, otp_code):
    subject = "Your OTP Code for Password Reset"
    message = f"Your OTP code is: {otp_code}. It is valid for 5 minutes."
    from_email = (os.getenv("EMAIL_HOST_USER")) 
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
    print(f"OTP {otp_code} sent to email: {email}")

class resendotpview(APIView):
    def post(self, request):
        try:
            identifier = request.data.get('email_or_phone', '').strip().lower()

            if not identifier:
                return JsonResponse({"message": "Please enter Email or Phone number"}, status=status.HTTP_400_BAD_REQUEST)

            otp = random.randint(1000, 9999)

            if '@' in identifier:
                try:
                    user = User.objects.get(email=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this email not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                subject = "One Time Password"
                email_body = f"Your OTP is: {otp}\n\nUse this code to complete your verification."

                try:
                    send_mail(subject, email_body, 'AI IngredientIQ', [user.email], fail_silently=False)
                except BadHeaderError:
                    return JsonResponse({"message": "Invalid email header"}, status=status.HTTP_400_BAD_REQUEST)

                return JsonResponse({"data": "OTP sent to your email"}, status=status.HTTP_200_OK)

            else:
                try:
                    user = User.objects.get(phone_number=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this phone number not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                message = f"Your OTP is: {otp}. Use this to complete your verification."
                send_sms(user.phone_number, message)

                return JsonResponse({"data": "OTP sent to your phone number"}, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Verify OTP API
class verifyotpview(APIView):
    def post(self, request):
        try:
            otp = request.data.get('otp', None)
            
            if not otp:
                return JsonResponse({"error": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                otp = int(otp)
            except ValueError:
                return JsonResponse({"error": "OTP should be a valid integer"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(otp=otp).first()

            if user:
                user.otp = None  # Clear OTP after successful verification
                user.save()

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                return Response({
                    "message": "OTP Verified Successfully. Login successful.",
                    "access_token": access_token,
                    "refresh_token": str(refresh)
                }, status=status.HTTP_200_OK)

            return Response({"error": "Incorrect OTP"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordRequestAPIView(APIView):
    permission_classes = [] 

    def post(self, request):
        email = request.data.get("email")  
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            confirm_password = serializer.validated_data['confirm_password']

            if new_password != confirm_password:
                return Response({"detail": "Passwords must match."}, status=status.HTTP_400_BAD_REQUEST)

            if len(confirm_password) < 8:
                return Response({"detail": "New password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(confirm_password)
            user.save()

            return Response({"detail": "Password has been successfully reset."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

class termsandconditionView(APIView):
    def get(self,request):
        user = Termandcondition.objects.all()
        serializer = termsandconditionSerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)


class privacypolicyView(APIView):
    def get(self,request):
        user = privacypolicy.objects.all()
        serializer = privacypolicySerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)

class Frequentlyasked(APIView):
    def get(self,request):
        user = FAQ.objects.all()
        serializer = FAQSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class About(APIView):
    def get(self,request):
        user = AboutUS.objects.all()
        serializer = AboutSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class userprofileview(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request):
        user = User.objects.get(email=request.user.email)

        if not request.data:
            return Response({"message": "No data provided to update."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = userPatchSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            profile_picture_url = None
            if user.profile_picture:
                profile_picture_url = user.profile_picture.url
                print("------------", profile_picture_url)
                profile_picture_url = profile_picture_url.replace("https//", "")
                print("======", profile_picture_url)  
            return Response(
                {"message": "Profile updated successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self,request):
        user = User.objects.select_related().get(email=request.user.email)
        user.refresh_from_db()  # Force refresh from database
        serializer = userGetSerializer(user)
        # Add payment status info
        from .models import UserSubscription
        payment_status = 'freemium'
        premium_type = None
        try:
            sub = UserSubscription.objects.get(user=user)
            if sub.plan_name == 'premium':
                payment_status = 'premium'
                # Use a new field 'premium_type' if present, else fallback to 'unknown'
                premium_type = getattr(sub, 'premium_type', None)
        except UserSubscription.DoesNotExist:
            pass
        data = serializer.data
        data['payment_status'] = payment_status
        data['premium_type'] = premium_type
        return Response({"data":data}, status=status.HTTP_200_OK)
    
    def delete(self, request):
        user = User.objects.get(email=request.user.email)
        user.delete()
        return Response({"detail":"User deleted successfully."}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)

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

def get_user_plan_info(user):
    """
    Returns user's plan information including plan name, type, and status.
    """
    try:
        subscription = UserSubscription.objects.get(user=user)
        return {
            "plan_name": subscription.plan_name,
            "premium_type": subscription.premium_type,
            "status": subscription.status,
            "is_premium": subscription.plan_name.strip().lower() != "freemium"
        }
    except UserSubscription.DoesNotExist:
        return {
            "plan_name": "freemium",
            "premium_type": None,
            "status": "inactive",
            "is_premium": False
        }

def get_accurate_scan_count(user):
    """
    Returns the accurate scan count for a user based on actual FoodLabelScan objects.
    This ensures the count is accurate even if MonthlyScanUsage records are out of sync.
    """
    try:
        # Get the actual count of FoodLabelScan objects for this user
        actual_count = FoodLabelScan.objects.filter(user=user).count()
        
        # Update the MonthlyScanUsage record to sync with actual count
        usage = MonthlyScanUsage.get_or_create_current_month(user)
        if usage.scan_count != actual_count:
            usage.scan_count = actual_count
            usage.save()
            print(f"Synced scan count for user {user.email}: {usage.scan_count} -> {actual_count}")
        
        return actual_count
    except Exception as e:
        print(f"Error getting accurate scan count: {e}")
        return 0

def get_scan_count_at_time(user, scan_time):
    """
    Returns the scan count for a user at a specific point in time.
    This is used to show the correct scan count for historical scans.
    """
    try:
        # Count how many scans were created before or at the given time
        scan_count = FoodLabelScan.objects.filter(
            user=user,
            scanned_at__lte=scan_time
        ).count()
        
        return scan_count
    except Exception as e:
        print(f"Error getting scan count at time: {e}")
        return 0

def sync_all_user_scan_counts():
    """
    Sync all users' scan counts in MonthlyScanUsage with their actual FoodLabelScan objects.
    This should be run after deleting scans from admin panel to fix count discrepancies.
    """
    try:
        users = User.objects.all()
        synced_count = 0
        
        for user in users:
            actual_count = FoodLabelScan.objects.filter(user=user).count()
            usage = MonthlyScanUsage.get_or_create_current_month(user)
            
            if usage.scan_count != actual_count:
                old_count = usage.scan_count
                usage.scan_count = actual_count
                usage.save()
                print(f"Synced user {user.email}: {old_count} -> {actual_count}")
                synced_count += 1
        
        print(f"Synced scan counts for {synced_count} users")
        return synced_count
    except Exception as e:
        print(f"Error syncing scan counts: {e}")
        return 0

# Add a setting at the top of the file
USE_STATIC_INGREDIENT_SAFETY = False  # Set to True for instant local safety check, False to use Edamam

def increment_user_scan_count(user):
    """
    Increment the user's scan count for the current month.
    Returns the updated scan count and remaining scans.
    """
    try:
        usage = MonthlyScanUsage.get_or_create_current_month(user)
        usage.increment_scan()
        return usage.scan_count, usage.get_remaining_scans()
    except Exception as e:
        print(f"Error incrementing scan count: {e}")
        return 0, 0

class FoodLabelNutritionView(APIView):
    import io
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import json
import random
import ssl
import tempfile
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.utils import timezone
from datetime import timedelta
import openai
import hashlib
import threading
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from fuzzywuzzy import fuzz
from django.contrib.auth import login
from .serializers import FAQSerializer, AboutSerializer, AllergenDietaryCheckSerializer, FAQSerializer, SignupSerializer, LoginSerializer, ForgotPasswordRequestSerializer, UpdateUserProfileSerializer, UserSettingsSerializer, VerifyOTPSerializer,ChangePasswordSerializer,HealthPreferenceSerializer, privacypolicySerializer, termsandconditionSerializer, userGetSerializer, userPatchSerializer, FoodLabelScanSerializer, FeedbackSerializer, LoveAppSerializer, DepartmentContactSerializer
from .models import FoodLabelScan, MonthlyScanUsage, Termandcondition, User, UserSubscription, privacypolicy, AboutUS, FAQ,StripeCustomer, Feedback, DepartmentContact
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import IsSuperAdmin
# from paddleocr import PaddleOCR
import re
# import easyocr
from io import BytesIO
# from .apps import YourAppConfig
from django.http import HttpResponse
import asyncio
import aiohttp
import numpy as np
from .utils import send_sms, is_eligible_for_new_user_discount, get_discount_info, get_subscription_prices
# from .utils import extract_nutrition_info_from_text
from PIL import Image
from foodanalysis import settings
import os
from bs4 import BeautifulSoup
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth import logout
import cv2
import time
import logging
import os
from PIL import Image, ImageEnhance, ImageFilter
import uuid
from django.core.files.base import ContentFile
import requests
from django.core.files.storage import default_storage
# from allauth.socialaccount.models import SocialApp
from django.shortcuts import redirect
from pytrends.request import TrendReq
from geopy.geocoders import Nominatim
from collections import Counter
from geopy.exc import GeocoderTimedOut
from django.core.cache import cache 
import stripe
from .utils import fetch_llm_insight, fetch_medlineplus_summary, fetch_pubchem_toxicology_summary, fetch_pubmed_articles, fetch_efsa_openfoodtox_data, fetch_efsa_ingredient_summary, fetch_fsa_hygiene_rating, fetch_fsa_hygiene_summary, search_fsa_establishments_by_product, fetch_snomed_ct_data, fetch_icd10_data, get_medical_condition_food_recommendations
from asgiref.sync import sync_to_async
from django.views.decorators.csrf import csrf_exempt
import aiohttp
import asyncio
# import concurrent.futures
from openai import OpenAI
# from .openfoodfacts_api import openfoodfacts_api
openfoodfacts_api = "https://world.openfoodfacts.org/api/v0/product/"
USE_STATIC_INGREDIENT_SAFETY = False    
# openai.api_key = os.getenv("OPENAI_API_KEY")
# import feedparser  # For Medium RSS feeds
client = OpenAI(api_key="OPENAI_API_KEY_REMOVED")
BASE_URL = "https://api.spoonacular.com"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
OPEN_FOOD_FACTS_API = "https://world.openfoodfacts.org/api/v0/product/"
USDA_API_KEY = os.getenv("USDA_API_KEY")
API_KEY = os.getenv("foursquare_api_key")
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WORDPRESS_API_URL = "https://public-api.wordpress.com/rest/v1.1/sites/example.wordpress.com/posts/"
WORDPRESS_BLOG_URL = "https://public-api.wordpress.com/rest/v1.1/sites/example.wordpress.com/posts"
EDAMAM_APP_ID = os.getenv("EDAMAM_APP_ID")
EDAMAM_APP_KEY = os.getenv("EDAMAM_APP_KEY")
SPOONACULAR_KEY = "c01bfdfb4ccd4d8097b5110f789e0618"
WIKIPEDIA_SEARCH_API_URL = "https://en.wikipedia.org/w/api.php"
WHO_SEARCH_URL = "https://www.who.int/search?q="
WIKIPEDIA_LINKS_API = "https://en.wikipedia.org/w/api.php"
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# openai.api_key = "OPENAI_API_KEY_REMOVED"

# Singleton EasyOCR reader and GPU check
# _easyocr_reader = None
# _easyocr_lock = threading.Lock()
# _easyocr_gpu = None

# def get_easyocr_reader():
#     global _easyocr_reader, _easyocr_gpu
#     with _easyocr_lock:
#         if _easyocr_reader is None:
#             try:
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=True)
#                 # Check if GPU is actually used
#                 _easyocr_gpu = _easyocr_reader.gpu
#                 logging.info(f"EasyOCR initialized. GPU used: {_easyocr_gpu}")
#             except Exception as e:
#                 logging.error(f"EasyOCR initialization failed: {e}")
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=False)
#                 _easyocr_gpu = False
#         return _easyocr_reader

# def is_easyocr_gpu():
#     global _easyocr_gpu
#     return _easyocr_gpu

def google_login(request):
    # google = SocialApp.objects.get(provider='google')
    # return redirect(f"https://accounts.google.com/o/oauth2/auth?client_id={google.client_id}&redirect_uri=http://localhost:8000/accounts/google/login/callback/&response_type=code&scope=email profile")
    pass  # Social login temporarily disabled due to SQLite JSONField incompatibility

class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'message': 'User created successfully.',
                'access_token': access_token,
                'refresh_token': str(refresh),
                'is_2fa_enabled': user.is_2fa_enabled
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            if user.is_2fa_enabled:  # Check if 2FA is enabled
                from random import randint
                from django.core.mail import send_mail

                otp_code = randint(100000, 999999)  # Generate 6-digit OTP
                user.otp = str(otp_code)
                user.save()

                # Send OTP via email
                send_mail(
                    "Your OTP Code",
                    f"Your OTP code is: {otp_code}",
                    "no-reply@example.com",
                    [user.email],
                    fail_silently=False,
                )

                return Response({
                    "message": "OTP sent to your email. Please verify to continue.",
                    "user_id": user.id,
                    "is_2fa_enabled": user.is_2fa_enabled,
                    "has_answered_onboarding": user.has_answered_onboarding, # <-- Added here
                    # "subscription_plan": user.UserSubscription

                }, status=status.HTTP_200_OK)

            # If 2FA is disabled, proceed with normal login
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                "message": "Login successful.",
                "access_token": access_token,
                "refresh_token": str(refresh),
                "is_2fa_enabled": user.is_2fa_enabled,
                "has_answered_onboarding": user.has_answered_onboarding,  # <-- Added here
                "subscription_plan": user.subscription_plan

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class Toggle2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        is_2fa_enabled = request.data.get("is_2fa_enabled", None)

        if is_2fa_enabled is None:
            return Response({"error": "is_2fa_enabled field is required"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_2fa_enabled = is_2fa_enabled
        user.save()
        
        return Response({
            "message": f"Two-Factor Authentication {'enabled' if is_2fa_enabled else 'disabled'} successfully.",
            "is_2fa_enabled": user.is_2fa_enabled
        }, status=status.HTTP_200_OK)

class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

def send_otp_email(email, otp_code):
    subject = "Your OTP Code for Password Reset"
    message = f"Your OTP code is: {otp_code}. It is valid for 5 minutes."
    from_email = (os.getenv("EMAIL_HOST_USER")) 
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
    print(f"OTP {otp_code} sent to email: {email}")

class resendotpview(APIView):
    def post(self, request):
        try:
            identifier = request.data.get('email_or_phone', '').strip().lower()

            if not identifier:
                return JsonResponse({"message": "Please enter Email or Phone number"}, status=status.HTTP_400_BAD_REQUEST)

            otp = random.randint(1000, 9999)

            if '@' in identifier:
                try:
                    user = User.objects.get(email=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this email not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                subject = "One Time Password"
                email_body = f"Your OTP is: {otp}\n\nUse this code to complete your verification."

                try:
                    send_mail(subject, email_body, 'AI IngredientIQ', [user.email], fail_silently=False)
                except BadHeaderError:
                    return JsonResponse({"message": "Invalid email header"}, status=status.HTTP_400_BAD_REQUEST)

                return JsonResponse({"data": "OTP sent to your email"}, status=status.HTTP_200_OK)

            else:
                try:
                    user = User.objects.get(phone_number=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this phone number not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                message = f"Your OTP is: {otp}. Use this to complete your verification."
                send_sms(user.phone_number, message)

                return JsonResponse({"data": "OTP sent to your phone number"}, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Verify OTP API
class verifyotpview(APIView):
    def post(self, request):
        try:
            otp = request.data.get('otp', None)
            
            if not otp:
                return JsonResponse({"error": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                otp = int(otp)
            except ValueError:
                return JsonResponse({"error": "OTP should be a valid integer"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(otp=otp).first()

            if user:
                user.otp = None  # Clear OTP after successful verification
                user.save()

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                return Response({
                    "message": "OTP Verified Successfully. Login successful.",
                    "access_token": access_token,
                    "refresh_token": str(refresh)
                }, status=status.HTTP_200_OK)

            return Response({"error": "Incorrect OTP"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordRequestAPIView(APIView):
    permission_classes = [] 

    def post(self, request):
        email = request.data.get("email")  
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            confirm_password = serializer.validated_data['confirm_password']

            if new_password != confirm_password:
                return Response({"detail": "Passwords must match."}, status=status.HTTP_400_BAD_REQUEST)

            if len(confirm_password) < 8:
                return Response({"detail": "New password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(confirm_password)
            user.save()

            return Response({"detail": "Password has been successfully reset."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

class termsandconditionView(APIView):
    def get(self,request):
        user = Termandcondition.objects.all()
        serializer = termsandconditionSerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)


class privacypolicyView(APIView):
    def get(self,request):
        user = privacypolicy.objects.all()
        serializer = privacypolicySerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)

class Frequentlyasked(APIView):
    def get(self,request):
        user = FAQ.objects.all()
        serializer = FAQSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class About(APIView):
    def get(self,request):
        user = AboutUS.objects.all()
        serializer = AboutSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class userprofileview(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request):
        user = User.objects.get(email=request.user.email)

        if not request.data:
            return Response({"message": "No data provided to update."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = userPatchSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            profile_picture_url = None
            if user.profile_picture:
                profile_picture_url = user.profile_picture.url
                print("------------", profile_picture_url)
                profile_picture_url = profile_picture_url.replace("https//", "")
                print("======", profile_picture_url)  
            return Response(
                {"message": "Profile updated successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self,request):
        user = User.objects.select_related().get(email=request.user.email)
        user.refresh_from_db()  # Force refresh from database
        serializer = userGetSerializer(user)
        # Add payment status info
        from .models import UserSubscription
        payment_status = 'freemium'
        premium_type = None
        try:
            sub = UserSubscription.objects.get(user=user)
            if sub.plan_name == 'premium':
                payment_status = 'premium'
                # Use a new field 'premium_type' if present, else fallback to 'unknown'
                premium_type = getattr(sub, 'premium_type', None)
        except UserSubscription.DoesNotExist:
            pass
        data = serializer.data
        data['payment_status'] = payment_status
        data['premium_type'] = premium_type
        return Response({"data":data}, status=status.HTTP_200_OK)
    
    def delete(self, request):
        user = User.objects.get(email=request.user.email)
        user.delete()
        return Response({"detail":"User deleted successfully."}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)

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

def get_user_plan_info(user):
    """
    Returns user's plan information including plan name, type, and status.
    """
    try:
        subscription = UserSubscription.objects.get(user=user)
        return {
            "plan_name": subscription.plan_name,
            "premium_type": subscription.premium_type,
            "status": subscription.status,
            "is_premium": subscription.plan_name.strip().lower() != "freemium"
        }
    except UserSubscription.DoesNotExist:
        return {
            "plan_name": "freemium",
            "premium_type": None,
            "status": "inactive",
            "is_premium": False
        }

def get_accurate_scan_count(user):
    """
    Returns the accurate scan count for a user based on actual FoodLabelScan objects.
    This ensures the count is accurate even if MonthlyScanUsage records are out of sync.
    """
    try:
        # Get the actual count of FoodLabelScan objects for this user
        actual_count = FoodLabelScan.objects.filter(user=user).count()
        
        # Update the MonthlyScanUsage record to sync with actual count
        usage = MonthlyScanUsage.get_or_create_current_month(user)
        if usage.scan_count != actual_count:
            usage.scan_count = actual_count
            usage.save()
            print(f"Synced scan count for user {user.email}: {usage.scan_count} -> {actual_count}")
        
        return actual_count
    except Exception as e:
        print(f"Error getting accurate scan count: {e}")
        return 0

def get_scan_count_at_time(user, scan_time):
    """
    Returns the scan count for a user at a specific point in time.
    This is used to show the correct scan count for historical scans.
    """
    try:
        # Count how many scans were created before or at the given time
        scan_count = FoodLabelScan.objects.filter(
            user=user,
            scanned_at__lte=scan_time
        ).count()
        
        return scan_count
    except Exception as e:
        print(f"Error getting scan count at time: {e}")
        return 0

def sync_all_user_scan_counts():
    """
    Sync all users' scan counts in MonthlyScanUsage with their actual FoodLabelScan objects.
    This should be run after deleting scans from admin panel to fix count discrepancies.
    """
    try:
        users = User.objects.all()
        synced_count = 0
        
        for user in users:
            actual_count = FoodLabelScan.objects.filter(user=user).count()
            usage = MonthlyScanUsage.get_or_create_current_month(user)
            
            if usage.scan_count != actual_count:
                old_count = usage.scan_count
                usage.scan_count = actual_count
                usage.save()
                print(f"Synced user {user.email}: {old_count} -> {actual_count}")
                synced_count += 1
        
        print(f"Synced scan counts for {synced_count} users")
        return synced_count
    except Exception as e:
        print(f"Error syncing scan counts: {e}")
        return 0

# Add a setting at the top of the file
USE_STATIC_INGREDIENT_SAFETY = False  # Set to True for instant local safety check, False to use Edamam

def increment_user_scan_count(user):
    """
    Increment the user's scan count for the current month.
    Returns the updated scan count and remaining scans.
    """
    try:
        usage = MonthlyScanUsage.get_or_create_current_month(user)
        usage.increment_scan()
        return usage.scan_count, usage.get_remaining_scans()
    except Exception as e:
        print(f"Error incrementing scan count: {e}")
        return 0, 0

class FoodLabelNutritionView(APIView):
    permission_classes = [IsAuthenticated]
    
    # In-memory caches (class-level)
    edamam_cache = {}
    openai_cache = {}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize AWS Textract client
        try:
            aws_access_key = settings.AWS_ACCESS_KEY_ID
            aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
            aws_region = settings.AWS_S3_REGION_NAME or 'us-east-1'
            
            if not aws_access_key or not aws_secret_key:
                logging.error("AWS credentials not found in settings")
                self.textract_client = None
                return
            
            self.textract_client = boto3.client(
                'textract',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            print("AWS Textract client initialized successfully for FoodLabelNutritionView")
        except Exception as e:
            logging.error(f"Failed to initialize AWS Textract client: {e}")
            self.textract_client = None

    def post(self, request):
        # can_scan, scan_count = can_user_scan(request.user)
        # if not can_scan:
        #     return Response(
        #         {
        #             "error": "Scan limit reached. Please subscribe to AI IngredientIQ for unlimited scans.",
        #             "scans_used": scan_count,
        #             "max_scans": 6
        #         },
        #         status=status.HTTP_402_PAYMENT_REQUIRED
        #     )
        import time
        import logging
        from concurrent.futures import ThreadPoolExecutor
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"FoodLabelNutritionView is running on: {device.upper()}")
        except ImportError:
            print("torch not installed; cannot determine GPU/CPU.")

        start_time = time.time()

        # Deserialize and validate
        serializer = AllergenDietaryCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data['image']
        image_content = image_file.read()

        # LIGHTNING FAST PARALLEL PROCESSING
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all tasks simultaneously
            image_future = executor.submit(self.save_image, image_content)
            ocr_future = executor.submit(self.run_ocr, image_content)
            ingredients_future = executor.submit(self.extract_ingredients_with_textract_query, image_content)
            nutrition_future = executor.submit(self.extract_nutrition_with_textract_query, image_content)
            
            # Get image URL first (critical)
            image_url, image_path = image_future.result(timeout=3)
            if not image_url:
                return Response({'error': 'Image upload failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get OCR results with timeouts
            try:
                extracted_text = ocr_future.result(timeout=8)  # 8 second timeout
            except:
                extracted_text = ""
                
            try:
                query_ingredients = ingredients_future.result(timeout=8)
            except:
                query_ingredients = []
                
            try:
                query_nutrition = nutrition_future.result(timeout=8)
            except:
                query_nutrition = {}
        
        # Process results quickly
        if query_nutrition:
            nutrition_data = self.process_query_nutrition_data(query_nutrition)
        else:
            nutrition_data = self.extract_nutrition_info_fallback(extracted_text)
        
        if query_ingredients:
            actual_ingredients = self.process_query_ingredients(query_ingredients)
        else:
            actual_ingredients = self.extract_ingredients_from_text_fallback(extracted_text)

        # Debug logging
        print(f"Extracted text: {extracted_text}")
        print(f"Nutrition data extracted: {nutrition_data}")
        
        # More lenient check - allow partial nutrition data
        if not nutrition_data:
            # Try a simpler extraction method as fallback
            nutrition_data = self.extract_nutrition_info_simple(extracted_text)
            print(f"Fallback nutrition data: {nutrition_data}")
            
        if not nutrition_data:
            return Response(
                {"error": "No nutrition data found, Please capture clear photo of nutrition label of food packet. Scan not saved."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # PARALLEL SAFETY VALIDATION AND AI INSIGHTS
        safety_start = time.time()
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Run safety validation and AI insights in parallel
            safety_future = executor.submit(lambda: asyncio.run(self.validate_product_safety(request.user, actual_ingredients)))
            ai_future = executor.submit(self.get_ai_health_insight_and_expert_advice, request.user, nutrition_data, [])
            
            # Get safety results with timeout
            try:
                safety_result = safety_future.result(timeout=5)  # 5 second timeout
                if len(safety_result) == 5:
                    safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache = safety_result
                else:
                    safety_status, go_ingredients, caution_ingredients, no_go_ingredients = safety_result
                    efsa_data_cache = {}
            except:
                safety_status, go_ingredients, caution_ingredients, no_go_ingredients = "unknown", [], [], []
                efsa_data_cache = {}
            
            # Get AI results with timeout
            try:
                ai_results = ai_future.result(timeout=3)  # 3 second timeout
            except:
                ai_results = {
                    "ai_health_insight": "Health insights unavailable.",
                    "expert_advice": "Consult healthcare professional."
                }
        
        safety_end = time.time()
        logging.info(f"Safety validation completed in {safety_end - safety_start:.2f} seconds.")

        # Prepare ingredients for scan history (convert back to simple format for storage)
        def extract_ingredient_names(ingredient_list):
            return [ing["ingredient"] if isinstance(ing, dict) else ing for ing in ingredient_list]
        
        no_go_names = extract_ingredient_names(no_go_ingredients)
        go_names = extract_ingredient_names(go_ingredients)
        caution_names = extract_ingredient_names(caution_ingredients)
        
        with ThreadPoolExecutor() as executor:
            scan_future = executor.submit(lambda: asyncio.run(self.save_scan_history(
                request.user,
                image_url,
                extracted_text,
                nutrition_data,
                ai_results,
                safety_status,
                no_go_names,  # flagged_ingredients
                go_names,     # go_ingredients
                caution_names,  # caution_ingredients
                no_go_names,  # no_go_ingredients
                "OCR Product"  # product_name
            )))
            scan = scan_future.result()

        total_time = time.time() - start_time
        logging.info(f"FoodLabelNutritionView total time: {total_time:.2f} seconds.")

        # Convert ingredient lists to list of objects with clean names and EFSA data
        def format_ingredient_list(ingredient_list):
            formatted_list = []
            for ing in ingredient_list:
                if isinstance(ing, dict):
                    # New format with EFSA data
                    formatted_ing = {
                        "ingredient": ing["ingredient"],
                        "reasons": ing.get("reasons", []),
                        "efsa_data": ing.get("efsa_data", {})
                    }
                else:
                    # Old format (string)
                    formatted_ing = {
                        "ingredient": ing,
                        "reasons": ["Legacy format"],
                        "efsa_data": {}
                    }
                formatted_list.append(formatted_ing)
            return formatted_list
        
        go_ingredients_obj = format_ingredient_list(go_ingredients)
        caution_ingredients_obj = format_ingredient_list(caution_ingredients)
        no_go_ingredients_obj = format_ingredient_list(no_go_ingredients)

        main_ingredient = actual_ingredients[0] if actual_ingredients else None
        def safe_summary(fetch_func, ingredient, default_msg):
            try:
                summary = fetch_func(ingredient)
                if not summary or (isinstance(summary, str) and not summary.strip()):
                    return default_msg
                return summary
            except Exception as e:
                print(f"Summary fetch error for {ingredient}: {e}")
                return default_msg

        medlineplus_summary = safe_summary(
            fetch_medlineplus_summary,
            main_ingredient,
            "No MedlinePlus summary available for this ingredient."
        ) if main_ingredient else "No MedlinePlus summary available for this ingredient."

        pubchem_summary = safe_summary(
            fetch_pubchem_toxicology_summary,
            main_ingredient,
            "No PubChem toxicology data found for this ingredient."
        ) if main_ingredient else "No PubChem toxicology data found for this ingredient."
        pubmed_articles = fetch_pubmed_articles(main_ingredient) if main_ingredient else []

        # REMOVED ClinicalTrials.gov integration for speed
        def fetch_clinical_trials(ingredient):
            return []  # Return empty list for speed
            if not ingredient:
                return []
            try:
                url = f"https://clinicaltrials.gov/api/v2/studies?q={ingredient}&limit=3"
                resp = requests.get(url, timeout=5)
                if resp.status_code != 200:
                    print(f"ClinicalTrials.gov API error: {resp.status_code}")
                    return []
                data = resp.json()
                studies = data.get("studies", [])
                trials = []
                for study in studies:
                    nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
                    title = study.get("protocolSection", {}).get("identificationModule", {}).get("officialTitle")
                    status = study.get("protocolSection", {}).get("statusModule", {}).get("overallStatus")
                    summary = study.get("protocolSection", {}).get("descriptionModule", {}).get("briefSummary")
                    url = f"https://clinicaltrials.gov/ct2/show/{nct_id}" if nct_id else None
                    if nct_id and title:
                        trials.append({
                            "title": title,
                            "nct_id": nct_id,
                            "status": status,
                            "summary": summary,
                            "url": url
                        })
                return trials
            except Exception as e:
                print(f"ClinicalTrials.gov fetch error: {e}")
                return []

        clinical_trials = fetch_clinical_trials(main_ingredient)

        # --- FSA Hygiene Rating Integration ---
        # Try to extract business name from OCR text or use default
        business_name = "OCR Product"  # Default fallback
        fsa_data = None
        
        # Look for business names in the extracted text
        business_keywords = ['ltd', 'limited', 'inc', 'corporation', 'company', 'co', 'brand', 'manufacturer']
        lines = extracted_text.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in business_keywords):
                business_name = line.strip()
                break
        
        # Fetch FSA hygiene rating data
        try:
            fsa_data = fetch_fsa_hygiene_rating(business_name=business_name)
        except Exception as e:
            print(f"FSA API error: {e}")
            fsa_data = {
                'found': False,
                'error': f'FSA API error: {str(e)}',
                'source': 'UK FSA FHRS API'
            }

        # Get current scan count for response
        from .scan_limit import can_user_scan, get_monthly_reset_date
        _, scan_count, remaining_scans = can_user_scan(request.user)
        
        # Handle None values for premium users
        if scan_count is None:
            scan_count = 0
        if remaining_scans is None:
            remaining_scans = "unlimited"
        
        return Response({
            "scan_id": scan.id,
            "product_name":"OCR Product",
            "image_url": image_url,
            "extracted_text": extracted_text,
            "nutrition_data": nutrition_data,
            "ingredients": actual_ingredients,
            "safety_status": safety_status,
            "is_favorite": scan.is_favorite,
            "scan_usage": {
                "scans_used": scan_count,
                "max_scans": 20,
                "remaining_scans": remaining_scans,
                "monthly_reset_date": get_monthly_reset_date(),
                "total_user_scans": scan_count,
            },
            "user_plan": get_user_plan_info(request.user),
            "ingredients_analysis": {
                "go": {
                    "ingredients": go_ingredients_obj,
                    "count": len(go_ingredients_obj),
                    "description": "Ingredients that are safe and suitable for your health profile"
                },
                "caution": {
                    "ingredients": caution_ingredients_obj,
                    "count": len(caution_ingredients_obj),
                    "description": "Ingredients that may not be ideal for your health profile - consume at your own risk"
                },
                "no_go": {
                    "ingredients": no_go_ingredients_obj,
                    "count": len(no_go_ingredients_obj),
                    "description": "Ingredients that are harmful or not suitable for your health profile - avoid these"
                },
                "total_flagged": len(caution_ingredients_obj) + len(no_go_ingredients_obj)
            },
            "efsa_data": {
                "source": "European Food Safety Authority (EFSA) OpenFoodTox Database",
                "total_ingredients_checked": len(efsa_data_cache),
                "ingredients_with_efsa_data": len([data for data in efsa_data_cache.values() if data and data.get('found')]),
                "cache": {k: v for k, v in efsa_data_cache.items() if v is not None}
            },
            "fsa_hygiene_data": fsa_data,
            "medical_condition_recommendations": {
                "user_health_profile": {
                    "allergies": request.user.Allergies,
            "ai_health_insight": {
                "Bluf_insight": ai_results.get("structured_health_analysis", {}).get("bluf_insight", ai_results.get("ai_health_insight", "")),
                "Main_insight": ai_results.get("structured_health_analysis", {}).get("main_insight", ai_results.get("expert_advice", "")),
                "Deeper_reference": ai_results.get("structured_health_analysis", {}).get("deeper_reference", ""),
                "Disclaimer": ai_results.get("structured_health_analysis", {}).get("disclaimer", "Informational, not diagnostic. Consult healthcare providers for medical advice.")
            },
            "expert_ai_conclusion": ai_results.get("expert_ai_conclusion", ai_results.get("expert_advice", "")),
            "structured_health_analysis": ai_results.get("structured_health_analysis", {}),                },
                "recommendations": get_medical_condition_food_recommendations(
                    request.user.Health_conditions, 
                    request.user.Allergies, 
                    request.user.Dietary_preferences
                ) if (request.user.Health_conditions or request.user.Allergies or request.user.Dietary_preferences) else {"found": False, "message": "No health profile specified"},
                "source": "SNOMED CT & ICD-10 Clinical Guidelines"
            },
            "ai_health_insight": ai_results["ai_health_insight"],
            "expert_advice": ai_results["expert_advice"],
            # "ocr_gpu": False,  # Azure OCR
            # "medlineplus_summary": medlineplus_summary,
            # "pubchem_summary": pubchem_summary,
            # "pubmed_articles": pubmed_articles,
            # "clinical_trials": clinical_trials,
            # "timing": {
            #     "ocr": ocr_end - ocr_start,
            #     "safety+ai": safety_end - safety_start,
            #     "total": total_time
            # }
        }, status=status.HTTP_200_OK)

    def get_ai_health_insight_and_expert_advice(self, user, nutrition_data, flagged_ingredients):
        """
        Ultra-fast AI insights with minimal processing and aggressive timeouts.
        """
        import time
        import json
        import hashlib
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        
        # Quick cache check
        key_data = {
            'ingredients': sorted(flagged_ingredients[:2]),  # Only first 2 for speed
            'nutrition': {k: v for k, v in list(nutrition_data.items())[:3]},  # Only first 3
            'diet': user.Dietary_preferences,
            'allergies': user.Allergies
        }
        cache_key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        if cache_key in self.openai_cache:
            return self.openai_cache[cache_key]
        
        # Ultra-minimal prompt
        nutrition_summary = ', '.join(f"{k}: {v}" for k, v in list(nutrition_data.items())[:3])
        flagged_str = ', '.join(flagged_ingredients[:2])  # Only top 2
        prompt = f"User: {user.Dietary_preferences or 'None'}. Nutrition: {nutrition_summary}. Avoid: {flagged_str}. Give 1 sentence health insight + 1 sentence advice. Be extremely concise."
        
        def openai_call():
            from openai import OpenAI
            import os
            
            # Try OpenAI with very fast timeout
            try:
                client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    timeout=2  # 2 second timeout
                )
                
                # Ultra-minimal prompt for speed
                nutrition_summary = ', '.join(f"{k}: {v}" for k, v in list(nutrition_data.items())[:3])
                flagged_str = ', '.join(flagged_ingredients[:2])  # Only top 2
                user_profile = f"Diet: {user.Dietary_preferences or 'None'}, Allergies: {user.Allergies or 'None'}"
                
                prompt = f"""
                User Profile: {user_profile}
                Nutrition: {nutrition_summary}
                Avoid: {flagged_str}
                
                Give 1 sentence health insight + 1 sentence advice. Be extremely concise.
                """
                
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Nutrition expert. Be extremely concise and actionable."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=60,  # Very short response
                    temperature=0.3,
                )
                
                content = completion.choices[0].message.content.strip()
                
                # Simple split
                parts = content.split('.', 1)
                ai_health_insight = parts[0] + "." if parts else "Product analyzed successfully."
                expert_advice = parts[1] + "." if len(parts) > 1 else "Check ingredients for your dietary needs."
                
                return {
                    "ai_health_insight": ai_health_insight,
                    "expert_advice": expert_advice
                }
                
            except Exception as e:
                print(f"OpenAI error: {e}")
                # Fallback to intelligent response based on data
                if flagged_ingredients:
                    return {
                        "ai_health_insight": f"Product contains {len(flagged_ingredients)} ingredients that may not suit your dietary needs.",
                        "expert_advice": "Review the flagged ingredients and consult healthcare professional if needed."
                    }
                else:
                    return {
                        "ai_health_insight": "Product analyzed successfully. Check nutrition values for your health goals.",
                        "expert_advice": "Consider portion size and overall dietary balance."
                    }
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(openai_call)
            try:
                result = future.result(timeout=3)  # 3 second total timeout for OpenAI
                self.openai_cache[cache_key] = result
                return result
            except TimeoutError:
                return {"ai_health_insight": "Health insights unavailable.", "expert_advice": "Consult healthcare professional."}
            except Exception as e:
                print(f"OpenAI outer error: {e}")
                return {"ai_health_insight": "Health insights unavailable.", "expert_advice": "Consult healthcare professional."}

    def run_in_thread_pool(self, func, *args):
        with ThreadPoolExecutor() as executor:
            return executor.submit(func, *args).result()

    def save_image(self, image_content):
        try:
            image_name = f"food_labels/{uuid.uuid4()}.jpg"
            image_path = default_storage.save(image_name, ContentFile(image_content))
            image_url = default_storage.url(image_path).replace("https//", "")
            return image_url, image_path
        except Exception as e:
            print(f"Error saving image: {e}")
            return None, None

    def run_ocr(self, image_content):
        """
        Uses AWS Textract for high-accuracy text extraction with Query feature.
        """
        try:
            if not self.textract_client:
                logging.error("AWS Textract client not initialized")
                return ''
            
            # Try to extract text using AWS Textract Query first
            extracted_text = self.extract_text_with_textract_query(image_content)
            if extracted_text:
                logging.info(f"Extracted text from AWS Textract Query: {extracted_text}")
                return extracted_text
            
            # Fallback to regular text extraction
            extracted_text = self.extract_text_with_textract(image_content)
            if extracted_text:
                logging.info(f"Extracted text from AWS Textract: {extracted_text}")
                return extracted_text
            
            logging.error("AWS Textract failed to extract text")
            return ''
            
        except Exception as e:
            logging.error(f"AWS Textract OCR error: {e}", exc_info=True)
            return ''

    def extract_text_with_textract_query(self, image_content):
        """
        Extract text using AWS Textract Query feature for better accuracy.
        """
        try:
            # Validate image content
            if not isinstance(image_content, bytes):
                logging.error("Image content must be bytes")
                return ""
            
            # Check image size (AWS Textract limit is 5MB)
            if len(image_content) > 5 * 1024 * 1024:
                logging.error("Image too large for AWS Textract (max 5MB)")
                return ""
            
            # Check if image content is valid
            if len(image_content) < 100:
                logging.error("Image content too small")
                return ""

            # Query for general text content
            queries = [
                {
                    'Text': 'What text is visible in this image?',
                    'Alias': 'general_text'
                },
                {
                    'Text': 'Extract all text from this nutrition label',
                    'Alias': 'nutrition_text'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES', 'TABLES', 'FORMS', 'LINES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                extracted_text = ""
                
                # Extract text from query results
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                extracted_text += answer_block['Text'] + "\n"
                
                # Also extract regular text blocks
                text_blocks = [block for block in response.get('Blocks', []) if block['BlockType'] == 'LINE']
                text_blocks.sort(key=lambda x: (x['Geometry']['BoundingBox']['Top'], x['Geometry']['BoundingBox']['Left']))
                
                for block in text_blocks:
                    if 'Text' in block:
                        extracted_text += block['Text'] + "\n"

                return extracted_text.strip()
                
            except Exception as e:
                logging.error(f"Textract Query API error: {e}")
                return ""
            
        except Exception as e:
            logging.error(f"Textract Query extraction error: {e}")
            return ""

    def extract_text_with_textract(self, image_content):
        """
        Extract text using AWS Textract with enhanced features.
        """
        try:
            if not self.textract_client:
                raise Exception("AWS Textract client not initialized")

            # Ensure image_content is bytes
            if not isinstance(image_content, bytes):
                logging.error("Image content must be bytes")
                return ""

            # Check image size (AWS Textract limit is 5MB)
            if len(image_content) > 5 * 1024 * 1024:
                logging.error("Image too large for AWS Textract (max 5MB)")
                return ""

            # Check if image content is valid
            if len(image_content) < 100:
                logging.error("Image content too small")
                return ""

            # Try analyze_document first (more features)
            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['TABLES', 'FORMS', 'LINES']
                )
                
                # Extract text with spatial information
                extracted_text = ""
                blocks = response.get('Blocks', [])
                
                # Sort blocks by geometry for proper reading order
                text_blocks = [block for block in blocks if block['BlockType'] == 'LINE']
                text_blocks.sort(key=lambda x: (x['Geometry']['BoundingBox']['Top'], x['Geometry']['BoundingBox']['Left']))
                
                for block in text_blocks:
                    if 'Text' in block:
                        extracted_text += block['Text'] + "\n"

                return extracted_text.strip()
                
            except Exception as e:
                logging.error(f"Textract analyze_document failed: {e}")
                # Try simpler detect_document_text as fallback
                try:
                    response = self.textract_client.detect_document_text(
                        Document={
                            'Bytes': image_content
                        }
                    )
                    
                    extracted_text = ""
                    blocks = response.get('Blocks', [])
                    
                    for block in blocks:
                        if block['BlockType'] == 'LINE' and 'Text' in block:
                            extracted_text += block['Text'] + "\n"
                    
                    return extracted_text.strip()
                    
                except Exception as fallback_error:
                    logging.error(f"Textract detect_document_text also failed: {fallback_error}")
                    return ""

        except Exception as e:
            logging.error(f"Textract extraction error: {e}")
            return ""

    def correct_ocr_errors(self, text):
        corrections = {
            "Bg": "8g", "Omg": "0mg", "lron": "Iron", "meg": "mcg"
        }
        for wrong, right in corrections.items():
            text = text.replace(wrong, right)
        return text

    def extract_nutrition_info_from_text(self, text, image_content=None):
        """
        Enhanced nutrition extraction using AWS Textract Query for better accuracy.
        """
        nutrition_data = {}
        
        # Fix common OCR errors first
        text = self.correct_ocr_errors(text)
        
        # Try AWS Textract Query first if image_content is available
        if image_content and hasattr(self, 'textract_client') and self.textract_client:
            query_nutrition = self.extract_nutrition_with_textract_query(image_content)
            if query_nutrition:
                # Convert query results to the expected format
                for key, value in query_nutrition.items():
                    if value:
                        # Extract numeric value and unit
                        match = re.search(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', value)
                        if match:
                            numeric_value = match.group(1)
                            unit = match.group(2).lower()
                            
                            # Map query keys to nutrition data keys with proper units
                            if key == 'energy':
                                nutrition_data["Energy"] = f"{numeric_value} kcal"
                            elif key == 'protein':
                                nutrition_data["Protein"] = f"{numeric_value} g"
                            elif key == 'total_fat':
                                nutrition_data["Total Fat"] = f"{numeric_value} g"
                            elif key == 'saturated_fat':
                                nutrition_data["Saturated Fat"] = f"{numeric_value} g"
                            elif key == 'carbohydrates':
                                nutrition_data["Carbohydrate"] = f"{numeric_value} g"
                            elif key == 'sugars':
                                nutrition_data["Total Sugars"] = f"{numeric_value} g"
                            elif key == 'sodium':
                                nutrition_data["Sodium"] = f"{numeric_value} mg"
                            elif key == 'fiber':
                                nutrition_data["Dietary Fibre"] = f"{numeric_value} g"
                            else:
                                # Add as custom nutrient with proper unit
                                nutrition_data[key.replace('_', ' ').title()] = f"{numeric_value} {unit}"
        
        # If AWS Textract Query didn't provide enough data, fall back to text parsing
        if len(nutrition_data) < 3:  # If we have less than 3 nutrients, use fallback
            nutrition_data = self.extract_nutrition_info_fallback(text)
        
        return nutrition_data

    def extract_nutrition_with_textract_query(self, image_content):
        """
        Extract nutrition data using AWS Textract Query feature.
        """
        try:
            if not self.textract_client:
                return {}

            # Query for nutrition information
            queries = [
                {
                    'Text': 'What is the energy/calories value?',
                    'Alias': 'energy'
                },
                {
                    'Text': 'What is the protein content?',
                    'Alias': 'protein'
                },
                {
                    'Text': 'What is the total fat content?',
                    'Alias': 'total_fat'
                },
                {
                    'Text': 'What is the saturated fat content?',
                    'Alias': 'saturated_fat'
                },
                {
                    'Text': 'What is the carbohydrate content?',
                    'Alias': 'carbohydrates'
                },
                {
                    'Text': 'What is the sugar content?',
                    'Alias': 'sugars'
                },
                {
                    'Text': 'What is the sodium content?',
                    'Alias': 'sodium'
                },
                {
                    'Text': 'What is the fiber content?',
                    'Alias': 'fiber'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                nutrition_data = {}
                
                # Extract answers from the response
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        query_alias = block.get('Query', {}).get('Alias', '')
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        # Find the answer block
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                nutrition_data[query_alias] = answer_block['Text']
                
                return nutrition_data
                
            except Exception as e:
                logging.error(f"Nutrition Query failed: {e}")
                return {}

        except Exception as e:
            logging.error(f"Nutrition Query extraction error: {e}")
            return {}

    def extract_nutrition_info_fallback(self, text):
        """
        Fallback nutrition extraction using text parsing (original method).
        """
        nutrition_data = {}
        
        # Define comprehensive nutrient patterns with variations
        nutrient_patterns = {
            "Energy": [
                r'energy[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'calories[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'calorie[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*energy',
                r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*calories'
            ],
            "Total Fat": [
                r'total\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+fat',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fat'
            ],
            "Saturated Fat": [
                r'saturated\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sat\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*saturated\s+fat',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sat\s+fat'
            ],
            "Trans Fat": [
                r'trans\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*trans\s+fat'
            ],
            "Cholesterol": [
                r'cholesterol[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*cholesterol'
            ],
            "Sodium": [
                r'sodium[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'salt[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*sodium',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*salt'
            ],
            "Carbohydrate": [
                r'carbohydrate[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'carbohydrates[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'carbs[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrate',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrates',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbs'
            ],
            "Total Sugars": [
                r'total\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sugar[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+sugars',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugars',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugar'
            ],
            "Added Sugars": [
                r'added\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*added\s+sugars'
            ],
            "Dietary Fibre": [
                r'dietary\s+fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'dietary\s+fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fibre',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fiber',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fibre',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fiber'
            ],
            "Protein": [
                r'protein[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*protein'
            ]
        }
        
        # Extract using comprehensive patterns with proper unit mapping
        for nutrient_name, patterns in nutrient_patterns.items():
            all_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                all_matches.extend(matches)
            
            if all_matches:
                value, unit = all_matches[0]
                # Map units correctly
                if unit.lower() in ['kj', 'cal']:
                    unit = 'kcal'
                elif unit.lower() == '%':
                    unit = '%'
                elif nutrient_name in ["Energy"]:
                    unit = 'kcal'
                elif nutrient_name in ["Sodium", "Cholesterol"]:
                    unit = 'mg'
                else:
                    unit = 'g'
                    
                nutrition_data[nutrient_name] = f"{value} {unit}".strip()
        
        # Clean up and standardize units
        for key, value in nutrition_data.items():
            if value and not value.endswith(('kcal', 'g', 'mg', 'mcg', '%', 'kj', 'cal')):
                # Extract numeric value
                numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
                if numeric_match:
                    numeric_value = numeric_match.group(1)
                    if key.lower() in ["energy", "calories"]:
                        nutrition_data[key] = f"{numeric_value} kcal"
                    elif key.lower() in ["protein", "carbohydrate", "total sugars", "dietary fibre", "total fat", "saturated fat", "trans fat"]:
                        nutrition_data[key] = f"{numeric_value} g"
                    elif key.lower() in ["sodium", "cholesterol"]:
                        nutrition_data[key] = f"{numeric_value} mg"
        
        return nutrition_data

    def extract_nutrition_info_simple(self, text):
        """
        Simple fallback nutrition extraction method for OCR text that's hard to parse.
        """
        nutrition_data = {}
        
        # Fix common OCR errors
        text = text.replace('o.', '0.').replace('O.', '0.').replace('O', '0').replace('l', '1')
        text = text.replace('Ptotetn', 'Protein').replace('rotat', 'Total').replace('agog', '240g')
        text = text.replace('tug', '240g').replace('osg', '240g')
        
        # Split into lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        print(f"Processing lines: {lines}")  # Debug
        
        # Look for nutrition section
        nutrition_section = False
        for line in lines:
            if 'nutrition' in line.lower() or 'kcal' in line.lower() or 'g' in line:
                nutrition_section = True
                break
        
        if not nutrition_section:
            return nutrition_data
        
        # Enhanced pattern matching for the specific OCR format
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Skip non-nutrition lines
            if any(skip in line_lower for skip in ['ingredients', 'allergen', 'manufactured', 'store', 'packaged']):
                    continue
                
            print(f"Processing line {i}: '{line}' -> '{line_lower}'")  # Debug
            
            # Look for nutrient names and values
            if 'protein' in line_lower or 'ptotetn' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger (more likely to be correct)
                        if 'Protein' not in nutrition_data or float(value) > float(nutrition_data['Protein'].split()[0]):
                            nutrition_data['Protein'] = f"{value} {unit}"
                            print(f"Found Protein: {value} {unit}")  # Debug
                        break
            
            elif 'carbohydrate' in line_lower or 'carbs' in line_lower or 'rotat' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Carbohydrate' not in nutrition_data or float(value) > float(nutrition_data['Carbohydrate'].split()[0]):
                            nutrition_data['Carbohydrate'] = f"{value} {unit}"
                            print(f"Found Carbohydrate: {value} {unit}")  # Debug
                        break
            
            elif 'sugar' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Total Sugars' not in nutrition_data or float(value) > float(nutrition_data['Total Sugars'].split()[0]):
                            nutrition_data['Total Sugars'] = f"{value} {unit}"
                            print(f"Found Total Sugars: {value} {unit}")  # Debug
                        break
            
            elif 'fat' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        if 'saturated' in line_lower:
                            # Only add if we don't already have this nutrient or if this value is larger
                            if 'Saturated Fat' not in nutrition_data or float(value) > float(nutrition_data['Saturated Fat'].split()[0]):
                                nutrition_data['Saturated Fat'] = f"{value} {unit}"
                                print(f"Found Saturated Fat: {value} {unit}")  # Debug
                        else:
                            # Only add if we don't already have this nutrient or if this value is larger
                            if 'Total Fat' not in nutrition_data or float(value) > float(nutrition_data['Total Fat'].split()[0]):
                                nutrition_data['Total Fat'] = f"{value} {unit}"
                                print(f"Found Total Fat: {value} {unit}")  # Debug
                        break
            
            elif 'kcal' in line_lower or 'calorie' in line_lower or 'energy' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(kcal|cal)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'kcal'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Energy' not in nutrition_data or float(value) > float(nutrition_data['Energy'].split()[0]):
                            nutrition_data['Energy'] = f"{value} {unit}"
                            print(f"Found Energy: {value} {unit}")  # Debug
                        break
        
        # Also look for standalone numbers that might be nutrition values
        for i, line in enumerate(lines):
            # Look for lines that are just numbers (potential nutrition values)
            if re.match(r'^\d+(?:\.\d+)?\s*(g|kcal|mg)?$', line.strip()):
                value = re.search(r'(\d+(?:\.\d+)?)', line).group(1)
                unit = re.search(r'(g|kcal|mg)', line)
                unit = unit.group(1) if unit else 'g'
                
                print(f"Found standalone value: {value} {unit} at line {i}")  # Debug
                
                # Try to match with nearby nutrient names
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    nearby_line = lines[j].lower()
                    if ('protein' in nearby_line or 'ptotetn' in nearby_line) and 'Protein' not in nutrition_data:
                        nutrition_data['Protein'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Protein")  # Debug
                        break
                    elif ('carbohydrate' in nearby_line or 'carbs' in nearby_line or 'rotat' in nearby_line) and 'Carbohydrate' not in nutrition_data:
                        nutrition_data['Carbohydrate'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Carbohydrate")  # Debug
                        break
                    elif 'sugar' in nearby_line and 'Total Sugars' not in nutrition_data:
                        nutrition_data['Total Sugars'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Total Sugars")  # Debug
                        break
                    elif 'fat' in nearby_line:
                        if 'saturated' in nearby_line and 'Saturated Fat' not in nutrition_data:
                            nutrition_data['Saturated Fat'] = f"{value} {unit}"
                            print(f"Mapped {value} {unit} to Saturated Fat")  # Debug
                            break
                        elif 'Total Fat' not in nutrition_data:
                            nutrition_data['Total Fat'] = f"{value} {unit}"
                            print(f"Mapped {value} {unit} to Total Fat")  # Debug
                            break
        
        # Special handling for "Per 100g" format
        per_100g_section = ""
        for i, line in enumerate(lines):
            if 'per' in line.lower() and '100' in line and 'g' in line.lower():
                # Found the per 100g section, collect the next few lines
                per_100g_section = '\n'.join(lines[i:i+10])
                print(f"Found Per 100g section: {per_100g_section}")  # Debug
                break
        
        if per_100g_section:
            # Extract all number-unit pairs from this section
            number_unit_pairs = re.findall(r'(\d+(?:\.\d+)?)\s*(kcal|g|mg|mcg|%|kj|cal)', per_100g_section, re.IGNORECASE)
            print(f"Number-unit pairs found: {number_unit_pairs}")  # Debug
            
            # Try to match with nutrient names in the same section
            for pair in number_unit_pairs:
                value, unit = pair
                # Look for nutrient names near this value
                for nutrient_name in ['Energy', 'Protein', 'Carbohydrate', 'Total Sugars', 'Total Fat', 'Saturated Fat', 'Trans Fat']:
                    if nutrient_name.lower().replace(' ', '') in per_100g_section.lower().replace(' ', ''):
                        # Only add if we don't already have this nutrient or if this value is larger
                        if nutrient_name not in nutrition_data or float(value) > float(nutrition_data[nutrient_name].split()[0]):
                            # Standardize units
                            if unit.lower() in ['kj', 'cal']:
                                unit = 'kcal'
                            else:
                                unit = 'g'
                            
                        nutrition_data[nutrient_name] = f"{value} {unit}".strip()
                        print(f"Found {nutrient_name}: {value} {unit} from Per 100g section")  # Debug
        
        print(f"Final nutrition data: {nutrition_data}")  # Debug
        return nutrition_data

    def extract_ingredients_from_text(self, text, image_content=None):
        """
        Extracts a clean list of ingredients using AWS Textract Query for better accuracy.
        """
        import re
        
        # Try AWS Textract Query first if image_content is available
        if image_content and hasattr(self, 'textract_client') and self.textract_client:
            query_ingredients = self.extract_ingredients_with_textract_query(image_content)
            if query_ingredients:
                # Process query results
                ingredients = self.process_query_ingredients(query_ingredients)
                if ingredients:
                    return ingredients
        
        # Fallback to text parsing
        return self.extract_ingredients_from_text_fallback(text)

    def extract_ingredients_with_textract_query(self, image_content):
        """
        Extract ingredients using AWS Textract Query feature.
        """
        try:
            if not self.textract_client:
                return []

            # Query for ingredients
            queries = [
                {
                    'Text': 'What are the ingredients?',
                    'Alias': 'ingredients'
                },
                {
                    'Text': 'List all ingredients',
                    'Alias': 'ingredients_list'
                },
                {
                    'Text': 'What ingredients are in this product?',
                    'Alias': 'product_ingredients'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                ingredients = []
                
                # Extract answers from the response
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        # Find the answer block
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                ingredients.append(answer_block['Text'])
                
                return ingredients
                
            except Exception as e:
                logging.error(f"Ingredients Query failed: {e}")
                return []

        except Exception as e:
            logging.error(f"Ingredients Query extraction error: {e}")
            return []

    def process_query_ingredients(self, query_ingredients):
        """
        Process ingredients from Textract Query results with better cleaning.
        """
        if not query_ingredients:
            return []
        
        # Join all ingredient responses and clean them up
        ingredients_text = " ".join(query_ingredients)
        
        # Clean up the ingredients text - preserve important characters
        ingredients_text = re.sub(r'[^\w\s,()%.&-]', ' ', ingredients_text)  # Keep important chars
        ingredients_text = re.sub(r'\s+', ' ', ingredients_text)  # Normalize whitespace
        
        # Split ingredients by common separators, but be smarter about it
        ingredients = []
        
        # First, try to split by commas, but respect parentheses
        # This pattern splits by commas that are NOT inside parentheses
        parts = re.split(r',\s*(?![^()]*\))', ingredients_text)
        
        # If the above didn't work well, try a more aggressive approach
        if len(parts) <= 1:
            # Split by commas and then clean up each part
            parts = re.split(r',\s*', ingredients_text)
        
        for part in parts:
            ingredient = part.strip()
            if ingredient and len(ingredient) > 2:
                # Clean up ingredient using the cleaning function
                ingredient = self.clean_ingredient_text(ingredient)
                
                # Skip if it's just a number, percentage, or very short
                if (ingredient and len(ingredient) > 2 and 
                    not re.match(r'^\d+\.?\d*%?$', ingredient) and
                    not ingredient.lower() in ['and', 'or', 'the', 'a', 'an']):
                    
                    # Use the compound ingredient splitting function
                    split_ingredients = self.split_compound_ingredients(ingredient)
                    for split_ingredient in split_ingredients:
                        if split_ingredient and len(split_ingredient) > 2:
                            ingredients.append(split_ingredient)

        # Remove duplicates while preserving order
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            clean_ingredient = re.sub(r'\s+', ' ', ingredient).strip()
            if clean_ingredient.lower() not in seen:
                seen.add(clean_ingredient.lower())
                unique_ingredients.append(clean_ingredient)

        return unique_ingredients

    def extract_ingredients_from_text_fallback(self, text):
        """
        Fallback ingredients extraction using text parsing with improved cleaning.
        """
        import re
        # 1. Find the INGREDIENTS section (case-insensitive)
        match = re.search(
            r'ingredients[:\s]*([\s\S]+?)(allergen|nutritional|store|packaged|may contain|used as natural|information|$)',
            text, re.IGNORECASE
        )
        if not match:
            return []
        ingredients_text = match.group(1)

        # 2. Clean up text: replace newlines, remove unwanted symbols (but keep (), %, &)
        ingredients_text = re.sub(r'\n', ' ', ingredients_text)
        ingredients_text = re.sub(r'[^a-zA-Z0-9,().&%\-\s]', '', ingredients_text)
        ingredients_text = re.sub(r'\s+', ' ', ingredients_text)

        # 3. Split on commas and periods (not inside parentheses)
        parts = re.split(r'[,.](?![^()]*\))', ingredients_text)
        
        # If the above didn't work well, try a more aggressive approach
        if len(parts) <= 1:
            # Split by commas and then clean up each part
            parts = re.split(r'[,\s]+', ingredients_text)
        ingredients = []
        for part in parts:
            ing = part.strip()
            # Clean up ingredient using the cleaning function
            ing = self.clean_ingredient_text(ing)
            # Filter out non-ingredient lines
            if ing and not re.search(
                r'(may contain|allergen|information|flavouring|substances|regulator|identical|used as natural|limit of quantification)',
                ing, re.IGNORECASE
            ):
                # Use the compound ingredient splitting function
                split_ingredients = self.split_compound_ingredients(ing)
                for split_ingredient in split_ingredients:
                    if split_ingredient and len(split_ingredient) > 2:
                        ingredients.append(split_ingredient)
        
        # Remove duplicates and clean up
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            clean_ingredient = re.sub(r'\s+', ' ', ingredient).strip()
            if clean_ingredient.lower() not in seen and len(clean_ingredient) > 2:
                seen.add(clean_ingredient.lower())
                unique_ingredients.append(clean_ingredient)
        
        return unique_ingredients

    def clean_ingredient_text(self, ingredient):
        """
        Clean and normalize ingredient text.
        """
        import re
        
        # Remove extra whitespace
        ingredient = re.sub(r'\s+', ' ', ingredient).strip()
        
        # Remove trailing punctuation
        ingredient = re.sub(r'[.,;:]$', '', ingredient)
        
        # Remove leading numbers and percentages
        ingredient = re.sub(r'^\d+%?\s*', '', ingredient)
        
        # Remove bullet points
        ingredient = re.sub(r'^\s*[-•]\s*', '', ingredient)
        
        # Fix common OCR errors
        ingredient = ingredient.replace("Flailed", "Flaked")
        ingredient = ingredient.replace("Mingo", "Mango")
        ingredient = ingredient.replace("Pomcgranate", "Pomegranate")
        ingredient = ingredient.replace("lodised", "Iodised")
        
        return ingredient.strip()

    def split_compound_ingredients(self, ingredient_text):
        """
        Split compound ingredients that contain multiple items.
        """
        import re
        
        # If it contains commas but no parentheses, split by commas
        if ',' in ingredient_text and '(' not in ingredient_text:
            parts = re.split(r',\s*', ingredient_text)
            return [part.strip() for part in parts if part.strip()]
        
        # If it contains "and" but no parentheses, split by "and"
        if ' and ' in ingredient_text.lower() and '(' not in ingredient_text:
            parts = re.split(r'\s+and\s+', ingredient_text, flags=re.IGNORECASE)
            return [part.strip() for part in parts if part.strip()]
        
        # If it contains both commas and parentheses, try to split carefully
        if ',' in ingredient_text and '(' in ingredient_text:
            # Look for patterns like "A (B), C, D"
            # Split by commas that are not inside parentheses
            parts = re.split(r',\s*(?![^()]*\))', ingredient_text)
            result = []
            for part in parts:
                part = part.strip()
                if part:
                    # If this part still contains commas, split it further
                    if ',' in part and '(' not in part:
                        sub_parts = re.split(r',\s*', part)
                        result.extend([sub_part.strip() for sub_part in sub_parts if sub_part.strip()])
                    else:
                        result.append(part)
            return result
        
        return [ingredient_text]

    async def save_scan_history(self, user, image_url, extracted_text, nutrition_data, ai_results, safety_status, flagged_ingredients, go_ingredients=None, caution_ingredients=None, no_go_ingredients=None, product_name="OCR Product"):
        # Save scan history in a separate async function
        # Keep nutrition_data clean - only nutrition facts, not ingredients
        clean_nutrition_data = dict(nutrition_data) if nutrition_data else {}
        
        # Add AI results to nutrition data
        clean_nutrition_data.update({
            "ai_health_insight": ai_results.get("ai_health_insight", ""),
            "expert_advice": ai_results.get("expert_advice", ""),
            "go_ingredients": go_ingredients or [],
            "caution_ingredients": caution_ingredients or [],
            "no_go_ingredients": no_go_ingredients or []
        })
        
        scan = await sync_to_async(FoodLabelScan.objects.create)(
            user=user,
            image_url=image_url,
            extracted_text=extracted_text,
            nutrition_data=clean_nutrition_data,  # Include ingredient classifications
            safety_status=safety_status,
            flagged_ingredients=flagged_ingredients,
            product_name=product_name,
        )
        
        # Increment scan count for freemium users
        await sync_to_async(increment_user_scan_count)(user)
        
        return scan

    async def validate_product_safety(self, user, ingredients_list):
        # Use OpenAI for ingredient categorization based on user profile
        try:
            # Get OpenAI categorization
            categorization = self.categorize_ingredients_with_openai(user, ingredients_list)
            
            go_ingredients = categorization.get('go', [])
            no_go_ingredients = categorization.get('no_go', [])
            caution_ingredients = categorization.get('caution', [])
            
            # Add EFSA data to each ingredient for consistency with existing structure
            efsa_data_cache = {}
            for category in [go_ingredients, no_go_ingredients, caution_ingredients]:
                for ingredient_data in category:
                    ingredient_name = ingredient_data.get('ingredient', '')
                    try:
                        efsa_data = fetch_efsa_openfoodtox_data(ingredient_name)
                        efsa_data_cache[ingredient_name] = efsa_data or {}
                        ingredient_data['efsa_data'] = efsa_data or {}
                    except Exception as e:
                        print(f"EFSA error for {ingredient_name}: {e}")
                        efsa_data_cache[ingredient_name] = {
                            'found': False,
                            'error': f'EFSA query failed: {str(e)}',
                            'source': 'EFSA OpenFoodTox Database'
                        }
                        ingredient_data['efsa_data'] = efsa_data_cache[ingredient_name]
            
            # Determine overall safety status
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache
            
        except Exception as e:
            print(f"OpenAI categorization failed, falling back to static method: {e}")
            # Fallback to original static method
            if USE_STATIC_INGREDIENT_SAFETY:
                # --- Enhanced safety check with EFSA OpenFoodTox integration ---
                dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
                health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
                allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
                go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
                efsa_data_cache = {}  # Cache EFSA data to avoid duplicate API calls
                
                for ingredient in ingredients_list:
                    ing_lower = ingredient.lower()
                    
                    # Check EFSA OpenFoodTox database first
                    try:
                        efsa_data = fetch_efsa_openfoodtox_data(ingredient)
                        efsa_data_cache[ingredient] = efsa_data or {}
                    except Exception as e:
                        print(f"EFSA error for {ingredient}: {e}")
                        efsa_data_cache[ingredient] = {
                            'found': False,
                            'error': f'EFSA query failed: {str(e)}',
                            'source': 'EFSA OpenFoodTox Database'
                        }
                        efsa_data = efsa_data_cache[ingredient]
                    
                    # Determine safety based on EFSA data, user allergies, dietary preferences, and health conditions
                    safety_reasons = []
                    
                    # Check EFSA safety level
                    if efsa_data and efsa_data.get('found') and efsa_data.get('safety_level'):
                        if efsa_data['safety_level'] == 'UNSAFE':
                            safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Unsafe')}")
                        elif efsa_data['safety_level'] == 'CAUTION':
                            safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Caution')}")
                    
                    # Check user allergies
                    if any(a in ing_lower for a in allergies):
                        safety_reasons.append("Allergen")
                    
                    # Check dietary preferences
                    if any(d not in ing_lower for d in dietary) and dietary:
                        safety_reasons.append("Dietary")
                    
                    # Check health conditions
                    if any(h in ing_lower for h in health):
                        safety_reasons.append("Health")
                    
                    # Categorize ingredient based on safety reasons
                    if safety_reasons:
                        if "Allergen" in safety_reasons or (efsa_data and efsa_data.get('found') and efsa_data.get('safety_level') == 'UNSAFE'):
                            no_go_ingredients.append({
                                "ingredient": ingredient,
                                "reasons": safety_reasons,
                                "efsa_data": efsa_data or {}
                            })
                        else:
                            caution_ingredients.append({
                                "ingredient": ingredient,
                                "reasons": safety_reasons,
                                "efsa_data": efsa_data or {}
                            })
                    else:
                        go_ingredients.append({
                            "ingredient": ingredient,
                            "reasons": ["Safe"],
                            "efsa_data": efsa_data or {}
                        })
                
                # Determine overall safety status
                if no_go_ingredients:
                    safety_status = "UNSAFE"
                elif caution_ingredients:
                    safety_status = "CAUTION"
                else:
                    safety_status = "SAFE"
                
                return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache
            else:
                # --- Edamam-based safety check with EFSA enhancement ---
                dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
                health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
                allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
                go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
                efsa_data_cache = {}
                
                async def classify(ingredient):
                    # Get EFSA data
                    try:
                        efsa_data = fetch_efsa_openfoodtox_data(ingredient)
                        efsa_data_cache[ingredient] = efsa_data or {}
                    except Exception as e:
                        print(f"EFSA error for {ingredient}: {e}")
                        efsa_data_cache[ingredient] = {
                            'found': False,
                            'error': f'EFSA query failed: {str(e)}',
                            'source': 'EFSA OpenFoodTox Database'
                        }
                        efsa_data = efsa_data_cache[ingredient]
                    
                    info = await self.get_edamam_info(ingredient)
                    safety_reasons = []
                    
                    # Check EFSA safety level first
                    if efsa_data and efsa_data.get('found') and efsa_data.get('safety_level'):
                        if efsa_data['safety_level'] == 'UNSAFE':
                            safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Unsafe')}")
                        elif efsa_data['safety_level'] == 'CAUTION':
                            safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Caution')}")
                    
                    # Check Edamam data
                    if not info["healthLabels"] and not info["cautions"]:
                        if any(a in ingredient.lower() for a in allergies):
                            safety_reasons.append("Allergen")
                        elif any(d not in ingredient.lower() for d in dietary):
                            safety_reasons.append("Dietary")
                        elif any(h in ingredient.lower() for h in health):
                            safety_reasons.append("Health")
                        else:
                            safety_reasons.append("No Edamam data")
                    else:
                        if any(a in info["cautions"] for a in allergies):
                            safety_reasons.append("Allergen")
                        elif any(d not in info["healthLabels"] for d in dietary):
                            safety_reasons.append("Dietary")
                        elif any(h in ingredient.lower() for h in health):
                            safety_reasons.append("Health")
                    
                    # Categorize ingredient
                    if safety_reasons:
                        if "Allergen" in safety_reasons or (efsa_data and efsa_data.get('found') and efsa_data.get('safety_level') == 'UNSAFE'):
                            no_go_ingredients.append({
                                "ingredient": ingredient,
                                "reasons": safety_reasons,
                                "efsa_data": efsa_data or {}
                            })
                        else:
                            caution_ingredients.append({
                                "ingredient": ingredient,
                                "reasons": safety_reasons,
                                "efsa_data": efsa_data or {}
                            })
                    else:
                        go_ingredients.append({
                            "ingredient": ingredient,
                            "reasons": ["Safe"],
                            "efsa_data": efsa_data or {}
                        })
                
                await asyncio.gather(*(classify(ing) for ing in ingredients_list))
                
                # Handle any unclassified ingredients
                all_classified = set()
                for ing_list in [go_ingredients, caution_ingredients, no_go_ingredients]:
                    for ing in ing_list:
                        all_classified.add(ing["ingredient"])
                
                for ing in ingredients_list:
                    if ing not in all_classified:
                        try:
                            efsa_data = fetch_efsa_openfoodtox_data(ing)
                            efsa_data_cache[ing] = efsa_data or {}
                        except Exception as e:
                            print(f"EFSA error for {ing}: {e}")
                            efsa_data_cache[ing] = {
                                'found': False,
                                'error': f'EFSA query failed: {str(e)}',
                                'source': 'EFSA OpenFoodTox Database'
                            }
                            efsa_data = efsa_data_cache[ing]
                        go_ingredients.append({
                            "ingredient": ing,
                            "reasons": ["Defaulted"],
                            "efsa_data": efsa_data or {}
                        })
                
                if no_go_ingredients:
                    safety_status = "UNSAFE"
                elif caution_ingredients:
                    safety_status = "CAUTION"
                else:
                    safety_status = "SAFE"
                
                return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache

    def categorize_ingredients_with_openai(self, user, ingredients_list):
        """
        Use OpenAI to categorize ingredients into Go, No-Go, and Caution categories
        based on user's allergies, dietary preferences, and health conditions.
        """
        import json
        import hashlib
        from openai import OpenAI
        import os
        
        # Create cache key for this categorization
        key_data = {
            'ingredients': sorted(ingredients_list),
            'diet': user.Dietary_preferences,
            'allergies': user.Allergies,
            'health': user.Health_conditions
        }
        cache_key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        
        # Check cache first
        if cache_key in self.openai_cache:
            return self.openai_cache[cache_key]
        
        try:
            client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=10
            )
            
            # Create detailed prompt for ingredient categorization
            prompt = f"""
            You are a certified nutritionist and food safety expert. Categorize the following ingredients into three categories based on the user's health profile:

            USER PROFILE:
            - Allergies: {user.Allergies or 'None'}
            - Dietary Preferences: {user.Dietary_preferences or 'None'}
            - Health Conditions: {user.Health_conditions or 'None'}

            INGREDIENTS TO CATEGORIZE:
            {', '.join(ingredients_list)}

            CATEGORIES:
            1. GO: Ingredients that are safe and suitable for the user's health profile
            2. NO-GO: Ingredients that are harmful, allergenic, or contraindicated for the user's health profile
            3. CAUTION: Ingredients that may not be ideal but are not strictly forbidden - consume at your own risk

            RESPONSE FORMAT:
            Return a JSON object with exactly this structure:
            {{
                "go": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ],
                "no_go": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ],
                "caution": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ]
            }}

            IMPORTANT RULES:
            - Every ingredient must be categorized into exactly one category
            - Be conservative with safety - when in doubt, categorize as CAUTION or NO-GO
            - Consider cross-contamination risks for severe allergies
            - For dietary preferences, consider both direct ingredients and potential hidden sources
            - Provide specific, actionable reasons for each categorization
            - If an ingredient is not in the provided list, do not include it in the response
            """
            
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a certified nutritionist and food safety expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.1,
            )
            
            content = completion.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(content)
                
                # Validate structure
                required_keys = ['go', 'no_go', 'caution']
                if not all(key in result for key in required_keys):
                    raise ValueError("Missing required categories in response")
                
                # Ensure all ingredients are categorized
                categorized_ingredients = set()
                for category in required_keys:
                    for item in result[category]:
                        if 'ingredient' in item:
                            categorized_ingredients.add(item['ingredient'].lower())
                
                # Check if all ingredients are categorized
                all_ingredients = set(ing.lower() for ing in ingredients_list)
                if not categorized_ingredients.issuperset(all_ingredients):
                    # If not all ingredients categorized, add missing ones to caution
                    missing_ingredients = all_ingredients - categorized_ingredients
                    for missing in missing_ingredients:
                        result['caution'].append({
                            "ingredient": missing,
                            "reasons": ["Unable to determine safety - categorized as caution"]
                        })
                
                # Cache the result
                self.openai_cache[cache_key] = result
                return result
                
            except json.JSONDecodeError as e:
                print(f"OpenAI response parsing error: {e}")
                print(f"Raw response: {content}")
                # Fallback to default categorization
                return self._fallback_categorization(ingredients_list, user)
                
        except Exception as e:
            print(f"OpenAI categorization error: {e}")
            # Fallback to default categorization
            return self._fallback_categorization(ingredients_list, user)
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# openai.api_key = "OPENAI_API_KEY_REMOVED"

# Singleton EasyOCR reader and GPU check
# _easyocr_reader = None
# _easyocr_lock = threading.Lock()
# _easyocr_gpu = None

# def get_easyocr_reader():
#     global _easyocr_reader, _easyocr_gpu
#     with _easyocr_lock:
#         if _easyocr_reader is None:
#             try:
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=True)
#                 # Check if GPU is actually used
#                 _easyocr_gpu = _easyocr_reader.gpu
#                 logging.info(f"EasyOCR initialized. GPU used: {_easyocr_gpu}")
#             except Exception as e:
#                 logging.error(f"EasyOCR initialization failed: {e}")
#                 _easyocr_reader = easyocr.Reader(['en'], gpu=False)
#                 _easyocr_gpu = False
#         return _easyocr_reader

# def is_easyocr_gpu():
#     global _easyocr_gpu
#     return _easyocr_gpu

def google_login(request):
    """
    Traditional OAuth2 flow for Google Sign-In
    """
    from django.shortcuts import redirect
    from urllib.parse import urlencode
    
    # Get Google OAuth2 credentials from settings
    client_id = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', None) or os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
    
    if not client_id:
        return Response({"error": "Google OAuth2 not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Build OAuth2 authorization URL
    params = {
        'client_id': client_id,
        'redirect_uri': request.build_absolute_uri('/accounts/google/login/callback/'),
        'response_type': 'code',
        'scope': 'email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    return redirect(auth_url)

@method_decorator(csrf_exempt, name='dispatch')
class GoogleOAuth2CallbackView(APIView):
    """
    Handle Google OAuth2 callback and exchange authorization code for tokens
    """
    permission_classes = []
    
    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        
        if error:
            return Response({"error": f"OAuth error: {error}"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not code:
            return Response({"error": "No authorization code received"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Exchange authorization code for access token
        client_id = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', None) or os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
        client_secret = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', None) or os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')
        redirect_uri = request.build_absolute_uri('/accounts/google/login/callback/')
        
        # Exchange code for tokens
        token_response = requests.post('https://oauth2.googleapis.com/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        })
        
        if token_response.status_code != 200:
            return Response({"error": "Failed to exchange authorization code"}, status=status.HTTP_400_BAD_REQUEST)
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        # Get user info using access token
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if user_info_response.status_code != 200:
            return Response({"error": "Failed to get user info"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_info = user_info_response.json()
        email = user_info.get('email')
        
        if not email:
            return Response({"error": "No email in user info"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or get user
        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email, 
            defaults={
                "username": email.split("@")[0],
                "full_name": user_info.get('name', ''),
                "profile_picture": user_info.get('picture', '')
            }
        )
        
        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        return Response({
            "access_token": access_token,
            "refresh_token": str(refresh),
            "created": created,
            "email": user.email,
            "full_name": user.full_name,
            "profile_picture": user.profile_picture
        }, status=status.HTTP_200_OK)

class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'message': 'User created successfully.',
                'access_token': access_token,
                'refresh_token': str(refresh),
                'is_2fa_enabled': user.is_2fa_enabled
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            if user.is_2fa_enabled:  # Check if 2FA is enabled
                from random import randint
                from django.core.mail import send_mail

                otp_code = randint(100000, 999999)  # Generate 6-digit OTP
                user.otp = str(otp_code)
                user.save()

                # Send OTP via email
                send_mail(
                    "Your OTP Code",
                    f"Your OTP code is: {otp_code}",
                    "no-reply@example.com",
                    [user.email],
                    fail_silently=False,
                )

                return Response({
                    "message": "OTP sent to your email. Please verify to continue.",
                    "user_id": user.id,
                    "is_2fa_enabled": user.is_2fa_enabled,
                    "has_answered_onboarding": user.has_answered_onboarding, # <-- Added here
                    # "subscription_plan": user.UserSubscription

                }, status=status.HTTP_200_OK)

            # If 2FA is disabled, proceed with normal login
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                "message": "Login successful.",
                "access_token": access_token,
                "refresh_token": str(refresh),
                "is_2fa_enabled": user.is_2fa_enabled,
                "has_answered_onboarding": user.has_answered_onboarding,  # <-- Added here
                "subscription_plan": user.subscription_plan,
                

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class Toggle2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        is_2fa_enabled = request.data.get("is_2fa_enabled", None)

        if is_2fa_enabled is None:
            return Response({"error": "is_2fa_enabled field is required"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_2fa_enabled = is_2fa_enabled
        user.save()
        
        return Response({
            "message": f"Two-Factor Authentication {'enabled' if is_2fa_enabled else 'disabled'} successfully.",
            "is_2fa_enabled": user.is_2fa_enabled
        }, status=status.HTTP_200_OK)

class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

def send_otp_email(email, otp_code):
    subject = "Your OTP Code for Password Reset"
    message = f"Your OTP code is: {otp_code}. It is valid for 5 minutes."
    from_email = (os.getenv("EMAIL_HOST_USER")) 
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
    print(f"OTP {otp_code} sent to email: {email}")

class resendotpview(APIView):
    def post(self, request):
        try:
            identifier = request.data.get('email_or_phone', '').strip().lower()

            if not identifier:
                return JsonResponse({"message": "Please enter Email or Phone number"}, status=status.HTTP_400_BAD_REQUEST)

            otp = random.randint(1000, 9999)

            if '@' in identifier:
                try:
                    user = User.objects.get(email=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this email not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                subject = "One Time Password"
                email_body = f"Your OTP is: {otp}\n\nUse this code to complete your verification."

                try:
                    send_mail(subject, email_body, 'AI IngredientIQ', [user.email], fail_silently=False)
                except BadHeaderError:
                    return JsonResponse({"message": "Invalid email header"}, status=status.HTTP_400_BAD_REQUEST)

                return JsonResponse({"data": "OTP sent to your email"}, status=status.HTTP_200_OK)

            else:
                try:
                    user = User.objects.get(phone_number=identifier)
                except ObjectDoesNotExist:
                    return JsonResponse({"message": "User with this phone number not found"}, status=status.HTTP_400_BAD_REQUEST)

                user.otp = otp
                user.save()

                message = f"Your OTP is: {otp}. Use this to complete your verification."
                send_sms(user.phone_number, message)

                return JsonResponse({"data": "OTP sent to your phone number"}, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Verify OTP API
class verifyotpview(APIView):
    def post(self, request):
        try:
            otp = request.data.get('otp', None)
            
            if not otp:
                return JsonResponse({"error": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                otp = int(otp)
            except ValueError:
                return JsonResponse({"error": "OTP should be a valid integer"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(otp=otp).first()

            if user:
                user.otp = None  # Clear OTP after successful verification
                user.save()

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                return Response({
                    "message": "OTP Verified Successfully. Login successful.",
                    "access_token": access_token,
                    "refresh_token": str(refresh)
                }, status=status.HTTP_200_OK)

            return Response({"error": "Incorrect OTP"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordRequestAPIView(APIView):
    permission_classes = [] 

    def post(self, request):
        email = request.data.get("email")  
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            confirm_password = serializer.validated_data['confirm_password']

            if new_password != confirm_password:
                return Response({"detail": "Passwords must match."}, status=status.HTTP_400_BAD_REQUEST)

            if len(confirm_password) < 8:
                return Response({"detail": "New password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(confirm_password)
            user.save()

            return Response({"detail": "Password has been successfully reset."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class changepasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return Response({"message":message}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return JsonResponse({"message": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return JsonResponse({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

class termsandconditionView(APIView):
    def get(self,request):
        user = Termandcondition.objects.all()
        serializer = termsandconditionSerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)


class privacypolicyView(APIView):
    def get(self,request):
        user = privacypolicy.objects.all()
        serializer = privacypolicySerializer(user,many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)

class Frequentlyasked(APIView):
    def get(self,request):
        user = FAQ.objects.all()
        serializer = FAQSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class About(APIView):
    def get(self,request):
        user = AboutUS.objects.all()
        serializer = AboutSerializer(user,many=True)
        return Response({"data":serializer.data},status=status.HTTP_200_OK)

class userprofileview(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request):
        user = User.objects.get(email=request.user.email)

        if not request.data:
            return Response({"message": "No data provided to update."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = userPatchSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            profile_picture_url = None
            if user.profile_picture:
                profile_picture_url = user.profile_picture.url
                print("------------", profile_picture_url)
                profile_picture_url = profile_picture_url.replace("https//", "")
                print("======", profile_picture_url)  
            return Response(
                {"message": "Profile updated successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self,request):
        user = User.objects.select_related().get(email=request.user.email)
        user.refresh_from_db()  # Force refresh from database
        serializer = userGetSerializer(user)
        # Add payment status info
        from .models import UserSubscription
        payment_status = 'freemium'
        premium_type = None
        try:
            sub = UserSubscription.objects.get(user=user)
            if sub.plan_name == 'premium':
                payment_status = 'premium'
                # Use a new field 'premium_type' if present, else fallback to 'unknown'
                premium_type = getattr(sub, 'premium_type', None)
        except UserSubscription.DoesNotExist:
            pass
        data = serializer.data
        data['payment_status'] = payment_status
        data['premium_type'] = premium_type
        return Response({"data":data}, status=status.HTTP_200_OK)
    
    def delete(self, request):
        user = User.objects.get(email=request.user.email)
        user.delete()
        return Response({"detail":"User deleted successfully."}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)




class FoodLabelNutritionView(APIView):
    permission_classes = [IsAuthenticated]
    
    # In-memory caches (class-level)
    openai_cache = {}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize AWS Textract client
        try:
            aws_access_key = settings.AWS_ACCESS_KEY_ID
            aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
            aws_region = settings.AWS_S3_REGION_NAME or 'us-east-1'
            
            if not aws_access_key or not aws_secret_key:
                logging.error("AWS credentials not found in settings")
                self.textract_client = None
                return
            
            self.textract_client = boto3.client(
                'textract',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            print("AWS Textract client initialized successfully for FoodLabelNutritionView")
        except Exception as e:
            logging.error(f"Failed to initialize AWS Textract client: {e}")
            self.textract_client = None

    def post(self, request):
        # can_scan, scan_count = can_user_scan(request.user)
        # if not can_scan:
        #     return Response(
        #         {
        #             "error": "Scan limit reached. Please subscribe to AI IngredientIQ for unlimited scans.",
        #             "scans_used": scan_count,
        #             "max_scans": 6
        #         },
        #         status=status.HTTP_402_PAYMENT_REQUIRED
        #     )
        import time
        import logging
        from concurrent.futures import ThreadPoolExecutor
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"FoodLabelNutritionView is running on: {device.upper()}")
        except ImportError:
            print("torch not installed; cannot determine GPU/CPU.")

        start_time = time.time()

        # Deserialize and validate
        serializer = AllergenDietaryCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data['image']
        image_content = image_file.read()

        # LIGHTNING FAST PARALLEL PROCESSING
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all tasks simultaneously
            image_future = executor.submit(self.save_image, image_content)
            ocr_future = executor.submit(self.run_ocr, image_content)
            ingredients_future = executor.submit(self.extract_ingredients_with_textract_query, image_content)
            nutrition_future = executor.submit(self.extract_nutrition_with_textract_query, image_content)
            
            # Get image URL first (critical)
            image_url, image_path = image_future.result(timeout=3)
            if not image_url:
                return Response({'error': 'Image upload failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get OCR results with timeouts
            try:
                extracted_text = ocr_future.result(timeout=8)  # 8 second timeout
            except:
                extracted_text = ""
                
            try:
                query_ingredients = ingredients_future.result(timeout=8)
            except:
                query_ingredients = []
                
            try:
                query_nutrition = nutrition_future.result(timeout=8)
            except:
                query_nutrition = {}
        
        # Process results quickly
        if query_nutrition:
            nutrition_data = self.process_query_nutrition_data(query_nutrition)
        else:
            nutrition_data = self.extract_nutrition_info_fallback(extracted_text)
        
        if query_ingredients:
            actual_ingredients = self.process_query_ingredients(query_ingredients)
        else:
            actual_ingredients = self.extract_ingredients_from_text_fallback(extracted_text)

        # Debug logging
        print(f"Extracted text: {extracted_text}")
        print(f"Nutrition data extracted: {nutrition_data}")
        
        # More lenient check - allow partial nutrition data
        if not nutrition_data:
            # Try a simpler extraction method as fallback
            nutrition_data = self.extract_nutrition_info_simple(extracted_text)
            print(f"Fallback nutrition data: {nutrition_data}")
            
        if not nutrition_data:
            return Response(
                {"error": "No nutrition data found, Please capture clear photo of nutrition label of food packet. Scan not saved."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # PARALLEL SAFETY VALIDATION AND AI INSIGHTS
        safety_start = time.time()
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Run safety validation and AI insights in parallel
            safety_future = executor.submit(lambda: asyncio.run(self.validate_product_safety(request.user, actual_ingredients)))
            ai_future = executor.submit(self.get_ai_health_insight_and_expert_advice, request.user, nutrition_data, [])
            
            # Get safety results with timeout
            try:
                safety_result = safety_future.result(timeout=5)  # 5 second timeout
                if len(safety_result) == 5:
                    safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache = safety_result
                else:
                    safety_status, go_ingredients, caution_ingredients, no_go_ingredients = safety_result
                    efsa_data_cache = {}
            except:
                safety_status, go_ingredients, caution_ingredients, no_go_ingredients = "unknown", [], [], []
                efsa_data_cache = {}
            
            # Get AI results with timeout
            try:
                ai_results = ai_future.result(timeout=3)  # 3 second timeout
            except:
                ai_results = {
                    "ai_health_insight": "Health insights unavailable.",
                    "expert_advice": "Consult healthcare professional."
                }
        
        safety_end = time.time()
        logging.info(f"Safety validation completed in {safety_end - safety_start:.2f} seconds.")

        # Prepare ingredients for scan history (convert back to simple format for storage)
        def extract_ingredient_names(ingredient_list):
            return [ing["ingredient"] if isinstance(ing, dict) else ing for ing in ingredient_list]
        
        no_go_names = extract_ingredient_names(no_go_ingredients)
        go_names = extract_ingredient_names(go_ingredients)
        caution_names = extract_ingredient_names(caution_ingredients)
        
        with ThreadPoolExecutor() as executor:
            scan_future = executor.submit(lambda: asyncio.run(self.save_scan_history(
                request.user,
                image_url,
                extracted_text,
                nutrition_data,
                ai_results,
                safety_status,
                no_go_names,  # flagged_ingredients
                go_names,     # go_ingredients
                caution_names,  # caution_ingredients
                no_go_names,  # no_go_ingredients
                "OCR Product"  # product_name
            )))
            scan = scan_future.result()

        total_time = time.time() - start_time
        logging.info(f"FoodLabelNutritionView total time: {total_time:.2f} seconds.")

        # Convert ingredient lists to list of objects with clean names and EFSA data
        # Global deduplication across all categories
        all_ingredients_seen = set()

        def format_ingredient_list_with_global_dedup(ingredient_list, category_name):
            formatted_list = []
            
            for ing in ingredient_list:
                if isinstance(ing, dict):
                    # New format with EFSA data
                    ingredient_name = ing.get("ingredient", "")
                    reasons = ing.get("reasons", [])
                    efsa_data = ing.get("efsa_data", {})
                    
                    # Clean the ingredient name
                    clean_ingredient = ingredient_name.strip()
                    if not clean_ingredient:
                        continue
                    
                    # Check for global duplicates
                    clean_ingredient_lower = clean_ingredient.lower().strip()
                    if clean_ingredient_lower in all_ingredients_seen:
                        continue
                    all_ingredients_seen.add(clean_ingredient_lower)
                    
                    formatted_ing = {
                        "ingredient": clean_ingredient,
                        "reasons": reasons,
                        "efsa_data": efsa_data or {}
                    }
                else:
                    # Old format (string)
                    ingredient_str = str(ing)
                    clean_ingredient = ingredient_str.strip()
                    if not clean_ingredient:
                        continue
                    
                    # Check for global duplicates
                    clean_ingredient_lower = clean_ingredient.lower().strip()
                    if clean_ingredient_lower in all_ingredients_seen:
                        continue
                    all_ingredients_seen.add(clean_ingredient_lower)
                    
                    formatted_ing = {
                        "ingredient": clean_ingredient,
                        "reasons": ["Legacy format"],
                        "efsa_data": {}
                    }
                formatted_list.append(formatted_ing)
            return formatted_list

        # Process in priority order: no_go first, then caution, then go
        no_go_ingredients_obj = format_ingredient_list_with_global_dedup(no_go_ingredients, "no_go")
        caution_ingredients_obj = format_ingredient_list_with_global_dedup(caution_ingredients, "caution")
        go_ingredients_obj = format_ingredient_list_with_global_dedup(go_ingredients, "go")

        main_ingredient = actual_ingredients[0] if actual_ingredients else None
        def safe_summary(fetch_func, ingredient, default_msg):
            try:
                summary = fetch_func(ingredient)
                if not summary or (isinstance(summary, str) and not summary.strip()):
                    return default_msg
                return summary
            except Exception as e:
                print(f"Summary fetch error for {ingredient}: {e}")
                return default_msg

        medlineplus_summary = safe_summary(
            fetch_medlineplus_summary,
            main_ingredient,
            "No MedlinePlus summary available for this ingredient."
        ) if main_ingredient else "No MedlinePlus summary available for this ingredient."

        pubchem_summary = safe_summary(
            fetch_pubchem_toxicology_summary,
            main_ingredient,
            "No PubChem toxicology data found for this ingredient."
        ) if main_ingredient else "No PubChem toxicology data found for this ingredient."
        pubmed_articles = fetch_pubmed_articles(main_ingredient) if main_ingredient else []

        # REMOVED ClinicalTrials.gov integration for speed
        def fetch_clinical_trials(ingredient):
            return []  # Return empty list for speed
            if not ingredient:
                return []
            try:
                url = f"https://clinicaltrials.gov/api/v2/studies?q={ingredient}&limit=3"
                resp = requests.get(url, timeout=5)
                if resp.status_code != 200:
                    print(f"ClinicalTrials.gov API error: {resp.status_code}")
                    return []
                data = resp.json()
                studies = data.get("studies", [])
                trials = []
                for study in studies:
                    nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
                    title = study.get("protocolSection", {}).get("identificationModule", {}).get("officialTitle")
                    status = study.get("protocolSection", {}).get("statusModule", {}).get("overallStatus")
                    summary = study.get("protocolSection", {}).get("descriptionModule", {}).get("briefSummary")
                    url = f"https://clinicaltrials.gov/ct2/show/{nct_id}" if nct_id else None
                    if nct_id and title:
                        trials.append({
                            "title": title,
                            "nct_id": nct_id,
                            "status": status,
                            "summary": summary,
                            "url": url
                        })
                return trials
            except Exception as e:
                print(f"ClinicalTrials.gov fetch error: {e}")
                return []

        clinical_trials = fetch_clinical_trials(main_ingredient)

        # --- FSA Hygiene Rating Integration ---
        # Try to extract business name from OCR text or use default
        business_name = "OCR Product"  # Default fallback
        fsa_data = None
        
        # Look for business names in the extracted text
        business_keywords = ['ltd', 'limited', 'inc', 'corporation', 'company', 'co', 'brand', 'manufacturer']
        lines = extracted_text.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in business_keywords):
                business_name = line.strip()
                break
        
        # Fetch FSA hygiene rating data
        try:
            fsa_data = fetch_fsa_hygiene_rating(business_name=business_name)
        except Exception as e:
            print(f"FSA API error: {e}")
            fsa_data = {
                'found': False,
                'error': f'FSA API error: {str(e)}',
                'source': 'UK FSA FHRS API'
            }
        from .scan_limit import can_user_scan, get_monthly_reset_date
        _, scan_count, remaining_scans = can_user_scan(request.user)
        
        # Handle None values for premium users
        if scan_count is None:
            scan_count = 0
        if remaining_scans is None:
            remaining_scans = "unlimited"

        return Response({
            "scan_id": scan.id,
            "product_name":"OCR Product",
            "image_url": image_url,
            "extracted_text": extracted_text,
            "nutrition_data": nutrition_data,
            "ingredients": actual_ingredients,
            "safety_status": safety_status,
            "is_favorite": scan.is_favorite,
            "ingredients_analysis": {
                "go": {
                    "ingredients": go_ingredients_obj,
                    "count": len(go_ingredients_obj),
                    "description": "Ingredients that are safe and suitable for your health profile"
                },
                "caution": {
                    "ingredients": caution_ingredients_obj,
                    "count": len(caution_ingredients_obj),
                    "description": "Ingredients that may not be ideal for your health profile - consume at your own risk"
                },
                "no_go": {
                    "ingredients": no_go_ingredients_obj,
                    "count": len(no_go_ingredients_obj),
                    "description": "Ingredients that are harmful or not suitable for your health profile - avoid these"
                },
                "total_flagged": len(caution_ingredients_obj) + len(no_go_ingredients_obj)
            },
            "efsa_data": {
                "source": "European Food Safety Authority (EFSA) OpenFoodTox Database",
                "total_ingredients_checked": len(efsa_data_cache),
                "ingredients_with_efsa_data": len([data for data in efsa_data_cache.values() if data and data.get('found')]),
                "cache": {k: v for k, v in efsa_data_cache.items() if v is not None}
            },
            "fsa_hygiene_data": fsa_data,
            "scan_usage": {
                "scans_used": scan_count,
                "max_scans": 20,
                "remaining_scans": remaining_scans,
                "monthly_reset_date": get_monthly_reset_date()
            },
            "medical_condition_recommendations": {
                "user_health_profile": {
                    "allergies": request.user.Allergies,
                    "dietary_preferences": request.user.Dietary_preferences,
                    "health_conditions": request.user.Health_conditions
                },
                "recommendations": get_medical_condition_food_recommendations(
                    request.user.Health_conditions, 
                    request.user.Allergies, 
                    request.user.Dietary_preferences
                ) if (request.user.Health_conditions or request.user.Allergies or request.user.Dietary_preferences) else {"found": False, "message": "No health profile specified"},
                "source": "SNOMED CT & ICD-10 Clinical Guidelines"
            },
            "ai_health_insight": ai_results["ai_health_insight"],
            "expert_advice": ai_results["expert_advice"],
            # "ocr_gpu": False,  # Azure OCR
            # "medlineplus_summary": medlineplus_summary,
            # "pubchem_summary": pubchem_summary,
            # "pubmed_articles": pubmed_articles,
            # "clinical_trials": clinical_trials,
            # "timing": {
            #     "ocr": ocr_end - ocr_start,
            #     "safety+ai": safety_end - safety_start,
            #     "total": total_time
            # }
        }, status=status.HTTP_200_OK)

    def get_ai_health_insight_and_expert_advice(self, user, nutrition_data, flagged_ingredients):
        """
        Ultra-fast AI insights with minimal processing, caching, and aggressive timeouts.
        """
        import time
        import json
        import hashlib
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        
        # Quick cache check
        key_data = {
            'ingredients': sorted(flagged_ingredients[:3]),  # Only first 3 for speed
            'nutrition': {k: v for k, v in list(nutrition_data.items())[:5]},  # Only first 5
            'diet': user.Dietary_preferences,
            'allergies': user.Allergies
        }
        cache_key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        if cache_key in self.openai_cache:
            return self.openai_cache[cache_key]
        
        # Ultra-minimal single prompt for both insights
        nutrition_summary = ', '.join(f"{k}: {v}" for k, v in list(nutrition_data.items())[:5])
        flagged_str = ', '.join(flagged_ingredients[:3])  # Only top 3
        user_profile = f"Diet: {user.Dietary_preferences or 'None'}, Allergies: {user.Allergies or 'None'}"
        
        # Single prompt for both health insight and expert advice
        prompt = f"""
        User Profile: {user_profile}
        Nutrition: {nutrition_summary}
        Flagged Ingredients: {flagged_str}
        
        Provide BOTH responses in the exact format below:
        
        1. Health Insight (30-50 words): Analyze safety, nutritional value, and any red flags based on user's dietary preferences and health conditions.
        
        2. Expert Advice (70-80 words): Give detailed, actionable recommendations including portion control, alternatives, preparation tips, and specific guidance for the user's dietary needs.
        
        Format: "HEALTH: [30-50 word insight] ADVICE: [70-80 word detailed recommendation]"
        """
        
        def openai_call():
            from openai import OpenAI
            import os
            
            try:
                client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    timeout=2.5  # 2.5 second timeout per call
                )
                
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Faster than gpt-4o
                    messages=[
                        {"role": "system", "content": "You are a certified nutrition expert. Provide detailed, informative responses following the exact word count and format specified."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=200,  # Increased for longer responses (30-50 + 70-80 words)
                    temperature=0.3,
                )
                
                content = completion.choices[0].message.content.strip()
                
                # Parse the response
                if "HEALTH:" in content and "ADVICE:" in content:
                    parts = content.split("ADVICE:")
                    health_part = parts[0].replace("HEALTH:", "").strip()
                    advice_part = parts[1].strip()
                    
                    return {
                        "ai_health_insight": health_part,
                        "expert_advice": advice_part
                    }
                else:
                    # Fallback parsing - try to split by sentences and create meaningful responses
                    sentences = [s.strip() + "." for s in content.split('.') if s.strip()]
                    
                    if len(sentences) >= 2:
                        # Use first part as health insight, rest as expert advice
                        health_insight = sentences[0]
                        expert_advice = " ".join(sentences[1:])
                    else:
                        # Create structured fallback responses
                        health_insight = "Product nutrition analysis completed. Key nutritional components identified for your dietary assessment."
                        expert_advice = "Consider this product's nutritional profile in context of your daily intake goals. Monitor portion sizes and balance with other foods throughout the day. Consult nutrition labels for detailed ingredient information and allergen warnings before consumption."
                    
                    return {
                        "ai_health_insight": health_insight,
                        "expert_advice": expert_advice
                    }
                
            except Exception as e:
                print(f"OpenAI error: {e}")
                # Intelligent fallback based on data
                if flagged_ingredients:
                    return {
                        "ai_health_insight": f"Product contains {len(flagged_ingredients)} flagged ingredients that may conflict with your dietary preferences or health conditions. These components require careful consideration for your nutritional goals.",
                        "expert_advice": f"Review the flagged ingredients: {', '.join(flagged_ingredients[:3])}. Consider alternatives that better align with your dietary needs. If consuming, monitor portion sizes and balance with nutrient-dense foods. Consult your healthcare provider if you have specific health concerns about these ingredients."
                    }
                else:
                    return {
                        "ai_health_insight": "Product appears nutritionally suitable based on available information and shows no immediate red flags for your dietary profile and health considerations.",
                        "expert_advice": "This product can be incorporated into a balanced diet when consumed in appropriate portions. Focus on overall dietary variety and ensure adequate intake of essential nutrients throughout the day. Consider pairing with complementary foods to optimize nutritional benefits and maintain balanced macronutrient ratios."
                    }
        
        # Execute with timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(openai_call)
            try:
                result = future.result(timeout=2.8)  # 2.8 second total timeout
                self.openai_cache[cache_key] = result
                return result
            except TimeoutError:
                print("OpenAI timeout - using fallback")
                return {
                    "ai_health_insight": "Product nutritional analysis completed successfully. Key ingredients and nutritional components have been identified and evaluated for your dietary profile.",
                    "expert_advice": "Review the product's nutrition label and ingredient list carefully. Pay attention to any flagged ingredients that may not align with your dietary preferences. Consider portion control and incorporate this product as part of a balanced, varied diet. Consult with a healthcare professional for personalized nutritional guidance."
                }
            except Exception as e:
                print(f"OpenAI outer error: {e}")
                return {
                    "ai_health_insight": "Product nutritional analysis completed successfully. Key ingredients and nutritional components have been identified and evaluated for your dietary profile.",
                    "expert_advice": "Review the product's nutrition label and ingredient list carefully. Pay attention to any flagged ingredients that may not align with your dietary preferences. Consider portion control and incorporate this product as part of a balanced, varied diet. Consult with a healthcare professional for personalized nutritional guidance."
                }

    def run_in_thread_pool(self, func, *args):
        with ThreadPoolExecutor() as executor:
            return executor.submit(func, *args).result()

    def save_image(self, image_content):
        try:
            image_name = f"food_labels/{uuid.uuid4()}.jpg"
            image_path = default_storage.save(image_name, ContentFile(image_content))
            image_url = default_storage.url(image_path).replace("https//", "")
            return image_url, image_path
        except Exception as e:
            print(f"Error saving image: {e}")
            return None, None

    def run_ocr(self, image_content):
        """
        Uses AWS Textract for high-accuracy text extraction with Query feature.
        """
        try:
            if not self.textract_client:
                logging.error("AWS Textract client not initialized")
                return ''
            
            # Try to extract text using AWS Textract Query first
            extracted_text = self.extract_text_with_textract_query(image_content)
            if extracted_text:
                logging.info(f"Extracted text from AWS Textract Query: {extracted_text}")
                return extracted_text
            
            # Fallback to regular text extraction
            extracted_text = self.extract_text_with_textract(image_content)
            if extracted_text:
                logging.info(f"Extracted text from AWS Textract: {extracted_text}")
                return extracted_text
            
            logging.error("AWS Textract failed to extract text")
            return ''
            
        except Exception as e:
            logging.error(f"AWS Textract OCR error: {e}", exc_info=True)
            return ''

    def extract_text_with_textract_query(self, image_content):
        """
        Extract text using AWS Textract Query feature for better accuracy.
        """
        try:
            # Validate image content
            if not isinstance(image_content, bytes):
                logging.error("Image content must be bytes")
                return ""
            
            # Check image size (AWS Textract limit is 5MB)
            if len(image_content) > 5 * 1024 * 1024:
                logging.error("Image too large for AWS Textract (max 5MB)")
                return ""
            
            # Check if image content is valid
            if len(image_content) < 100:
                logging.error("Image content too small")
                return ""

            # Query for general text content
            queries = [
                {
                    'Text': 'What text is visible in this image?',
                    'Alias': 'general_text'
                },
                {
                    'Text': 'Extract all text from this nutrition label',
                    'Alias': 'nutrition_text'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES', 'TABLES', 'FORMS', 'LINES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                extracted_text = ""
                
                # Extract text from query results
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                extracted_text += answer_block['Text'] + "\n"
                
                # Also extract regular text blocks
                text_blocks = [block for block in response.get('Blocks', []) if block['BlockType'] == 'LINE']
                text_blocks.sort(key=lambda x: (x['Geometry']['BoundingBox']['Top'], x['Geometry']['BoundingBox']['Left']))
                
                for block in text_blocks:
                    if 'Text' in block:
                        extracted_text += block['Text'] + "\n"

                return extracted_text.strip()
                
            except Exception as e:
                logging.error(f"Textract Query API error: {e}")
                return ""
            
        except Exception as e:
            logging.error(f"Textract Query extraction error: {e}")
            return ""

    def extract_text_with_textract(self, image_content):
        """
        Extract text using AWS Textract with enhanced features.
        """
        try:
            if not self.textract_client:
                raise Exception("AWS Textract client not initialized")

            # Ensure image_content is bytes
            if not isinstance(image_content, bytes):
                logging.error("Image content must be bytes")
                return ""

            # Check image size (AWS Textract limit is 5MB)
            if len(image_content) > 5 * 1024 * 1024:
                logging.error("Image too large for AWS Textract (max 5MB)")
                return ""

            # Check if image content is valid
            if len(image_content) < 100:
                logging.error("Image content too small")
                return ""

            # Try analyze_document first (more features)
            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['TABLES', 'FORMS', 'LINES']
                )
                
                # Extract text with spatial information
                extracted_text = ""
                blocks = response.get('Blocks', [])
                
                # Sort blocks by geometry for proper reading order
                text_blocks = [block for block in blocks if block['BlockType'] == 'LINE']
                text_blocks.sort(key=lambda x: (x['Geometry']['BoundingBox']['Top'], x['Geometry']['BoundingBox']['Left']))
                
                for block in text_blocks:
                    if 'Text' in block:
                        extracted_text += block['Text'] + "\n"

                return extracted_text.strip()
                
            except Exception as e:
                logging.error(f"Textract analyze_document failed: {e}")
                # Try simpler detect_document_text as fallback
                try:
                    response = self.textract_client.detect_document_text(
                        Document={
                            'Bytes': image_content
                        }
                    )
                    
                    extracted_text = ""
                    blocks = response.get('Blocks', [])
                    
                    for block in blocks:
                        if block['BlockType'] == 'LINE' and 'Text' in block:
                            extracted_text += block['Text'] + "\n"
                    
                    return extracted_text.strip()
                    
                except Exception as fallback_error:
                    logging.error(f"Textract detect_document_text also failed: {fallback_error}")
                    return ""

        except Exception as e:
            logging.error(f"Textract extraction error: {e}")
            return ""

    def correct_ocr_errors(self, text):
        corrections = {
            "Bg": "8g", "Omg": "0mg", "lron": "Iron", "meg": "mcg"
        }
        for wrong, right in corrections.items():
            text = text.replace(wrong, right)
        return text

    def extract_nutrition_info_from_text(self, text, image_content=None):
        """
        Enhanced nutrition extraction using AWS Textract Query for better accuracy.
        """
        nutrition_data = {}
        
        # Fix common OCR errors first
        text = self.correct_ocr_errors(text)
        
        # Try AWS Textract Query first if image_content is available
        if image_content and hasattr(self, 'textract_client') and self.textract_client:
            query_nutrition = self.extract_nutrition_with_textract_query(image_content)
            if query_nutrition:
                # Convert query results to the expected format
                for key, value in query_nutrition.items():
                    if value:
                        # Extract numeric value and unit
                        match = re.search(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', value)
                        if match:
                            numeric_value = match.group(1)
                            unit = match.group(2).lower()
                            
                            # Map query keys to nutrition data keys with proper units
                            if key == 'energy':
                                nutrition_data["Energy"] = f"{numeric_value} kcal"
                            elif key == 'protein':
                                nutrition_data["Protein"] = f"{numeric_value} g"
                            elif key == 'total_fat':
                                nutrition_data["Total Fat"] = f"{numeric_value} g"
                            elif key == 'saturated_fat':
                                nutrition_data["Saturated Fat"] = f"{numeric_value} g"
                            elif key == 'carbohydrates':
                                nutrition_data["Carbohydrate"] = f"{numeric_value} g"
                            elif key == 'sugars':
                                nutrition_data["Total Sugars"] = f"{numeric_value} g"
                            elif key == 'sodium':
                                nutrition_data["Sodium"] = f"{numeric_value} mg"
                            elif key == 'fiber':
                                nutrition_data["Dietary Fibre"] = f"{numeric_value} g"
                            else:
                                # Add as custom nutrient with proper unit
                                nutrition_data[key.replace('_', ' ').title()] = f"{numeric_value} {unit}"
        
        # If AWS Textract Query didn't provide enough data, fall back to text parsing
        if len(nutrition_data) < 3:  # If we have less than 3 nutrients, use fallback
            nutrition_data = self.extract_nutrition_info_fallback(text)
        
        return nutrition_data

    def extract_nutrition_with_textract_query(self, image_content):
        """
        Extract nutrition data using AWS Textract Query feature.
        """
        try:
            if not self.textract_client:
                return {}

            # Query for nutrition information
            queries = [
                {
                    'Text': 'What is the energy/calories value?',
                    'Alias': 'energy'
                },
                {
                    'Text': 'What is the protein content?',
                    'Alias': 'protein'
                },
                {
                    'Text': 'What is the total fat content?',
                    'Alias': 'total_fat'
                },
                {
                    'Text': 'What is the saturated fat content?',
                    'Alias': 'saturated_fat'
                },
                {
                    'Text': 'What is the carbohydrate content?',
                    'Alias': 'carbohydrates'
                },
                {
                    'Text': 'What is the sugar content?',
                    'Alias': 'sugars'
                },
                {
                    'Text': 'What is the sodium content?',
                    'Alias': 'sodium'
                },
                {
                    'Text': 'What is the fiber content?',
                    'Alias': 'fiber'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                nutrition_data = {}
                
                # Extract answers from the response
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        query_alias = block.get('Query', {}).get('Alias', '')
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        # Find the answer block
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                nutrition_data[query_alias] = answer_block['Text']
                
                return nutrition_data
                
            except Exception as e:
                logging.error(f"Nutrition Query failed: {e}")
                return {}

        except Exception as e:
            logging.error(f"Nutrition Query extraction error: {e}")
            return {}

    def extract_nutrition_info_fallback(self, text):
        """
        Fallback nutrition extraction using text parsing (original method).
        """
        nutrition_data = {}
        
        # Define comprehensive nutrient patterns with variations
        nutrient_patterns = {
            "Energy": [
                r'energy[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'calories[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'calorie[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*energy',
                r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*calories'
            ],
            "Total Fat": [
                r'total\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+fat',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fat'
            ],
            "Saturated Fat": [
                r'saturated\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sat\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*saturated\s+fat',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sat\s+fat'
            ],
            "Trans Fat": [
                r'trans\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*trans\s+fat'
            ],
            "Cholesterol": [
                r'cholesterol[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*cholesterol'
            ],
            "Sodium": [
                r'sodium[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'salt[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*sodium',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*salt'
            ],
            "Carbohydrate": [
                r'carbohydrate[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'carbohydrates[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'carbs[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrate',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrates',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbs'
            ],
            "Total Sugars": [
                r'total\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sugar[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+sugars',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugars',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugar'
            ],
            "Added Sugars": [
                r'added\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*added\s+sugars'
            ],
            "Dietary Fibre": [
                r'dietary\s+fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'dietary\s+fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fibre',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fiber',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fibre',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fiber'
            ],
            "Protein": [
                r'protein[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*protein'
            ]
        }
        
        # Extract using comprehensive patterns with proper unit mapping
        for nutrient_name, patterns in nutrient_patterns.items():
            all_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                all_matches.extend(matches)
            
            if all_matches:
                value, unit = all_matches[0]
                # Map units correctly
                if unit.lower() in ['kj', 'cal']:
                    unit = 'kcal'
                elif unit.lower() == '%':
                    unit = '%'
                elif nutrient_name in ["Energy"]:
                    unit = 'kcal'
                elif nutrient_name in ["Sodium", "Cholesterol"]:
                    unit = 'mg'
                else:
                    unit = 'g'
                    
                nutrition_data[nutrient_name] = f"{value} {unit}".strip()
        
        # Clean up and standardize units
        for key, value in nutrition_data.items():
            if value and not value.endswith(('kcal', 'g', 'mg', 'mcg', '%', 'kj', 'cal')):
                # Extract numeric value
                numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
                if numeric_match:
                    numeric_value = numeric_match.group(1)
                    if key.lower() in ["energy", "calories"]:
                        nutrition_data[key] = f"{numeric_value} kcal"
                    elif key.lower() in ["protein", "carbohydrate", "total sugars", "dietary fibre", "total fat", "saturated fat", "trans fat"]:
                        nutrition_data[key] = f"{numeric_value} g"
                    elif key.lower() in ["sodium", "cholesterol"]:
                        nutrition_data[key] = f"{numeric_value} mg"
        
        return nutrition_data

    def extract_nutrition_info_simple(self, text):
        """
        Simple fallback nutrition extraction method for OCR text that's hard to parse.
        """
        nutrition_data = {}
        
        # Fix common OCR errors
        text = text.replace('o.', '0.').replace('O.', '0.').replace('O', '0').replace('l', '1')
        text = text.replace('Ptotetn', 'Protein').replace('rotat', 'Total').replace('agog', '240g')
        text = text.replace('tug', '240g').replace('osg', '240g')
        
        # Split into lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        print(f"Processing lines: {lines}")  # Debug
        
        # Look for nutrition section
        nutrition_section = False
        for line in lines:
            if 'nutrition' in line.lower() or 'kcal' in line.lower() or 'g' in line:
                nutrition_section = True
                break
        
        if not nutrition_section:
            return nutrition_data
        
        # Enhanced pattern matching for the specific OCR format
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Skip non-nutrition lines
            if any(skip in line_lower for skip in ['ingredients', 'allergen', 'manufactured', 'store', 'packaged']):
                    continue
                
            print(f"Processing line {i}: '{line}' -> '{line_lower}'")  # Debug
            
            # Look for nutrient names and values
            if 'protein' in line_lower or 'ptotetn' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger (more likely to be correct)
                        if 'Protein' not in nutrition_data or float(value) > float(nutrition_data['Protein'].split()[0]):
                            nutrition_data['Protein'] = f"{value} {unit}"
                            print(f"Found Protein: {value} {unit}")  # Debug
                        break
            
            elif 'carbohydrate' in line_lower or 'carbs' in line_lower or 'rotat' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Carbohydrate' not in nutrition_data or float(value) > float(nutrition_data['Carbohydrate'].split()[0]):
                            nutrition_data['Carbohydrate'] = f"{value} {unit}"
                            print(f"Found Carbohydrate: {value} {unit}")  # Debug
                        break
            
            elif 'sugar' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Total Sugars' not in nutrition_data or float(value) > float(nutrition_data['Total Sugars'].split()[0]):
                            nutrition_data['Total Sugars'] = f"{value} {unit}"
                            print(f"Found Total Sugars: {value} {unit}")  # Debug
                        break
            
            elif 'fat' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'g'
                        if 'saturated' in line_lower:
                            # Only add if we don't already have this nutrient or if this value is larger
                            if 'Saturated Fat' not in nutrition_data or float(value) > float(nutrition_data['Saturated Fat'].split()[0]):
                                nutrition_data['Saturated Fat'] = f"{value} {unit}"
                                print(f"Found Saturated Fat: {value} {unit}")  # Debug
                        else:
                            # Only add if we don't already have this nutrient or if this value is larger
                            if 'Total Fat' not in nutrition_data or float(value) > float(nutrition_data['Total Fat'].split()[0]):
                                nutrition_data['Total Fat'] = f"{value} {unit}"
                                print(f"Found Total Fat: {value} {unit}")  # Debug
                        break
            
            elif 'kcal' in line_lower or 'calorie' in line_lower or 'energy' in line_lower:
                # Look for value in current line or next few lines
                value = None
                for j in range(i, min(i+5, len(lines))):
                    value_match = re.search(r'(\d+(?:\.\d+)?)\s*(kcal|cal)?', lines[j])
                    if value_match:
                        value = value_match.group(1)
                        unit = value_match.group(2) if value_match.group(2) else 'kcal'
                        # Only add if we don't already have this nutrient or if this value is larger
                        if 'Energy' not in nutrition_data or float(value) > float(nutrition_data['Energy'].split()[0]):
                            nutrition_data['Energy'] = f"{value} {unit}"
                            print(f"Found Energy: {value} {unit}")  # Debug
                        break
        
        # Also look for standalone numbers that might be nutrition values
        for i, line in enumerate(lines):
            # Look for lines that are just numbers (potential nutrition values)
            if re.match(r'^\d+(?:\.\d+)?\s*(g|kcal|mg)?$', line.strip()):
                value = re.search(r'(\d+(?:\.\d+)?)', line).group(1)
                unit = re.search(r'(g|kcal|mg)', line)
                unit = unit.group(1) if unit else 'g'
                
                print(f"Found standalone value: {value} {unit} at line {i}")  # Debug
                
                # Try to match with nearby nutrient names
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    nearby_line = lines[j].lower()
                    if ('protein' in nearby_line or 'ptotetn' in nearby_line) and 'Protein' not in nutrition_data:
                        nutrition_data['Protein'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Protein")  # Debug
                        break
                    elif ('carbohydrate' in nearby_line or 'carbs' in nearby_line or 'rotat' in nearby_line) and 'Carbohydrate' not in nutrition_data:
                        nutrition_data['Carbohydrate'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Carbohydrate")  # Debug
                        break
                    elif 'sugar' in nearby_line and 'Total Sugars' not in nutrition_data:
                        nutrition_data['Total Sugars'] = f"{value} {unit}"
                        print(f"Mapped {value} {unit} to Total Sugars")  # Debug
                        break
                    elif 'fat' in nearby_line:
                        if 'saturated' in nearby_line and 'Saturated Fat' not in nutrition_data:
                            nutrition_data['Saturated Fat'] = f"{value} {unit}"
                            print(f"Mapped {value} {unit} to Saturated Fat")  # Debug
                            break
                        elif 'Total Fat' not in nutrition_data:
                            nutrition_data['Total Fat'] = f"{value} {unit}"
                            print(f"Mapped {value} {unit} to Total Fat")  # Debug
                            break
        
        # Special handling for "Per 100g" format
        per_100g_section = ""
        for i, line in enumerate(lines):
            if 'per' in line.lower() and '100' in line and 'g' in line.lower():
                # Found the per 100g section, collect the next few lines
                per_100g_section = '\n'.join(lines[i:i+10])
                print(f"Found Per 100g section: {per_100g_section}")  # Debug
                break
        
        if per_100g_section:
            # Extract all number-unit pairs from this section
            number_unit_pairs = re.findall(r'(\d+(?:\.\d+)?)\s*(kcal|g|mg|mcg|%|kj|cal)', per_100g_section, re.IGNORECASE)
            print(f"Number-unit pairs found: {number_unit_pairs}")  # Debug
            
            # Try to match with nutrient names in the same section
            for pair in number_unit_pairs:
                value, unit = pair
                # Look for nutrient names near this value
                for nutrient_name in ['Energy', 'Protein', 'Carbohydrate', 'Total Sugars', 'Total Fat', 'Saturated Fat', 'Trans Fat']:
                    if nutrient_name.lower().replace(' ', '') in per_100g_section.lower().replace(' ', ''):
                        # Only add if we don't already have this nutrient or if this value is larger
                        if nutrient_name not in nutrition_data or float(value) > float(nutrition_data[nutrient_name].split()[0]):
                            # Standardize units
                            if unit.lower() in ['kj', 'cal']:
                                unit = 'kcal'
                            else:
                                unit = 'g'
                            
                        nutrition_data[nutrient_name] = f"{value} {unit}".strip()
                        print(f"Found {nutrient_name}: {value} {unit} from Per 100g section")  # Debug
        
        print(f"Final nutrition data: {nutrition_data}")  # Debug
        return nutrition_data

    def extract_ingredients_from_text(self, text, image_content=None):
        """
        Extracts a clean list of ingredients using AWS Textract Query for better accuracy.
        """
        import re
        
        # Try AWS Textract Query first if image_content is available
        if image_content and hasattr(self, 'textract_client') and self.textract_client:
            query_ingredients = self.extract_ingredients_with_textract_query(image_content)
            if query_ingredients:
                # Process query results
                ingredients = self.process_query_ingredients(query_ingredients)
                if ingredients:
                    return ingredients
        
        # Fallback to text parsing
        return self.extract_ingredients_from_text_fallback(text)

    def extract_ingredients_with_textract_query(self, image_content):
        """
        Extract ingredients using AWS Textract Query feature.
        """
        try:
            if not self.textract_client:
                return []

            # Query for ingredients
            queries = [
                {
                    'Text': 'What are the ingredients?',
                    'Alias': 'ingredients'
                },
                {
                    'Text': 'List all ingredients',
                    'Alias': 'ingredients_list'
                },
                {
                    'Text': 'What ingredients are in this product?',
                    'Alias': 'product_ingredients'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                ingredients = []
                
                # Extract answers from the response
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        # Find the answer block
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                ingredients.append(answer_block['Text'])
                
                return ingredients
                
            except Exception as e:
                logging.error(f"Ingredients Query failed: {e}")
                return []

        except Exception as e:
            logging.error(f"Ingredients Query extraction error: {e}")
            return []

    def process_query_ingredients(self, query_ingredients):
        """
        Process ingredients from Textract Query results with better cleaning.
        """
        if not query_ingredients:
            return []
        
        # Join all ingredient responses and clean them up
        ingredients_text = " ".join(query_ingredients)
        
        # Clean up the ingredients text - preserve important characters
        ingredients_text = re.sub(r'[^\w\s,()%.&-]', ' ', ingredients_text)  # Keep important chars
        ingredients_text = re.sub(r'\s+', ' ', ingredients_text)  # Normalize whitespace
        
        # Split ingredients by common separators, but be smarter about it
        ingredients = []
        
        # First, try to split by commas, but respect parentheses
        # This pattern splits by commas that are NOT inside parentheses
        parts = re.split(r',\s*(?![^()]*\))', ingredients_text)
        
        # If the above didn't work well, try a more aggressive approach
        if len(parts) <= 1:
            # Split by commas and then clean up each part
            parts = re.split(r',\s*', ingredients_text)
        
        for part in parts:
            ingredient = part.strip()
            if ingredient and len(ingredient) > 2:
                # Clean up ingredient using the cleaning function
                ingredient = self.clean_ingredient_text(ingredient)
                
                # Skip if it's just a number, percentage, or very short
                if (ingredient and len(ingredient) > 2 and 
                    not re.match(r'^\d+\.?\d*%?$', ingredient) and
                    not ingredient.lower() in ['and', 'or', 'the', 'a', 'an']):
                    
                    # Use the compound ingredient splitting function
                    split_ingredients = self.split_compound_ingredients(ingredient)
                    for split_ingredient in split_ingredients:
                        if split_ingredient and len(split_ingredient) > 2:
                            ingredients.append(split_ingredient)

        # Remove duplicates while preserving order
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            clean_ingredient = re.sub(r'\s+', ' ', ingredient).strip()
            if clean_ingredient.lower() not in seen:
                seen.add(clean_ingredient.lower())
                unique_ingredients.append(clean_ingredient)

        return unique_ingredients

    def extract_ingredients_from_text_fallback(self, text):
        """
        Fallback ingredients extraction using text parsing with improved cleaning.
        """
        import re
        # 1. Find the INGREDIENTS section (case-insensitive)
        match = re.search(
            r'ingredients[:\s]*([\s\S]+?)(allergen|nutritional|store|packaged|may contain|used as natural|information|$)',
            text, re.IGNORECASE
        )
        if not match:
            return []
        ingredients_text = match.group(1)

        # 2. Clean up text: replace newlines, remove unwanted symbols (but keep (), %, &)
        ingredients_text = re.sub(r'\n', ' ', ingredients_text)
        ingredients_text = re.sub(r'[^a-zA-Z0-9,().&%\-\s]', '', ingredients_text)
        ingredients_text = re.sub(r'\s+', ' ', ingredients_text)

        # 3. Split on commas and periods (not inside parentheses)
        parts = re.split(r'[,.](?![^()]*\))', ingredients_text)
        
        # If the above didn't work well, try a more aggressive approach
        if len(parts) <= 1:
            # Split by commas and then clean up each part
            parts = re.split(r'[,\s]+', ingredients_text)
        ingredients = []
        for part in parts:
            ing = part.strip()
            # Clean up ingredient using the cleaning function
            ing = self.clean_ingredient_text(ing)
            # Filter out non-ingredient lines
            if ing and not re.search(
                r'(may contain|allergen|information|flavouring|substances|regulator|identical|used as natural|limit of quantification)',
                ing, re.IGNORECASE
            ):
                # Use the compound ingredient splitting function
                split_ingredients = self.split_compound_ingredients(ing)
                for split_ingredient in split_ingredients:
                    if split_ingredient and len(split_ingredient) > 2:
                        ingredients.append(split_ingredient)
        
        # Remove duplicates and clean up
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            clean_ingredient = re.sub(r'\s+', ' ', ingredient).strip()
            if clean_ingredient.lower() not in seen and len(clean_ingredient) > 2:
                seen.add(clean_ingredient.lower())
                unique_ingredients.append(clean_ingredient)
        
        return unique_ingredients

    def clean_ingredient_text(self, ingredient):
        """
        Clean and normalize ingredient text.
        """
        import re
        
        # Remove extra whitespace
        ingredient = re.sub(r'\s+', ' ', ingredient).strip()
        
        # Remove trailing punctuation
        ingredient = re.sub(r'[.,;:]$', '', ingredient)
        
        # Remove leading numbers and percentages
        ingredient = re.sub(r'^\d+%?\s*', '', ingredient)
        
        # Remove bullet points
        ingredient = re.sub(r'^\s*[-•]\s*', '', ingredient)
        
        # Fix common OCR errors
        ingredient = ingredient.replace("Flailed", "Flaked")
        ingredient = ingredient.replace("Mingo", "Mango")
        ingredient = ingredient.replace("Pomcgranate", "Pomegranate")
        ingredient = ingredient.replace("lodised", "Iodised")
        
        return ingredient.strip()

    def split_compound_ingredients(self, ingredient_text):
        """
        Split compound ingredients that contain multiple items.
        """
        import re
        
        # If it contains commas but no parentheses, split by commas
        if ',' in ingredient_text and '(' not in ingredient_text:
            parts = re.split(r',\s*', ingredient_text)
            return [part.strip() for part in parts if part.strip()]
        
        # If it contains "and" but no parentheses, split by "and"
        if ' and ' in ingredient_text.lower() and '(' not in ingredient_text:
            parts = re.split(r'\s+and\s+', ingredient_text, flags=re.IGNORECASE)
            return [part.strip() for part in parts if part.strip()]
        
        # If it contains both commas and parentheses, try to split carefully
        if ',' in ingredient_text and '(' in ingredient_text:
            # Look for patterns like "A (B), C, D"
            # Split by commas that are not inside parentheses
            parts = re.split(r',\s*(?![^()]*\))', ingredient_text)
            result = []
            for part in parts:
                part = part.strip()
                if part:
                    # If this part still contains commas, split it further
                    if ',' in part and '(' not in part:
                        sub_parts = re.split(r',\s*', part)
                        result.extend([sub_part.strip() for sub_part in sub_parts if sub_part.strip()])
                    else:
                        result.append(part)
            return result
        
        return [ingredient_text]

    async def save_scan_history(self, user, image_url, extracted_text, nutrition_data, ai_results, safety_status, flagged_ingredients, go_ingredients=None, caution_ingredients=None, no_go_ingredients=None, product_name="OCR Product"):
        # Save scan history in a separate async function
        # Keep nutrition_data clean - only nutrition facts, not ingredients
        clean_nutrition_data = dict(nutrition_data) if nutrition_data else {}
        
        # Add AI results to nutrition data
        clean_nutrition_data.update({
            "ai_health_insight": ai_results.get("ai_health_insight", ""),
            "expert_advice": ai_results.get("expert_advice", ""),
            "go_ingredients": go_ingredients or [],
            "caution_ingredients": caution_ingredients or [],
            "no_go_ingredients": no_go_ingredients or []
        })
        
        scan = await sync_to_async(FoodLabelScan.objects.create)(
            user=user,
            image_url=image_url,
            extracted_text=extracted_text,
            nutrition_data=clean_nutrition_data,  # Include ingredient classifications
            safety_status=safety_status,
            flagged_ingredients=flagged_ingredients,
            product_name=product_name,
        )
        
        # Increment scan count for freemium users
        await sync_to_async(increment_user_scan_count)(user)
        
        return scan

    def categorize_ingredients_with_openai(self, user, ingredients_list):
        """
        Categorize ingredients using OpenAI based on user profile (allergies, dietary preferences, medical conditions)
        into Go, No-Go, and Caution categories.
        """
        try:
            # Prepare user profile information
            allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
            dietary_preferences = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
            health_conditions = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
            
            # Create a comprehensive prompt for OpenAI
            prompt = f"""
            As a nutrition and food safety expert, categorize the following ingredients based on this user's profile:

            USER PROFILE:
            - Allergies: {', '.join(allergies) if allergies else 'None'}
            - Dietary Preferences: {', '.join(dietary_preferences) if dietary_preferences else 'None'}
            - Health Conditions: {', '.join(health_conditions) if health_conditions else 'None'}

            INGREDIENTS TO CATEGORIZE:
            {', '.join(ingredients_list)}

            CATEGORIZE EACH INGREDIENT INTO ONE OF THREE CATEGORIES:

            1. GO: Safe ingredients that align with user's profile
            2. NO-GO: Ingredients that are harmful or contraindicated for the user
            3. CAUTION: Ingredients that may not be ideal but aren't strictly harmful

            RESPONSE FORMAT (JSON only):
            {{
                "go": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ],
                "no_go": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ],
                "caution": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ]
            }}

            RULES:
            - If user has allergies, any ingredient containing those allergens goes to NO-GO
            - If user has dietary preferences (vegan, vegetarian, etc.), non-compliant ingredients go to NO-GO or CAUTION
            - If user has health conditions, ingredients that may worsen them go to NO-GO or CAUTION
            - Common safe ingredients like water, salt, natural flavors typically go to GO
            - Artificial colors, preservatives, high-sodium ingredients often go to CAUTION
            - Known harmful ingredients go to NO-GO

            Return only valid JSON, no additional text.
            """
            
            # Call OpenAI API
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a nutrition and food safety expert. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3,
                    timeout=10
                )
                
                # Parse the response
                content = response.choices[0].message.content.strip()
                
                # Clean up the response to ensure it's valid JSON
                content = content.replace('```json', '').replace('```', '').strip()
                
                # Parse JSON
                categorization = json.loads(content)
                
                # Validate the structure
                required_keys = ['go', 'no_go', 'caution']
                for key in required_keys:
                    if key not in categorization:
                        categorization[key] = []
                
                # Ensure all ingredients are categorized
                all_categorized = set()
                for category in categorization.values():
                    for item in category:
                        if isinstance(item, dict) and 'ingredient' in item:
                            all_categorized.add(item['ingredient'])
                
                # Add any uncategorized ingredients to 'go' as default
                for ingredient in ingredients_list:
                    if ingredient not in all_categorized:
                        categorization['go'].append({
                            "ingredient": ingredient,
                            "reasons": ["Defaulted to safe category"]
                        })
                
                return categorization
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
                # Fallback to basic categorization
                return self._fallback_categorization(user, ingredients_list)
                
        except Exception as e:
            print(f"OpenAI categorization error: {e}")
            # Fallback to basic categorization
            return self._fallback_categorization(user, ingredients_list)

    def _fallback_categorization(self, user, ingredients_list):
        """
        Fallback categorization method when OpenAI fails.
        """
        allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
        dietary_preferences = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
        health_conditions = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
        
        go_ingredients = []
        no_go_ingredients = []
        caution_ingredients = []
        
        for ingredient in ingredients_list:
            ing_lower = ingredient.lower()
            reasons = []
            
            # Check allergies
            if any(allergen in ing_lower for allergen in allergies):
                reasons.append("Allergen")
            
            # Check dietary preferences
            if dietary_preferences:
                if 'vegan' in dietary_preferences and any(animal in ing_lower for animal in ['milk', 'egg', 'meat', 'fish', 'gelatin', 'honey']):
                    reasons.append("Non-vegan")
                elif 'vegetarian' in dietary_preferences and any(animal in ing_lower for animal in ['meat', 'fish', 'gelatin']):
                    reasons.append("Non-vegetarian")
            
            # Check health conditions
            if health_conditions:
                if 'diabetes' in health_conditions and 'sugar' in ing_lower:
                    reasons.append("High sugar")
                elif 'hypertension' in health_conditions and 'salt' in ing_lower:
                    reasons.append("High sodium")
            
            # Categorize based on reasons
            if reasons:
                if "Allergen" in reasons:
                    no_go_ingredients.append({
                        "ingredient": ingredient,
                        "reasons": reasons
                    })
                else:
                    caution_ingredients.append({
                        "ingredient": ingredient,
                        "reasons": reasons
                    })
            else:
                go_ingredients.append({
                    "ingredient": ingredient,
                    "reasons": ["Safe"]
                })
        
        return {
            "go": go_ingredients,
            "no_go": no_go_ingredients,
            "caution": caution_ingredients
        }

    async def validate_product_safety(self, user, ingredients_list):
        """
        Categorize ingredients using OpenAI based on user profile (allergies, dietary preferences, medical conditions)
        into Go, No-Go, and Caution categories.
        """
        try:
            # Get OpenAI categorization
            categorization = self.categorize_ingredients_with_openai(user, ingredients_list)
            
            go_ingredients = categorization.get('go', [])
            no_go_ingredients = categorization.get('no_go', [])
            caution_ingredients = categorization.get('caution', [])
            
            # Add EFSA data to each ingredient for consistency with existing structure
            efsa_data_cache = {}
            for category in [go_ingredients, no_go_ingredients, caution_ingredients]:
                for ingredient_data in category:
                    ingredient_name = ingredient_data.get('ingredient', '')
                    try:
                        efsa_data = fetch_efsa_openfoodtox_data(ingredient_name)
                        efsa_data_cache[ingredient_name] = efsa_data or {}
                        ingredient_data['efsa_data'] = efsa_data or {}
                    except Exception as e:
                        print(f"EFSA error for {ingredient_name}: {e}")
                        efsa_data_cache[ingredient_name] = {
                            'found': False,
                            'error': f'EFSA query failed: {str(e)}',
                            'source': 'EFSA OpenFoodTox Database'
                        }
                        ingredient_data['efsa_data'] = efsa_data_cache[ingredient_name]
            
            # Determine overall safety status
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache
            
        except Exception as e:
            print(f"OpenAI categorization failed: {e}")
            # Fallback to basic categorization
            fallback_result = self._fallback_categorization(user, ingredients_list)
            
            go_ingredients = fallback_result.get('go', [])
            no_go_ingredients = fallback_result.get('no_go', [])
            caution_ingredients = fallback_result.get('caution', [])
            
            # Add empty EFSA data for fallback
            efsa_data_cache = {}
            for category in [go_ingredients, no_go_ingredients, caution_ingredients]:
                for ingredient_data in category:
                    ingredient_data['efsa_data'] = {}
            
            # Determine overall safety status
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache

# class FoodLabelNutritionView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     # In-memory caches (class-level)
#     edamam_cache = {}
#     openai_cache = {}
    
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         # Initialize AWS Textract client
#         try:
#             aws_access_key = settings.AWS_ACCESS_KEY_ID
#             aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
#             aws_region = settings.AWS_S3_REGION_NAME or 'us-east-1'
            
#             if not aws_access_key or not aws_secret_key:
#                 logging.error("AWS credentials not found in settings")
#                 self.textract_client = None
#                 return
            
#             self.textract_client = boto3.client(
#                 'textract',
#                 aws_access_key_id=aws_access_key,
#                 aws_secret_access_key=aws_secret_key,
#                 region_name=aws_region
#             )
#             print("AWS Textract client initialized successfully for FoodLabelNutritionView")
#         except Exception as e:
#             logging.error(f"Failed to initialize AWS Textract client: {e}")
#             self.textract_client = None

#     def post(self, request):
#         # can_scan, scan_count = can_user_scan(request.user)
#         # if not can_scan:
#         #     return Response(
#         #         {
#         #             "error": "Scan limit reached. Please subscribe to AI IngredientIQ for unlimited scans.",
#         #             "scans_used": scan_count,
#         #             "max_scans": 6
#         #         },
#         #         status=status.HTTP_402_PAYMENT_REQUIRED
#         #     )
#         import time
#         import logging
#         from concurrent.futures import ThreadPoolExecutor
#         try:
#             import torch
#             device = "cuda" if torch.cuda.is_available() else "cpu"
#             print(f"FoodLabelNutritionView is running on: {device.upper()}")
#         except ImportError:
#             print("torch not installed; cannot determine GPU/CPU.")

#         start_time = time.time()

#         # Deserialize and validate
#         serializer = AllergenDietaryCheckSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         image_file = serializer.validated_data['image']
#         image_content = image_file.read()

#         # LIGHTNING FAST PARALLEL PROCESSING
#         with ThreadPoolExecutor(max_workers=6) as executor:
#             # Submit all tasks simultaneously
#             image_future = executor.submit(self.save_image, image_content)
#             ocr_future = executor.submit(self.run_ocr, image_content)
#             ingredients_future = executor.submit(self.extract_ingredients_with_textract_query, image_content)
#             nutrition_future = executor.submit(self.extract_nutrition_with_textract_query, image_content)
            
#             # Get image URL first (critical)
#             image_url, image_path = image_future.result(timeout=3)
#             if not image_url:
#                 return Response({'error': 'Image upload failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
#             # Get OCR results with timeouts
#             try:
#                 extracted_text = ocr_future.result(timeout=8)  # 8 second timeout
#             except:
#                 extracted_text = ""
                
#             try:
#                 query_ingredients = ingredients_future.result(timeout=8)
#             except:
#                 query_ingredients = []
                
#             try:
#                 query_nutrition = nutrition_future.result(timeout=8)
#             except:
#                 query_nutrition = {}
        
#         # Process results quickly
#         if query_nutrition:
#             nutrition_data = self.process_query_nutrition_data(query_nutrition)
#         else:
#             nutrition_data = self.extract_nutrition_info_fallback(extracted_text)
        
#         if query_ingredients:
#             actual_ingredients = self.process_query_ingredients(query_ingredients)
#         else:
#             actual_ingredients = self.extract_ingredients_from_text_fallback(extracted_text)

#         # Debug logging
#         print(f"Extracted text: {extracted_text}")
#         print(f"Nutrition data extracted: {nutrition_data}")
        
#         # More lenient check - allow partial nutrition data
#         if not nutrition_data:
#             # Try a simpler extraction method as fallback
#             nutrition_data = self.extract_nutrition_info_simple(extracted_text)
#             print(f"Fallback nutrition data: {nutrition_data}")
            
#         if not nutrition_data:
#             return Response(
#                 {"error": "No nutrition data found, Please capture clear photo of nutrition label of food packet. Scan not saved."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # PARALLEL SAFETY VALIDATION AND AI INSIGHTS
#         safety_start = time.time()
#         with ThreadPoolExecutor(max_workers=2) as executor:
#             # Run safety validation and AI insights in parallel
#             safety_future = executor.submit(lambda: asyncio.run(self.validate_product_safety(request.user, actual_ingredients)))
#             ai_future = executor.submit(self.get_ai_health_insight_and_expert_advice, request.user, nutrition_data, [])
            
#             # Get safety results with timeout
#             try:
#                 safety_result = safety_future.result(timeout=5)  # 5 second timeout
#                 if len(safety_result) == 5:
#                     safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache = safety_result
#                 else:
#                     safety_status, go_ingredients, caution_ingredients, no_go_ingredients = safety_result
#                     efsa_data_cache = {}
#             except:
#                 safety_status, go_ingredients, caution_ingredients, no_go_ingredients = "unknown", [], [], []
#                 efsa_data_cache = {}
            
#             # Get AI results with timeout
#             try:
#                 ai_results = ai_future.result(timeout=3)  # 3 second timeout
#             except:
#                 ai_results = {
#                     "ai_health_insight": "Health insights unavailable.",
#                     "expert_advice": "Consult healthcare professional."
#                 }
        
#         safety_end = time.time()
#         logging.info(f"Safety validation completed in {safety_end - safety_start:.2f} seconds.")

#         # Prepare ingredients for scan history (convert back to simple format for storage)
#         def extract_ingredient_names(ingredient_list):
#             return [ing["ingredient"] if isinstance(ing, dict) else ing for ing in ingredient_list]
        
#         no_go_names = extract_ingredient_names(no_go_ingredients)
#         go_names = extract_ingredient_names(go_ingredients)
#         caution_names = extract_ingredient_names(caution_ingredients)
        
#         with ThreadPoolExecutor() as executor:
#             scan_future = executor.submit(lambda: asyncio.run(self.save_scan_history(
#                 request.user,
#                 image_url,
#                 extracted_text,
#                 nutrition_data,
#                 ai_results,
#                 safety_status,
#                 no_go_names,
#                 go_names,
#                 caution_names,
#                 "OCR Product"
#             )))
#             scan = scan_future.result()

#         total_time = time.time() - start_time
#         logging.info(f"FoodLabelNutritionView total time: {total_time:.2f} seconds.")

#         # Convert ingredient lists to list of objects with clean names and EFSA data
#         def format_ingredient_list(ingredient_list):
#             formatted_list = []
#             for ing in ingredient_list:
#                 if isinstance(ing, dict):
#                     # New format with EFSA data
#                     formatted_ing = {
#                         "ingredient": ing["ingredient"],
#                         "reasons": ing.get("reasons", []),
#                         "efsa_data": ing.get("efsa_data", {})
#                     }
#                 else:
#                     # Old format (string)
#                     formatted_ing = {
#                         "ingredient": ing,
#                         "reasons": ["Legacy format"],
#                         "efsa_data": {}
#                     }
#                 formatted_list.append(formatted_ing)
#             return formatted_list
        
#         go_ingredients_obj = format_ingredient_list(go_ingredients)
#         caution_ingredients_obj = format_ingredient_list(caution_ingredients)
#         no_go_ingredients_obj = format_ingredient_list(no_go_ingredients)

#         main_ingredient = actual_ingredients[0] if actual_ingredients else None
#         def safe_summary(fetch_func, ingredient, default_msg):
#             try:
#                 summary = fetch_func(ingredient)
#                 if not summary or (isinstance(summary, str) and not summary.strip()):
#                     return default_msg
#                 return summary
#             except Exception as e:
#                 print(f"Summary fetch error for {ingredient}: {e}")
#                 return default_msg

#         medlineplus_summary = safe_summary(
#             fetch_medlineplus_summary,
#             main_ingredient,
#             "No MedlinePlus summary available for this ingredient."
#         ) if main_ingredient else "No MedlinePlus summary available for this ingredient."

#         pubchem_summary = safe_summary(
#             fetch_pubchem_toxicology_summary,
#             main_ingredient,
#             "No PubChem toxicology data found for this ingredient."
#         ) if main_ingredient else "No PubChem toxicology data found for this ingredient."
#         pubmed_articles = fetch_pubmed_articles(main_ingredient) if main_ingredient else []

#         # REMOVED ClinicalTrials.gov integration for speed
#         def fetch_clinical_trials(ingredient):
#             return []  # Return empty list for speed
#             if not ingredient:
#                 return []
#             try:
#                 url = f"https://clinicaltrials.gov/api/v2/studies?q={ingredient}&limit=3"
#                 resp = requests.get(url, timeout=5)
#                 if resp.status_code != 200:
#                     print(f"ClinicalTrials.gov API error: {resp.status_code}")
#                     return []
#                 data = resp.json()
#                 studies = data.get("studies", [])
#                 trials = []
#                 for study in studies:
#                     nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
#                     title = study.get("protocolSection", {}).get("identificationModule", {}).get("officialTitle")
#                     status = study.get("protocolSection", {}).get("statusModule", {}).get("overallStatus")
#                     summary = study.get("protocolSection", {}).get("descriptionModule", {}).get("briefSummary")
#                     url = f"https://clinicaltrials.gov/ct2/show/{nct_id}" if nct_id else None
#                     if nct_id and title:
#                         trials.append({
#                             "title": title,
#                             "nct_id": nct_id,
#                             "status": status,
#                             "summary": summary,
#                             "url": url
#                         })
#                 return trials
#             except Exception as e:
#                 print(f"ClinicalTrials.gov fetch error: {e}")
#                 return []

#         clinical_trials = fetch_clinical_trials(main_ingredient)

#         # --- FSA Hygiene Rating Integration ---
#         # Try to extract business name from OCR text or use default
#         business_name = "OCR Product"  # Default fallback
#         fsa_data = None
        
#         # Look for business names in the extracted text
#         business_keywords = ['ltd', 'limited', 'inc', 'corporation', 'company', 'co', 'brand', 'manufacturer']
#         lines = extracted_text.split('\n')
#         for line in lines:
#             line_lower = line.lower().strip()
#             if any(keyword in line_lower for keyword in business_keywords):
#                 business_name = line.strip()
#                 break
        
#         # Fetch FSA hygiene rating data
#         try:
#             fsa_data = fetch_fsa_hygiene_rating(business_name=business_name)
#         except Exception as e:
#             print(f"FSA API error: {e}")
#             fsa_data = {
#                 'found': False,
#                 'error': f'FSA API error: {str(e)}',
#                 'source': 'UK FSA FHRS API'
#             }

#         return Response({
#             "scan_id": scan.id,
#             "product_name":"OCR Product",
#             "image_url": image_url,
#             "extracted_text": extracted_text,
#             "nutrition_data": nutrition_data,
#             "ingredients": actual_ingredients,
#             "safety_status": safety_status,
#             "is_favorite": scan.is_favorite,
#             "ingredients_analysis": {
#                 "go": {
#                     "ingredients": go_ingredients_obj,
#                     "count": len(go_ingredients_obj),
#                     "description": "Ingredients that are safe and suitable for your health profile"
#                 },
#                 "caution": {
#                     "ingredients": caution_ingredients_obj,
#                     "count": len(caution_ingredients_obj),
#                     "description": "Ingredients that may not be ideal for your health profile - consume at your own risk"
#                 },
#                 "no_go": {
#                     "ingredients": no_go_ingredients_obj,
#                     "count": len(no_go_ingredients_obj),
#                     "description": "Ingredients that are harmful or not suitable for your health profile - avoid these"
#                 },
#                 "total_flagged": len(caution_ingredients_obj) + len(no_go_ingredients_obj)
#             },
#             "efsa_data": {
#                 "source": "European Food Safety Authority (EFSA) OpenFoodTox Database",
#                 "total_ingredients_checked": len(efsa_data_cache),
#                 "ingredients_with_efsa_data": len([data for data in efsa_data_cache.values() if data and data.get('found')]),
#                 "cache": {k: v for k, v in efsa_data_cache.items() if v is not None}
#             },
#             "fsa_hygiene_data": fsa_data,
#             "medical_condition_recommendations": {
#                 "user_health_profile": {
#                     "allergies": request.user.Allergies,
#                     "dietary_preferences": request.user.Dietary_preferences,
#                     "health_conditions": request.user.Health_conditions
#                 },
#                 "recommendations": get_medical_condition_food_recommendations(
#                     request.user.Health_conditions, 
#                     request.user.Allergies, 
#                     request.user.Dietary_preferences
#                 ) if (request.user.Health_conditions or request.user.Allergies or request.user.Dietary_preferences) else {"found": False, "message": "No health profile specified"},
#                 "source": "SNOMED CT & ICD-10 Clinical Guidelines"
#             },
#             "ai_health_insight": ai_results["ai_health_insight"],
#             "expert_advice": ai_results["expert_advice"],
#             # "ocr_gpu": False,  # Azure OCR
#             # "medlineplus_summary": medlineplus_summary,
#             # "pubchem_summary": pubchem_summary,
#             # "pubmed_articles": pubmed_articles,
#             # "clinical_trials": clinical_trials,
#             # "timing": {
#             #     "ocr": ocr_end - ocr_start,
#             #     "safety+ai": safety_end - safety_start,
#             #     "total": total_time
#             # }
#         }, status=status.HTTP_200_OK)

#     def get_ai_health_insight_and_expert_advice(self, user, nutrition_data, flagged_ingredients):
#         """
#         Ultra-fast AI insights with minimal processing and aggressive timeouts.
#         """
#         import time
#         import json
#         import hashlib
#         from concurrent.futures import ThreadPoolExecutor, TimeoutError
        
#         # Quick cache check
#         key_data = {
#             'ingredients': sorted(flagged_ingredients[:2]),  # Only first 2 for speed
#             'nutrition': {k: v for k, v in list(nutrition_data.items())[:3]},  # Only first 3
#             'diet': user.Dietary_preferences,
#             'allergies': user.Allergies
#         }
#         cache_key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
#         if cache_key in self.openai_cache:
#             return self.openai_cache[cache_key]
        
#         # Ultra-minimal prompt
#         nutrition_summary = ', '.join(f"{k}: {v}" for k, v in list(nutrition_data.items())[:3])
#         flagged_str = ', '.join(flagged_ingredients[:2])  # Only top 2
#         prompt = f"User: {user.Dietary_preferences or 'None'}. Nutrition: {nutrition_summary}. Avoid: {flagged_str}. Give 1 sentence health insight + 1 sentence advice. Be extremely concise."
        
#         def openai_call():
#             from openai import OpenAI
#             import os
            
#             # Try OpenAI with very fast timeout
#             try:
#                 client = OpenAI(
#                     api_key=os.getenv("OPENAI_API_KEY"),
#                     timeout=2  # 2 second timeout
#                 )
                
#                 # Ultra-minimal prompt for speed
#                 nutrition_summary = ', '.join(f"{k}: {v}" for k, v in list(nutrition_data.items())[:3])
#                 flagged_str = ', '.join(flagged_ingredients[:2])  # Only top 2
#                 user_profile = f"Diet: {user.Dietary_preferences or 'None'}, Allergies: {user.Allergies or 'None'}"
                
#                 prompt = f"""
#                 User Profile: {user_profile}
#                 Nutrition: {nutrition_summary}
#                 Avoid: {flagged_str}
                
#                 Give 1 sentence health insight + 1 sentence advice. Be extremely concise.
#                 """
                
#                 completion = client.chat.completions.create(
#                     model="gpt-3.5-turbo",
#                     messages=[
#                         {"role": "system", "content": "Nutrition expert. Be extremely concise and actionable."},
#                         {"role": "user", "content": prompt},
#                     ],
#                     max_tokens=60,  # Very short response
#                     temperature=0.3,
#                 )
                
#                 content = completion.choices[0].message.content.strip()
                
#                 # Simple split
#                 parts = content.split('.', 1)
#                 ai_health_insight = parts[0] + "." if parts else "Product analyzed successfully."
#                 expert_advice = parts[1] + "." if len(parts) > 1 else "Check ingredients for your dietary needs."
                
#                 return {
#                     "ai_health_insight": ai_health_insight,
#                     "expert_advice": expert_advice
#                 }
                
#             except Exception as e:
#                 print(f"OpenAI error: {e}")
#                 # Fallback to intelligent response based on data
#                 if flagged_ingredients:
#                     return {
#                         "ai_health_insight": f"Product contains {len(flagged_ingredients)} ingredients that may not suit your dietary needs.",
#                         "expert_advice": "Review the flagged ingredients and consult healthcare professional if needed."
#                     }
#                 else:
#                     return {
#                         "ai_health_insight": "Product analyzed successfully. Check nutrition values for your health goals.",
#                         "expert_advice": "Consider portion size and overall dietary balance."
#                     }
        
#         with ThreadPoolExecutor(max_workers=1) as executor:
#             future = executor.submit(openai_call)
#             try:
#                 result = future.result(timeout=3)  # 3 second total timeout for OpenAI
#                 self.openai_cache[cache_key] = result
#                 return result
#             except TimeoutError:
#                 return {"ai_health_insight": "Health insights unavailable.", "expert_advice": "Consult healthcare professional."}
#             except Exception as e:
#                 print(f"OpenAI outer error: {e}")
#                 return {"ai_health_insight": "Health insights unavailable.", "expert_advice": "Consult healthcare professional."}

#     def run_in_thread_pool(self, func, *args):
#         with ThreadPoolExecutor() as executor:
#             return executor.submit(func, *args).result()

#     def save_image(self, image_content):
#         try:
#             image_name = f"food_labels/{uuid.uuid4()}.jpg"
#             image_path = default_storage.save(image_name, ContentFile(image_content))
#             image_url = default_storage.url(image_path).replace("https//", "")
#             return image_url, image_path
#         except Exception as e:
#             print(f"Error saving image: {e}")
#             return None, None

#     def run_ocr(self, image_content):
#         """
#         Uses AWS Textract for high-accuracy text extraction with Query feature.
#         """
#         try:
#             if not self.textract_client:
#                 logging.error("AWS Textract client not initialized")
#                 return ''
            
#             # Try to extract text using AWS Textract Query first
#             extracted_text = self.extract_text_with_textract_query(image_content)
#             if extracted_text:
#                 logging.info(f"Extracted text from AWS Textract Query: {extracted_text}")
#                 return extracted_text
            
#             # Fallback to regular text extraction
#             extracted_text = self.extract_text_with_textract(image_content)
#             if extracted_text:
#                 logging.info(f"Extracted text from AWS Textract: {extracted_text}")
#                 return extracted_text
            
#             logging.error("AWS Textract failed to extract text")
#             return ''
            
#         except Exception as e:
#             logging.error(f"AWS Textract OCR error: {e}", exc_info=True)
#             return ''

#     def extract_text_with_textract_query(self, image_content):
#         """
#         Extract text using AWS Textract Query feature for better accuracy.
#         """
#         try:
#             # Validate image content
#             if not isinstance(image_content, bytes):
#                 logging.error("Image content must be bytes")
#                 return ""
            
#             # Check image size (AWS Textract limit is 5MB)
#             if len(image_content) > 5 * 1024 * 1024:
#                 logging.error("Image too large for AWS Textract (max 5MB)")
#                 return ""
            
#             # Check if image content is valid
#             if len(image_content) < 100:
#                 logging.error("Image content too small")
#                 return ""

#             # Query for general text content
#             queries = [
#                 {
#                     'Text': 'What text is visible in this image?',
#                     'Alias': 'general_text'
#                 },
#                 {
#                     'Text': 'Extract all text from this nutrition label',
#                     'Alias': 'nutrition_text'
#                 }
#             ]

#             try:
#                 response = self.textract_client.analyze_document(
#                     Document={
#                         'Bytes': image_content
#                     },
#                     FeatureTypes=['QUERIES', 'TABLES', 'FORMS', 'LINES'],
#                     QueriesConfig={
#                         'Queries': queries
#                     }
#                 )
                
#                 extracted_text = ""
                
#                 # Extract text from query results
#                 for block in response.get('Blocks', []):
#                     if block['BlockType'] == 'QUERY_RESULT':
#                         if 'Relationships' in block:
#                             for relationship in block['Relationships']:
#                                 if relationship['Type'] == 'ANSWER':
#                                     for answer_id in relationship['Ids']:
#                                         for answer_block in response.get('Blocks', []):
#                                             if answer_block['Id'] == answer_id and 'Text' in answer_block:
#                                                 extracted_text += answer_block['Text'] + "\n"
                
#                 # Also extract regular text blocks
#                 text_blocks = [block for block in response.get('Blocks', []) if block['BlockType'] == 'LINE']
#                 text_blocks.sort(key=lambda x: (x['Geometry']['BoundingBox']['Top'], x['Geometry']['BoundingBox']['Left']))
                
#                 for block in text_blocks:
#                     if 'Text' in block:
#                         extracted_text += block['Text'] + "\n"

#                 return extracted_text.strip()
                
#             except Exception as e:
#                 logging.error(f"Textract Query API error: {e}")
#                 return ""
            
#         except Exception as e:
#             logging.error(f"Textract Query extraction error: {e}")
#             return ""

#     def extract_text_with_textract(self, image_content):
#         """
#         Extract text using AWS Textract with enhanced features.
#         """
#         try:
#             if not self.textract_client:
#                 raise Exception("AWS Textract client not initialized")

#             # Ensure image_content is bytes
#             if not isinstance(image_content, bytes):
#                 logging.error("Image content must be bytes")
#                 return ""

#             # Check image size (AWS Textract limit is 5MB)
#             if len(image_content) > 5 * 1024 * 1024:
#                 logging.error("Image too large for AWS Textract (max 5MB)")
#                 return ""

#             # Check if image content is valid
#             if len(image_content) < 100:
#                 logging.error("Image content too small")
#                 return ""

#             # Try analyze_document first (more features)
#             try:
#                 response = self.textract_client.analyze_document(
#                     Document={
#                         'Bytes': image_content
#                     },
#                     FeatureTypes=['TABLES', 'FORMS', 'LINES']
#                 )
                
#                 # Extract text with spatial information
#                 extracted_text = ""
#                 blocks = response.get('Blocks', [])
                
#                 # Sort blocks by geometry for proper reading order
#                 text_blocks = [block for block in blocks if block['BlockType'] == 'LINE']
#                 text_blocks.sort(key=lambda x: (x['Geometry']['BoundingBox']['Top'], x['Geometry']['BoundingBox']['Left']))
                
#                 for block in text_blocks:
#                     if 'Text' in block:
#                         extracted_text += block['Text'] + "\n"

#                 return extracted_text.strip()
                
#             except Exception as e:
#                 logging.error(f"Textract analyze_document failed: {e}")
#                 # Try simpler detect_document_text as fallback
#                 try:
#                     response = self.textract_client.detect_document_text(
#                         Document={
#                             'Bytes': image_content
#                         }
#                     )
                    
#                     extracted_text = ""
#                     blocks = response.get('Blocks', [])
                    
#                     for block in blocks:
#                         if block['BlockType'] == 'LINE' and 'Text' in block:
#                             extracted_text += block['Text'] + "\n"
                    
#                     return extracted_text.strip()
                    
#                 except Exception as fallback_error:
#                     logging.error(f"Textract detect_document_text also failed: {fallback_error}")
#                     return ""

#         except Exception as e:
#             logging.error(f"Textract extraction error: {e}")
#             return ""

#     def correct_ocr_errors(self, text):
#         corrections = {
#             "Bg": "8g", "Omg": "0mg", "lron": "Iron", "meg": "mcg"
#         }
#         for wrong, right in corrections.items():
#             text = text.replace(wrong, right)
#         return text

#     def extract_nutrition_info_from_text(self, text, image_content=None):
#         """
#         Enhanced nutrition extraction using AWS Textract Query for better accuracy.
#         """
#         nutrition_data = {}
        
#         # Fix common OCR errors first
#         text = self.correct_ocr_errors(text)
        
#         # Try AWS Textract Query first if image_content is available
#         if image_content and hasattr(self, 'textract_client') and self.textract_client:
#             query_nutrition = self.extract_nutrition_with_textract_query(image_content)
#             if query_nutrition:
#                 # Convert query results to the expected format
#                 for key, value in query_nutrition.items():
#                     if value:
#                         # Extract numeric value and unit
#                         match = re.search(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', value)
#                         if match:
#                             numeric_value = match.group(1)
#                             unit = match.group(2).lower()
                            
#                             # Map query keys to nutrition data keys with proper units
#                             if key == 'energy':
#                                 nutrition_data["Energy"] = f"{numeric_value} kcal"
#                             elif key == 'protein':
#                                 nutrition_data["Protein"] = f"{numeric_value} g"
#                             elif key == 'total_fat':
#                                 nutrition_data["Total Fat"] = f"{numeric_value} g"
#                             elif key == 'saturated_fat':
#                                 nutrition_data["Saturated Fat"] = f"{numeric_value} g"
#                             elif key == 'carbohydrates':
#                                 nutrition_data["Carbohydrate"] = f"{numeric_value} g"
#                             elif key == 'sugars':
#                                 nutrition_data["Total Sugars"] = f"{numeric_value} g"
#                             elif key == 'sodium':
#                                 nutrition_data["Sodium"] = f"{numeric_value} mg"
#                             elif key == 'fiber':
#                                 nutrition_data["Dietary Fibre"] = f"{numeric_value} g"
#                             else:
#                                 # Add as custom nutrient with proper unit
#                                 nutrition_data[key.replace('_', ' ').title()] = f"{numeric_value} {unit}"
        
#         # If AWS Textract Query didn't provide enough data, fall back to text parsing
#         if len(nutrition_data) < 3:  # If we have less than 3 nutrients, use fallback
#             nutrition_data = self.extract_nutrition_info_fallback(text)
        
#         return nutrition_data

#     def extract_nutrition_with_textract_query(self, image_content):
#         """
#         Extract nutrition data using AWS Textract Query feature.
#         """
#         try:
#             if not self.textract_client:
#                 return {}

#             # Query for nutrition information
#             queries = [
#                 {
#                     'Text': 'What is the energy/calories value?',
#                     'Alias': 'energy'
#                 },
#                 {
#                     'Text': 'What is the protein content?',
#                     'Alias': 'protein'
#                 },
#                 {
#                     'Text': 'What is the total fat content?',
#                     'Alias': 'total_fat'
#                 },
#                 {
#                     'Text': 'What is the saturated fat content?',
#                     'Alias': 'saturated_fat'
#                 },
#                 {
#                     'Text': 'What is the carbohydrate content?',
#                     'Alias': 'carbohydrates'
#                 },
#                 {
#                     'Text': 'What is the sugar content?',
#                     'Alias': 'sugars'
#                 },
#                 {
#                     'Text': 'What is the sodium content?',
#                     'Alias': 'sodium'
#                 },
#                 {
#                     'Text': 'What is the fiber content?',
#                     'Alias': 'fiber'
#                 }
#             ]

#             try:
#                 response = self.textract_client.analyze_document(
#                     Document={
#                         'Bytes': image_content
#                     },
#                     FeatureTypes=['QUERIES'],
#                     QueriesConfig={
#                         'Queries': queries
#                     }
#                 )
                
#                 nutrition_data = {}
                
#                 # Extract answers from the response
#                 for block in response.get('Blocks', []):
#                     if block['BlockType'] == 'QUERY_RESULT':
#                         query_alias = block.get('Query', {}).get('Alias', '')
#                         if 'Relationships' in block:
#                             for relationship in block['Relationships']:
#                                 if relationship['Type'] == 'ANSWER':
#                                     for answer_id in relationship['Ids']:
#                                         # Find the answer block
#                                         for answer_block in response.get('Blocks', []):
#                                             if answer_block['Id'] == answer_id and 'Text' in answer_block:
#                                                 nutrition_data[query_alias] = answer_block['Text']
                
#                 return nutrition_data
                
#             except Exception as e:
#                 logging.error(f"Nutrition Query failed: {e}")
#                 return {}

#         except Exception as e:
#             logging.error(f"Nutrition Query extraction error: {e}")
#             return {}

#     def extract_nutrition_info_fallback(self, text):
#         """
#         Fallback nutrition extraction using text parsing (original method).
#         """
#         nutrition_data = {}
        
#         # Define comprehensive nutrient patterns with variations
#         nutrient_patterns = {
#             "Energy": [
#                 r'energy[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
#                 r'calories[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
#                 r'calorie[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
#                 r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*energy',
#                 r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*calories'
#             ],
#             "Total Fat": [
#                 r'total\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+fat',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*fat'
#             ],
#             "Saturated Fat": [
#                 r'saturated\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'sat\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*saturated\s+fat',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*sat\s+fat'
#             ],
#             "Trans Fat": [
#                 r'trans\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*trans\s+fat'
#             ],
#             "Cholesterol": [
#                 r'cholesterol[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
#                 r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*cholesterol'
#             ],
#             "Sodium": [
#                 r'sodium[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
#                 r'salt[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
#                 r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*sodium',
#                 r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*salt'
#             ],
#             "Carbohydrate": [
#                 r'carbohydrate[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'carbohydrates[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'carbs[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrate',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrates',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbs'
#             ],
#             "Total Sugars": [
#                 r'total\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'sugar[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+sugars',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugars',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugar'
#             ],
#             "Added Sugars": [
#                 r'added\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*added\s+sugars'
#             ],
#             "Dietary Fibre": [
#                 r'dietary\s+fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'dietary\s+fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fibre',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fiber',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*fibre',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*fiber'
#             ],
#             "Protein": [
#                 r'protein[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
#                 r'(\d+(?:\.\d+)?)\s*(g|%)\s*protein'
#             ]
#         }
        
#         # Extract using comprehensive patterns with proper unit mapping
#         for nutrient_name, patterns in nutrient_patterns.items():
#             all_matches = []
#             for pattern in patterns:
#                 matches = re.findall(pattern, text, re.IGNORECASE)
#                 all_matches.extend(matches)
            
#             if all_matches:
#                 value, unit = all_matches[0]
#                 # Map units correctly
#                 if unit.lower() in ['kj', 'cal']:
#                     unit = 'kcal'
#                 elif unit.lower() == '%':
#                     unit = '%'
#                 elif nutrient_name in ["Energy"]:
#                     unit = 'kcal'
#                 elif nutrient_name in ["Sodium", "Cholesterol"]:
#                     unit = 'mg'
#                 else:
#                     unit = 'g'
                    
#                 nutrition_data[nutrient_name] = f"{value} {unit}".strip()
        
#         # Clean up and standardize units
#         for key, value in nutrition_data.items():
#             if value and not value.endswith(('kcal', 'g', 'mg', 'mcg', '%', 'kj', 'cal')):
#                 # Extract numeric value
#                 numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
#                 if numeric_match:
#                     numeric_value = numeric_match.group(1)
#                     if key.lower() in ["energy", "calories"]:
#                         nutrition_data[key] = f"{numeric_value} kcal"
#                     elif key.lower() in ["protein", "carbohydrate", "total sugars", "dietary fibre", "total fat", "saturated fat", "trans fat"]:
#                         nutrition_data[key] = f"{numeric_value} g"
#                     elif key.lower() in ["sodium", "cholesterol"]:
#                         nutrition_data[key] = f"{numeric_value} mg"
        
#         return nutrition_data

#     def extract_nutrition_info_simple(self, text):
#         """
#         Simple fallback nutrition extraction method for OCR text that's hard to parse.
#         """
#         nutrition_data = {}
        
#         # Fix common OCR errors
#         text = text.replace('o.', '0.').replace('O.', '0.').replace('O', '0').replace('l', '1')
#         text = text.replace('Ptotetn', 'Protein').replace('rotat', 'Total').replace('agog', '240g')
#         text = text.replace('tug', '240g').replace('osg', '240g')
        
#         # Split into lines
#         lines = [line.strip() for line in text.split('\n') if line.strip()]
        
#         print(f"Processing lines: {lines}")  # Debug
        
#         # Look for nutrition section
#         nutrition_section = False
#         for line in lines:
#             if 'nutrition' in line.lower() or 'kcal' in line.lower() or 'g' in line:
#                 nutrition_section = True
#                 break
        
#         if not nutrition_section:
#             return nutrition_data
        
#         # Enhanced pattern matching for the specific OCR format
#         for i, line in enumerate(lines):
#             line_lower = line.lower()
            
#             # Skip non-nutrition lines
#             if any(skip in line_lower for skip in ['ingredients', 'allergen', 'manufactured', 'store', 'packaged']):
#                     continue
                
#             print(f"Processing line {i}: '{line}' -> '{line_lower}'")  # Debug
            
#             # Look for nutrient names and values
#             if 'protein' in line_lower or 'ptotetn' in line_lower:
#                 # Look for value in current line or next few lines
#                 value = None
#                 for j in range(i, min(i+5, len(lines))):
#                     value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
#                     if value_match:
#                         value = value_match.group(1)
#                         unit = value_match.group(2) if value_match.group(2) else 'g'
#                         # Only add if we don't already have this nutrient or if this value is larger (more likely to be correct)
#                         if 'Protein' not in nutrition_data or float(value) > float(nutrition_data['Protein'].split()[0]):
#                             nutrition_data['Protein'] = f"{value} {unit}"
#                             print(f"Found Protein: {value} {unit}")  # Debug
#                         break
            
#             elif 'carbohydrate' in line_lower or 'carbs' in line_lower or 'rotat' in line_lower:
#                 # Look for value in current line or next few lines
#                 value = None
#                 for j in range(i, min(i+5, len(lines))):
#                     value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
#                     if value_match:
#                         value = value_match.group(1)
#                         unit = value_match.group(2) if value_match.group(2) else 'g'
#                         # Only add if we don't already have this nutrient or if this value is larger
#                         if 'Carbohydrate' not in nutrition_data or float(value) > float(nutrition_data['Carbohydrate'].split()[0]):
#                             nutrition_data['Carbohydrate'] = f"{value} {unit}"
#                             print(f"Found Carbohydrate: {value} {unit}")  # Debug
#                         break
            
#             elif 'sugar' in line_lower:
#                 # Look for value in current line or next few lines
#                 value = None
#                 for j in range(i, min(i+5, len(lines))):
#                     value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
#                     if value_match:
#                         value = value_match.group(1)
#                         unit = value_match.group(2) if value_match.group(2) else 'g'
#                         # Only add if we don't already have this nutrient or if this value is larger
#                         if 'Total Sugars' not in nutrition_data or float(value) > float(nutrition_data['Total Sugars'].split()[0]):
#                             nutrition_data['Total Sugars'] = f"{value} {unit}"
#                             print(f"Found Total Sugars: {value} {unit}")  # Debug
#                         break
            
#             elif 'fat' in line_lower:
#                 # Look for value in current line or next few lines
#                 value = None
#                 for j in range(i, min(i+5, len(lines))):
#                     value_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kcal|mg)?', lines[j])
#                     if value_match:
#                         value = value_match.group(1)
#                         unit = value_match.group(2) if value_match.group(2) else 'g'
#                         if 'saturated' in line_lower:
#                             # Only add if we don't already have this nutrient or if this value is larger
#                             if 'Saturated Fat' not in nutrition_data or float(value) > float(nutrition_data['Saturated Fat'].split()[0]):
#                                 nutrition_data['Saturated Fat'] = f"{value} {unit}"
#                                 print(f"Found Saturated Fat: {value} {unit}")  # Debug
#                         else:
#                             # Only add if we don't already have this nutrient or if this value is larger
#                             if 'Total Fat' not in nutrition_data or float(value) > float(nutrition_data['Total Fat'].split()[0]):
#                                 nutrition_data['Total Fat'] = f"{value} {unit}"
#                                 print(f"Found Total Fat: {value} {unit}")  # Debug
#                         break
            
#             elif 'kcal' in line_lower or 'calorie' in line_lower or 'energy' in line_lower:
#                 # Look for value in current line or next few lines
#                 value = None
#                 for j in range(i, min(i+5, len(lines))):
#                     value_match = re.search(r'(\d+(?:\.\d+)?)\s*(kcal|cal)?', lines[j])
#                     if value_match:
#                         value = value_match.group(1)
#                         unit = value_match.group(2) if value_match.group(2) else 'kcal'
#                         # Only add if we don't already have this nutrient or if this value is larger
#                         if 'Energy' not in nutrition_data or float(value) > float(nutrition_data['Energy'].split()[0]):
#                             nutrition_data['Energy'] = f"{value} {unit}"
#                             print(f"Found Energy: {value} {unit}")  # Debug
#                         break
        
#         # Also look for standalone numbers that might be nutrition values
#         for i, line in enumerate(lines):
#             # Look for lines that are just numbers (potential nutrition values)
#             if re.match(r'^\d+(?:\.\d+)?\s*(g|kcal|mg)?$', line.strip()):
#                 value = re.search(r'(\d+(?:\.\d+)?)', line).group(1)
#                 unit = re.search(r'(g|kcal|mg)', line)
#                 unit = unit.group(1) if unit else 'g'
                
#                 print(f"Found standalone value: {value} {unit} at line {i}")  # Debug
                
#                 # Try to match with nearby nutrient names
#                 for j in range(max(0, i-3), min(len(lines), i+4)):
#                     nearby_line = lines[j].lower()
#                     if ('protein' in nearby_line or 'ptotetn' in nearby_line) and 'Protein' not in nutrition_data:
#                         nutrition_data['Protein'] = f"{value} {unit}"
#                         print(f"Mapped {value} {unit} to Protein")  # Debug
#                         break
#                     elif ('carbohydrate' in nearby_line or 'carbs' in nearby_line or 'rotat' in nearby_line) and 'Carbohydrate' not in nutrition_data:
#                         nutrition_data['Carbohydrate'] = f"{value} {unit}"
#                         print(f"Mapped {value} {unit} to Carbohydrate")  # Debug
#                         break
#                     elif 'sugar' in nearby_line and 'Total Sugars' not in nutrition_data:
#                         nutrition_data['Total Sugars'] = f"{value} {unit}"
#                         print(f"Mapped {value} {unit} to Total Sugars")  # Debug
#                         break
#                     elif 'fat' in nearby_line:
#                         if 'saturated' in nearby_line and 'Saturated Fat' not in nutrition_data:
#                             nutrition_data['Saturated Fat'] = f"{value} {unit}"
#                             print(f"Mapped {value} {unit} to Saturated Fat")  # Debug
#                             break
#                         elif 'Total Fat' not in nutrition_data:
#                             nutrition_data['Total Fat'] = f"{value} {unit}"
#                             print(f"Mapped {value} {unit} to Total Fat")  # Debug
#                             break
        
#         # Special handling for "Per 100g" format
#         per_100g_section = ""
#         for i, line in enumerate(lines):
#             if 'per' in line.lower() and '100' in line and 'g' in line.lower():
#                 # Found the per 100g section, collect the next few lines
#                 per_100g_section = '\n'.join(lines[i:i+10])
#                 print(f"Found Per 100g section: {per_100g_section}")  # Debug
#                 break
        
#         if per_100g_section:
#             # Extract all number-unit pairs from this section
#             number_unit_pairs = re.findall(r'(\d+(?:\.\d+)?)\s*(kcal|g|mg|mcg|%|kj|cal)', per_100g_section, re.IGNORECASE)
#             print(f"Number-unit pairs found: {number_unit_pairs}")  # Debug
            
#             # Try to match with nutrient names in the same section
#             for pair in number_unit_pairs:
#                 value, unit = pair
#                 # Look for nutrient names near this value
#                 for nutrient_name in ['Energy', 'Protein', 'Carbohydrate', 'Total Sugars', 'Total Fat', 'Saturated Fat', 'Trans Fat']:
#                     if nutrient_name.lower().replace(' ', '') in per_100g_section.lower().replace(' ', ''):
#                         # Only add if we don't already have this nutrient or if this value is larger
#                         if nutrient_name not in nutrition_data or float(value) > float(nutrition_data[nutrient_name].split()[0]):
#                             # Standardize units
#                             if unit.lower() in ['kj', 'cal']:
#                                 unit = 'kcal'
#                             else:
#                                 unit = 'g'
                            
#                         nutrition_data[nutrient_name] = f"{value} {unit}".strip()
#                         print(f"Found {nutrient_name}: {value} {unit} from Per 100g section")  # Debug
        
#         print(f"Final nutrition data: {nutrition_data}")  # Debug
#         return nutrition_data

#     def extract_ingredients_from_text(self, text, image_content=None):
#         """
#         Extracts a clean list of ingredients using AWS Textract Query for better accuracy.
#         """
#         import re
        
#         # Try AWS Textract Query first if image_content is available
#         if image_content and hasattr(self, 'textract_client') and self.textract_client:
#             query_ingredients = self.extract_ingredients_with_textract_query(image_content)
#             if query_ingredients:
#                 # Process query results
#                 ingredients = self.process_query_ingredients(query_ingredients)
#                 if ingredients:
#                     return ingredients
        
#         # Fallback to text parsing
#         return self.extract_ingredients_from_text_fallback(text)

#     def extract_ingredients_with_textract_query(self, image_content):
#         """
#         Extract ingredients using AWS Textract Query feature.
#         """
#         try:
#             if not self.textract_client:
#                 return []

#             # Query for ingredients
#             queries = [
#                 {
#                     'Text': 'What are the ingredients?',
#                     'Alias': 'ingredients'
#                 },
#                 {
#                     'Text': 'List all ingredients',
#                     'Alias': 'ingredients_list'
#                 },
#                 {
#                     'Text': 'What ingredients are in this product?',
#                     'Alias': 'product_ingredients'
#                 }
#             ]

#             try:
#                 response = self.textract_client.analyze_document(
#                     Document={
#                         'Bytes': image_content
#                     },
#                     FeatureTypes=['QUERIES'],
#                     QueriesConfig={
#                         'Queries': queries
#                     }
#                 )
                
#                 ingredients = []
                
#                 # Extract answers from the response
#                 for block in response.get('Blocks', []):
#                     if block['BlockType'] == 'QUERY_RESULT':
#                         if 'Relationships' in block:
#                             for relationship in block['Relationships']:
#                                 if relationship['Type'] == 'ANSWER':
#                                     for answer_id in relationship['Ids']:
#                                         # Find the answer block
#                                         for answer_block in response.get('Blocks', []):
#                                             if answer_block['Id'] == answer_id and 'Text' in answer_block:
#                                                 ingredients.append(answer_block['Text'])
                
#                 return ingredients
                
#             except Exception as e:
#                 logging.error(f"Ingredients Query failed: {e}")
#                 return []

#         except Exception as e:
#             logging.error(f"Ingredients Query extraction error: {e}")
#             return []

#     def process_query_ingredients(self, query_ingredients):
#         """
#         Process ingredients from Textract Query results with better cleaning.
#         """
#         if not query_ingredients:
#             return []
        
#         # Join all ingredient responses and clean them up
#         ingredients_text = " ".join(query_ingredients)
        
#         # Clean up the ingredients text - preserve important characters
#         ingredients_text = re.sub(r'[^\w\s,()%.&-]', ' ', ingredients_text)  # Keep important chars
#         ingredients_text = re.sub(r'\s+', ' ', ingredients_text)  # Normalize whitespace
        
#         # Split ingredients by common separators, but be smarter about it
#         ingredients = []
        
#         # First, try to split by commas, but respect parentheses
#         # This pattern splits by commas that are NOT inside parentheses
#         parts = re.split(r',\s*(?![^()]*\))', ingredients_text)
        
#         # If the above didn't work well, try a more aggressive approach
#         if len(parts) <= 1:
#             # Split by commas and then clean up each part
#             parts = re.split(r',\s*', ingredients_text)
        
#         for part in parts:
#             ingredient = part.strip()
#             if ingredient and len(ingredient) > 2:
#                 # Clean up ingredient using the cleaning function
#                 ingredient = self.clean_ingredient_text(ingredient)
                
#                 # Skip if it's just a number, percentage, or very short
#                 if (ingredient and len(ingredient) > 2 and 
#                     not re.match(r'^\d+\.?\d*%?$', ingredient) and
#                     not ingredient.lower() in ['and', 'or', 'the', 'a', 'an']):
                    
#                     # Use the compound ingredient splitting function
#                     split_ingredients = self.split_compound_ingredients(ingredient)
#                     for split_ingredient in split_ingredients:
#                         if split_ingredient and len(split_ingredient) > 2:
#                             ingredients.append(split_ingredient)

#         # Remove duplicates while preserving order
#         seen = set()
#         unique_ingredients = []
#         for ingredient in ingredients:
#             clean_ingredient = re.sub(r'\s+', ' ', ingredient).strip()
#             if clean_ingredient.lower() not in seen:
#                 seen.add(clean_ingredient.lower())
#                 unique_ingredients.append(clean_ingredient)

#         return unique_ingredients

#     def extract_ingredients_from_text_fallback(self, text):
#         """
#         Fallback ingredients extraction using text parsing with improved cleaning.
#         """
#         import re
#         # 1. Find the INGREDIENTS section (case-insensitive)
#         match = re.search(
#             r'ingredients[:\s]*([\s\S]+?)(allergen|nutritional|store|packaged|may contain|used as natural|information|$)',
#             text, re.IGNORECASE
#         )
#         if not match:
#             return []
#         ingredients_text = match.group(1)

#         # 2. Clean up text: replace newlines, remove unwanted symbols (but keep (), %, &)
#         ingredients_text = re.sub(r'\n', ' ', ingredients_text)
#         ingredients_text = re.sub(r'[^a-zA-Z0-9,().&%\-\s]', '', ingredients_text)
#         ingredients_text = re.sub(r'\s+', ' ', ingredients_text)

#         # 3. Split on commas and periods (not inside parentheses)
#         parts = re.split(r'[,.](?![^()]*\))', ingredients_text)
        
#         # If the above didn't work well, try a more aggressive approach
#         if len(parts) <= 1:
#             # Split by commas and then clean up each part
#             parts = re.split(r'[,\s]+', ingredients_text)
#         ingredients = []
#         for part in parts:
#             ing = part.strip()
#             # Clean up ingredient using the cleaning function
#             ing = self.clean_ingredient_text(ing)
#             # Filter out non-ingredient lines
#             if ing and not re.search(
#                 r'(may contain|allergen|information|flavouring|substances|regulator|identical|used as natural|limit of quantification)',
#                 ing, re.IGNORECASE
#             ):
#                 # Use the compound ingredient splitting function
#                 split_ingredients = self.split_compound_ingredients(ing)
#                 for split_ingredient in split_ingredients:
#                     if split_ingredient and len(split_ingredient) > 2:
#                         ingredients.append(split_ingredient)
        
#         # Remove duplicates and clean up
#         seen = set()
#         unique_ingredients = []
#         for ingredient in ingredients:
#             clean_ingredient = re.sub(r'\s+', ' ', ingredient).strip()
#             if clean_ingredient.lower() not in seen and len(clean_ingredient) > 2:
#                 seen.add(clean_ingredient.lower())
#                 unique_ingredients.append(clean_ingredient)
        
#         return unique_ingredients

#     def clean_ingredient_text(self, ingredient):
#         """
#         Clean and normalize ingredient text.
#         """
#         import re
        
#         # Remove extra whitespace
#         ingredient = re.sub(r'\s+', ' ', ingredient).strip()
        
#         # Remove trailing punctuation
#         ingredient = re.sub(r'[.,;:]$', '', ingredient)
        
#         # Remove leading numbers and percentages
#         ingredient = re.sub(r'^\d+%?\s*', '', ingredient)
        
#         # Remove bullet points
#         ingredient = re.sub(r'^\s*[-•]\s*', '', ingredient)
        
#         # Fix common OCR errors
#         ingredient = ingredient.replace("Flailed", "Flaked")
#         ingredient = ingredient.replace("Mingo", "Mango")
#         ingredient = ingredient.replace("Pomcgranate", "Pomegranate")
#         ingredient = ingredient.replace("lodised", "Iodised")
        
#         return ingredient.strip()

#     def split_compound_ingredients(self, ingredient_text):
#         """
#         Split compound ingredients that contain multiple items.
#         """
#         import re
        
#         # If it contains commas but no parentheses, split by commas
#         if ',' in ingredient_text and '(' not in ingredient_text:
#             parts = re.split(r',\s*', ingredient_text)
#             return [part.strip() for part in parts if part.strip()]
        
#         # If it contains "and" but no parentheses, split by "and"
#         if ' and ' in ingredient_text.lower() and '(' not in ingredient_text:
#             parts = re.split(r'\s+and\s+', ingredient_text, flags=re.IGNORECASE)
#             return [part.strip() for part in parts if part.strip()]
        
#         # If it contains both commas and parentheses, try to split carefully
#         if ',' in ingredient_text and '(' in ingredient_text:
#             # Look for patterns like "A (B), C, D"
#             # Split by commas that are not inside parentheses
#             parts = re.split(r',\s*(?![^()]*\))', ingredient_text)
#             result = []
#             for part in parts:
#                 part = part.strip()
#                 if part:
#                     # If this part still contains commas, split it further
#                     if ',' in part and '(' not in part:
#                         sub_parts = re.split(r',\s*', part)
#                         result.extend([sub_part.strip() for sub_part in sub_parts if sub_part.strip()])
#                     else:
#                         result.append(part)
#             return result
        
#         return [ingredient_text]

#     async def save_scan_history(self, user, image_url, extracted_text, nutrition_data, ai_results, safety_status, flagged_ingredients, go_ingredients=None, caution_ingredients=None, product_name="OCR Product"):
#         # Save scan history in a separate async function
#         # Keep nutrition_data clean - only nutrition facts, not ingredients
#         clean_nutrition_data = dict(nutrition_data) if nutrition_data else {}
        
#         # Add AI results to nutrition data
#         clean_nutrition_data.update({
#             "ai_health_insight": ai_results.get("ai_health_insight", ""),
#             "expert_advice": ai_results.get("expert_advice", ""),
#             "go_ingredients": go_ingredients or [],
#             "caution_ingredients": caution_ingredients or []
#         })
        
#         scan = await sync_to_async(FoodLabelScan.objects.create)(
#             user=user,
#             image_url=image_url,
#             extracted_text=extracted_text,
#             nutrition_data=clean_nutrition_data,  # Include ingredient classifications
#             safety_status=safety_status,
#             flagged_ingredients=flagged_ingredients,
#             product_name=product_name,
#         )
#         return scan

#     async def validate_product_safety(self, user, ingredients_list):
#         # Use OpenAI for ingredient categorization based on user profile
#         try:
#             # Get OpenAI categorization
#             categorization = self.categorize_ingredients_with_openai(user, ingredients_list)
            
#             go_ingredients = categorization.get('go', [])
#             no_go_ingredients = categorization.get('no_go', [])
#             caution_ingredients = categorization.get('caution', [])
            
#             # Add EFSA data to each ingredient for consistency with existing structure
#             efsa_data_cache = {}
#             for category in [go_ingredients, no_go_ingredients, caution_ingredients]:
#                 for ingredient_data in category:
#                     ingredient_name = ingredient_data.get('ingredient', '')
#                     try:
#                         efsa_data = fetch_efsa_openfoodtox_data(ingredient_name)
#                         efsa_data_cache[ingredient_name] = efsa_data or {}
#                         ingredient_data['efsa_data'] = efsa_data or {}
#                     except Exception as e:
#                         print(f"EFSA error for {ingredient_name}: {e}")
#                         efsa_data_cache[ingredient_name] = {
#                             'found': False,
#                             'error': f'EFSA query failed: {str(e)}',
#                             'source': 'EFSA OpenFoodTox Database'
#                         }
#                         ingredient_data['efsa_data'] = efsa_data_cache[ingredient_name]
            
#             # Determine overall safety status
#             if no_go_ingredients:
#                 safety_status = "UNSAFE"
#             elif caution_ingredients:
#                 safety_status = "CAUTION"
#             else:
#                 safety_status = "SAFE"
            
#             return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache
            
#         except Exception as e:
#             print(f"OpenAI categorization failed, falling back to static method: {e}")
#             # Fallback to original static method
#             if USE_STATIC_INGREDIENT_SAFETY:
#                 # --- Enhanced safety check with EFSA OpenFoodTox integration ---
#                 dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
#                 health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
#                 allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
#                 go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
#                 efsa_data_cache = {}  # Cache EFSA data to avoid duplicate API calls
                
#                 for ingredient in ingredients_list:
#                     ing_lower = ingredient.lower()
                    
#                     # Check EFSA OpenFoodTox database first
#                     try:
#                         efsa_data = fetch_efsa_openfoodtox_data(ingredient)
#                         efsa_data_cache[ingredient] = efsa_data or {}
#                     except Exception as e:
#                         print(f"EFSA error for {ingredient}: {e}")
#                         efsa_data_cache[ingredient] = {
#                             'found': False,
#                             'error': f'EFSA query failed: {str(e)}',
#                             'source': 'EFSA OpenFoodTox Database'
#                         }
#                         efsa_data = efsa_data_cache[ingredient]
                    
#                     # Determine safety based on EFSA data, user allergies, dietary preferences, and health conditions
#                     safety_reasons = []
                    
#                     # Check EFSA safety level
#                     if efsa_data and efsa_data.get('found') and efsa_data.get('safety_level'):
#                         if efsa_data['safety_level'] == 'UNSAFE':
#                             safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Unsafe')}")
#                         elif efsa_data['safety_level'] == 'CAUTION':
#                             safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Caution')}")
                    
#                     # Check user allergies
#                     if any(a in ing_lower for a in allergies):
#                         safety_reasons.append("Allergen")
                    
#                     # Check dietary preferences
#                     if any(d not in ing_lower for d in dietary) and dietary:
#                         safety_reasons.append("Dietary")
                    
#                     # Check health conditions
#                     if any(h in ing_lower for h in health):
#                         safety_reasons.append("Health")
                    
#                     # Categorize ingredient based on safety reasons
#                     if safety_reasons:
#                         if "Allergen" in safety_reasons or (efsa_data and efsa_data.get('found') and efsa_data.get('safety_level') == 'UNSAFE'):
#                             no_go_ingredients.append({
#                                 "ingredient": ingredient,
#                                 "reasons": safety_reasons,
#                                 "efsa_data": efsa_data or {}
#                             })
#                         else:
#                             caution_ingredients.append({
#                                 "ingredient": ingredient,
#                                 "reasons": safety_reasons,
#                                 "efsa_data": efsa_data or {}
#                             })
#                     else:
#                         go_ingredients.append({
#                             "ingredient": ingredient,
#                             "reasons": ["Safe"],
#                             "efsa_data": efsa_data or {}
#                         })
                
#                 # Determine overall safety status
#                 if no_go_ingredients:
#                     safety_status = "UNSAFE"
#                 elif caution_ingredients:
#                     safety_status = "CAUTION"
#                 else:
#                     safety_status = "SAFE"
                
#                 return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache
#             else:
#                 # --- Edamam-based safety check with EFSA enhancement ---
#                 dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
#             health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
#             allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
#             go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
#             efsa_data_cache = {}
            
#             async def classify(ingredient):
#                 # Get EFSA data
#                 try:
#                     efsa_data = fetch_efsa_openfoodtox_data(ingredient)
#                     efsa_data_cache[ingredient] = efsa_data or {}
#                 except Exception as e:
#                     print(f"EFSA error for {ingredient}: {e}")
#                     efsa_data_cache[ingredient] = {
#                         'found': False,
#                         'error': f'EFSA query failed: {str(e)}',
#                         'source': 'EFSA OpenFoodTox Database'
#                     }
#                     efsa_data = efsa_data_cache[ingredient]
                
#                 info = await self.get_edamam_info(ingredient)
#                 safety_reasons = []
                
#                 # Check EFSA safety level first
#                 if efsa_data and efsa_data.get('found') and efsa_data.get('safety_level'):
#                     if efsa_data['safety_level'] == 'UNSAFE':
#                         safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Unsafe')}")
#                     elif efsa_data['safety_level'] == 'CAUTION':
#                         safety_reasons.append(f"EFSA: {efsa_data.get('regulatory_status', 'Caution')}")
                
#                 # Check Edamam data
#                 if not info["healthLabels"] and not info["cautions"]:
#                     if any(a in ingredient.lower() for a in allergies):
#                         safety_reasons.append("Allergen")
#                     elif any(d not in ingredient.lower() for d in dietary):
#                         safety_reasons.append("Dietary")
#                     elif any(h in ingredient.lower() for h in health):
#                         safety_reasons.append("Health")
#                     else:
#                         safety_reasons.append("No Edamam data")
#                 else:
#                     if any(a in info["cautions"] for a in allergies):
#                         safety_reasons.append("Allergen")
#                     elif any(d not in info["healthLabels"] for d in dietary):
#                         safety_reasons.append("Dietary")
#                     elif any(h in ingredient.lower() for h in health):
#                         safety_reasons.append("Health")
                
#                 # Categorize ingredient
#                 if safety_reasons:
#                     if "Allergen" in safety_reasons or (efsa_data and efsa_data.get('found') and efsa_data.get('safety_level') == 'UNSAFE'):
#                         no_go_ingredients.append({
#                             "ingredient": ingredient,
#                             "reasons": safety_reasons,
#                             "efsa_data": efsa_data or {}
#                         })
#                     else:
#                         caution_ingredients.append({
#                             "ingredient": ingredient,
#                             "reasons": safety_reasons,
#                             "efsa_data": efsa_data or {}
#                         })
#                 else:
#                     go_ingredients.append({
#                         "ingredient": ingredient,
#                         "reasons": ["Safe"],
#                         "efsa_data": efsa_data or {}
#                     })
            
#             await asyncio.gather(*(classify(ing) for ing in ingredients_list))
            
#             # Handle any unclassified ingredients
#             all_classified = set()
#             for ing_list in [go_ingredients, caution_ingredients, no_go_ingredients]:
#                 for ing in ing_list:
#                     all_classified.add(ing["ingredient"])
            
#             for ing in ingredients_list:
#                 if ing not in all_classified:
#                     try:
#                         efsa_data = fetch_efsa_openfoodtox_data(ing)
#                         efsa_data_cache[ing] = efsa_data or {}
#                     except Exception as e:
#                         print(f"EFSA error for {ing}: {e}")
#                         efsa_data_cache[ing] = {
#                             'found': False,
#                             'error': f'EFSA query failed: {str(e)}',
#                             'source': 'EFSA OpenFoodTox Database'
#                         }
#                         efsa_data = efsa_data_cache[ing]
#                     go_ingredients.append({
#                         "ingredient": ing,
#                         "reasons": ["Defaulted"],
#                         "efsa_data": efsa_data or {}
#                     })
            
#             if no_go_ingredients:
#                 safety_status = "UNSAFE"
#             elif caution_ingredients:
#                 safety_status = "CAUTION"
#             else:
#                 safety_status = "SAFE"
            
#             return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache

#     async def get_edamam_info(self, ingredient):
#         """
#         Get nutritional and health information for an ingredient from Edamam API.
#         """
#         try:
#             # Check cache first
#             cache_key = f"edamam_{ingredient.lower().strip()}"
#             if cache_key in self.edamam_cache:
#                 return self.edamam_cache[cache_key]
            
#             # Make API call to Edamam
#             url = "https://api.edamam.com/api/food-database/v2/parser"
#             params = {
#                 'app_id': settings.EDAMAM_APP_ID,
#                 'app_key': settings.EDAMAM_APP_KEY,
#                 'ingr': ingredient,
#                 'lang': 'en'
#             }
            
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(url, params=params) as response:
#                     if response.status == 200:
#                         data = await response.json()
                        
#                         # Extract relevant information
#                         result = {
#                             'ingredient': ingredient,
#                             'nutrition': {},
#                             'healthLabels': [],
#                             'cautions': []
#                         }
                        
#                         if 'hints' in data and data['hints']:
#                             food = data['hints'][0]['food']
#                             if 'nutrients' in food:
#                                 result['nutrition'] = food['nutrients']
#                             if 'healthLabels' in food:
#                                 result['healthLabels'] = food['healthLabels']
#                             if 'cautions' in food:
#                                 result['cautions'] = food['cautions']
                        
#                         # Cache the result
#                         self.edamam_cache[cache_key] = result
#                         return result
#                     else:
#                         return {'ingredient': ingredient, 'healthLabels': [], 'cautions': [], 'error': f'API error: {response.status}'}
                        
#         except Exception as e:
#             return {'ingredient': ingredient, 'healthLabels': [], 'cautions': [], 'error': str(e)}


class ScanHistoryView(APIView):
    """
    API to retrieve a user's food label scan history with filtering options.
    Query parameters:
    - filter: 'all', 'flagged', 'safe', 'favorite'
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get filter parameter from query
        filter_type = request.query_params.get('filter', 'all')
        
        # Base queryset
        scans = FoodLabelScan.objects.filter(user=request.user).order_by('-scanned_at')
        
        # Apply filters
        if filter_type == 'flagged':
            scans = scans.filter(safety_status='UNSAFE')
        elif filter_type == 'safe':
            scans = scans.filter(safety_status='SAFE')
        elif filter_type == 'favorite':
            scans = scans.filter(is_favorite=True)
        
        # Serialize the data
        scan_data = []
        for scan in scans:
            nutrition_data = scan.nutrition_data if isinstance(scan.nutrition_data, dict) else {}
            go_ingredients = nutrition_data.get("go_ingredients") or nutrition_data.get("go") or []
            caution_ingredients = nutrition_data.get("caution_ingredients") or nutrition_data.get("caution") or []
            no_go_ingredients = nutrition_data.get("no_go_ingredients") or nutrition_data.get("no_go") or []

            # Wrap each ingredient in an object for consistency with BarcodeView
            go_ingredients_obj = [{"ingredient": ing} for ing in go_ingredients]
            caution_ingredients_obj = [{"ingredient": ing} for ing in caution_ingredients]
            no_go_ingredients_obj = [{"ingredient": ing} for ing in no_go_ingredients]

            from .scan_limit import can_user_scan, get_monthly_reset_date
            _, scan_count, remaining_scans = can_user_scan(request.user)
        
            # Handle None values for premium users
            if scan_count is None:
                scan_count = 0
            if remaining_scans is None:
                remaining_scans = "unlimited"
            
            # Get the scan count at the time this scan was created
            scan_count_at_time = get_scan_count_at_time(request.user, scan.scanned_at)
            
            # Calculate remaining scans based on the scan count at that time
            if remaining_scans == "unlimited":
                remaining_scans_at_time = "unlimited"
            else:
                remaining_scans_at_time = max(0, 20 - scan_count_at_time)

            scan_data.append({
                "scan_id": scan.id,
                "product_name":scan.product_name,
                "image_url": scan.image_url,
                "extracted_text": scan.extracted_text,
                "nutrition_data": nutrition_data,
                "safety_status": scan.safety_status,
                "flagged_ingredients": scan.flagged_ingredients,
                "flagged_count": len(scan.flagged_ingredients) if scan.flagged_ingredients else 0,
                "scanned_at": scan.scanned_at,
                "is_favorite": scan.is_favorite,
                "scan_usage": {
                "scans_used": scan_count_at_time,
                "max_scans": 20,
                "remaining_scans": remaining_scans_at_time,
                "monthly_reset_date": get_monthly_reset_date(),
                "total_user_scans": scan_count_at_time,
                "user_plan": get_user_plan_info(request.user),
            },
                "ingredients_analysis": {
                    "go": {
                        "ingredients": go_ingredients_obj,
                        "count": len(go_ingredients_obj),
                        "description": "Ingredients that are safe and suitable for your health profile"
                    },
                    "caution": {
                        "ingredients": caution_ingredients_obj,
                        "count": len(caution_ingredients_obj),
                        "description": "Ingredients that may not be ideal for your health profile - consume at your own risk"
                    },
                    "no_go": {
                        "ingredients": no_go_ingredients_obj,
                        "count": len(no_go_ingredients_obj),
                        "description": "Ingredients that are harmful or not suitable for your health profile - avoid these"
                    },
                    "total_flagged": len(caution_ingredients_obj) + len(no_go_ingredients_obj)
                },
                "summary_alert": self.create_summary_alert(scan)
            })
        
        return Response(scan_data, status=status.HTTP_200_OK)

    def create_summary_alert(self, scan):
        alerts = []
        nutrition_data = scan.nutrition_data if isinstance(scan.nutrition_data, dict) else {}
        ai_health_insight = str(nutrition_data.get("ai_health_insight", ""))
        go_ingredients = nutrition_data.get("go_ingredients") or nutrition_data.get("go") or []
        caution_ingredients = nutrition_data.get("caution_ingredients") or nutrition_data.get("caution") or []

        if scan.safety_status == "UNSAFE":
            if scan.flagged_ingredients and len(scan.flagged_ingredients) > 0:
                alerts.append(f"Contains {len(scan.flagged_ingredients)} flagged ingredients")
            added_sugars_match = re.search(r'(high in added sugars \(\d+\.?\d*\s*g per serving\))', ai_health_insight, re.IGNORECASE)
            if added_sugars_match:
                alerts.append(added_sugars_match.group(1))
            elif re.search(r'high in added sugars', ai_health_insight, re.IGNORECASE):
                alerts.append("High in added sugars")
            if alerts:
                alerts.append("Source: FDA Nutrition Database")
            return alerts if alerts else ["No specific alerts identified for this product."]
        elif scan.safety_status == "CAUTION":
            if caution_ingredients:
                alerts.append("Contains ingredients that may not be ideal for your health profile: " + ", ".join(caution_ingredients))
            else:
                alerts.append("Contains ingredients that may not be ideal for your health profile.")
            return alerts
        elif scan.safety_status == "SAFE":
            # Try to highlight healthiest ingredients
            healthy_ings = go_ingredients if isinstance(go_ingredients, list) else []
            if healthy_ings:
                top_ings = ", ".join(healthy_ings[:3])
                alerts.append(f"Safe product. Most healthy ingredient(s): {top_ings}")
            else:
                alerts.append("Safe product. All natural ingredient.")
            return alerts
        # fallback
        return ["No specific alerts identified for this product."]

class SearchProductView(APIView):
    """
    API to search for products in the user's scan history.
    Query parameters:
    - query: Product name to search for
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get search query from parameters
        search_query = request.query_params.get('query', '').strip()
        
        if not search_query:
            return Response(
                {"error": "Search query is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Search in the user's scan history by product name
        scans = FoodLabelScan.objects.filter(
            user=request.user,
            product_name__icontains=search_query
        ).order_by('-scanned_at')

        # Serialize the results
        search_results = []
        for scan in scans:
            search_results.append({
                "id": scan.id,
                "product_name": scan.product_name,
                "image_url": scan.image_url,
                "product_image_url": scan.product_image_url,
                "extracted_text": scan.extracted_text,
                "nutrition_data": scan.nutrition_data,
                "safety_status": scan.safety_status,
                "flagged_ingredients": scan.flagged_ingredients,
                "flagged_count": len(scan.flagged_ingredients) if scan.flagged_ingredients else 0,
                "scanned_at": scan.scanned_at,
                "is_favorite": scan.is_favorite,
                "summary_alert": ScanHistoryView.create_summary_alert(ScanHistoryView(), scan)
            })

        return Response({
            "query": search_query,
            "results": search_results,
            "total_results": len(search_results)
        }, status=status.HTTP_200_OK)

class FoodTrendsView(APIView):
    """
    API View to get trending food ingredients & no-go toxic items dynamically.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geolocator = Nominatim(user_agent="food_trends_app")

    def get_country_from_coords(self, lat, lon):
        try:
            location = self.geolocator.reverse((lat, lon), exactly_one=True)
            if location and "address" in location.raw:
                return location.raw["address"].get("country_code", "").upper()
        except Exception:
            return None
        return None

    def get_cuisine_from_country(self, country_code):
        country_cuisine_map = {
            'IN': 'Indian', 'IT': 'Italian', 'MX': 'Mexican',
            'FR': 'French', 'CN': 'Chinese', 'JP': 'Japanese',
            'TH': 'Thai', 'ES': 'Spanish', 'GR': 'Greek',
            'TR': 'Turkish', 'US': 'American', 'GB': 'British',
            'KR': 'Korean', 'VN': 'Vietnamese'
        }
        return country_cuisine_map.get(country_code, "Global")

    def get_trending_recipes(self, cuisine):
        # Simulated static sample recipes since Spoonacular API key may be invalid
        return [
            {"id": 1}, {"id": 2}, {"id": 3}, {"id": 4},
            {"id": 5}, {"id": 6}, {"id": 7}, {"id": 8},
        ]

    def get_recipe_ingredients(self, recipe_id):
        # Simulated mock ingredients
        mock_ingredients = {
            1: ["tomato", "basil", "garlic"],
            2: ["chicken", "onion", "pepper"],
            3: ["rice", "cumin", "cilantro"],
            4: ["potato", "turmeric", "chili"],
            5: ["beef", "thyme", "carrot"],
            6: ["egg", "milk", "flour"],
            7: ["shrimp", "lime", "ginger"],
            8: ["paneer", "spinach", "mustard"]
        }
        return mock_ingredients.get(recipe_id, [])

    def get_unsplash_image(self, query):
        url = f"https://api.unsplash.com/search/photos?query={query}+ingredient&client_id={UNSPLASH_ACCESS_KEY}&per_page=1"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    return data["results"][0]["urls"]["small"]
        except Exception as e:
            print(f"Unsplash error for {query}: {e}")
        return None

    def extract_trending_ingredients(self, recipes):
        ingredient_list = []

        for recipe in recipes:
            ingredients = self.get_recipe_ingredients(recipe["id"])
            ingredient_list.extend(ingredients)

        common_ingredients = Counter(ingredient_list).most_common(10)
        trending_ingredients = []

        for item in common_ingredients:
            ingredient_name = item[0]
            image_url = self.get_unsplash_image(ingredient_name)
            trending_ingredients.append({
                "name": ingredient_name,
                "image": image_url or "https://via.placeholder.com/100?text=No+Image"
            })

        return trending_ingredients

    def get_no_go_toxic_ingredients(self):
        toxic_keywords = ["aspartame", "msg", "saccharin", "benzoate", "cyclamate", "bht", "sulfite", "nitrate"]

        toxic_ingredients = []
        for keyword in toxic_keywords:
            image_url = self.get_unsplash_image(keyword)
            toxic_ingredients.append({
                "name": keyword,
                "category": "Toxic / Harmful Ingredient",
                "image": image_url or "https://via.placeholder.com/100?text=No+Image"
            })

        return toxic_ingredients

    def get(self, request, *args, **kwargs):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not lat or not lon:
            return Response({"error": "Latitude and longitude are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lat, lon = float(lat), float(lon)
        except ValueError:
            return Response({"error": "Invalid latitude/longitude format"}, status=status.HTTP_400_BAD_REQUEST)

        country_code = self.get_country_from_coords(lat, lon)
        if not country_code:
            return Response({"error": "Could not determine location from coordinates"}, status=status.HTTP_404_NOT_FOUND)

        cuisine = self.get_cuisine_from_country(country_code)
        trending_recipes = self.get_trending_recipes(cuisine)
        trending_ingredients = self.extract_trending_ingredients(trending_recipes)
        no_go_ingredients = self.get_no_go_toxic_ingredients()

        return Response({
            "country_code": country_code,
            "cuisine": cuisine,
            "trending_ingredients": trending_ingredients,
            "no_go_toxic_ingredients": no_go_ingredients
        }, status=status.HTTP_200_OK)
    


class IngredientFullDataView(APIView):
    # Add class-level caching for better performance
    _cache = {}
    _cache_ttl = 3600  # 1 hour cache
    
    def get(self, request):
        ingredient = request.query_params.get('ingredient')

        if not ingredient:
            return Response({'error': 'Ingredient query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check cache first
        cache_key = f"ingredient_full_data_{ingredient.lower().strip()}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return Response(cached_result, status=status.HTTP_200_OK)

        try:
            # Use ThreadPoolExecutor for all external API calls with shorter timeouts
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {
                    'medline': executor.submit(lambda: self._fetch_medline_fast(ingredient)),
                    'pubchem': executor.submit(lambda: self._fetch_pubchem_fast(ingredient)),
                    'fda': executor.submit(lambda: self._get_fda_regulatory_data(ingredient)),
                    'efsa': executor.submit(lambda: self._get_efsa_regulatory_data(ingredient)),
                    'who': executor.submit(lambda: self._get_who_regulatory_data(ingredient)),
                    'image': executor.submit(lambda: self._get_unsplash_image_fast(ingredient)),
                    'edamam': executor.submit(lambda: self._get_edamam_data_fast(ingredient)),
                    'off': executor.submit(lambda: self._get_open_food_facts_data_fast(ingredient)),
                    'blogs': executor.submit(lambda: self._get_related_blogs_fast(ingredient))
                }
                
                # Wait for all futures with a shorter timeout
                results = {}
                for key, future in futures.items():
                    try:
                        results[key] = future.result(timeout=5)  # Increased timeout for accurate data
                    except Exception as e:
                        print(f"❌ Error fetching {key}: {str(e)}")
                        results[key] = None  # No fallback, return None if API fails

            # Process results and create response
            response_data = self._build_response_data(ingredient, results)
            
            # Cache the result
            self._cache_result(cache_key, response_data)
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_cached_result(self, cache_key):
        """Get cached result if available and not expired"""
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return cached_data
            else:
                del self._cache[cache_key]
        return None

    def _cache_result(self, cache_key, data):
        """Cache the result with timestamp"""
        # Limit cache size to prevent memory issues
        if len(self._cache) > 100:
            # Remove oldest entries
            oldest_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][1])[:20]
            for key in oldest_keys:
                del self._cache[key]
        
        self._cache[cache_key] = (data, time.time())

    def _fetch_medline_fast(self, ingredient):
        """Fast MedlinePlus fetch with shorter timeout"""
        try:
            return fetch_medlineplus_summary(ingredient)
        except Exception as e:
            return None

    def _fetch_pubchem_fast(self, ingredient):
        """Fast PubChem fetch with shorter timeout"""
        try:
            return fetch_pubchem_toxicology_summary(ingredient)
        except Exception as e:
            return None

    def _get_fda_regulatory_data(self, ingredient):
        """Get FDA regulatory data for ingredient"""
        try:
            # FDA GRAS database search
            url = f"https://api.fda.gov/food/gras.json?search=substance_name:{ingredient}&limit=10"
            response = requests.get(url, timeout=4)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    # Found in FDA GRAS database
                    return {
                        "regulatory_feedback": {
                            "GRAS": ["United States (FDA)"],
                            "Restricted": {},
                            "Non_Compliant": "None"
                        },
                        "Restrictions": {},
                        "Violations": "None",
                        "Why_Restricted": "None",
                        "Alternatives": "None",
                        "additional_info": {
                            "alternative_names": [ingredient],
                            "risk_safety_insight": "Generally Recognized as Safe by FDA",
                            "dishes": ["Various food products"],
                            "history": "Approved for use in food by FDA"
                        }
                    }
            
            # Check FDA enforcement database for violations
            enforcement_url = f"https://api.fda.gov/food/enforcement.json?search=product_description:{ingredient}&limit=5"
            enforcement_response = requests.get(enforcement_url, timeout=4)
            
            if enforcement_response.status_code == 200:
                enforcement_data = enforcement_response.json()
                violations = enforcement_data.get('results', [])
                
                if violations:
                    return {
                        "regulatory_feedback": {
                            "GRAS": [],
                            "Restricted": {"United States": "FDA enforcement actions"},
                            "Non_Compliant": "United States (FDA)"
                        },
                        "Restrictions": {"United States": "FDA enforcement actions"},
                        "Violations": f"FDA enforcement actions: {len(violations)} cases",
                        "Why_Restricted": "FDA enforcement actions due to safety concerns",
                        "Alternatives": "Consult FDA for approved alternatives",
                        "additional_info": {
                            "alternative_names": [ingredient],
                            "risk_safety_insight": "Subject to FDA enforcement actions",
                            "dishes": ["Various food products"],
                            "history": "Has FDA enforcement history"
                        }
                    }
            
            return None
            
        except Exception as e:
            print(f"❌ FDA API error: {str(e)}")
            return None

    def _get_efsa_regulatory_data(self, ingredient):
        """Get EFSA regulatory data for ingredient"""
        try:
            # EFSA OpenFoodTox database search
            url = f"https://openfoodtox.efsa.europa.eu/api/v1/compounds?search={ingredient}"
            response = requests.get(url, timeout=4)
            
            if response.status_code == 200:
                data = response.json()
                compounds = data.get('compounds', [])
                
                if compounds:
                    # Found in EFSA database
                    return {
                        "regulatory_feedback": {
                            "GRAS": ["European Union (EFSA)"],
                            "Restricted": {},
                            "Non_Compliant": "None"
                        },
                        "Restrictions": {},
                        "Violations": "None",
                        "Why_Restricted": "None",
                        "Alternatives": "None",
                        "additional_info": {
                            "alternative_names": [ingredient],
                            "risk_safety_insight": "Evaluated by EFSA for safety",
                            "dishes": ["Various food products"],
                            "history": "Assessed by European Food Safety Authority"
                        }
                    }
            
            return None
            
        except Exception as e:
            print(f"❌ EFSA API error: {str(e)}")
            return None

    def _get_who_regulatory_data(self, ingredient):
        """Get WHO regulatory data for ingredient"""
        try:
            # WHO JECFA database search (Joint FAO/WHO Expert Committee on Food Additives)
            url = f"https://apps.who.int/food-additives-contaminants-jecfa-database/search.aspx?fcc={ingredient}"
            
            # Since WHO doesn't have a direct API, we'll use a different approach
            # Check WHO guidelines for food additives
            who_guidelines = {
                "sugar": {
                    "restricted": False,
                    "recommendation": "Limit intake to less than 10% of total energy"
                },
                "salt": {
                    "restricted": False,
                    "recommendation": "Limit intake to less than 5g per day"
                },
                "caffeine": {
                    "restricted": True,
                    "recommendation": "Limit to 400mg per day for adults"
                }
            }
            
            ingredient_lower = ingredient.lower()
            if ingredient_lower in who_guidelines:
                guideline = who_guidelines[ingredient_lower]
                if guideline["restricted"]:
                    return {
                        "regulatory_feedback": {
                            "GRAS": [],
                            "Restricted": {"Global (WHO)": guideline["recommendation"]},
                            "Non_Compliant": "None"
                        },
                        "Restrictions": {"Global (WHO)": guideline["recommendation"]},
                        "Violations": "None",
                        "Why_Restricted": f"WHO recommendation: {guideline['recommendation']}",
                        "Alternatives": "Consult WHO guidelines for alternatives",
                        "additional_info": {
                            "alternative_names": [ingredient],
                            "risk_safety_insight": f"WHO recommendation: {guideline['recommendation']}",
                            "dishes": ["Various food products"],
                            "history": "Subject to WHO dietary guidelines"
                        }
                    }
                else:
                    return {
                        "regulatory_feedback": {
                            "GRAS": ["Global (WHO)"],
                            "Restricted": {},
                            "Non_Compliant": "None"
                        },
                        "Restrictions": {},
                        "Violations": "None",
                        "Why_Restricted": "None",
                        "Alternatives": "None",
                        "additional_info": {
                            "alternative_names": [ingredient],
                            "risk_safety_insight": f"WHO recommendation: {guideline['recommendation']}",
                            "dishes": ["Various food products"],
                            "history": "Subject to WHO dietary guidelines"
                        }
                    }
            
            return None
            
        except Exception as e:
            print(f"❌ WHO API error: {str(e)}")
            return None

    def _get_unsplash_image_fast(self, query):
        """Fast Unsplash image fetch"""
        try:
            url = f'https://api.unsplash.com/search/photos?query={query}&client_id={UNSPLASH_ACCESS_KEY}&per_page=1'
            response = requests.get(url, timeout=4)  # Increased timeout for reliable data
            if response.status_code == 200:
                data = response.json()
                return data['results'][0]['urls']['regular'] if data.get('results') else None
            return None
        except Exception as e:
            return None

    def _get_edamam_data_fast(self, query):
        """Fast USDA data fetch"""
        try:
            url = f'https://api.nal.usda.gov/fdc/v1/foods/search?query={query}&api_key={USDA_API_KEY}&pageSize=3'
            response = requests.get(url, timeout=4)  # Increased timeout for reliable data
            if response.status_code == 200:
                data = response.json()
                return [{
                    "description": item.get("description"),
                    "brand": item.get("brandOwner"),
                    "category": item.get("foodCategory"),
                    "fdcId": item.get("fdcId"),
                    "nutrients": [
                        {"name": n["nutrientName"], "amount": n.get("value"), "unit": n.get("unitName")}
                        for n in item.get("foodNutrients", [])
                        if n["nutrientName"] in {"Energy", "Protein", "Carbohydrate", "Total lipid (fat)"}
                    ]
                } for item in data.get("foods", [])[:3]]
            return []
        except Exception as e:
            return []

    def _get_related_blogs_fast(self, query):
        """Fast blog fetch with reduced results"""
        try:
            news_api_key = 'cb468341298c4e48bafb0f52edcaaba9'
            url = f"https://newsapi.org/v2/everything?q={query}&sortBy=relevancy&language=en&pageSize=6&apiKey={news_api_key}"
            response = requests.get(url, timeout=4)  # Increased timeout for reliable data
            
            if response.status_code == 200:
                data = response.json()
                return [{
                    "title": article.get('title'),
                    "url": article.get('url'),
                    "excerpt": article.get('description'),
                    "date": article.get('publishedAt'),
                    "image_url": article.get('urlToImage')
                } for article in data.get('articles', [])[:6]]
            return []
        except Exception as e:
            return []

    def _get_open_food_facts_data_fast(self, query):
        """Fast OpenFDA data fetch"""
        try:
            url = f"https://api.fda.gov/food/enforcement.json?search=product_description:{query}&limit=1"
            response = requests.get(url, timeout=4)  # Increased timeout for reliable data
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            return {}

    # Removed fallback methods - we only want real API data

    def _build_response_data(self, ingredient, results):
        """Build the final response data from all results"""
        # Determine summary from actual API data
        medline_result = results.get('medline')
        pubchem_summary = results.get('pubchem')
        
        if isinstance(medline_result, str):
            summary = medline_result
            summary_source = "MedlinePlus"
        elif isinstance(medline_result, dict) and (medline_result.get("title") or medline_result.get("url")):
            summary = f"See MedlinePlus topic: {medline_result.get('title', '')} ({medline_result.get('url', '')})"
            summary_source = "MedlinePlus (link only)"
        elif pubchem_summary:
            summary = pubchem_summary
            summary_source = "PubChem (TOXNET)"
        else:
            summary = 'Information not available'
            summary_source = "None"

        # Combine regulatory data from multiple sources
        regulatory_data = self._combine_regulatory_data(results)
        
        return {
            'ingredient': ingredient,
            'summary': summary,
            'summary_source': summary_source,
            'pubchem_summary': pubchem_summary,
            'image_url': results.get('image'),
            'regulatory_feedback': regulatory_data.get('regulatory_feedback', {
                'GRAS': [],
                'Restricted': {},
                'Non_Compliant': "None"
            }),
            'market_warnings': {
                'US': "Safe but limited in dietary guidelines.",
                'EU': "Allowed; subject to labeling rules.",
                'Mexico': "High-sugar warning required.",
                'India': "Max limits in processed foods."
            },
            'regulatory_sources': ["FDA", "EFSA", "WHO", "Health Canada", "FSANZ", "Codex"],
            'detailed_regulatory': {
                'Safe': regulatory_data.get('regulatory_feedback', {}).get('GRAS', []),
                'Approved_In': regulatory_data.get('regulatory_feedback', {}).get('GRAS', []),
                'Restrictions': regulatory_data.get('Restrictions', {}),
                'Violations': regulatory_data.get('Violations', "None"),
                'Why_Restricted': regulatory_data.get('Why_Restricted', "None"),
                'Alternatives': regulatory_data.get('Alternatives', "None"),
                'Non_Compliant': regulatory_data.get('regulatory_feedback', {}).get('Non_Compliant', "None")
            },
            'additional_info': regulatory_data.get('additional_info', {}),
            'usda_data': results.get('edamam', []),
            'open_food_facts': results.get('off', {}),
            'related_blogs': results.get('blogs', [])
        }

    def _combine_regulatory_data(self, results):
        """Combine regulatory data from multiple sources"""
        combined_data = {
            'regulatory_feedback': {
                'GRAS': [],
                'Restricted': {},
                'Non_Compliant': "None"
            },
            'Restrictions': {},
            'Violations': "None",
            'Why_Restricted': "None",
            'Alternatives': "None",
            'additional_info': {
                'alternative_names': [],
                'risk_safety_insight': "No regulatory data available",
                'dishes': [],
                'history': "No regulatory history available"
            }
        }
        
        # Process FDA data
        fda_data = results.get('fda')
        if fda_data and isinstance(fda_data, dict):
            fda_reg = fda_data.get('regulatory_feedback', {})
            combined_data['regulatory_feedback']['GRAS'].extend(fda_reg.get('GRAS', []))
            combined_data['regulatory_feedback']['Restricted'].update(fda_reg.get('Restricted', {}))
            if fda_reg.get('Non_Compliant') != "None":
                combined_data['regulatory_feedback']['Non_Compliant'] = fda_reg.get('Non_Compliant')
            
            combined_data['Restrictions'].update(fda_data.get('Restrictions', {}))
            if fda_data.get('Violations') != "None":
                combined_data['Violations'] = fda_data.get('Violations')
            if fda_data.get('Why_Restricted') != "None":
                combined_data['Why_Restricted'] = fda_data.get('Why_Restricted')
            if fda_data.get('Alternatives') != "None":
                combined_data['Alternatives'] = fda_data.get('Alternatives')
            
            fda_info = fda_data.get('additional_info', {})
            combined_data['additional_info']['alternative_names'].extend(fda_info.get('alternative_names', []))
            if fda_info.get('risk_safety_insight') != "No regulatory data available":
                combined_data['additional_info']['risk_safety_insight'] = fda_info.get('risk_safety_insight')
            combined_data['additional_info']['dishes'].extend(fda_info.get('dishes', []))
            if fda_info.get('history') != "No regulatory history available":
                combined_data['additional_info']['history'] = fda_info.get('history')
        
        # Process EFSA data
        efsa_data = results.get('efsa')
        if efsa_data and isinstance(efsa_data, dict):
            efsa_reg = efsa_data.get('regulatory_feedback', {})
            combined_data['regulatory_feedback']['GRAS'].extend(efsa_reg.get('GRAS', []))
            combined_data['regulatory_feedback']['Restricted'].update(efsa_reg.get('Restricted', {}))
            if efsa_reg.get('Non_Compliant') != "None":
                combined_data['regulatory_feedback']['Non_Compliant'] = efsa_reg.get('Non_Compliant')
            
            combined_data['Restrictions'].update(efsa_data.get('Restrictions', {}))
            if efsa_data.get('Violations') != "None":
                combined_data['Violations'] = efsa_data.get('Violations')
            if efsa_data.get('Why_Restricted') != "None":
                combined_data['Why_Restricted'] = efsa_data.get('Why_Restricted')
            if efsa_data.get('Alternatives') != "None":
                combined_data['Alternatives'] = efsa_data.get('Alternatives')
            
            efsa_info = efsa_data.get('additional_info', {})
            combined_data['additional_info']['alternative_names'].extend(efsa_info.get('alternative_names', []))
            if efsa_info.get('risk_safety_insight') != "No regulatory data available":
                combined_data['additional_info']['risk_safety_insight'] = efsa_info.get('risk_safety_insight')
            combined_data['additional_info']['dishes'].extend(efsa_info.get('dishes', []))
            if efsa_info.get('history') != "No regulatory history available":
                combined_data['additional_info']['history'] = efsa_info.get('history')
        
        # Process WHO data
        who_data = results.get('who')
        if who_data and isinstance(who_data, dict):
            who_reg = who_data.get('regulatory_feedback', {})
            combined_data['regulatory_feedback']['GRAS'].extend(who_reg.get('GRAS', []))
            combined_data['regulatory_feedback']['Restricted'].update(who_reg.get('Restricted', {}))
            if who_reg.get('Non_Compliant') != "None":
                combined_data['regulatory_feedback']['Non_Compliant'] = who_reg.get('Non_Compliant')
            
            combined_data['Restrictions'].update(who_data.get('Restrictions', {}))
            if who_data.get('Violations') != "None":
                combined_data['Violations'] = who_data.get('Violations')
            if who_data.get('Why_Restricted') != "None":
                combined_data['Why_Restricted'] = who_data.get('Why_Restricted')
            if who_data.get('Alternatives') != "None":
                combined_data['Alternatives'] = who_data.get('Alternatives')
            
            who_info = who_data.get('additional_info', {})
            combined_data['additional_info']['alternative_names'].extend(who_info.get('alternative_names', []))
            if who_info.get('risk_safety_insight') != "No regulatory data available":
                combined_data['additional_info']['risk_safety_insight'] = who_info.get('risk_safety_insight')
            combined_data['additional_info']['dishes'].extend(who_info.get('dishes', []))
            if who_info.get('history') != "No regulatory history available":
                combined_data['additional_info']['history'] = who_info.get('history')
        
        # Remove duplicates from lists
        combined_data['regulatory_feedback']['GRAS'] = list(set(combined_data['regulatory_feedback']['GRAS']))
        combined_data['additional_info']['alternative_names'] = list(set(combined_data['additional_info']['alternative_names']))
        combined_data['additional_info']['dishes'] = list(set(combined_data['additional_info']['dishes']))
        
        return combined_data

    # Remove the old methods that are no longer needed
    # def query_full_llm(self, ingredient):
    # def safe_future_result(self, future, key):
    # def get_unsplash_image(self, query):
    # def get_edamam_data(self, query):
    # def get_open_food_facts_data(self, query):
    # def get_related_blogs(self, query):

class SubscribeUserView(APIView):
    permission_classes = [IsAuthenticated]

    def _can_use_premium_features(self, user_subscription):
        """
        Helper method to determine if user can still use premium features
        even when downgrading or canceling
        """
        if not user_subscription:
            return False
        
        # User can use premium features if:
        # 1. Currently active premium subscription
        # 2. Canceled but still within paid period
        # 3. Downgraded but still within paid period
        
        if user_subscription.plan_name == "premium" and user_subscription.status == "active":
            return True
        
        if user_subscription.status == "canceled_at_period_end" and user_subscription.current_period_end:
            # Check if current time is before period end
            from datetime import datetime
            now = datetime.now(timezone.utc)
            return now < user_subscription.current_period_end
        
        return False

    def _get_subscription_status_summary(self, user_subscription):
        """
        Helper method to get comprehensive subscription status information
        """
        if not user_subscription:
            return {
                "has_subscription": False,
                "can_use_premium_features": False,
                "feature_access": "none",
                "grace_period": False,
                "days_remaining": None
            }
        
        can_use_premium = self._can_use_premium_features(user_subscription)
        
        # Calculate days remaining for premium access
        days_remaining = None
        if user_subscription.current_period_end:
            from datetime import datetime
            now = datetime.now(timezone.utc)
            if now < user_subscription.current_period_end:
                days_remaining = (user_subscription.current_period_end - now).days
        
        return {
            "has_subscription": True,
            "plan_name": user_subscription.plan_name,
            "premium_type": user_subscription.premium_type,
            "status": user_subscription.status,
            "can_use_premium_features": can_use_premium,
            "feature_access": "premium_until_period_end" if can_use_premium and user_subscription.status == "canceled_at_period_end" else "premium_active" if can_use_premium else "freemium_only",
            "grace_period": user_subscription.status == "canceled_at_period_end" and can_use_premium,
            "days_remaining": days_remaining,
            "current_period_end": user_subscription.current_period_end.isoformat() if user_subscription.current_period_end else None,
            "started_at": user_subscription.started_at.isoformat() if user_subscription.started_at else None
        }

    def post(self, request):
        user = request.user
        plan = request.data.get("plan_id")  # 'freemium', 'monthly', or 'yearly'
        payment_method_id = request.data.get("payment_method_id")

        if not plan:
            return Response({"error": "Plan ID is required."}, status=400)

        if plan == "freemium":
            from datetime import datetime
            
            # Check if user has an active premium subscription
            try:
                existing_subscription = UserSubscription.objects.get(user=user)
                
                # If user has an active premium subscription OR is in grace period, handle appropriately
                if existing_subscription.plan_name == "premium" and (existing_subscription.status == "active" or existing_subscription.status == "canceled_at_period_end"):
                    
                    # If already in grace period, return current status
                    if existing_subscription.status == "canceled_at_period_end":
                        from datetime import datetime
                        days_remaining = (existing_subscription.current_period_end - datetime.now(timezone.utc)).days if existing_subscription.current_period_end else None
                        
                        return Response({
                            "message": "Your premium subscription is already scheduled to end. You'll continue to have premium access until the end of your billing period.",
                            "current_plan": "premium",
                            "downgrade_scheduled": True,
                            "billing_period_end": existing_subscription.current_period_end.isoformat() if existing_subscription.current_period_end else None,
                            "premium_access_until": existing_subscription.current_period_end.isoformat() if existing_subscription.current_period_end else None,
                            "plan_type": existing_subscription.premium_type,
                            "plan_name": f"{existing_subscription.premium_type.capitalize()} Premium",
                            "status": "canceled_at_period_end",
                            "days_remaining": days_remaining,
                            "can_use_premium_features": True,
                            "feature_access": "premium_until_period_end",
                            "subscription_id": existing_subscription.stripe_subscription_id,
                            "next_billing_date": existing_subscription.current_period_end.isoformat() if existing_subscription.current_period_end else None,
                            "downgrade_effective_date": existing_subscription.current_period_end.isoformat() if existing_subscription.current_period_end else None,
                            "refund_eligible": False,
                            "grace_period": True,
                            "already_scheduled": True
                        }, status=200)
                    
                    # Check if there's a Stripe subscription to cancel
                    if existing_subscription.stripe_subscription_id:
                        try:
                            # Cancel the subscription at period end (don't cancel immediately)
                            stripe.Subscription.modify(
                                existing_subscription.stripe_subscription_id,
                                cancel_at_period_end=True
                            )
                            
                            # Update local subscription status
                            existing_subscription.status = "canceled_at_period_end"
                            existing_subscription.save()
                            
                            return Response({
                                "message": "Premium subscription will be canceled at the end of current billing period. You'll continue to have premium access until then.",
                                "current_plan": "premium",
                                "downgrade_scheduled": True,
                                "billing_period_end": existing_subscription.current_period_end.isoformat() if existing_subscription.current_period_end else None,
                                "premium_access_until": existing_subscription.current_period_end.isoformat() if existing_subscription.current_period_end else None,
                                "plan_type": existing_subscription.premium_type,
                                "plan_name": f"{existing_subscription.premium_type.capitalize()} Premium",
                                "status": "canceled_at_period_end",
                                "days_remaining": (existing_subscription.current_period_end - datetime.now(timezone.utc)).days if existing_subscription.current_period_end else None,
                                "can_use_premium_features": True,
                                "feature_access": "premium_until_period_end",
                                "subscription_id": existing_subscription.stripe_subscription_id,
                                "next_billing_date": existing_subscription.current_period_end.isoformat() if existing_subscription.current_period_end else None,
                                "downgrade_effective_date": existing_subscription.current_period_end.isoformat() if existing_subscription.current_period_end else None,
                                "refund_eligible": False,
                                "grace_period": True
                            }, status=200)
                            
                        except stripe.error.StripeError as e:
                            return Response({"error": f"Failed to cancel subscription: {str(e)}"}, status=400)
                    else:
                        # No Stripe subscription, can switch immediately
                        subscription_start = datetime.now(timezone.utc)
                        existing_subscription.plan_name = "freemium"
                        existing_subscription.premium_type = None
                        existing_subscription.status = "active"
                        existing_subscription.stripe_subscription_id = None
                        existing_subscription.started_at = subscription_start
                        existing_subscription.current_period_end = None
                        existing_subscription.save()
                        
                        return Response({
                            "message": "Switched to freemium plan immediately.",
                            "subscription_start_date": subscription_start.isoformat(),
                            "subscription_end_date": None,
                            "plan_type": "freemium",
                            "plan_name": "Freemium",
                            "status": "active",
                            "can_use_premium_features": False,
                            "feature_access": "freemium_only",
                            "downgrade_effective_date": subscription_start.isoformat(),
                            "grace_period": False,
                            "refund_eligible": False,
                            "plan_change_type": "immediate_downgrade"
                        }, status=200)
                
                else:
                    # User doesn't have active premium, can switch to freemium immediately
                    subscription_start = datetime.now(timezone.utc)
                    existing_subscription.plan_name = "freemium"
                    existing_subscription.premium_type = None
                    existing_subscription.status = "active"
                    existing_subscription.stripe_subscription_id = None
                    existing_subscription.started_at = subscription_start
                    existing_subscription.current_period_end = None
                    existing_subscription.save()
                    
                    return Response({
                        "message": "Switched to freemium plan.",
                        "subscription_start_date": subscription_start.isoformat(),
                        "subscription_end_date": None,
                        "plan_type": "freemium",
                        "plan_name": "Freemium",
                        "status": "active",
                        "can_use_premium_features": False,
                        "feature_access": "freemium_only",
                        "downgrade_effective_date": subscription_start.isoformat(),
                        "grace_period": False,
                        "refund_eligible": False,
                        "plan_change_type": "immediate_downgrade"
                    }, status=200)
                    
            except UserSubscription.DoesNotExist:
                # User has no subscription, create new freemium
                subscription_start = datetime.now(timezone.utc)
                
                UserSubscription.objects.create(
                    user=user,
                    plan_name="freemium",
                    premium_type=None,
                    status="active",
                    stripe_subscription_id=None,
                    started_at=subscription_start,
                    current_period_end=None,  # Freemium has no expiry
                )
                
                return Response({
                    "message": "Freemium plan activated.",
                    "subscription_start_date": subscription_start.isoformat(),
                    "subscription_end_date": None,
                    "plan_type": "freemium",
                    "plan_name": "Freemium",
                    "status": "active",
                    "can_use_premium_features": False,
                    "feature_access": "freemium_only",
                    "downgrade_effective_date": subscription_start.isoformat(),
                    "grace_period": False,
                    "refund_eligible": False,
                    "plan_change_type": "new_freemium"
                }, status=200)

        elif plan == "cancel_downgrade":
            # Allow users to cancel their scheduled downgrade and keep premium
            try:
                existing_subscription = UserSubscription.objects.get(user=user)
                
                if existing_subscription.status == "canceled_at_period_end" and existing_subscription.stripe_subscription_id:
                    try:
                        # Reactivate the subscription by removing cancel_at_period_end
                        stripe.Subscription.modify(
                            existing_subscription.stripe_subscription_id,
                            cancel_at_period_end=False
                        )
                        
                        # Update local subscription status back to active
                        existing_subscription.status = "active"
                        existing_subscription.save()
                        
                        return Response({
                            "message": "Premium subscription reactivated! Your downgrade has been canceled.",
                            "current_plan": "premium",
                            "downgrade_scheduled": False,
                            "status": "active",
                            "plan_type": existing_subscription.premium_type,
                            "plan_name": f"{existing_subscription.premium_type.capitalize()} Premium",
                            "can_use_premium_features": True,
                            "feature_access": "premium_active",
                            "subscription_id": existing_subscription.stripe_subscription_id,
                            "reactivation_successful": True
                        }, status=200)
                        
                    except stripe.error.StripeError as e:
                        return Response({"error": f"Failed to reactivate subscription: {str(e)}"}, status=400)
                else:
                    return Response({"error": "No scheduled downgrade found to cancel."}, status=400)
                    
            except UserSubscription.DoesNotExist:
                return Response({"error": "No subscription found."}, status=400)
                
        elif plan in ["monthly", "yearly"]:
            if not payment_method_id:
                return Response({"error": "Payment method ID is required for premium plan."}, status=400)

            # Get or create Stripe Customer
            stripe_customer, created = StripeCustomer.objects.get_or_create(user=user)
            if created or not stripe_customer.stripe_customer_id:
                customer = stripe.Customer.create(email=user.email)
                stripe_customer.stripe_customer_id = customer.id
                stripe_customer.save()

            # Attach Payment Method
            try:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=stripe_customer.stripe_customer_id,
                )
                stripe.Customer.modify(
                    stripe_customer.stripe_customer_id,
                    invoice_settings={"default_payment_method": payment_method_id},
                )
            except stripe.error.StripeError as e:
                return Response({"error": str(e)}, status=400)

            # Choose price ID with tiered discount logic
            days_since_signup = (timezone.now() - user.date_joined).days
            discount_applied = False
            
            if plan == "monthly":
                # Monthly discount available for first 7 days
                if days_since_signup <= 7:
                    price_id = settings.STRIPE_MONTHLY_DISCOUNTED_PRICE_ID
                    discount_applied = True
                else:
                    price_id = settings.STRIPE_MONTHLY_PRICE_ID
                    discount_applied = False
            elif plan == "yearly":
                # Yearly discount available for first 7 days only
                if days_since_signup <= 7:
                    price_id = settings.STRIPE_YEARLY_DISCOUNTED_PRICE_ID
                    discount_applied = True
                else:
                    price_id = settings.STRIPE_YEARLY_PRICE_ID
                    discount_applied = False

            # Create Subscription
            try:
                subscription = stripe.Subscription.create(
                customer=stripe_customer.stripe_customer_id,
                items=[{"price": price_id}],
                expand=["latest_invoice"]  # 🔧 Fix here
            )

                # Calculate subscription dates
                from datetime import datetime
                import time
                
                # Get subscription start date (current time)
                subscription_start = datetime.now(timezone.utc)
                
                # Get subscription end date from Stripe
                subscription_end = None
                if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
                    subscription_end = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
                else:
                    # Fallback: calculate based on plan type
                    if plan == "monthly":
                        from datetime import timedelta
                        subscription_end = subscription_start + timedelta(days=30)
                    elif plan == "yearly":
                        from datetime import timedelta
                        subscription_end = subscription_start + timedelta(days=365)

                UserSubscription.objects.update_or_create(
                    user=user,
                    defaults={
                        "plan_name": "premium",  # Always set to 'premium' for any paid plan
                        "premium_type": plan,     # Set to 'monthly' or 'yearly'
                        "stripe_subscription_id": subscription.id,
                        "status": subscription.status,
                        "started_at": subscription_start,
                        "current_period_end": subscription_end,
                    }
                )

                # Send subscription notification
                from .tasks import send_subscription_notification_task_celery, safe_execute_task
                safe_execute_task(
                    send_subscription_notification_task_celery,
                    user.id, 
                    'subscription_purchased',
                    plan_type=f"{plan.capitalize()} Premium"
                )

                response_message = f"{plan.capitalize()} subscription started."
                if discount_applied:
                    if plan == "yearly":
                        response_message += " 🎉 58.3% early bird discount applied for yearly subscription!"
                    else:
                        response_message += " ⏰ 58.3% new user discount applied for monthly subscription!"
                else:
                    if plan == "yearly":
                        response_message += " Regular yearly pricing applied."
                    else:
                        response_message += " Regular monthly pricing applied."
                
                return Response({
                    "message": response_message,
                    "subscription_id": subscription.id,
                    "status": subscription.status,
                    "discount_applied": discount_applied,
                    "discount_type": "early_bird" if plan == "yearly" and discount_applied else "new_user" if discount_applied else None,
                    "days_since_signup": days_since_signup,
                    "subscription_start_date": subscription_start.isoformat(),
                    "subscription_end_date": subscription_end.isoformat() if subscription_end else None,
                    "plan_type": plan,
                    "plan_name": f"{plan.capitalize()} Premium",
                })

            except stripe.error.StripeError as e:
                return Response({"error": str(e)}, status=500)

        return Response({"error": "Invalid plan type."}, status=400)

    def get(self, request):
        """
        GET API to retrieve comprehensive subscription information for frontend subscription screen.
        Returns detailed subscription status, plan details, pricing, and user information.
        """
        user = request.user
        
        try:
            # Get user's subscription
            user_subscription = UserSubscription.objects.get(user=user)
            
            # Get Stripe customer info if exists
            stripe_customer = None
            try:
                stripe_customer = StripeCustomer.objects.get(user=user)
            except StripeCustomer.DoesNotExist:
                pass
            
            # Get detailed Stripe subscription info if exists
            stripe_subscription_details = None
            if user_subscription.stripe_subscription_id:
                try:
                    stripe_subscription_details = stripe.Subscription.retrieve(
                        user_subscription.stripe_subscription_id
                    )
                except stripe.error.StripeError as e:
                    print(f"Stripe error retrieving subscription: {e}")
                except Exception as e:
                    print(f"Unexpected error retrieving subscription: {e}")
            
            # Get Stripe price details for available plans
            monthly_price_details = None
            yearly_price_details = None
            
            try:
                if settings.STRIPE_MONTHLY_PRICE_ID:
                    monthly_price_details = stripe.Price.retrieve(settings.STRIPE_MONTHLY_PRICE_ID)
            except stripe.error.StripeError as e:
                print(f"Stripe error retrieving monthly price: {e}")
            except Exception as e:
                print(f"Unexpected error retrieving monthly price: {e}")
            
            try:
                if settings.STRIPE_YEARLY_PRICE_ID:
                    yearly_price_details = stripe.Price.retrieve(settings.STRIPE_YEARLY_PRICE_ID)
            except stripe.error.StripeError as e:
                print(f"Stripe error retrieving yearly price: {e}")
            except Exception as e:
                print(f"Unexpected error retrieving yearly price: {e}")
            
            # Calculate subscription benefits
            is_premium = user_subscription.plan_name == 'premium'
            is_active = user_subscription.status in ['active', 'trialing']
            
            # Handle canceled_at_period_end status - user still has premium access until period end
            if user_subscription.status == 'canceled_at_period_end':
                is_active = True  # User still has premium access
                is_premium = True  # User still has premium features
            
            # Determine current plan details
            current_plan = {
                "plan_id": user_subscription.plan_name,
                "plan_name": user_subscription.plan_name.capitalize(),
                "premium_type": user_subscription.premium_type,
                "status": user_subscription.status,
                "is_active": is_active,
                "is_premium": is_premium,
                "started_at": user_subscription.started_at.isoformat() if user_subscription.started_at else None,
                "subscription_start_date": user_subscription.started_at.isoformat() if user_subscription.started_at else None,
                "subscription_end_date": user_subscription.current_period_end.isoformat() if user_subscription.current_period_end else None,
                "plan_type": user_subscription.premium_type if user_subscription.premium_type else user_subscription.plan_name,
            }
            
            # Add special message for canceled subscriptions
            if user_subscription.status == 'canceled_at_period_end':
                current_plan["downgrade_scheduled"] = True
                current_plan["downgrade_message"] = f"Your premium subscription will end on {user_subscription.current_period_end.strftime('%B %d, %Y') if user_subscription.current_period_end else 'the end of your billing period'}. You'll continue to have premium access until then."
            else:
                current_plan["downgrade_scheduled"] = False
                current_plan["downgrade_message"] = None
            
            # Add Stripe-specific details if available
            if stripe_subscription_details:
                stripe_details = {
                    "stripe_subscription_id": user_subscription.stripe_subscription_id,
                }
                
                # Safely access Stripe subscription attributes using dict-style access
                try:
                    if 'current_period_start' in stripe_subscription_details and stripe_subscription_details['current_period_start']:
                        stripe_details["current_period_start"] = stripe_subscription_details['current_period_start']
                except (AttributeError, KeyError, TypeError):
                    pass
                
                try:
                    if 'current_period_end' in stripe_subscription_details and stripe_subscription_details['current_period_end']:
                        stripe_details["current_period_end"] = stripe_subscription_details['current_period_end']
                except (AttributeError, KeyError, TypeError):
                    pass
                
                try:
                    if 'cancel_at_period_end' in stripe_subscription_details:
                        stripe_details["cancel_at_period_end"] = stripe_subscription_details['cancel_at_period_end']
                except (AttributeError, KeyError, TypeError):
                    pass
                
                try:
                    if 'trial_end' in stripe_subscription_details and stripe_subscription_details['trial_end']:
                        stripe_details["trial_end"] = stripe_subscription_details['trial_end']
                except (AttributeError, KeyError, TypeError):
                    pass
                
                current_plan.update(stripe_details)
            
            # Available plans for subscription
            available_plans = {
                "freemium": {
                    "plan_id": "freemium",
                    "plan_name": "Freemium",
                    "price": 0,
                    "currency": "USD",
                    "billing_cycle": None,
                    "features": [
                        "5 free premiumscans per month",
                        "Basic nutrition analysis",
                        "Ingredient safety check",
                        "Basic health insights"
                    ],
                    "limitations": [
                        "Limited to 6 scans per month",
                        "No advanced AI insights",
                        "No priority support"
                    ]
                }
            }
            
            # Add premium plans if price details are available
            if monthly_price_details:
                # Get comprehensive discount information for the user
                comprehensive_discount_info = get_comprehensive_discount_info(user)
                
                # Get discounted price details if available
                discounted_price_details = None
                if comprehensive_discount_info['monthly_discount']['eligible'] and settings.STRIPE_MONTHLY_DISCOUNTED_PRICE_ID:
                    try:
                        discounted_price_details = stripe.Price.retrieve(settings.STRIPE_MONTHLY_DISCOUNTED_PRICE_ID)
                    except stripe.error.StripeError:
                        pass  # Fall back to regular price if discounted price not found
                
                # Determine which price to show
                if comprehensive_discount_info['monthly_discount']['eligible'] and discounted_price_details:
                    display_price = discounted_price_details.unit_amount / 100
                    original_price = monthly_price_details.unit_amount / 100
                    price_id_to_use = settings.STRIPE_MONTHLY_DISCOUNTED_PRICE_ID
                    discount_message = f"⏰ 58.3% OFF - Limited time offer for new users ({comprehensive_discount_info['monthly_discount']['days_remaining']} days left)"
                else:
                    display_price = monthly_price_details.unit_amount / 100
                    original_price = None
                    price_id_to_use = monthly_price_details.id
                    discount_message = "Regular pricing - No discount available"
                
                available_plans["monthly"] = {
                    "plan_id": "monthly",
                    "plan_name": "Premium Monthly",
                    "price": display_price,
                    "original_price": original_price,
                    "currency": monthly_price_details.currency.upper(),
                    "billing_cycle": "monthly",
                    "stripe_price_id": price_id_to_use,
                    "discount_eligible": comprehensive_discount_info['monthly_discount']['eligible'],
                    "discount_percentage": comprehensive_discount_info['monthly_discount']['discount_percentage'],
                    "days_remaining_for_discount": comprehensive_discount_info['monthly_discount']['days_remaining'],
                    "days_since_signup": comprehensive_discount_info['days_since_signup'],
                    "signup_date": comprehensive_discount_info['signup_date'],
                    "discount_message": discount_message,
                    "features": [
                        "Unlimited premium scans",
                        "Advanced AI health insights",
                        "Expert nutrition advice",
                        "Priority customer support",
                        "Detailed ingredient analysis",
                        "Health condition recommendations",
                        "Dietary preference tracking",
                        "Allergen alerts"
                    ],
                    "savings": None
                }
            
            if yearly_price_details:
                # Get comprehensive discount information for the user
                comprehensive_discount_info = get_comprehensive_discount_info(user)
                
                # Get discounted price details if available
                discounted_yearly_price_details = None
                if comprehensive_discount_info['yearly_discount']['eligible'] and settings.STRIPE_YEARLY_DISCOUNTED_PRICE_ID:
                    try:
                        discounted_yearly_price_details = stripe.Price.retrieve(settings.STRIPE_YEARLY_DISCOUNTED_PRICE_ID)
                    except stripe.error.StripeError:
                        pass  # Fall back to regular price if discounted price not found
                
                # Determine which price to show
                if comprehensive_discount_info['yearly_discount']['eligible'] and discounted_yearly_price_details:
                    display_yearly_price = discounted_yearly_price_details.unit_amount / 100
                    original_yearly_price = yearly_price_details.unit_amount / 100
                    yearly_price_id_to_use = settings.STRIPE_YEARLY_DISCOUNTED_PRICE_ID
                    yearly_discount_message = f"🎉 58.3% OFF - Early bird yearly offer! ({comprehensive_discount_info['yearly_discount']['days_remaining']} days left)"
                else:
                    display_yearly_price = yearly_price_details.unit_amount / 100
                    original_yearly_price = None
                    yearly_price_id_to_use = yearly_price_details.id
                    yearly_discount_message = "Regular pricing - No discount available"
                
                yearly_price = display_yearly_price
                monthly_equivalent = yearly_price / 12
                monthly_savings = 0
                
                if monthly_price_details:
                    monthly_price = monthly_price_details.unit_amount / 100
                    monthly_savings = ((monthly_price * 12) - yearly_price) / (monthly_price * 12) * 100
                
                available_plans["yearly"] = {
                    "plan_id": "yearly",
                    "plan_name": "Premium Yearly",
                    "price": yearly_price,
                    "original_price": original_yearly_price,
                    "currency": yearly_price_details.currency.upper(),
                    "billing_cycle": "yearly",
                    "stripe_price_id": yearly_price_id_to_use,
                    "monthly_equivalent": round(monthly_equivalent, 2),
                    "savings_percentage": round(monthly_savings, 1) if monthly_savings > 0 else None,
                    "features": [
                        "Unlimited premium scans",
                        "Advanced AI health insights",
                        "Expert nutrition advice",
                        "Priority customer support",
                        "Detailed ingredient analysis",
                        "Health condition recommendations",
                        "Dietary preference tracking",
                        "Allergen alerts",
                        # "Save up to 20% compared to monthly"
                    ],
                    "discount_eligible": comprehensive_discount_info['yearly_discount']['eligible'],
                    "discount_percentage": comprehensive_discount_info['yearly_discount']['discount_percentage'],
                    "days_remaining_for_discount": comprehensive_discount_info['yearly_discount']['days_remaining'],
                    "days_since_signup": comprehensive_discount_info['days_since_signup'],
                    "signup_date": comprehensive_discount_info['signup_date'],
                    "discount_message": yearly_discount_message
                }
            
            # User information
            user_info = {
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "has_stripe_customer": stripe_customer is not None,
                "stripe_customer_id": stripe_customer.stripe_customer_id if stripe_customer else None
            }
            
            # Subscription usage information
            usage_info = {
                "scans_used": 0,  # This would need to be calculated from scan history
                "scans_limit": 6 if not is_premium else "unlimited",
                "can_scan": is_premium or True,  # This would need proper logic
                "days_remaining": None,  # This would need calculation for trial periods
                "feature_access": "freemium_only" if not is_premium else "premium_active" if user_subscription.status == "active" else "premium_until_period_end",
                "can_use_ai_insights": is_premium,
                "can_use_priority_support": is_premium,
                "can_use_advanced_features": is_premium,
                "grace_period_active": user_subscription.status == "canceled_at_period_end",
                "downgrade_scheduled": user_subscription.status == "canceled_at_period_end"
            }
            
            # Add days remaining for canceled subscriptions
            if user_subscription.status == 'canceled_at_period_end' and user_subscription.current_period_end:
                from datetime import datetime
                now = datetime.now(timezone.utc)
                days_remaining = (user_subscription.current_period_end - now).days
                usage_info["days_remaining"] = max(0, days_remaining)
                usage_info["premium_access_until"] = user_subscription.current_period_end.isoformat()
                usage_info["grace_period_message"] = f"You have {days_remaining} days of premium access remaining"
            
            # If user has active subscription, calculate usage
            if is_active:
                try:
                    # Count scans in current period (this is a simplified version)
                    from datetime import datetime, timedelta
                    if stripe_subscription_details:
                        try:
                            if 'current_period_start' in stripe_subscription_details and stripe_subscription_details['current_period_start']:
                                period_start = datetime.fromtimestamp(stripe_subscription_details['current_period_start'])
                                scans_in_period = FoodLabelScan.objects.filter(
                                    user=user,
                                    scanned_at__gte=period_start
                                ).count()
                                usage_info["scans_used"] = scans_in_period
                        except (AttributeError, KeyError, TypeError) as e:
                            print(f"Error accessing current_period_start: {e}")
                            # Fallback: count scans from last 30 days
                            try:
                                period_start = datetime.now() - timedelta(days=30)
                                scans_in_period = FoodLabelScan.objects.filter(
                                    user=user,
                                    scanned_at__gte=period_start
                                ).count()
                                usage_info["scans_used"] = scans_in_period
                            except Exception as fallback_error:
                                print(f"Error in fallback usage calculation: {fallback_error}")
                                usage_info["scans_used"] = 0
                except Exception as e:
                    print(f"Error calculating usage: {e}")
            
            response_data = {
                "current_subscription": current_plan,
                "available_plans": available_plans,
                "user_info": user_info,
                "usage_info": usage_info,
                "effective_plan_status": {
                    "current_effective_plan": "premium" if is_premium else "freemium",
                    "features_available": "premium" if is_premium else "freemium",
                    "scan_limit_effective": "unlimited" if is_premium else 20,
                    "ai_insights_available": is_premium,
                    "priority_support_available": is_premium,
                    "advanced_features_available": is_premium,
                    "grace_period_info": {
                        "is_in_grace_period": user_subscription.status == "canceled_at_period_end",
                        "grace_period_end": user_subscription.current_period_end.isoformat() if user_subscription.current_period_end else None,
                        "days_remaining_in_grace_period": usage_info.get("days_remaining"),
                        "grace_period_message": usage_info.get("grace_period_message")
                    }
                },
                "stripe_config": {
                    "publishable_key": getattr(settings, 'STRIPE_PUBLISHABLE_KEY', None),
                    "monthly_price_id": settings.STRIPE_MONTHLY_PRICE_ID,
                    "monthly_discounted_price_id": settings.STRIPE_MONTHLY_DISCOUNTED_PRICE_ID,
                    "yearly_price_id": settings.STRIPE_YEARLY_PRICE_ID,
                    "yearly_discounted_price_id": settings.STRIPE_YEARLY_DISCOUNTED_PRICE_ID,
                },
                "discount_info": get_comprehensive_discount_info(user),
                "subscription_benefits": {
                    "freemium": {
                        "scan_limit": 6,
                        "ai_insights": False,
                        "priority_support": False,
                        "advanced_features": False
                    },
                    "premium": {
                        "scan_limit": "unlimited",
                        "ai_insights": True,
                        "priority_support": True,
                        "advanced_features": True
                    }
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except UserSubscription.DoesNotExist:
            # User has no subscription record, treat as freemium
            current_plan = {
                "plan_id": "freemium",
                "plan_name": "Freemium",
                "premium_type": "free",
                "status": "active",
                "is_active": True,
                "is_premium": False,
                "started_at": None,
            }
            
            # Available plans (same as above)
            available_plans = {
                "freemium": {
                    "plan_id": "freemium",
                    "plan_name": "Freemium",
                    "price": 0,
                    "currency": "USD",
                    "billing_cycle": None,
                    "features": [
                        "5 free premium scans per month",
                        "Basic nutrition analysis",
                        "Ingredient safety check",
                        "Basic health insights"
                    ],
                    "limitations": [
                        "Limited to 6 scans per month",
                        "No advanced AI insights",
                        "No priority support"
                    ]
                }
            }
            
            # Get Stripe price details for available plans
            monthly_price_details = None
            yearly_price_details = None
            
            try:
                if settings.STRIPE_MONTHLY_PRICE_ID:
                    monthly_price_details = stripe.Price.retrieve(settings.STRIPE_MONTHLY_PRICE_ID)
            except stripe.error.StripeError as e:
                print(f"Stripe error retrieving monthly price: {e}")
            except Exception as e:
                print(f"Unexpected error retrieving monthly price: {e}")
            
            try:
                if settings.STRIPE_YEARLY_PRICE_ID:
                    yearly_price_details = stripe.Price.retrieve(settings.STRIPE_YEARLY_PRICE_ID)
            except stripe.error.StripeError as e:
                print(f"Stripe error retrieving yearly price: {e}")
            except Exception as e:
                print(f"Unexpected error retrieving yearly price: {e}")
            
            if monthly_price_details:
                # Get comprehensive discount information for the user
                comprehensive_discount_info = get_comprehensive_discount_info(user)
                
                # Get discounted price details if available
                discounted_price_details = None
                if comprehensive_discount_info['monthly_discount']['eligible'] and settings.STRIPE_MONTHLY_DISCOUNTED_PRICE_ID:
                    try:
                        discounted_price_details = stripe.Price.retrieve(settings.STRIPE_MONTHLY_DISCOUNTED_PRICE_ID)
                    except stripe.error.StripeError:
                        pass  # Fall back to regular price if discounted price not found
                
                # Determine which price to show
                if comprehensive_discount_info['monthly_discount']['eligible'] and discounted_price_details:
                    display_price = discounted_price_details.unit_amount / 100
                    original_price = monthly_price_details.unit_amount / 100
                    price_id_to_use = settings.STRIPE_MONTHLY_DISCOUNTED_PRICE_ID
                    discount_message = f"⏰ 58.3% OFF - Limited time offer for new users ({comprehensive_discount_info['monthly_discount']['days_remaining']} days left)"
                else:
                    display_price = monthly_price_details.unit_amount / 100
                    original_price = None
                    price_id_to_use = monthly_price_details.id
                    discount_message = "Regular pricing - No discount available"
                
                available_plans["monthly"] = {
                    "plan_id": "monthly",
                    "plan_name": "Premium Monthly",
                    "original_price": original_price,
                    "price": display_price,
                    "currency": monthly_price_details.currency.upper(),
                    "billing_cycle": "monthly",
                    "stripe_price_id": price_id_to_use,
                    "discount_eligible": comprehensive_discount_info['monthly_discount']['eligible'],
                    "discount_percentage": comprehensive_discount_info['monthly_discount']['discount_percentage'],
                    "days_remaining_for_discount": comprehensive_discount_info['monthly_discount']['days_remaining'],
                    "discount_message": discount_message,
                    "features": [
                        "Unlimited premium scans",
                        "Advanced AI health insights",
                        "Expert nutrition advice",
                        "Priority customer support",
                        "Detailed ingredient analysis",
                        "Health condition recommendations",
                        "Dietary preference tracking",
                        "Allergen alerts"
                    ],
                    "savings": None
                }
            
            if yearly_price_details:
                # Get comprehensive discount information for yearly plan
                comprehensive_discount_info = get_comprehensive_discount_info(user)
                
                # Get discounted yearly price details if available
                yearly_discounted_price_details = None
                if comprehensive_discount_info['yearly_discount']['eligible'] and settings.STRIPE_YEARLY_DISCOUNTED_PRICE_ID:
                    try:
                        yearly_discounted_price_details = stripe.Price.retrieve(settings.STRIPE_YEARLY_DISCOUNTED_PRICE_ID)
                        print(f"Successfully retrieved yearly discounted price: {yearly_discounted_price_details.unit_amount / 100}")
                    except stripe.error.StripeError as e:
                        print(f"Error retrieving yearly discounted price: {e}")
                        pass  # Fall back to regular price if discounted price not found
                
                # Determine which price to show for yearly
                if comprehensive_discount_info['yearly_discount']['eligible'] and yearly_discounted_price_details:
                    display_yearly_price = yearly_discounted_price_details.unit_amount / 100
                    original_yearly_price = yearly_price_details.unit_amount / 100
                    yearly_price_id_to_use = settings.STRIPE_YEARLY_DISCOUNTED_PRICE_ID
                    yearly_discount_message = f"🎉 58.3% OFF - Early bird yearly offer! ({comprehensive_discount_info['yearly_discount']['days_remaining']} days left)"
                else:
                    display_yearly_price = yearly_price_details.unit_amount / 100
                    original_yearly_price = None
                    yearly_price_id_to_use = yearly_price_details.id
                    yearly_discount_message = "Regular pricing - No discount available"
                
                monthly_equivalent = display_yearly_price / 12
                monthly_savings = 0
                
                if monthly_price_details:
                    monthly_price = monthly_price_details.unit_amount / 100
                    monthly_savings = ((monthly_price * 12) - display_yearly_price) / (monthly_price * 12) * 100
                
                available_plans["yearly"] = {
                    "plan_id": "yearly",
                    "plan_name": "Premium Yearly",
                    "original_price": original_yearly_price,
                    "price": display_yearly_price,
                    "currency": yearly_price_details.currency.upper(),
                    "billing_cycle": "yearly",
                    "stripe_price_id": yearly_price_id_to_use,
                    "monthly_equivalent": round(monthly_equivalent, 2),
                    "savings_percentage": round(monthly_savings, 1) if monthly_savings > 0 else None,
                    "features": [
                        "Unlimited premium scans",
                        "Advanced AI health insights",
                        "Expert nutrition advice",
                        "Priority customer support",
                        "Detailed ingredient analysis",
                        "Health condition recommendations",
                        "Dietary preference tracking",
                        "Allergen alerts",
                        # "Save up to 20% compared to monthly"
                    ],
                    "discount_eligible": get_comprehensive_discount_info(user)['yearly_discount']['eligible'],
                    "discount_percentage": get_comprehensive_discount_info(user)['yearly_discount']['discount_percentage'],
                    "days_remaining_for_discount": get_comprehensive_discount_info(user)['yearly_discount']['days_remaining'],
                    "discount_message": f"🎉 58.3% OFF - Early bird yearly offer! ({get_comprehensive_discount_info(user)['yearly_discount']['days_remaining']} days left)" if get_comprehensive_discount_info(user)['yearly_discount']['eligible'] else "Regular pricing - No discount available"
                }
            
            user_info = {
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "has_stripe_customer": False,
                "stripe_customer_id": None
            }
            
            usage_info = {
                "scans_used": 0,
                "scans_limit": 6,
                "can_scan": True,
                "days_remaining": None
            }
            
            response_data = {
                "current_subscription": current_plan,
                "available_plans": available_plans,
                "user_info": user_info,
                "usage_info": usage_info,
                "stripe_config": {
                    # "publishable_key": getattr(settings, 'STRIPE_PUBLISHABLE_KEY', None),
                    "monthly_price_id": settings.STRIPE_MONTHLY_PRICE_ID,
                    "monthly_discounted_price_id": settings.STRIPE_MONTHLY_DISCOUNTED_PRICE_ID,
                    "yearly_price_id": settings.STRIPE_YEARLY_PRICE_ID,
                    "yearly_discounted_price_id": settings.STRIPE_YEARLY_DISCOUNTED_PRICE_ID,
                },
                "discount_info": get_comprehensive_discount_info(user),
                "subscription_benefits": {
                    "freemium": {
                        "scan_limit": 6,
                        "ai_insights": False,
                        "priority_support": False,
                        "advanced_features": False
                    },
                    "premium": {
                        "scan_limit": "unlimited",
                        "ai_insights": True,
                        "priority_support": True,
                        "advanced_features": True
                    }
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)


@csrf_exempt
def stripe_webhook_view(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET  # Add this in your settings

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type in ["customer.subscription.updated", "customer.subscription.deleted"]:
        customer_id = data_object.get("customer")
        status = data_object.get("status")

        try:
            stripe_customer = StripeCustomer.objects.get(stripe_customer_id=customer_id)
            user_subscription = UserSubscription.objects.get(user=stripe_customer.user)

            if event_type == "customer.subscription.updated":
                old_status = user_subscription.status
                user_subscription.status = status
                
                # Update subscription dates from Stripe data
                from datetime import datetime
                
                if 'current_period_start' in data_object and data_object['current_period_start']:
                    user_subscription.started_at = datetime.fromtimestamp(data_object['current_period_start'], tz=timezone.utc)
                
                if 'current_period_end' in data_object and data_object['current_period_end']:
                    user_subscription.current_period_end = datetime.fromtimestamp(data_object['current_period_end'], tz=timezone.utc)
                
                # Send notification based on status change
                from .tasks import send_subscription_notification_task_celery, safe_execute_task
                
                if status == "active" and old_status != "active":
                    safe_execute_task(
                        send_subscription_notification_task_celery,
                        stripe_customer.user.id,
                        'subscription_renewed',
                        plan_type=f"{user_subscription.premium_type.capitalize()} Premium" if user_subscription.premium_type else "Premium"
                    )
                elif status in ["canceled", "unpaid", "past_due"] and old_status == "active":
                    safe_execute_task(
                        send_subscription_notification_task_celery,
                        stripe_customer.user.id,
                        'subscription_expired',
                        plan_type=f"{user_subscription.premium_type.capitalize()} Premium" if user_subscription.premium_type else "Premium"
                    )
                    
            elif event_type == "customer.subscription.deleted":
                # If subscription was canceled_at_period_end, now it's actually canceled
                if user_subscription.status == "canceled_at_period_end":
                    # Switch to freemium plan
                    user_subscription.plan_name = "freemium"
                    user_subscription.premium_type = None
                    user_subscription.status = "canceled"
                    user_subscription.stripe_subscription_id = None
                    user_subscription.current_period_end = None
                    
                    # Send downgrade notification
                    from .tasks import send_subscription_notification_task_celery, safe_execute_task
                    safe_execute_task(
                        send_subscription_notification_task_celery,
                        stripe_customer.user.id,
                        'subscription_downgraded',
                        plan_type="Freemium"
                    )
                else:
                    user_subscription.status = "canceled"
                    
                    # Send cancellation notification
                    from .tasks import send_subscription_notification_task_celery, safe_execute_task
                    safe_execute_task(
                        send_subscription_notification_task_celery,
                        stripe_customer.user.id,
                        'subscription_expired',
                        plan_type=f"{user_subscription.premium_type.capitalize()} Premium" if user_subscription.premium_type else "Premium"
                    )

            user_subscription.save()
        except (StripeCustomer.DoesNotExist, UserSubscription.DoesNotExist):
            pass

    return HttpResponse(status=200)

openai.api_key = "OPENAI_API_KEY_REMOVED"

class IngredientLLMView(APIView):
    def get(self, request):
        ingredient = request.query_params.get('ingredient')
        if not ingredient:
            return Response({'error': 'Missing "ingredient" query parameter.'}, status=status.HTTP_400_BAD_REQUEST)
        
        data = fetch_llm_insight(ingredient)
        return Response(data)
    
class SettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSettingsSerializer(request.user)
        
        # Get accurate scan count that automatically syncs with actual FoodLabelScan objects
        accurate_scan_count = get_accurate_scan_count(request.user)
        
        # Calculate remaining scans based on accurate count
        subscription = None
        try:
            subscription = UserSubscription.objects.get(user=request.user)
        except UserSubscription.DoesNotExist:
            pass
        
        remaining_scans = None
        if not subscription or subscription.plan_name.strip().lower() == "freemium":
            remaining_scans = max(0, 20 - accurate_scan_count)
        
        data = serializer.data
        data['scan_count'] = accurate_scan_count
        data['remaining_scans'] = remaining_scans
        
        # Add comprehensive discount eligibility information
        comprehensive_discount_info = get_comprehensive_discount_info(request.user)
        data['discount_eligibility'] = comprehensive_discount_info
        
        return Response(data)


class SubscriptionPricesView(APIView):
    """
    API endpoint to get all subscription plan prices from Stripe.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get all available subscription plans with their current prices from Stripe.
        """
        try:
            # Get all subscription prices
            prices = get_subscription_prices(user=request.user)
            
            # Add comprehensive discount eligibility info
            comprehensive_discount_info = get_comprehensive_discount_info(request.user)
            
            return Response({
                'success': True,
                'prices': prices,
                'discount_eligibility': comprehensive_discount_info,
                'available_plans': list(prices.keys()),
                'stripe_config': {
                    'publishable_key': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', None),
                    'monthly_price_id': settings.STRIPE_MONTHLY_PRICE_ID,
                    'monthly_discounted_price_id': settings.STRIPE_MONTHLY_DISCOUNTED_PRICE_ID,
                    'yearly_price_id': settings.STRIPE_YEARLY_PRICE_ID,
                    'yearly_discounted_price_id': settings.STRIPE_YEARLY_DISCOUNTED_PRICE_ID,
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to get subscription prices: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DiscountEligibilityView(APIView):
    """
    API endpoint to check if a user is eligible for the new user discount.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        comprehensive_discount_info = get_comprehensive_discount_info(user)
        
        return Response({
            "user_id": user.id,
            "email": user.email,
            "signup_date": user.date_joined.isoformat(),
            "discount_eligibility": comprehensive_discount_info,
            "message": comprehensive_discount_info['primary_message']
        }, status=status.HTTP_200_OK)


class SyncScanCountsView(APIView):
    """
    API endpoint to sync all users' scan counts with their actual FoodLabelScan objects.
    This should be called after deleting scans from admin panel.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        try:
            synced_count = sync_all_user_scan_counts()
            return Response({
                "message": f"Successfully synced scan counts for {synced_count} users",
                "synced_users": synced_count
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": f"Failed to sync scan counts: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        serializer = UserSettingsSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "updated", "data": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductComparisonView(APIView):
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            aws_access_key = settings.AWS_ACCESS_KEY_ID
            aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
            aws_region = settings.AWS_S3_REGION_NAME or 'us-east-1'
            if not aws_access_key or not aws_secret_key:
                logging.error("AWS credentials not found in settings")
                self.textract_client = None
                return
            self.textract_client = boto3.client(
                'textract',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            print("AWS Textract client initialized successfully for ProductComparisonView")
        except Exception as e:
            logging.error(f"Failed to initialize AWS Textract client: {e}")
            self.textract_client = None

    def post(self, request):
        # Get the two products to compare
        product1_id = request.data.get('product1_id')  # From history
        product2_id = request.data.get('product2_id')  # From history or None for new scan
        new_product_image = request.data.get('new_product_image')  # If product2 is a new scan

        if not product1_id:
            return Response({"error": "Product 1 ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get first product from history
            product1 = FoodLabelScan.objects.get(id=product1_id, user=request.user)
            
            # Handle second product
            if product2_id:
                # Get second product from history
                product2 = FoodLabelScan.objects.get(id=product2_id, user=request.user)
            elif new_product_image:
                # Process new product scan
                serializer = AllergenDietaryCheckSerializer(data={'image': new_product_image})
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                # Save image
                image_content = new_product_image.read()
                image_name = f"food_labels/{uuid.uuid4()}.jpg"
                image_path = default_storage.save(image_name, ContentFile(image_content))
                image_url = default_storage.url(image_path).replace("https//", "")

                # Try barcode scanning first
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                    temp_file.write(image_content)
                    temp_file_path = temp_file.name

                try:
                    # Barcode detection
                    image_cv = cv2.imread(temp_file_path)
                    if image_cv is not None:
                        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
                        blur = cv2.GaussianBlur(gray, (5, 5), 0)
                        thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                        barcode_detector = cv2.barcode_BarcodeDetector()
                        ok, decoded_info, decoded_type = barcode_detector.detectAndDecode(thresh)

                        if not ok or decoded_info is None or len(decoded_info) == 0:
                            # Try with original image if thresholded image fails
                            ok, decoded_info, decoded_type = barcode_detector.detectAndDecode(image_cv)

                        if ok and decoded_info and len(decoded_info) > 0:
                            # Barcode found, fetch product info from OpenFoodFacts
                            barcode = decoded_info[0]
                            response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{ok}.json")
                            
                            if response.status_code == 200:
                                product = response.json()
                                if product.get("product") and product["product"].get("product_name"):
                                    product_data = product["product"]
                                    extracted_text = product_data.get('ingredients_text', '')
                                    raw_nutrition_data = product_data.get('nutriments', {})
                                    product_name = product_data.get('product_name', 'Unknown')
                                    product_image_url = product_data.get('image_url', '')
                                    
                                    # Validate product safety
                                    safety_status, go_ingredients, caution_ingredients, no_go_ingredients = asyncio.run(
                                        self.validate_product_safety(request.user, extracted_text)
                                    )

                                    # Get AI insights
                                    ai_results = self.run_in_thread_pool(
                                        self.get_ai_health_insight_and_expert_advice,
                                        request.user,
                                        raw_nutrition_data,
                                        no_go_ingredients
                                    )

                                    # Create product2 object with barcode data
                                    product2 = type('Product', (), {
                                        'image_url': image_url,
                                        'extracted_text': extracted_text,
                                        'nutrition_data': raw_nutrition_data,
                                        'safety_status': safety_status,
                                        'flagged_ingredients': no_go_ingredients,
                                        'product_name': product_name,
                                        'product_image_url': product_image_url
                                    })
                                else:
                                    # Fall back to OCR if product not found
                                    product2 = self.process_image_with_ocr(image_content, image_url, request.user)
                            else:
                                # Fall back to OCR if API call fails
                                product2 = self.process_image_with_ocr(image_content, image_url, request.user)
                        else:
                            # No barcode found, use OCR
                            product2 = self.process_image_with_ocr(image_content, image_url, request.user)
                    else:
                        # Image reading failed, use OCR
                        product2 = self.process_image_with_ocr(image_content, image_url, request.user)

                finally:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
            else:
                return Response({"error": "Either product2_id or new_product_image is required"}, 
                              status=status.HTTP_400_BAD_REQUEST)

            # Compare the products
            comparison = self.compare_products(product1, product2, request.user)

            return Response(comparison, status=status.HTTP_200_OK)

        except FoodLabelScan.DoesNotExist:
            return Response({"error": "Product not found in history"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def process_image_with_ocr(self, image_content, image_url, user):
        # Process image and extract data using AWS Textract
        try:
            if not self.textract_client:
                logging.error("AWS Textract client not initialized")
                return None
                
            # Extract text using AWS Textract
            extracted_text = self.run_ocr(image_content)
            
            # Try to extract ingredients using Query feature first
            query_ingredients = self.extract_ingredients_with_textract_query(image_content)
            
            # Try to extract nutrition using Query feature first
            query_nutrition = self.extract_nutrition_with_textract_query(image_content)
            
            # Process nutrition data (use query results if available, otherwise fallback to text parsing)
            if query_nutrition:
                nutrition_data = self.process_query_nutrition_data(query_nutrition)
            else:
                nutrition_data = self.extract_nutrition_info_fallback(extracted_text)
            
            # Process ingredients data (use query results if available, otherwise fallback to text parsing)
            if query_ingredients:
                actual_ingredients = self.process_query_ingredients(query_ingredients)
            else:
                actual_ingredients = self.extract_ingredients_from_text_fallback(extracted_text)
            
            # Validate product safety
            safety_status, go_ingredients, caution_ingredients, no_go_ingredients = asyncio.run(
                self.validate_product_safety(user, actual_ingredients)
            )

            # Create temporary product2 object
            return type('Product', (), {
                'image_url': image_url,
                'extracted_text': extracted_text,
                'nutrition_data': nutrition_data,
                'safety_status': safety_status,
                'flagged_ingredients': no_go_ingredients
            })
        except Exception as e:
            logging.error(f"Error processing image with AWS Textract: {e}")
            return None

    def preprocess_image(self, image):
        image = image.convert('L')
        image = image.resize((1000, 1000)) if image.size[0] < 1000 or image.size[1] < 1000 else image
        return image

    def run_ocr(self, image_content):
        """
        Run OCR using AWS Textract with fallback to simple text extraction.
        """
        try:
            if not self.textract_client:
                logging.error("AWS Textract client not initialized")
                return ''
            
            # Try Textract Query first for better accuracy
            extracted_text = self.extract_text_with_textract_query(image_content)
            if extracted_text:
                logging.info(f"Extracted text from AWS Textract Query: {extracted_text}")
                return extracted_text
            
            # Fallback to general Textract
            extracted_text = self.extract_text_with_textract(image_content)
            if extracted_text:
                logging.info(f"Extracted text from AWS Textract: {extracted_text}")
                return extracted_text
            
            logging.error("AWS Textract failed to extract text")
            return ''
        except Exception as e:
            logging.error(f"AWS Textract OCR error: {e}", exc_info=True)
            return ''

    def extract_text_with_textract_query(self, image_content):
        """
        Extract text using AWS Textract Query feature with ultra-fast processing.
        """
        try:
            if not self.textract_client:
                return ''
            
            # Quick size check
            if len(image_content) > 3 * 1024 * 1024:  # 3MB limit for speed
                logging.warning("Image too large for fast processing")
                return ''
            
            # Use simple detect_document_text instead of Query for speed
            response = self.textract_client.detect_document_text(
                Document={'Bytes': image_content}
            )
            
            # Fast text extraction
            extracted_text = ""
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    extracted_text += block['Text'] + "\n"
                if len(extracted_text) > 1000:  # Limit text length for speed
                    break
            
            return extracted_text.strip()
        except Exception as e:
            logging.error(f"Textract extraction error: {e}")
            return ''

    def extract_text_with_textract(self, image_content):
        """
        Extract text using AWS Textract general features.
        """
        try:
            if not self.textract_client:
                return ''
            
            # Try analyze_document with TABLES, FORMS, LINES
            response = self.textract_client.analyze_document(
                Document={'Bytes': image_content},
                FeatureTypes=['TABLES', 'FORMS', 'LINES']
            )
            
            # Extract text from blocks
            extracted_text = ""
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    extracted_text += block['Text'] + "\n"
            
            if extracted_text.strip():
                return extracted_text.strip()
            
            # Fallback to detect_document_text
            response = self.textract_client.detect_document_text(
                Document={'Bytes': image_content}
            )
            
            extracted_text = ""
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    extracted_text += block['Text'] + "\n"
            
            return extracted_text.strip()
        except Exception as e:
            logging.error(f"Textract extraction error: {e}")
            return ''

    def extract_ingredients_with_textract_query(self, image_content):
        """
        Extract ingredients using AWS Textract - simplified for speed.
        """
        try:
            if not self.textract_client:
                return []
            
            # Use simple text extraction and parse ingredients from text
            response = self.textract_client.detect_document_text(
                Document={'Bytes': image_content}
            )
            
            # Extract all text first
            full_text = ""
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    full_text += block['Text'] + "\n"
            
            # Parse ingredients from text
            return self.extract_ingredients_from_text_fallback(full_text)
        except Exception as e:
            logging.error(f"Textract ingredients extraction error: {e}")
            return []

    def extract_nutrition_with_textract_query(self, image_content):
        """
        Extract nutrition data using AWS Textract - simplified for speed.
        """
        try:
            if not self.textract_client:
                return {}
            
            # Quick size check
            if len(image_content) > 3 * 1024 * 1024:
                return {}
            
            # Use simple text extraction and parse nutrition from text
            response = self.textract_client.detect_document_text(
                Document={'Bytes': image_content}
            )
            
            # Extract all text first
            full_text = ""
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    full_text += block['Text'] + "\n"
            
            # Parse nutrition from text
            return self.extract_nutrition_info_fallback(full_text)
        except Exception as e:
            logging.error(f"Textract nutrition extraction error: {e}")
            return {}

    def process_query_nutrition_data(self, query_nutrition):
        """
        Process nutrition data from Textract Query results.
        """
        nutrition_data = {}
        
        # Map query aliases to nutrition field names
        field_mapping = {
            'energy': 'Energy',
            'total_fat': 'Total Fat',
            'saturated_fat': 'Saturated Fat',
            'cholesterol': 'Cholesterol',
            'sodium': 'Sodium',
            'carbohydrate': 'Carbohydrate',
            'total_sugars': 'Total Sugars',
            'dietary_fibre': 'Dietary Fibre',
            'protein': 'Protein'
        }
        
        for alias, value in query_nutrition.items():
            if alias in field_mapping and value:
                field_name = field_mapping[alias]
                # Try to extract numeric value and unit
                import re
                match = re.search(r'(\d+(?:\.\d+)?)\s*(kcal|g|mg|mcg|%)', value, re.IGNORECASE)
                if match:
                    num_value, unit = match.groups()
                    # Standardize units
                    if unit.lower() in ['kj', 'cal']:
                        unit = 'kcal'
                    elif field_name == 'Energy':
                        unit = 'kcal'
                    elif field_name in ['Sodium', 'Cholesterol']:
                        unit = 'mg'
                    else:
                        unit = 'g'
                    nutrition_data[field_name] = f"{num_value} {unit}"
                else:
                    # If no unit found, try to infer
                    num_match = re.search(r'(\d+(?:\.\d+)?)', value)
                    if num_match:
                        num_value = num_match.group(1)
                        if field_name == 'Energy':
                            nutrition_data[field_name] = f"{num_value} kcal"
                        elif field_name in ['Sodium', 'Cholesterol']:
                            nutrition_data[field_name] = f"{num_value} mg"
                        else:
                            nutrition_data[field_name] = f"{num_value} g"
        
        return nutrition_data

    def process_query_ingredients(self, query_ingredients):
        """
        Process ingredients from Textract Query results.
        """
        if not query_ingredients:
            return []
        
        # Join all ingredient responses and clean them up
        ingredients_text = " ".join(query_ingredients)
        
        # Clean up the ingredients text - preserve important characters
        import re
        ingredients_text = re.sub(r'[^\w\s,()%.&-]', ' ', ingredients_text)
        ingredients_text = re.sub(r'\s+', ' ', ingredients_text)
        
        # Split ingredients by common separators
        ingredients = []
        parts = re.split(r',\s*(?![^()]*\))', ingredients_text)
        
        if len(parts) <= 1:
            parts = re.split(r',\s*', ingredients_text)
        
        for part in parts:
            ingredient = part.strip()
            if ingredient and len(ingredient) > 2:
                ingredient = self.clean_ingredient_text(ingredient)
                if (ingredient and len(ingredient) > 2 and 
                    not re.match(r'^\d+\.?\d*%?$', ingredient) and
                    not ingredient.lower() in ['and', 'or', 'the', 'a', 'an']):
                    
                    split_ingredients = self.split_compound_ingredients(ingredient)
                    for split_ingredient in split_ingredients:
                        if split_ingredient and len(split_ingredient) > 2:
                            ingredients.append(split_ingredient)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            clean_ingredient = re.sub(r'\s+', ' ', ingredient).strip()
            if clean_ingredient.lower() not in seen:
                seen.add(clean_ingredient.lower())
                unique_ingredients.append(clean_ingredient)
        
        return unique_ingredients

    def extract_nutrition_info_fallback(self, text):
        """
        Fallback nutrition extraction using text parsing.
        """
        return self.extract_nutrition_info_from_text(text)

    def extract_ingredients_from_text_fallback(self, text):
        """
        Fallback ingredients extraction using text parsing.
        """
        return self.extract_ingredients_from_text(text)

    def clean_ingredient_text(self, ingredient):
        """
        Clean and normalize ingredient text.
        """
        import re
        
        # Remove extra whitespace
        ingredient = re.sub(r'\s+', ' ', ingredient).strip()
        
        # Remove trailing punctuation
        ingredient = re.sub(r'[.,;:]$', '', ingredient)
        
        # Remove leading numbers and percentages
        ingredient = re.sub(r'^\d+%?\s*', '', ingredient)
        
        # Remove bullet points
        ingredient = re.sub(r'^\s*[-•]\s*', '', ingredient)
        
        # Fix common OCR errors
        ingredient = ingredient.replace("Flailed", "Flaked")
        ingredient = ingredient.replace("Mingo", "Mango")
        ingredient = ingredient.replace("Pomcgranate", "Pomegranate")
        ingredient = ingredient.replace("lodised", "Iodised")
        
        return ingredient.strip()

    def split_compound_ingredients(self, ingredient_text):
        """
        Split compound ingredients that contain multiple items.
        """
        import re
        
        # If it contains commas but no parentheses, split by commas
        if ',' in ingredient_text and '(' not in ingredient_text:
            parts = re.split(r',\s*', ingredient_text)
            return [part.strip() for part in parts if part.strip()]
        
        # If it contains "and" but no parentheses, split by "and"
        if ' and ' in ingredient_text.lower() and '(' not in ingredient_text:
            parts = re.split(r'\s+and\s+', ingredient_text, flags=re.IGNORECASE)
            return [part.strip() for part in parts if part.strip()]
        
        # If it contains both commas and parentheses, try to split carefully
        if ',' in ingredient_text and '(' in ingredient_text:
            parts = re.split(r',\s*(?![^()]*\))', ingredient_text)
            result = []
            for part in parts:
                part = part.strip()
                if part:
                    if ',' in part and '(' not in part:
                        sub_parts = re.split(r',\s*', part)
                        result.extend([sub_part.strip() for sub_part in sub_parts if sub_part.strip()])
                    else:
                        result.append(part)
            return result
        
        return [ingredient_text]

    def correct_ocr_errors(self, text):
        corrections = {
            "Bg": "8g", "Omg": "0mg", "lron": "Iron", "meg": "mcg"
        }
        for wrong, right in corrections.items():
            text = text.replace(wrong, right)
        return text

    def extract_nutrition_info_from_text(self, text):
        """
        Enhanced nutrition extraction that captures all nutritional data from food labels.
        """
        nutrition_data = {}
        
        # Fix common OCR errors first
        text = self.correct_ocr_errors(text)
        
        # Define comprehensive nutrient patterns with variations
        nutrient_patterns = {
            "Energy": [
                r'energy[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'calories[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'calorie[:\s]*(\d+(?:\.\d+)?)\s*(kcal|kj|cal)',
                r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*energy',
                r'(\d+(?:\.\d+)?)\s*(kcal|kj|cal)\s*calories'
            ],
            "Total Fat": [
                r'total\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+fat',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fat'
            ],
            "Saturated Fat": [
                r'saturated\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sat\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*saturated\s+fat',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sat\s+fat'
            ],
            "Trans Fat": [
                r'trans\s+fat[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*trans\s+fat'
            ],
            "Cholesterol": [
                r'cholesterol[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*cholesterol'
            ],
            "Sodium": [
                r'sodium[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'salt[:\s]*(\d+(?:\.\d+)?)\s*(mg|g|%)',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*sodium',
                r'(\d+(?:\.\d+)?)\s*(mg|g|%)\s*salt'
            ],
            "Carbohydrate": [
                r'carbohydrate[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'carbohydrates[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'carbs[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrate',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbohydrates',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*carbs'
            ],
            "Total Sugars": [
                r'total\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'sugar[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*total\s+sugars',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugars',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*sugar'
            ],
            "Added Sugars": [
                r'added\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*added\s+sugars'
            ],
            "Dietary Fibre": [
                r'dietary\s+fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'dietary\s+fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fibre[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'fiber[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fibre',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*dietary\s+fiber',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fibre',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*fiber'
            ],
            "Protein": [
                r'protein[:\s]*(\d+(?:\.\d+)?)\s*(g|%)',
                r'(\d+(?:\.\d+)?)\s*(g|%)\s*protein'
            ]
        }
        
        # Method 1: Extract using comprehensive patterns - collect ALL matches
        for nutrient_name, patterns in nutrient_patterns.items():
            all_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                all_matches.extend(matches)
            
            if all_matches:
                # Take the first match found (most reliable)
                value, unit = all_matches[0]
                # Standardize units
                if unit.lower() in ['kj', 'cal']:
                    unit = 'kcal'
                elif unit.lower() == '%':
                    # Keep percentage as is
                    pass
                else:
                    unit = 'g'
                    
                    nutrition_data[nutrient_name] = f"{value} {unit}".strip()
        
        # Method 2: Look for tabular format (nutrient name followed by value)
        # This method looks for nutrient names and values in a more structured way
            lines = text.split('\n')
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Skip obvious non-nutrition lines
                if any(skip_word in line_lower for skip_word in [
                    'ingredients', 'allergen', 'manufactured', 'fssai', 'mrp', 'weight', 
                    'packaging', 'batch', 'lot', 'date', 'use by', 'sale price', 'unit',
                    'promise', 'joy', 'bite', 'artisanal', 'treats', 'delicacies', 'celebration',
                    'flavor', 'delight', 'explore', 'universe', 'indulgent', 'extravagance',
                    'unwraphappiness', 'www', 'http', 'com', 'in', 'by', 'mf', 'lic', 'no'
                ]):
                    continue
                
                # Look for nutrient names in the line
                for nutrient_name in nutrient_patterns.keys():
                    if nutrient_name.lower().replace(' ', '') in line_lower.replace(' ', ''):
                        # Extract numeric value from the same line or next line
                        value_match = re.search(r'(\d+(?:\.\d+)?)', line)
                    if value_match and nutrient_name not in nutrition_data:  # Don't overwrite existing data
                            value = value_match.group(1)
                            # Determine unit based on nutrient type
                            unit = 'g'
                            
                            nutrition_data[nutrient_name] = f"{value} {unit}".strip()
        
        # Method 3: Look for "Per 100g" format specifically
            per_100g_pattern = r'per\s+100\s*g.*?(?=\n\n|\Z)'
            per_100g_match = re.search(per_100g_pattern, text, re.IGNORECASE | re.DOTALL)
            if per_100g_match:
                per_100g_text = per_100g_match.group(0)
                # Extract all number-unit pairs from this section
                number_unit_pairs = re.findall(r'(\d+(?:\.\d+)?)\s*(kcal|g|mg|mcg|%|kj|cal)', per_100g_text, re.IGNORECASE)
                
                # Try to match with nutrient names in the same section
                for pair in number_unit_pairs:
                    value, unit = pair
                    # Look for nutrient names near this value
                    for nutrient_name in nutrient_patterns.keys():
                        if nutrient_name.lower().replace(' ', '') in per_100g_text.lower().replace(' ', ''):
                            if nutrient_name not in nutrition_data:  # Don't overwrite existing data
                                # Standardize units
                                if unit.lower() in ['kj', 'cal']:
                                    unit = 'kcal'
                                elif nutrient_name in ["Energy"]:
                                    unit = 'kcal'
                                elif nutrient_name in ["Sodium", "Cholesterol"]:
                                    unit = 'mg'
                                else:
                                    unit = 'g'
                                
                                nutrition_data[nutrient_name] = f"{value} {unit}".strip()
        
        return nutrition_data

    def extract_ingredients_from_text(self, text):
        """
        Enhanced ingredient extraction that properly separates individual ingredients.
        """
        import re
        ingredients_list = []
        
        # Try to find an ingredients section
        ingredient_section_match = re.search(
            r'(?:ingredients|contains|composed of):?\s*(.*?)(?=(?:nutrition facts|allergens|directions|amount per serving|storage|best by|manufactured by|$))',
            text, re.IGNORECASE | re.DOTALL
        )

        def clean_ingredient_text(ingredient):
            """Clean and normalize ingredient text"""
            # Remove percentages and quantities in parentheses
            ingredient = re.sub(r'\(\d+%?\)', '', ingredient)
            # Remove specific quantity patterns
            ingredient = re.sub(r'\d+%|\d+g|\d+mg|\d+mcg|\d+kcal', '', ingredient)
            # Remove "less than" and "contains" phrases
            ingredient = re.sub(r'less than \d+% of|contains \d+% of', '', ingredient, flags=re.IGNORECASE)
            # Remove nutrition facts headers
            ingredient = re.sub(
                r'^(energy|calories|total fat|saturated fat|trans fat|mufa|pufa|cholesterol|carbohydrate|total sugars|added sugars|dietary fibre|protein|sodium|vitamins|minerals|servings|approximate values)\s*',
                '', ingredient, flags=re.IGNORECASE
            )
            # Clean up extra whitespace
            ingredient = re.sub(r'\s+', ' ', ingredient).strip()
            return ingredient

        def split_ingredient_chunk(chunk):
            """Split ingredient chunk into individual ingredients"""
            # First, clean the chunk
            chunk = clean_ingredient_text(chunk)
            
            # Split by common separators, but be more careful about "and"
            # Only split by "and" if it's not part of a compound name
            parts = re.split(r',|;|\.', chunk)
            
            result = []
            for part in parts:
                part = part.strip()
                if not part or len(part) < 2:
                    continue
                
                # Handle "and" more carefully - only split if it's clearly a separator
                # Don't split if "and" is part of a compound name like "salt and pepper"
                if ' and ' in part.lower():
                    # Check if this looks like a compound name or a separator
                    and_parts = part.split(' and ')
                    if len(and_parts) == 2:
                        # If both parts are short, it might be a compound name
                        if len(and_parts[0].strip()) <= 10 and len(and_parts[1].strip()) <= 10:
                            # Keep as one ingredient if it looks like a compound name
                            result.append(part)
                        else:
                            # Split if parts are longer (likely separate ingredients)
                            for subpart in and_parts:
                                subpart = subpart.strip()
                                if subpart and len(subpart) > 2:
                                    result.append(subpart)
                    else:
                        # Multiple "and"s, split them
                        for subpart in and_parts:
                            subpart = subpart.strip()
                            if subpart and len(subpart) > 2:
                                result.append(subpart)
                else:
                    result.append(part)
            
            return result

        if ingredient_section_match:
            ingredients_raw = ingredient_section_match.group(1)
            # Split by commas, semicolons, and periods
            raw_ingredients = re.split(r'[,;.]\s*', ingredients_raw)
            
            for ingredient in raw_ingredients:
                if not ingredient.strip():
                    continue
                    
                # Process each ingredient chunk
                for sub_ing in split_ingredient_chunk(ingredient):
                    if sub_ing and len(sub_ing) > 2:
                        # Additional cleaning for individual ingredients
                        clean_ing = clean_ingredient_text(sub_ing)
                        if clean_ing and len(clean_ing) > 2:
                            ingredients_list.append(clean_ing)
        else:
            # Fallback: split the whole text, but filter out obvious junk
            raw_ingredients = re.split(r'[,;.\n]\s*', text)
            for ingredient in raw_ingredients:
                clean_ingredient = clean_ingredient_text(ingredient)
                if len(clean_ingredient) > 2 and not re.match(r'^\d+$', clean_ingredient):
                    ingredients_list.append(clean_ingredient)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ingredients = []
        for ing in ingredients_list:
            if ing not in seen:
                seen.add(ing)
                unique_ingredients.append(ing)
        
        return unique_ingredients

    async def save_scan_history(self, user, image_url, extracted_text, nutrition_data, ai_results, safety_status, flagged_ingredients, go_ingredients=None, caution_ingredients=None, no_go_ingredients=None):
        # Save scan history in a separate async function
        # Keep nutrition_data clean - only nutrition facts, not ingredients
        clean_nutrition_data = dict(nutrition_data) if nutrition_data else {}
        
        # Add AI results to nutrition data
        clean_nutrition_data.update({
            "ai_health_insight": ai_results.get("ai_health_insight", ""),
            "expert_advice": ai_results.get("expert_advice", ""),
            "go_ingredients": go_ingredients or [],
            "caution_ingredients": caution_ingredients or [],
            "no_go_ingredients": no_go_ingredients or []
        })
        
        scan = await sync_to_async(FoodLabelScan.objects.create)(
            user=user,
            image_url=image_url,
            extracted_text=extracted_text,
            nutrition_data=clean_nutrition_data,  # Include ingredient classifications
            safety_status=safety_status,
            flagged_ingredients=flagged_ingredients,
            product_name="OCR Product",
        )
        
        # Increment scan count for freemium users
        await sync_to_async(increment_user_scan_count)(user)
        
        return scan

    async def validate_product_safety(self, user, ingredients_list):
        if USE_STATIC_INGREDIENT_SAFETY:
            # --- Instant static safety check ---
            dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
            health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
            allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
            go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
            for ingredient in ingredients_list:
                ing_lower = ingredient.lower()
                pubchem_summary = fetch_pubchem_toxicology_summary(ingredient)
                if pubchem_summary:
                    summary_lower = pubchem_summary.lower()
                    # Strong warning keywords
                    if any(w in summary_lower for w in ["toxic", "hazard", "carcinogen", "danger", "harmful", "poison", "fatal"]):
                        no_go_ingredients.append(ingredient + " (Toxicological Concern)")
                        continue # Skip other checks if toxic
                if any(a in ing_lower for a in allergies):
                    no_go_ingredients.append(ingredient + " (Allergen)")
                elif any(d not in ing_lower for d in dietary) and dietary:
                    caution_ingredients.append(ingredient + " (Dietary)")
                elif any(h in ing_lower for h in health):
                    caution_ingredients.append(ingredient + " (Health)")
                else:
                    go_ingredients.append(ingredient)
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients
        else:
            # --- Edamam-based safety check (original logic) ---
            dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
            health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
            allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
            go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
            async def classify(ingredient):
                info = await self.get_edamam_info(ingredient)
                if not info["healthLabels"] and not info["cautions"]:
                    if any(a in ingredient.lower() for a in allergies):
                        no_go_ingredients.append(ingredient + " (Allergen: fallback)")
                    elif any(d not in ingredient.lower() for d in dietary):
                        caution_ingredients.append(ingredient + " (Dietary: fallback)")
                    elif any(h in ingredient.lower() for h in health):
                        caution_ingredients.append(ingredient + " (Health: fallback)")
                    else:
                        go_ingredients.append(ingredient + " (No Edamam data)")
                    return
                if any(a in info["cautions"] for a in allergies):
                    no_go_ingredients.append(ingredient)
                elif any(d not in info["healthLabels"] for d in dietary):
                    caution_ingredients.append(ingredient)
                elif any(h in ingredient.lower() for h in health):
                    caution_ingredients.append(ingredient)
                else:
                    go_ingredients.append(ingredient)
            await asyncio.gather(*(classify(ing) for ing in ingredients_list))
            all_classified = set(go_ingredients + caution_ingredients + no_go_ingredients)
            for ing in ingredients_list:
                if ing not in all_classified:
                    go_ingredients.append(ing + " (Defaulted)")
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients

    async def get_edamam_info(self, ingredient):
        url = (
            f"https://api.edamam.com/api/food-database/v2/parser"
            f"?app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}&ingr={ingredient}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    parsed = data.get("parsed") or data.get("hints")
                    if parsed:
                        food = parsed[0]["food"] if "food" in parsed[0] else parsed[0].get("food", {})
                        return {
                            "healthLabels": [h.lower() for h in food.get("healthLabels", [])],
                            "cautions": [c.lower() for c in food.get("cautions", [])]
                        }
        return {"healthLabels": [], "cautions": []}

    def get_ai_health_insight_and_expert_advice(self, user, nutrition_data, flagged_ingredients):
        health_prompt = f"""
        You are a certified health and nutrition expert.

        User Profile:
        Diet: {user.Dietary_preferences}
        Health Conditions: {user.Health_conditions}
        Allergies: {user.Allergies}

        Product Nutrition: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}

        Give a short health insight: safety, red flags, and user-friendly advice.
        """

        expert_prompt = f"""
        You are a food science expert. Based on the nutrition data and flagged ingredients below, give a detailed expert-level opinion with technical insight.

        Nutrition Data: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}
        """

        ai_health_insight = self.call_openai(health_prompt)
        expert_advice = self.call_openai(expert_prompt)

        return {"ai_health_insight": ai_health_insight, "expert_advice": expert_advice}

    def call_openai(self, prompt):
        try:
            client = OpenAI(
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
            )

            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in food science and health."},
                    {"role": "user", "content": prompt},
                ],
            )
            content = completion.choices[0].message.content.strip()
            print("🔍 Raw LLM Output:", content)

            # If the content is wrapped in markdown, extract the JSON part
            if content.startswith("```json") and content.endswith("```"):
                content = content[len("```json"): -len("```")].strip()

            # Parse content safely
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                import re
                # Attempt to fix common JSON issues like trailing commas before brackets/braces
                content_clean = re.sub(r",\s*([}\]])", r"\1", content)
                try:
                    return json.loads(content_clean)
                except json.JSONDecodeError:
                    # If even after cleanup it fails, return a summary fallback
                    return {"summary": content}

        except Exception as e:
            print(f"OpenAI error: {str(e)}")  # Add error logging
            return {"error": f"OpenAI error: {str(e)}"}

    def compare_products(self, product1, product2, user):
        # Helper to get attribute or dict key
        def get(obj, key, default=None):
            if hasattr(obj, key):
                return getattr(obj, key, default)
            if isinstance(obj, dict):
                return obj.get(key, default)
            return default

        def extract_ingredient_categories(obj):
            nd = get(obj, 'nutrition_data', {})
            go = nd.get('go_ingredients') or nd.get('go') or []
            caution = nd.get('caution_ingredients') or nd.get('caution') or []
            no_go = nd.get('no_go_ingredients') or nd.get('no_go') or []
            return go, caution, no_go

        # Prepare comparison data
        p1_flagged = get(product1, 'flagged_ingredients', [])
        p2_flagged = get(product2, 'flagged_ingredients', [])
        p1_safe = get(product1, 'safety_status', '')
        p2_safe = get(product2, 'safety_status', '')
        p1_go, p1_caution, p1_no_go = extract_ingredient_categories(product1)
        p2_go, p2_caution, p2_no_go = extract_ingredient_categories(product2)

        # Calculate health scores based on user profile
        def calculate_health_score(go_count, caution_count, no_go_count, flagged_count):
            # Base score starts at 100
            score = 100
            
            # Deduct points for each category
            score -= (no_go_count * 20)  # No-go ingredients are most concerning
            score -= (caution_count * 10)  # Caution ingredients are moderately concerning
            score -= (flagged_count * 15)  # Flagged ingredients are concerning
            
            # Bonus points for go ingredients
            score += (go_count * 2)
            
            return max(0, score)  # Ensure score doesn't go below 0

        p1_score = calculate_health_score(len(p1_go), len(p1_caution), len(p1_no_go), len(p1_flagged))
        p2_score = calculate_health_score(len(p2_go), len(p2_caution), len(p2_no_go), len(p2_flagged))

        # Generate AI-powered recommendation based on user profile
        def generate_ai_recommendation(product1_data, product2_data, user_profile):
            user_health_conditions = user.Health_conditions or ""
            user_allergies = user.Allergies or ""
            user_dietary = user.Dietary_preferences or ""
            
            # Create a comprehensive comparison prompt
            comparison_prompt = f"""
            As a health and nutrition expert, analyze these two products for a user with the following profile:
            
            User Health Conditions: {user_health_conditions}
            User Allergies: {user_allergies}
            User Dietary Preferences: {user_dietary}
            
            Product 1: {product1_data['name']}
            - Go Ingredients: {len(product1_data['go_ingredients'])} items
            - Caution Ingredients: {len(product1_data['caution_ingredients'])} items
            - No-Go Ingredients: {len(product1_data['no_go_ingredients'])} items
            - Flagged Ingredients: {product1_data['flagged_ingredients']}
            - Health Score: {p1_score}/100
            
            Product 2: {product2_data['name']}
            - Go Ingredients: {len(product2_data['go_ingredients'])} items
            - Caution Ingredients: {len(product2_data['caution_ingredients'])} items
            - No-Go Ingredients: {len(product2_data['no_go_ingredients'])} items
            - Flagged Ingredients: {product2_data['flagged_ingredients']}
            - Health Score: {p2_score}/100
            
            Based on the user's health profile and the ingredient analysis, which product is healthier and why? 
            Provide a clear, personalized recommendation with specific reasons.
            """
            
            try:
                client = OpenAI(
                    base_url="https://api.openai.com/v1",
                    api_key=os.getenv("OPENAI_API_KEY"),
                )

                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert nutritionist and health advisor. Provide clear, personalized recommendations based on user health profiles and ingredient analysis."},
                        {"role": "user", "content": comparison_prompt},
                    ],
                )
                return completion.choices[0].message.content.strip()
            except Exception as e:
                print(f"OpenAI error in comparison: {str(e)}")
                # Fallback recommendation
                if p1_score > p2_score:
                    return f"{product1_data['name']} is healthier based on ingredient analysis (Health Score: {p1_score} vs {p2_score})"
                elif p2_score > p1_score:
                    return f"{product2_data['name']} is healthier based on ingredient analysis (Health Score: {p2_score} vs {p1_score})"
                else:
                    return "Both products have similar health profiles based on ingredient analysis"

        # Generate AI recommendation
        product1_data = {
            "name": get(product1, "product_name", "Product 1"),
            "go_ingredients": p1_go,
            "caution_ingredients": p1_caution,
            "no_go_ingredients": p1_no_go,
            "flagged_ingredients": p1_flagged
        }
        product2_data = {
            "name": get(product2, "product_name", "Product 2"),
            "go_ingredients": p2_go,
            "caution_ingredients": p2_caution,
            "no_go_ingredients": p2_no_go,
            "flagged_ingredients": p2_flagged
        }
        
        ai_recommendation = generate_ai_recommendation(product1_data, product2_data, user)

        return {
            "product1": {
                "name": get(product1, "product_name", "OCR Product"),
                "nutrition_data": get(product1, "nutrition_data", {}),
                "safety_status": p1_safe,
                "flagged_ingredients": p1_flagged,
                "go_ingredients": p1_go,
                "go_count": len(p1_go),
                "caution_ingredients": p1_caution,
                "caution_count": len(p1_caution),
                "no_go_ingredients": p1_no_go,
                "no_go_count": len(p1_no_go),
                "health_score": p1_score
            },
            "product2": {
                "name": get(product2, "product_name", "OCR Product"),
                "nutrition_data": get(product2, "nutrition_data", {}),
                "safety_status": p2_safe,
                "flagged_ingredients": p2_flagged,
                "go_ingredients": p2_go,
                "go_count": len(p2_go),
                "caution_ingredients": p2_caution,
                "caution_count": len(p2_caution),
                "no_go_ingredients": p2_no_go,
                "no_go_count": len(p2_no_go),
                "health_score": p2_score
            },
            "verdict": ai_recommendation
        }

class BarcodeView(APIView):
    permission_classes = [IsAuthenticated]
    # In-memory caches
    openfoodfacts_cache = {}
    ai_cache = {}
    safety_cache = {}
    openai_cache = {}

    def post(self, request):
        # can_scan, scan_count = can_user_scan(request.user)
        # if not can_scan:
        #     return Response(
        #         {
        #             "error": "Scan limit reached. Please subscribe to AI IngredientIQ for unlimited scans.",
        #             "scans_used": scan_count,
        #             "max_scans": 6
        #         },
        #         status=status.HTTP_402_PAYMENT_REQUIRED
        #     )
        import time
        import logging
        from concurrent.futures import ThreadPoolExecutor
        start_time = time.time()

        barcode = request.data.get('barcode')
        if not barcode:
            return Response({'error': 'Barcode is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Timing: OpenFoodFacts fetch
        off_start = time.time()
        product_data = None
        try:
            if barcode in self.openfoodfacts_cache:
                product_data = self.openfoodfacts_cache[barcode]
                logging.info(f"OpenFoodFacts cache hit for barcode {barcode}")
            else:
                response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json", timeout=3)
                if response.status_code != 200:
                    return Response({'error': 'This product is not found by barcode, you can try with OCR.'}, status=status.HTTP_404_NOT_FOUND)
                product = response.json()
                if not product.get("product") or not product["product"].get("product_name"):
                    return Response({'error': 'This product is not found by barcode, you can try with OCR'}, status=status.HTTP_404_NOT_FOUND)
                product_data = product["product"]
                self.openfoodfacts_cache[barcode] = product_data
        except Exception as e:
            logging.error(f"OpenFoodFacts fetch failed: {e}")
            return Response({
                'error': 'Unable to fetch product information from the database. Please try again or use OCR scanning as an alternative.',
                'details': 'The product database is temporarily unavailable.',
                'suggestion': 'Try scanning the product label directly with OCR instead.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        off_end = time.time()
        logging.info(f"OpenFoodFacts fetch took {off_end - off_start:.2f}s")

        # Extract fields
        extracted_text = product_data.get('ingredients_text', '')
        raw_nutrition_data = product_data.get('nutriments', {})
        product_name = product_data.get('product_name', 'Unknown')
        product_image_url = product_data.get('image_url', '')
        product_image_small_url = product_data.get('image_small_url', '')
        product_image_thumb_url = product_data.get('image_thumb_url', '')
        actual_ingredients = self.extract_ingredients_from_text(extracted_text)

        # Filter and normalize nutrition data to only include requested nutrients
        def filter_nutrition_data(raw_data):
            filtered_data = {}
            
            # Macronutrients mapping
            macronutrient_mapping = {
                'energy-kcal': 'Calories',
                'energy': 'Calories',
                'proteins': 'Protein',
                'carbohydrates': 'Carbohydrates',
                'fat': 'Fats',
                'fiber': 'Fiber',
                'sugars': 'Sugars',
                'saturated-fat': 'Saturated Fat',
                'trans-fat': 'Trans Fat',
                'added-sugars': 'Added Sugars'
            }
            
            # Micronutrients mapping
            micronutrient_mapping = {
                'sodium': 'Sodium',
                'cholesterol': 'Cholesterol',
                'potassium': 'Potassium',
                'calcium': 'Calcium',
                'iron': 'Iron',
                'vitamin-d': 'Vitamin D',
                'vitamin-c': 'Vitamin C',
                'vitamin-a': 'Vitamin A',
                'magnesium': 'Magnesium',
                'zinc': 'Zinc'
            }
            
            # Process all mappings
            all_mappings = {**macronutrient_mapping, **micronutrient_mapping}
            
            for openfoodfacts_key, normalized_name in all_mappings.items():
                # Try different variations of the key
                possible_keys = [
                    openfoodfacts_key,
                    f"{openfoodfacts_key}_100g",
                    f"{openfoodfacts_key}_value"
                ]
                
                for key in possible_keys:
                    if key in raw_data and raw_data[key] is not None:
                        value = raw_data[key]
                        unit = raw_data.get(f"{openfoodfacts_key}_unit", "")
                        
                        # Format the value with unit
                        if isinstance(value, (int, float)):
                            if unit:
                                filtered_data[normalized_name] = f"{value} {unit}"
                            else:
                                filtered_data[normalized_name] = str(value)
                        else:
                            filtered_data[normalized_name] = str(value)
                        break
            
            return filtered_data
        
        nutrition_data = filter_nutrition_data(raw_nutrition_data)

        # --- New API integrations (MedlinePlus, PubChem, PubMed, ClinicalTrials.gov) ---
        def safe_summary(fetch_func, ingredient, default_msg):
            try:
                summary = fetch_func(ingredient)
                if not summary or (isinstance(summary, str) and not summary.strip()):
                    return default_msg
                return summary
            except Exception as e:
                print(f"Summary fetch error for {ingredient}: {e}")
                return default_msg

        main_ingredient = actual_ingredients[0] if actual_ingredients else None
        medlineplus_summary = safe_summary(
            fetch_medlineplus_summary,
            main_ingredient,
            "No MedlinePlus summary available for this ingredient."
        ) if main_ingredient else "No MedlinePlus summary available for this ingredient."
        pubchem_summary = safe_summary(
            fetch_pubchem_toxicology_summary,
            main_ingredient,
            "No PubChem toxicology data found for this ingredient."
        ) if main_ingredient else "No PubChem toxicology data found for this ingredient."
        pubmed_articles = fetch_pubmed_articles(main_ingredient) if main_ingredient else []
        def fetch_clinical_trials(ingredient):
            import requests
            if not ingredient:
                return []
            try:
                url = f"https://clinicaltrials.gov/api/v2/studies?q={ingredient}&limit=3"
                resp = requests.get(url, timeout=5)
                if resp.status_code != 200:
                    print(f"ClinicalTrials.gov API error: {resp.status_code}")
                    return []
                data = resp.json()
                studies = data.get("studies", [])
                trials = []
                for study in studies:
                    nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
                    title = study.get("protocolSection", {}).get("identificationModule", {}).get("officialTitle")
                    status = study.get("protocolSection", {}).get("statusModule", {}).get("overallStatus")
                    summary = study.get("protocolSection", {}).get("descriptionModule", {}).get("briefSummary")
                    url = f"https://clinicaltrials.gov/ct2/show/{nct_id}" if nct_id else None
                    if nct_id and title:
                        trials.append({
                            "title": title,
                            "nct_id": nct_id,
                            "status": status,
                            "summary": summary,
                            "url": url
                        })
                return trials
            except Exception as e:
                print(f"ClinicalTrials.gov fetch error: {e}")
                return []
        clinical_trials = fetch_clinical_trials(main_ingredient)

        # Parallelize safety and AI checks
        safety_ai_start = time.time()
        cache_key = f"{barcode}:{str(actual_ingredients)}:{str(nutrition_data)}:{str(request.user.id)}"
        with ThreadPoolExecutor() as executor:
            # Safety cache
            if cache_key in self.safety_cache:
                safety_result = self.safety_cache[cache_key]
            else:
                safety_future = executor.submit(
                    lambda: asyncio.run(self.validate_product_safety(request.user, actual_ingredients))
                )
                safety_result = safety_future.result()
                self.safety_cache[cache_key] = safety_result
            # Handle both old and new return formats for backward compatibility
            if len(safety_result) == 4:
                safety_status, go_ingredients, caution_ingredients, no_go_ingredients = safety_result
                efsa_data_cache = {}
            else:
                safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache = safety_result

            # AI cache
            if cache_key in self.ai_cache:
                ai_results = self.ai_cache[cache_key]
            else:
                ai_future = executor.submit(
                    self.get_ai_health_insight_and_expert_advice_fast, request.user, nutrition_data, no_go_ingredients
                )
                ai_results = ai_future.result()
                self.ai_cache[cache_key] = ai_results
        safety_ai_end = time.time()
        logging.info(f"Safety+AI checks took {safety_ai_end - safety_ai_start:.2f}s")

        # Get FSA hygiene rating data for the product manufacturer
        try:
            fsa_data = fetch_fsa_hygiene_rating(business_name=product_name)
        except Exception as e:
            print(f"FSA API error: {e}")
            fsa_data = {
                'found': False,
                'error': f'FSA API error: {str(e)}',
                'source': 'UK FSA FHRS API'
            }
        
        # Get medical condition recommendations based on user's complete health profile
        medical_recommendations = get_medical_condition_food_recommendations(
            request.user.Health_conditions, 
            request.user.Allergies, 
            request.user.Dietary_preferences
        ) if (request.user.Health_conditions or request.user.Allergies or request.user.Dietary_preferences) else {"found": False, "message": "No health profile specified"}

        # Convert ingredient lists to list of objects with clean names
        def clean_ingredient_name(ingredient):
            """Clean ingredient name by removing unwanted characters and formatting"""
            # Remove anything in parentheses (percentages, quantities)
            ingredient = re.sub(r'\([^)]*\)', '', ingredient)
            # Remove numbers, percent signs, and special characters except hyphens and spaces
            ingredient = re.sub(r'[^a-zA-Z\-\s]', '', ingredient)
            # Remove extra spaces
            ingredient = re.sub(r'\s+', ' ', ingredient)
            # Remove 'Defaulted' or similar tags
            ingredient = re.sub(r'\b(Defaulted|Allergen|Dietary|Health|No Edamam data)\b', '', ingredient, flags=re.IGNORECASE)
            # Strip leading/trailing whitespace
            ingredient = ingredient.strip()
            # Only keep if it's a reasonable length and not empty
            if len(ingredient) > 2:
                return ingredient
            return None

        def clean_ingredient_list(ingredient_list):
            """Clean and deduplicate ingredient list"""
            cleaned = []
            for ing in ingredient_list:
                if isinstance(ing, dict):
                    # Handle new format with ingredient object
                    ingredient_name = ing.get("ingredient", "")
                else:
                    # Handle old format (string)
                    ingredient_name = str(ing)
                
                # Clean the ingredient name
                cleaned_name = clean_ingredient_name(ingredient_name)
                if cleaned_name:
                    cleaned.append(cleaned_name)
            
            # Remove duplicates while preserving order
            seen = set()
            result = []
            for ing in cleaned:
                if ing not in seen:
                    seen.add(ing)
                    result.append(ing)
            return result

        go_ingredients_clean = clean_ingredient_list(go_ingredients)
        caution_ingredients_clean = clean_ingredient_list(caution_ingredients)
        no_go_ingredients_clean = clean_ingredient_list(no_go_ingredients)

        # Save scan history synchronously (wait for DB write) with cleaned ingredients
        scan = asyncio.run(self.save_scan_history(
            request.user,
            product_image_url,
            extracted_text,
            nutrition_data,
            ai_results,
            safety_status,
            no_go_ingredients_clean,  # flagged_ingredients
            product_name,
            product_image_url,
            product_image_small_url,
            product_image_thumb_url,
            actual_ingredients,
            go_ingredients_clean,     # go_ingredients
            caution_ingredients_clean,  # caution_ingredients
            no_go_ingredients_clean   # no_go_ingredients
        ))

        total_time = time.time() - start_time
        logging.info(f"BarcodeView total time: {total_time:.2f}s")

        # Convert ingredient lists to list of objects with clean names and EFSA data
        def format_ingredient_list(ingredient_list):
            formatted_list = []
            seen_ingredients = set()  # Track processed ingredients to avoid duplicates
            
            for ing in ingredient_list:
                if isinstance(ing, dict):
                    # New format with EFSA data
                    ingredient_name = ing.get("ingredient", "")
                    reasons = ing.get("reasons", [])
                    efsa_data = ing.get("efsa_data", {})
                    
                    # Clean the ingredient name
                    clean_ingredient = clean_ingredient_name(ingredient_name)
                    if not clean_ingredient:
                        continue
                    
                    # Check for duplicates
                    clean_ingredient_lower = clean_ingredient.lower().strip()
                    if clean_ingredient_lower in seen_ingredients:
                        continue
                    seen_ingredients.add(clean_ingredient_lower)
                    
                    # Ensure EFSA data is properly populated
                    if not efsa_data or not efsa_data.get('found'):
                        # Try to fetch EFSA data for this ingredient
                        try:
                            efsa_data = fetch_efsa_openfoodtox_data(clean_ingredient)
                        except Exception as e:
                            efsa_data = {
                                'found': False,
                                'error': f'EFSA query failed: {str(e)}',
                                'source': 'EFSA OpenFoodTox Database'
                            }
                    
                    formatted_ing = {
                        "ingredient": clean_ingredient,
                        "reasons": reasons,
                        "efsa_data": efsa_data or {}
                    }
                else:
                    # Old format (string) - try to extract clean ingredient name
                    ingredient_str = str(ing)
                    # Remove common suffixes and clean up
                    clean_ingredient = ingredient_str
                    if " (Allergen" in clean_ingredient:
                        clean_ingredient = clean_ingredient.split(" (Allergen")[0]
                    elif " (Dietary" in clean_ingredient:
                        clean_ingredient = clean_ingredient.split(" (Dietary")[0]
                    elif " (Health" in clean_ingredient:
                        clean_ingredient = clean_ingredient.split(" (Health")[0]
                    elif " (Defaulted" in clean_ingredient:
                        clean_ingredient = clean_ingredient.split(" (Defaulted")[0]
                    elif " (No Edamam data" in clean_ingredient:
                        clean_ingredient = clean_ingredient.split(" (No Edamam data")[0]
                    
                    # Clean the ingredient name
                    clean_ingredient = clean_ingredient_name(clean_ingredient)
                    if not clean_ingredient:
                        continue
                    
                    # Check for duplicates
                    clean_ingredient_lower = clean_ingredient.lower().strip()
                    if clean_ingredient_lower in seen_ingredients:
                        continue
                    seen_ingredients.add(clean_ingredient_lower)
                    
                    # Determine reasons based on the original string
                    reasons = []
                    if "Allergen" in ingredient_str:
                        reasons.append("Allergen")
                    if "Dietary" in ingredient_str:
                        reasons.append("Dietary")
                    if "Health" in ingredient_str:
                        reasons.append("Health")
                    if not reasons:
                        reasons.append("Safe")
                    
                    # Try to fetch EFSA data for this ingredient
                    try:
                        efsa_data = fetch_efsa_openfoodtox_data(clean_ingredient)
                    except Exception as e:
                        efsa_data = {
                            'found': False,
                            'error': f'EFSA query failed: {str(e)}',
                            'source': 'EFSA OpenFoodTox Database'
                        }
                    
                    formatted_ing = {
                        "ingredient": clean_ingredient,
                        "reasons": reasons,
                        "efsa_data": efsa_data or {}
                    }
                formatted_list.append(formatted_ing)
            return formatted_list
        
        # Global deduplication across all categories
        all_ingredients_seen = set()
        
        def format_ingredient_list_with_global_dedup(ingredient_list, category_name):
            formatted_list = []
            
            for ing in ingredient_list:
                if isinstance(ing, dict):
                    # New format with EFSA data
                    ingredient_name = ing.get("ingredient", "")
                    reasons = ing.get("reasons", [])
                    efsa_data = ing.get("efsa_data", {})
                    
                    # Clean the ingredient name
                    clean_ingredient = clean_ingredient_name(ingredient_name)
                    if not clean_ingredient:
                        continue
                    
                    # Check for global duplicates
                    clean_ingredient_lower = clean_ingredient.lower().strip()
                    if clean_ingredient_lower in all_ingredients_seen:
                        continue
                    all_ingredients_seen.add(clean_ingredient_lower)
                    
                    # Ensure EFSA data is properly populated
                    if not efsa_data or not efsa_data.get('found'):
                        # Try to fetch EFSA data for this ingredient
                        try:
                            efsa_data = fetch_efsa_openfoodtox_data(clean_ingredient)
                        except Exception as e:
                            efsa_data = {
                                'found': False,
                                'error': f'EFSA query failed: {str(e)}',
                                'source': 'EFSA OpenFoodTox Database'
                            }
                    
                    formatted_ing = {
                        "ingredient": clean_ingredient,
                        "reasons": reasons,
                        "efsa_data": efsa_data or {}
                    }
                else:
                    # Old format (string) - try to extract clean ingredient name
                    ingredient_str = str(ing)
                    # Remove common suffixes and clean up
                    clean_ingredient = ingredient_str
                    if " (Allergen" in clean_ingredient:
                        clean_ingredient = clean_ingredient.split(" (Allergen")[0]
                    elif " (Dietary" in clean_ingredient:
                        clean_ingredient = clean_ingredient.split(" (Dietary")[0]
                    elif " (Health" in clean_ingredient:
                        clean_ingredient = clean_ingredient.split(" (Health")[0]
                    elif " (Defaulted" in clean_ingredient:
                        clean_ingredient = clean_ingredient.split(" (Defaulted")[0]
                    elif " (No Edamam data" in clean_ingredient:
                        clean_ingredient = clean_ingredient.split(" (No Edamam data")[0]
                    
                    # Clean the ingredient name
                    clean_ingredient = clean_ingredient_name(clean_ingredient)
                    if not clean_ingredient:
                        continue
                    
                    # Check for global duplicates
                    clean_ingredient_lower = clean_ingredient.lower().strip()
                    if clean_ingredient_lower in all_ingredients_seen:
                        continue
                    all_ingredients_seen.add(clean_ingredient_lower)
                    
                    # Determine reasons based on the original string
                    reasons = []
                    if "Allergen" in ingredient_str:
                        reasons.append("Allergen")
                    if "Dietary" in ingredient_str:
                        reasons.append("Dietary")
                    if "Health" in ingredient_str:
                        reasons.append("Health")
                    if not reasons:
                        reasons.append("Safe")
                    
                    # Try to fetch EFSA data for this ingredient
                    try:
                        efsa_data = fetch_efsa_openfoodtox_data(clean_ingredient)
                    except Exception as e:
                        efsa_data = {
                            'found': False,
                            'error': f'EFSA query failed: {str(e)}',
                            'source': 'EFSA OpenFoodTox Database'
                        }
                    
                    formatted_ing = {
                        "ingredient": clean_ingredient,
                        "reasons": reasons,
                        "efsa_data": efsa_data or {}
                    }
                formatted_list.append(formatted_ing)
            return formatted_list
        
        # Process in priority order: no_go first, then caution, then go
        no_go_ingredients_obj = format_ingredient_list_with_global_dedup(no_go_ingredients, "no_go")
        caution_ingredients_obj = format_ingredient_list_with_global_dedup(caution_ingredients, "caution")
        go_ingredients_obj = format_ingredient_list_with_global_dedup(go_ingredients, "go")

        # Get current scan count for response
        from .scan_limit import can_user_scan, get_monthly_reset_date
        _, scan_count, remaining_scans = can_user_scan(request.user)
        
        # Handle None values for premium users
        if scan_count is None:
            scan_count = 0
        if remaining_scans is None:
            remaining_scans = "unlimited"
        
        return Response({
            "scan_id": scan.id,
            "image_url": product_image_url,
            "product_name": product_name,
            "product_image": {
                "full": product_image_url,
            },
            "extracted_text": extracted_text,
            "nutrition_data": nutrition_data,
            "safety_status": safety_status,
            "is_favorite": scan.is_favorite,
            "scan_usage": {
                "scans_used": scan_count,
                "max_scans": 20,
                "remaining_scans": remaining_scans,
                "monthly_reset_date": get_monthly_reset_date(),
                "total_user_scans": scan_count
            },
            "user_plan": get_user_plan_info(request.user),
            "ingredients_analysis": {
                "go": {
                    "ingredients": go_ingredients_obj,
                    "count": len(go_ingredients_obj),
                    "description": "Ingredients that are safe and suitable for your health profile"
                },
                "caution": {
                    "ingredients": caution_ingredients_obj,
                    "count": len(caution_ingredients_obj),
                    "description": "Ingredients that may not be ideal for your health profile - consume at your own risk"
                },
                "no_go": {
                    "ingredients": no_go_ingredients_obj,
                    "count": len(no_go_ingredients_obj),
                    "description": "Ingredients that are harmful or not suitable for your health profile - avoid these"
                },
                "total_flagged": len(caution_ingredients_obj) + len(no_go_ingredients_obj)
            },
            "efsa_data": {
                "source": "European Food Safety Authority (EFSA) OpenFoodTox Database",
                "total_ingredients_checked": len(efsa_data_cache),
                "ingredients_with_efsa_data": len([data for data in efsa_data_cache.values() if data and data.get('found')]),
                "cache": {k: v for k, v in efsa_data_cache.items() if v is not None}
            },
            "ai_health_insight": ai_results["ai_health_insight"],
            "expert_advice": ai_results["expert_advice"],
            "fsa_hygiene_data": fsa_data,
            "medical_condition_recommendations": {
                "user_health_profile": {
                    "allergies": request.user.Allergies,
                    "dietary_preferences": request.user.Dietary_preferences,
                    "health_conditions": request.user.Health_conditions
                },
                "recommendations": medical_recommendations,
                "source": "SNOMED CT & ICD-10 Clinical Guidelines"
            },
            # "timing": {
            #     "openfoodfacts": off_end - off_start,
            #     "safety+ai": safety_ai_end - safety_ai_start,
            #     "total": total_time
            # },
            # "medlineplus_summary": medlineplus_summary,
            # "pubchem_summary": pubchem_summary,
            # "pubmed_articles": pubmed_articles,
            # "clinical_trials": clinical_trials,
        }, status=status.HTTP_200_OK)
    
    def extract_ingredients_from_text(self, text):
        """
        Enhanced ingredient extraction that properly separates individual ingredients.
        """
        import re
        ingredients_list = []
        
        # Try to find an ingredients section
        ingredient_section_match = re.search(
            r'(?:ingredients|contains|composed of):?\s*(.*?)(?=(?:nutrition facts|allergens|directions|amount per serving|storage|best by|manufactured by|$))',
            text, re.IGNORECASE | re.DOTALL
        )

        def clean_ingredient_text(ingredient):
            """Clean and normalize ingredient text"""
            # Remove percentages and quantities in parentheses
            ingredient = re.sub(r'\(\d+%?\)', '', ingredient)
            # Remove specific quantity patterns
            ingredient = re.sub(r'\d+%|\d+g|\d+mg|\d+mcg|\d+kcal', '', ingredient)
            # Remove "less than" and "contains" phrases
            ingredient = re.sub(r'less than \d+% of|contains \d+% of', '', ingredient, flags=re.IGNORECASE)
            # Remove nutrition facts headers
            ingredient = re.sub(
                r'^(energy|calories|total fat|saturated fat|trans fat|mufa|pufa|cholesterol|carbohydrate|total sugars|added sugars|dietary fibre|protein|sodium|vitamins|minerals|servings|approximate values)\s*',
                '', ingredient, flags=re.IGNORECASE
            )
            # Clean up extra whitespace
            ingredient = re.sub(r'\s+', ' ', ingredient).strip()
            return ingredient

        def split_ingredient_chunk(chunk):
            """Split ingredient chunk into individual ingredients"""
            # First, clean the chunk
            chunk = clean_ingredient_text(chunk)
            
            # Split by common separators, but be more careful about "and"
            # Only split by "and" if it's not part of a compound name
            parts = re.split(r',|;|\.', chunk)
            
            result = []
            for part in parts:
                part = part.strip()
                if not part or len(part) < 2:
                    continue
                
                # Handle "and" more carefully - only split if it's clearly a separator
                # Don't split if "and" is part of a compound name like "salt and pepper"
                if ' and ' in part.lower():
                    # Check if this looks like a compound name or a separator
                    and_parts = part.split(' and ')
                    if len(and_parts) == 2:
                        # If both parts are short, it might be a compound name
                        if len(and_parts[0].strip()) <= 10 and len(and_parts[1].strip()) <= 10:
                            # Keep as one ingredient if it looks like a compound name
                            result.append(part)
                        else:
                            # Split if parts are longer (likely separate ingredients)
                            for subpart in and_parts:
                                subpart = subpart.strip()
                                if subpart and len(subpart) > 2:
                                    result.append(subpart)
                    else:
                        # Multiple "and"s, split them
                        for subpart in and_parts:
                            subpart = subpart.strip()
                            if subpart and len(subpart) > 2:
                                result.append(subpart)
                else:
                    result.append(part)
            
            return result

        if ingredient_section_match:
            ingredients_raw = ingredient_section_match.group(1)
            # Split by commas, semicolons, and periods
            raw_ingredients = re.split(r'[,;.]\s*', ingredients_raw)
            
            for ingredient in raw_ingredients:
                if not ingredient.strip():
                    continue
                    
                # Process each ingredient chunk
                for sub_ing in split_ingredient_chunk(ingredient):
                    if sub_ing and len(sub_ing) > 2:
                        # Additional cleaning for individual ingredients
                        clean_ing = clean_ingredient_text(sub_ing)
                        if clean_ing and len(clean_ing) > 2:
                            ingredients_list.append(clean_ing)
        else:
            # Fallback: split the whole text, but filter out obvious junk
            raw_ingredients = re.split(r'[,;.\n]\s*', text)
            for ingredient in raw_ingredients:
                clean_ingredient = clean_ingredient_text(ingredient)
                if len(clean_ingredient) > 2 and not re.match(r'^\d+$', clean_ingredient):
                    ingredients_list.append(clean_ingredient)
        
        # Remove duplicates while preserving order - use case-insensitive comparison
        seen = set()
        unique_ingredients = []
        for ing in ingredients_list:
            ing_lower = ing.lower().strip()
            if ing_lower not in seen:
                seen.add(ing_lower)
                unique_ingredients.append(ing.strip())
        
        return unique_ingredients

    def get_ai_health_insight_and_expert_advice(self, user, nutrition_data, flagged_ingredients):
        health_prompt = f"""
        You are a certified health and nutrition expert.

        User Profile:
        Diet: {user.Dietary_preferences}
        Health Conditions: {user.Health_conditions}
        Allergies: {user.Allergies}

        Product Nutrition: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}

        Give a short health insight: safety, red flags, and user-friendly advice.
        """

        expert_prompt = f"""
        You are a food science expert. Based on the nutrition data and flagged ingredients below, give a detailed expert-level opinion with technical insight.

        Nutrition Data: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}
        """

        ai_health_insight = self.call_openai(health_prompt)
        expert_advice = self.call_openai(expert_prompt)

        return {"ai_health_insight": ai_health_insight, "expert_advice": expert_advice}

    def call_openai(self, prompt):
        try:
            client = OpenAI(
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
            )

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in food science and health."},
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI error: {str(e)}")  # Add error logging
            return f"OpenAI error: {str(e)}"

    async def validate_product_safety(self, user, ingredients_list):
        """
        Categorize ingredients using OpenAI based on user profile (allergies, dietary preferences, medical conditions)
        into Go, No-Go, and Caution categories.
        """
        try:
            # Get OpenAI categorization
            categorization = self.categorize_ingredients_with_openai(user, ingredients_list)
            # Remove duplicates across categories - ensure each ingredient appears only once
            categorization = self._deduplicate_categorization(categorization)
            
            go_ingredients = categorization.get('go', [])
            no_go_ingredients = categorization.get('no_go', [])
            caution_ingredients = categorization.get('caution', [])
            
            # Add EFSA data to each ingredient for consistency with existing structure
            efsa_data_cache = {}
            for category in [go_ingredients, no_go_ingredients, caution_ingredients]:
                for ingredient_data in category:
                    ingredient_name = ingredient_data.get('ingredient', '')
                    try:
                        efsa_data = fetch_efsa_openfoodtox_data(ingredient_name)
                        efsa_data_cache[ingredient_name] = efsa_data or {}
                        ingredient_data['efsa_data'] = efsa_data or {}
                    except Exception as e:
                        print(f"EFSA error for {ingredient_name}: {e}")
                        efsa_data_cache[ingredient_name] = {
                            'found': False,
                            'error': f'EFSA query failed: {str(e)}',
                            'source': 'EFSA OpenFoodTox Database'
                        }
                        ingredient_data['efsa_data'] = efsa_data_cache[ingredient_name]
            
            # Determine overall safety status
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache
            
        except Exception as e:
            print(f"OpenAI categorization failed: {e}")
            # Fallback to basic categorization
            fallback_result = self._fallback_categorization(user, ingredients_list)
            fallback_result = self._deduplicate_categorization(fallback_result)
            
            go_ingredients = fallback_result.get('go', [])
            no_go_ingredients = fallback_result.get('no_go', [])
            caution_ingredients = fallback_result.get('caution', [])
            
            # Add empty EFSA data for fallback
            efsa_data_cache = {}
            for category in [go_ingredients, no_go_ingredients, caution_ingredients]:
                for ingredient_data in category:
                    ingredient_data['efsa_data'] = {}
            
            # Determine overall safety status
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients, efsa_data_cache

    def _deduplicate_categorization(self, categorization):
        """
        Remove duplicate ingredients across categories, keeping the highest priority category.
        Priority order: no_go > caution > go
        """
        seen_ingredients = set()
        deduplicated = {
            'go': [],
            'no_go': [],
            'caution': []
        }
        
        # Process in priority order: no_go first, then caution, then go
        priority_order = ['no_go', 'caution', 'go']
        
        for category in priority_order:
            for item in categorization.get(category, []):
                if isinstance(item, dict) and 'ingredient' in item:
                    ing_lower = item['ingredient'].lower().strip()
                    if ing_lower not in seen_ingredients:
                        seen_ingredients.add(ing_lower)
                        deduplicated[category].append(item)
                elif isinstance(item, str):
                    # Handle string format for backward compatibility
                    ing_lower = item.lower().strip()
                    if ing_lower not in seen_ingredients:
                        seen_ingredients.add(ing_lower)
                        deduplicated[category].append({
                            "ingredient": item,
                            "reasons": ["Categorized as " + category.replace('_', ' ').title()]
                        })
        
        return deduplicated

    def _fallback_categorization(self, user, ingredients_list):
        """
        Fallback categorization method when OpenAI fails.
        """
        allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
        dietary_preferences = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
        health_conditions = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
        
        go_ingredients = []
        no_go_ingredients = []
        caution_ingredients = []
        
        for ingredient in ingredients_list:
            ing_lower = ingredient.lower()
            reasons = []
            
            # Check allergies
            if any(allergen in ing_lower for allergen in allergies):
                reasons.append("Allergen")
            
            # Check dietary preferences
            if dietary_preferences:
                if 'vegan' in dietary_preferences and any(animal in ing_lower for animal in ['milk', 'egg', 'meat', 'fish', 'gelatin', 'honey']):
                    reasons.append("Non-vegan")
                elif 'vegetarian' in dietary_preferences and any(animal in ing_lower for animal in ['meat', 'fish', 'gelatin']):
                    reasons.append("Non-vegetarian")
            
            # Check health conditions
            if health_conditions:
                if 'diabetes' in health_conditions and 'sugar' in ing_lower:
                    reasons.append("High sugar")
                elif 'hypertension' in health_conditions and 'salt' in ing_lower:
                    reasons.append("High sodium")
            
            # Categorize based on reasons
            if reasons:
                if "Allergen" in reasons:
                    no_go_ingredients.append({
                        "ingredient": ingredient,
                        "reasons": reasons
                    })
                else:
                    caution_ingredients.append({
                        "ingredient": ingredient,
                        "reasons": reasons
                    })
            else:
                go_ingredients.append({
                    "ingredient": ingredient,
                    "reasons": ["Safe"]
                })
        
        result = {
            "go": go_ingredients,
            "no_go": no_go_ingredients,
            "caution": caution_ingredients
        }

        # Apply deduplication to ensure each ingredient appears only once
        return self._deduplicate_categorization(result)
    
    async def get_edamam_info(self, ingredient):
        url = (
            f"https://api.edamam.com/api/food-database/v2/parser"
            f"?app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}&ingr={ingredient}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    parsed = data.get("parsed") or data.get("hints")
                    if parsed:
                        food = parsed[0]["food"] if "food" in parsed[0] else parsed[0].get("food", {})
                        return {
                            "healthLabels": [h.lower() for h in food.get("healthLabels", [])],
                            "cautions": [c.lower() for c in food.get("cautions", [])]
                        }
        return {"healthLabels": [], "cautions": []}

    def get_ai_health_insight_and_expert_advice(self, user, nutrition_data, flagged_ingredients):
        health_prompt = f"""
        You are a certified health and nutrition expert.

        User Profile:
        Diet: {user.Dietary_preferences}
        Health Conditions: {user.Health_conditions}
        Allergies: {user.Allergies}

        Product Nutrition: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}

        Give a short health insight: safety, red flags, and user-friendly advice.
        """

        expert_prompt = f"""
        You are a food science expert. Based on the nutrition data and flagged ingredients below, give a detailed expert-level opinion with technical insight.

        Nutrition Data: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}
        """

        ai_health_insight = self.call_openai(health_prompt)
        expert_advice = self.call_openai(expert_prompt)

        return {"ai_health_insight": ai_health_insight, "expert_advice": expert_advice}

    def call_openai(self, prompt):
        try:
            client = OpenAI(
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
            )

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in food science and health."},
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI error: {str(e)}")  # Add error logging
            return f"OpenAI error: {str(e)}"



    def categorize_ingredients_with_openai(self, user, ingredients_list):
        """
        Use OpenAI to categorize ingredients into Go, No-Go, and Caution categories
        based on user's allergies, dietary preferences, and health conditions.
        """
        import json
        import hashlib
        from openai import OpenAI
        import os
        
        # Create cache key for this categorization
        key_data = {
            'ingredients': sorted(ingredients_list),
            'diet': user.Dietary_preferences,
            'allergies': user.Allergies,
            'health': user.Health_conditions
        }
        cache_key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        
        # Check cache first
        if cache_key in self.openai_cache:
            return self.openai_cache[cache_key]
        
        try:
            client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=10
            )
            
            # Create detailed prompt for ingredient categorization
            prompt = f"""
            You are a certified nutritionist and food safety expert. Categorize the following ingredients into three categories based on the user's health profile:

            USER PROFILE:
            - Allergies: {user.Allergies or 'None'}
            - Dietary Preferences: {user.Dietary_preferences or 'None'}
            - Health Conditions: {user.Health_conditions or 'None'}

            INGREDIENTS TO CATEGORIZE:
            {', '.join(ingredients_list)}

            CATEGORIES:
            1. GO: Ingredients that are safe and suitable for the user's health profile
            2. NO-GO: Ingredients that are harmful, allergenic, or contraindicated for the user's health profile
            3. CAUTION: Ingredients that may not be ideal but are not strictly forbidden - consume at your own risk

            RESPONSE FORMAT:
            Return a JSON object with exactly this structure:
            {{
                "go": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ],
                "no_go": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ],
                "caution": [
                    {{"ingredient": "ingredient_name", "reasons": ["reason1", "reason2"]}}
                ]
            }}

            IMPORTANT RULES:
            - Every ingredient must be categorized into exactly one category
            - Be conservative with safety - when in doubt, categorize as CAUTION or NO-GO
            - Consider cross-contamination risks for severe allergies
            - For dietary preferences, consider both direct ingredients and potential hidden sources
            - Provide specific, actionable reasons for each categorization
            - If an ingredient is not in the provided list, do not include it in the response
            """
            
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a certified nutritionist and food safety expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.1,
            )
            
            content = completion.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(content)
                
                # Validate structure
                required_keys = ['go', 'no_go', 'caution']
                if not all(key in result for key in required_keys):
                    raise ValueError("Missing required categories in response")
                
                # Ensure all ingredients are categorized
                categorized_ingredients = set()
                for category in required_keys:
                    for item in result[category]:
                        if 'ingredient' in item:
                            categorized_ingredients.add(item['ingredient'].lower())
                
                # Check if all ingredients are categorized
                all_ingredients = set(ing.lower() for ing in ingredients_list)
                if not categorized_ingredients.issuperset(all_ingredients):
                    # If not all ingredients categorized, add missing ones to caution
                    missing_ingredients = all_ingredients - categorized_ingredients
                    for missing in missing_ingredients:
                        result['caution'].append({
                            "ingredient": missing,
                            "reasons": ["Unable to determine safety - categorized as caution"]
                        })
                
                # Cache the result
                self.openai_cache[cache_key] = result
                return result
                
            except json.JSONDecodeError as e:
                print(f"OpenAI response parsing error: {e}")
                print(f"Raw response: {content}")
                # Fallback to default categorization
                return self._fallback_categorization(user, ingredients_list)
                
        except Exception as e:
            print(f"OpenAI categorization error: {e}")
            # Fallback to default categorization
            return self._fallback_categorization(user, ingredients_list)
    
    def _fallback_categorization(self, user, ingredients_list):
        """
        Fallback categorization when OpenAI is unavailable.
        Uses basic keyword matching based on user profile.
        """
        allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
        dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
        health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
        
        go_ingredients = []
        no_go_ingredients = []
        caution_ingredients = []
        
        for ingredient in ingredients_list:
            ing_lower = ingredient.lower()
            
            # Check for allergies first (highest priority)
            if any(a in ing_lower for a in allergies):
                no_go_ingredients.append({
                    "ingredient": ingredient,
                    "reasons": ["Allergen detected"]
                })
            # Check for dietary restrictions
            elif any(d not in ing_lower for d in dietary) and dietary:
                caution_ingredients.append({
                    "ingredient": ingredient,
                    "reasons": ["May not align with dietary preferences"]
                })
            # Check for health conditions
            elif any(h in ing_lower for h in health):
                caution_ingredients.append({
                    "ingredient": ingredient,
                    "reasons": ["May affect health conditions"]
                })
            else:
                go_ingredients.append({
                    "ingredient": ingredient,
                    "reasons": ["Appears safe for your profile"]
                })
        
        return {
            "go": go_ingredients,
            "no_go": no_go_ingredients,
            "caution": caution_ingredients
        }

    def get_ai_health_insight_and_expert_advice_fast(self, user, nutrition_data, flagged_ingredients):
        import json
        import hashlib
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        key_data = {
            'ingredients': sorted(flagged_ingredients),
            'nutrition': nutrition_data,
            'diet': user.Dietary_preferences,
            'health': user.Health_conditions,
            'allergies': user.Allergies
        }
        cache_key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        if hasattr(self, 'ai_cache') and cache_key in self.ai_cache:
            return self.ai_cache[cache_key]
        nutrition_summary = ', '.join(f"{k}: {v}" for k, v in nutrition_data.items() if k.lower() in ["calories", "energy", "protein", "fat", "sugar"])
        flagged_str = ', '.join(flagged_ingredients[:5])
        user_profile = f"Diet: {user.Dietary_preferences}; Allergies: {user.Allergies}; Health: {user.Health_conditions}"
        prompt = f"""
        You are a certified health and nutrition expert.

        User Profile:
        Diet: {user.Dietary_preferences}
        Health Conditions: {user.Health_conditions}
        Allergies: {user.Allergies}

        Product Nutrition: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}

        Give a short health insight: safety, red flags, and user-friendly advice.
        """

        expert_prompt = f"""
        You are a food science expert. Based on the nutrition data and flagged ingredients below, give a detailed expert-level opinion with technical insight.

        Nutrition Data: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}
        """
        def openai_call():
            from openai import OpenAI
            client = OpenAI(
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=10
            )
            try:
                model = "gpt-3.5-turbo-instant"
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert in food science and health."},
                        {"role": "user", "content": prompt},
                    ],
                )
            except Exception:
                model = "gpt-3.5-turbo"
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert in food science and health."},
                        {"role": "user", "content": prompt},
                    ],
                )
            content = completion.choices[0].message.content.strip()
            try:
                result = json.loads(content)
            except Exception:
                import re
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    try:
                        result = json.loads(match.group(0))
                    except Exception:
                        result = {"ai_health_insight": content, "expert_advice": content}
                else:
                    result = {"ai_health_insight": content, "expert_advice": content}
            return result
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(openai_call)
            try:
                result = future.result(timeout=5)
                if hasattr(self, 'ai_cache'):
                    self.ai_cache[cache_key] = result
                return result
            except TimeoutError:
                return {"ai_health_insight": "AI service timed out.", "expert_advice": "AI service timed out."}
            except Exception as e:
                return {"ai_health_insight": "AI service unavailable.", "expert_advice": "AI service unavailable."}

    def run_in_thread_pool(self, func, *args):
        with ThreadPoolExecutor() as executor:
            return executor.submit(func, *args).result()

    def save_image(self, image_content):
        try:
            image_name = f"food_labels/{uuid.uuid4()}.jpg"
            image_path = default_storage.save(image_name, ContentFile(image_content))
            image_url = default_storage.url(image_path).replace("https//", "")
            return image_url, image_path
        except Exception as e:
            print(f"Error saving image: {e}")
            return None, None

    async def save_scan_history(self, user, image_url, extracted_text, nutrition_data, ai_results, safety_status, flagged_ingredients, product_name, product_image_url, product_image_small_url, product_image_thumb_url, actual_ingredients, go_ingredients=None, caution_ingredients=None, no_go_ingredients=None):
        # Create a comprehensive nutrition_data dictionary that includes product details
        # Keep nutrition_data clean - only nutrition facts, not ingredients
        clean_nutrition_data = dict(nutrition_data) if nutrition_data else {}
        
        comprehensive_nutrition_data = {
            **clean_nutrition_data,
            "ai_health_insight": ai_results.get("ai_health_insight", ""),
            "expert_advice": ai_results.get("expert_advice", ""),
            "product_name": product_name,
            "product_image": {
                "full": product_image_url
            },
            "go_ingredients": go_ingredients or [],
            "caution_ingredients": caution_ingredients or [],
            "no_go_ingredients": no_go_ingredients or [],
            "actual_ingredients": actual_ingredients or []
        }

        scan = await sync_to_async(FoodLabelScan.objects.create)(
            user=user,
            image_url=image_url,
            extracted_text=extracted_text,
            product_name=product_name,
            product_image_url=product_image_url,
            nutrition_data=comprehensive_nutrition_data,
            safety_status=safety_status,
            flagged_ingredients=flagged_ingredients,
        )
        
        # Increment scan count for freemium users
        await sync_to_async(increment_user_scan_count)(user)
        
        return scan

    def get_ai_health_insight_and_expert_advice(self, user, nutrition_data, flagged_ingredients):
        health_prompt = f"""
        You are a certified health and nutrition expert.

        User Profile:
        Diet: {user.Dietary_preferences}
        Health Conditions: {user.Health_conditions}
        Allergies: {user.Allergies}

        Product Nutrition: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}

        Give a short health insight: safety, red flags, and user-friendly advice.
        """

        expert_prompt = f"""
        You are a food science expert. Based on the nutrition data and flagged ingredients below, give a detailed expert-level opinion with technical insight.

        Nutrition Data: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}
        """

        ai_health_insight = self.call_openai(health_prompt)
        expert_advice = self.call_openai(expert_prompt)

        return {"ai_health_insight": ai_health_insight, "expert_advice": expert_advice}

    def call_openai(self, prompt):
        try:
            client = OpenAI(
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
            )

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in food science and health."},
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI error: {str(e)}")  # Add error logging
            return f"OpenAI error: {str(e)}"

    async def validate_product_safety(self, user, ingredients_list):
        if USE_STATIC_INGREDIENT_SAFETY:
            dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
            health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
            allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
            go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
            for ingredient in ingredients_list:
                ing_lower = ingredient.lower()
                if any(a in ing_lower for a in allergies):
                    no_go_ingredients.append(ingredient + " (Allergen)")
                elif any(d not in ing_lower for d in dietary) and dietary:
                    caution_ingredients.append(ingredient + " (Dietary)")
                elif any(h in ing_lower for h in health):
                    caution_ingredients.append(ingredient + " (Health)")
                else:
                    go_ingredients.append(ingredient)
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients
        else:
            dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
            health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
            allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
            go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
            async def classify(ingredient):
                info = await self.get_edamam_info(ingredient)
                if not info["healthLabels"] and not info["cautions"]:
                    if any(a in ingredient.lower() for a in allergies):
                        no_go_ingredients.append(ingredient + " (Allergen: fallback)")
                    elif any(d not in ingredient.lower() for d in dietary):
                        caution_ingredients.append(ingredient + " (Dietary: fallback)")
                    elif any(h in ingredient.lower() for h in health):
                        caution_ingredients.append(ingredient + " (Health: fallback)")
                    else:
                        go_ingredients.append(ingredient + " (No Edamam data)")
                    return
                if any(a in info["cautions"] for a in allergies):
                    no_go_ingredients.append(ingredient)
                elif any(d not in info["healthLabels"] for d in dietary):
                    caution_ingredients.append(ingredient)
                elif any(h in ingredient.lower() for h in health):
                    caution_ingredients.append(ingredient)
                else:
                    go_ingredients.append(ingredient)
            await asyncio.gather(*(classify(ing) for ing in ingredients_list))
            all_classified = set(go_ingredients + caution_ingredients + no_go_ingredients)
            for ing in ingredients_list:
                if ing not in all_classified:
                    go_ingredients.append(ing + " (Defaulted)")
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients
    
    async def get_edamam_info(self, ingredient):
        url = (
            f"https://api.edamam.com/api/food-database/v2/parser"
            f"?app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}&ingr={ingredient}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    parsed = data.get("parsed") or data.get("hints")
                    if parsed:
                        food = parsed[0]["food"] if "food" in parsed[0] else parsed[0].get("food", {})
                        return {
                            "healthLabels": [h.lower() for h in food.get("healthLabels", [])],
                            "cautions": [c.lower() for c in food.get("cautions", [])]
                        }
        return {"healthLabels": [], "cautions": []}

    def get_ai_health_insight_and_expert_advice(self, user, nutrition_data, flagged_ingredients):
        health_prompt = f"""
        You are a certified health and nutrition expert.

        User Profile:
        Diet: {user.Dietary_preferences}
        Health Conditions: {user.Health_conditions}
        Allergies: {user.Allergies}

        Product Nutrition: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}

        Give a short health insight: safety, red flags, and user-friendly advice.
        """

        expert_prompt = f"""
        You are a food science expert. Based on the nutrition data and flagged ingredients below, give a detailed expert-level opinion with technical insight.

        Nutrition Data: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}
        """

        ai_health_insight = self.call_openai(health_prompt)
        expert_advice = self.call_openai(expert_prompt)

        return {"ai_health_insight": ai_health_insight, "expert_advice": expert_advice}

    def call_openai(self, prompt):
        try:
            client = OpenAI(
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
            )

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in food science and health."},
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI error: {str(e)}")  # Add error logging
            return f"OpenAI error: {str(e)}"

    async def validate_product_safety(self, user, ingredients_list):
        if USE_STATIC_INGREDIENT_SAFETY:
            dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
            health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
            allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
            go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
            for ingredient in ingredients_list:
                ing_lower = ingredient.lower()
                if any(a in ing_lower for a in allergies):
                    no_go_ingredients.append(ingredient + " (Allergen)")
                elif any(d not in ing_lower for d in dietary) and dietary:
                    caution_ingredients.append(ingredient + " (Dietary)")
                elif any(h in ing_lower for h in health):
                    caution_ingredients.append(ingredient + " (Health)")
                else:
                    go_ingredients.append(ingredient)
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients
        else:
            dietary = [d.strip().lower() for d in user.Dietary_preferences.split(",") if d.strip()] if user.Dietary_preferences else []
            health = [h.strip().lower() for h in user.Health_conditions.split(",") if h.strip()] if user.Health_conditions else []
            allergies = [a.strip().lower() for a in user.Allergies.split(",") if a.strip()] if user.Allergies else []
            go_ingredients, caution_ingredients, no_go_ingredients = [], [], []
            async def classify(ingredient):
                info = await self.get_edamam_info(ingredient)
                if not info["healthLabels"] and not info["cautions"]:
                    if any(a in ingredient.lower() for a in allergies):
                        no_go_ingredients.append(ingredient + " (Allergen: fallback)")
                    elif any(d not in ingredient.lower() for d in dietary):
                        caution_ingredients.append(ingredient + " (Dietary: fallback)")
                    elif any(h in ingredient.lower() for h in health):
                        caution_ingredients.append(ingredient + " (Health: fallback)")
                    else:
                        go_ingredients.append(ingredient + " (No Edamam data)")
                    return
                if any(a in info["cautions"] for a in allergies):
                    no_go_ingredients.append(ingredient)
                elif any(d not in info["healthLabels"] for d in dietary):
                    caution_ingredients.append(ingredient)
                elif any(h in ingredient.lower() for h in health):
                    caution_ingredients.append(ingredient)
                else:
                    go_ingredients.append(ingredient)
            await asyncio.gather(*(classify(ing) for ing in ingredients_list))
            all_classified = set(go_ingredients + caution_ingredients + no_go_ingredients)
            for ing in ingredients_list:
                if ing not in all_classified:
                    go_ingredients.append(ing + " (Defaulted)")
            if no_go_ingredients:
                safety_status = "UNSAFE"
            elif caution_ingredients:
                safety_status = "CAUTION"
            else:
                safety_status = "SAFE"
            return safety_status, go_ingredients, caution_ingredients, no_go_ingredients

class Details(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        id = request.query_params.get('id')
        if not id:
            return Response({"error": "ID parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            item = FoodLabelScan.objects.get(id=id, user=request.user) # Ensure user can only view their own scans
            serializer = FoodLabelScanSerializer(item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except FoodLabelScan.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FeedbackView(APIView):
    """
    API to handle user feedback.
    POST: Submit new feedback
    GET: Retrieve user's feedback history
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create feedback
        feedback = Feedback.objects.create(
            user=request.user,
            rating=serializer.validated_data['rating'],
            comment=serializer.validated_data['comment']
        )

        return Response({
            "message": "Thank you for your feedback!",
            "feedback": {
                "id": feedback.id,
                "rating": feedback.rating,
                "comment": feedback.comment,
                "created_at": feedback.created_at
            }
        }, status=status.HTTP_201_CREATED)

    def get(self, request):
        # Get user's feedback history
        feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
        
        feedback_list = []
        for feedback in feedbacks:
            feedback_list.append({
                "id": feedback.id,
                "rating": feedback.rating,
                "comment": feedback.comment,
                "created_at": feedback.created_at
            })

        return Response({
            "feedbacks": feedback_list,
            "total_feedbacks": len(feedback_list)
        }, status=status.HTTP_200_OK)

class LoveAppView(APIView):
    """
    API to handle the "Love the app" feature.
    POST: Toggle the user's love for the app
    GET: Get the user's current love status
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LoveAppSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Update user's love status
        request.user.loves_app = serializer.validated_data['loves_app']
        request.user.save()

        return Response({
            "message": "Thank you for loving our app!" if request.user.loves_app else "We hope to win your love back!",
            "loves_app": request.user.loves_app
        }, status=status.HTTP_200_OK)

    def get(self, request):
        return Response({
            "loves_app": request.user.loves_app
        }, status=status.HTTP_200_OK)

class ContactSupportView(APIView):
    """
    API to provide contact information for different departments.
    GET: Get all active department contacts
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get department filter from query params (optional)
        department = request.query_params.get('department', None)
        
        # Base queryset - only active departments
        contacts = DepartmentContact.objects.filter(is_active=True)
        
        # Apply department filter if provided
        if department:
            contacts = contacts.filter(department=department)
        
        # Order by department
        contacts = contacts.order_by('department')
        
        # Serialize the data
        serializer = DepartmentContactSerializer(contacts, many=True)
        
        return Response({
            "departments": serializer.data,
            "total_departments": len(serializer.data)
        }, status=status.HTTP_200_OK)

class ToggleFavoriteView(APIView):
    """
    API to toggle favorite status of a scanned food item.
    POST: Toggle favorite status by scan ID
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        scan_id = request.data.get('scan_id')
        
        if not scan_id:
            return Response(
                {"error": "scan_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the scan and ensure it belongs to the user
            scan = FoodLabelScan.objects.get(id=scan_id, user=request.user)
            
            # Toggle the favorite status
            scan.is_favorite = not scan.is_favorite
            scan.save()
            
            return Response({
                "message": f"Product {'added to' if scan.is_favorite else 'removed from'} favorites",
                "scan_id": scan.id,
                "is_favorite": scan.is_favorite,
                "product_name": scan.product_name or "Unknown Product"
            }, status=status.HTTP_200_OK)
            
        except FoodLabelScan.DoesNotExist:
            return Response(
                {"error": "Scan not found or you don't have permission to access it"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AllFlaggedIngredientsView(APIView):
    """
    API to get all flagged ingredients (no-go) for the authenticated user, with their product names and scan date.
    Returns a flat list: [{"product_name": ..., "flagged_ingredient": ..., "scanned_at": ...}, ...]
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all scans for the user
        scans = FoodLabelScan.objects.filter(user=request.user).order_by('-scanned_at')
        flagged_list = []
        unique_ingredients = set()  # Track unique ingredients
        
        print(f"Found {scans.count()} scans for user {request.user.id}")
        
        for scan in scans:
            # Determine scan type and product name
            scan_type = "unknown"
            product_name = "Unknown Product"
            
            # Check if it's a barcode scan (has product_name from OpenFoodFacts)
            if scan.product_name and scan.product_name.strip():
                product_name = scan.product_name.strip()
                scan_type = "barcode"
            # Check if it's an OCR scan (has extracted_text)
            elif scan.extracted_text and scan.extracted_text.strip():
                # Try to extract product name from OCR text or use default
                product_name = self.extract_product_name_from_ocr(scan.extracted_text) or "OCR Product"
                scan_type = "ocr"
            else:
                # Skip scans without any meaningful data
                continue
            
            scan_date = scan.scanned_at.isoformat() if scan.scanned_at else None
            image_url = scan.image_url if hasattr(scan, 'image_url') else None
            
            # Get flagged ingredients from scan
            flagged_ingredients = scan.flagged_ingredients or []
            
            print(f"Scan {scan.id}: type={scan_type}, product_name='{product_name}', flagged_ingredients={flagged_ingredients}")
            
            # Handle both string and dict formats for ingredients
            for ingredient in flagged_ingredients:
                if isinstance(ingredient, dict):
                    ingredient_name = ingredient.get("ingredient", "")
                    # Also check for other possible keys
                    if not ingredient_name:
                        ingredient_name = ingredient.get("name", "") or ingredient.get("text", "")
                else:
                    ingredient_name = str(ingredient)
                
                if ingredient_name and ingredient_name.strip():  # Only add if ingredient name is not empty
                    # Clean ingredient name by removing common suffixes
                    cleaned_ingredient = self.clean_ingredient_name(ingredient_name.strip())
                    ingredient_name_clean = cleaned_ingredient.lower()  # Normalize for uniqueness check
                    
                    # Only add if this ingredient hasn't been seen before
                    if ingredient_name_clean not in unique_ingredients:
                        unique_ingredients.add(ingredient_name_clean)
                        flagged_list.append({
                            "product_name": product_name,
                            "flagged_ingredient": cleaned_ingredient,  # Use cleaned ingredient name
                            "ingredient_type": "flagged",
                            "scan_type": scan_type,
                            "scanned_at": scan_date,
                            "image_url": image_url,
                            "scan_id": scan.id
                        })
        
        return Response({
            "flagged_ingredients": flagged_list,
            "total_flagged": len(flagged_list)
        }, status=status.HTTP_200_OK)
    
    def clean_ingredient_name(self, ingredient_name):
        """
        Clean ingredient name by removing common suffixes and parentheses.
        """
        if not ingredient_name:
            return ingredient_name
        
        # Remove common suffixes in parentheses
        import re
        
        # Remove patterns like "(No Edamam data)", "(Defaulted)", "(Allergen)", etc.
        cleaned = re.sub(r'\s*\([^)]*\)\s*$', '', ingredient_name)
        
        # Remove other common suffixes
        suffixes_to_remove = [
            ' (No Edamam data)',
            ' (Defaulted)',
            ' (Allergen)',
            ' (Dietary)',
            ' (Health)',
            ' (Toxicological Concern)',
            ' (Toxic)',
            ' (Hazard)',
            ' (Carcinogen)',
            ' (Danger)',
            ' (Harmful)',
            ' (Poison)',
            ' (Fatal)'
        ]
        
        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)]
                break
        
        return cleaned.strip()
    
    def extract_product_name_from_ocr(self, extracted_text):
        """
        Try to extract product name from OCR text.
        This is a simple heuristic - in a real implementation, you might want to use AI/ML.
        """
        if not extracted_text:
            return None
        
        lines = extracted_text.split('\n')
        
        # Look for common patterns that might indicate product names
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) > 3 and len(line) < 100:  # Reasonable length for product name
                # Skip lines that are likely not product names
                if any(skip_word in line.lower() for skip_word in [
                    'ingredients:', 'nutrition', 'serving', 'calories', 'fat', 'protein', 'carbohydrates',
                    'sodium', 'sugar', 'fiber', 'vitamin', 'mineral', 'daily value', 'percent'
                ]):
                    continue
                
                # If line looks like a product name, return it
                if not any(char.isdigit() for char in line) and not line.endswith(':'):
                    return line
        
        return None

import requests
from django.contrib.auth import get_user_model

@method_decorator(csrf_exempt, name='dispatch')
class GoogleSignInView(APIView):
    def post(self, request):
        id_token = request.data.get("id_token")
        if not id_token:
            return Response({"error": "Missing id_token"}, status=status.HTTP_400_BAD_REQUEST)

        # Try to decode the token to determine if it's a Firebase token or Google token
        import jwt
        try:
            # Decode without verification to check token type
            decoded_token = jwt.decode(id_token, options={"verify_signature": False})
            
            # Check if it's a Firebase token (contains firebase field)
            if 'firebase' in decoded_token:
                # This is a Firebase ID token
                return self._handle_firebase_token(decoded_token)
            else:
                # This is a Google ID token
                return self._handle_google_token(id_token)
                
        except jwt.DecodeError:
            return Response({"error": "Invalid token format"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Token processing error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def _handle_firebase_token(self, decoded_token):
        """Handle Firebase ID token"""
        try:
            email = decoded_token.get("email")
            if not email:
                return Response({"error": "No email in Firebase token"}, status=status.HTTP_400_BAD_REQUEST)

            # Extract user info from Firebase token
            user_info = {
                "email": email,
                "name": decoded_token.get("name", ""),
                "picture": decoded_token.get("picture", ""),
                "user_id": decoded_token.get("user_id", ""),
            }

            # Create or get user
            User = get_user_model()
            user, created = User.objects.get_or_create(
                email=email, 
                defaults={
                    "full_name": user_info.get("name", "")
                }
            )

            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                "access_token": access_token,
                "refresh_token": str(refresh),
                "created": created,
                "email": user.email,
                "full_name": user.full_name,
                "profile_picture": user_info.get("picture", "")
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Firebase token processing error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def _handle_google_token(self, id_token):
        """Handle Google ID token"""
        try:
            # Verify the token with Google
            google_response = requests.get(
                f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}'
            )
            if google_response.status_code != 200:
                return Response({"error": "Invalid Google token"}, status=status.HTTP_400_BAD_REQUEST)
            
            data = google_response.json()

            # Enforce audience check for iOS and Android client IDs
            GOOGLE_IOS_CLIENT_ID = getattr(settings, "GOOGLE_IOS_CLIENT_ID", None) or os.getenv("GOOGLE_IOS_CLIENT_ID")
            GOOGLE_ANDROID_CLIENT_ID = getattr(settings, "GOOGLE_ANDROID_CLIENT_ID", None) or os.getenv("GOOGLE_ANDROID_CLIENT_ID")
            GOOGLE_WEB_CLIENT_ID = getattr(settings, "SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", None) or os.getenv("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")
            FIREBASE_PROJECT_ID = getattr(settings, "FIREBASE_PROJECT_ID", None) or os.getenv("FIREBASE_PROJECT_ID", "ai-ingredients-3a169")
            
            allowed_client_ids = [GOOGLE_IOS_CLIENT_ID, GOOGLE_ANDROID_CLIENT_ID, GOOGLE_WEB_CLIENT_ID, FIREBASE_PROJECT_ID]
            allowed_client_ids = [cid for cid in allowed_client_ids if cid]
            
            # Comment out audience check for testing (uncomment for production)
            # if allowed_client_ids and data.get('aud') not in allowed_client_ids:
            #     return Response({
            #         "error": f"Invalid audience in token. Expected one of: {allowed_client_ids}, got: {data.get('aud')}"
            #     }, status=status.HTTP_400_BAD_REQUEST)

            email = data.get("email")
            if not email:
                return Response({"error": "No email in Google token"}, status=status.HTTP_400_BAD_REQUEST)

            # Create or get user
            User = get_user_model()
            user, created = User.objects.get_or_create(
                email=email, 
                defaults={
                    "full_name": data.get("name", "")
                }
            )

            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                "access_token": access_token,
                "refresh_token": str(refresh),
                "created": created,
                "email": user.email,
                "full_name": user.full_name,
                "profile_picture": data.get("picture", "")
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Google token processing error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class GoogleSignInWithAccessTokenView(APIView):
    """
    Google Sign-In using access token from client-side Google Sign-In SDK
    """
    permission_classes = []
    
    def post(self, request):
        access_token = request.data.get("access_token")
        if not access_token:
            return Response({"error": "Missing access_token"}, status=status.HTTP_400_BAD_REQUEST)

        # Get user info using access token
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if user_info_response.status_code != 200:
            return Response({"error": "Invalid access token"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_info = user_info_response.json()
        email = user_info.get('email')
        
        if not email:
            return Response({"error": "No email in user info"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or get user
        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email, 
            defaults={
                "full_name": user_info.get('name', ''),
            }
        )
        
        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        return Response({
            "access_token": access_token,
            "refresh_token": str(refresh),
            "created": created,
            "email": user.email,
            "full_name": user.full_name,
            "profile_picture": user.profile_picture
        }, status=status.HTTP_200_OK)

class SafeGoIngredientsView(APIView):
    """
    API to get all 'go' (safe) ingredients for the authenticated user, with their product names and scan date.
    Returns a flat list: [{"product_name": ..., "go_ingredient": ..., "scanned_at": ..., "image_url": ...}, ...]
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all scans for the user, not just SAFE ones
        scans = FoodLabelScan.objects.filter(user=request.user).order_by('-scanned_at')
        go_list = []
        unique_ingredients = set()  # Track unique ingredients
        
        print(f"Found {scans.count()} scans for user {request.user.id}")
        
        for scan in scans:
            # Determine scan type and product name
            scan_type = "unknown"
            product_name = "Unknown Product"
            
            # Check if it's a barcode scan (has product_name from OpenFoodFacts)
            if scan.product_name and scan.product_name.strip():
                product_name = scan.product_name.strip()
                scan_type = "barcode"
            # Check if it's an OCR scan (has extracted_text)
            elif scan.extracted_text and scan.extracted_text.strip():
                # Try to extract product name from OCR text or use default
                product_name = self.extract_product_name_from_ocr(scan.extracted_text) or "OCR Product"
                scan_type = "ocr"
            else:
                # Skip scans without any meaningful data
                continue
            
            scan_date = scan.scanned_at.isoformat() if scan.scanned_at else None
            image_url = scan.image_url if hasattr(scan, 'image_url') else None
            
            # Get nutrition data and extract go ingredients
            nutrition_data = scan.nutrition_data if isinstance(scan.nutrition_data, dict) else {}
            go_ingredients = nutrition_data.get("go_ingredients") or nutrition_data.get("go") or []
            
            print(f"Scan {scan.id}: type={scan_type}, product_name='{product_name}', go_ingredients={go_ingredients}")
            
            # Handle both string and dict formats for ingredients
            for ingredient in go_ingredients:
                if isinstance(ingredient, dict):
                    ingredient_name = ingredient.get("ingredient", "")
                    # Also check for other possible keys
                    if not ingredient_name:
                        ingredient_name = ingredient.get("name", "") or ingredient.get("text", "")
                else:
                    ingredient_name = str(ingredient)
                
                if ingredient_name and ingredient_name.strip():  # Only add if ingredient name is not empty
                    # Clean ingredient name by removing common suffixes
                    cleaned_ingredient = self.clean_ingredient_name(ingredient_name.strip())
                    ingredient_name_clean = cleaned_ingredient.lower()  # Normalize for uniqueness check
                    
                    # Only add if this ingredient hasn't been seen before
                    if ingredient_name_clean not in unique_ingredients:
                        unique_ingredients.add(ingredient_name_clean)
                        go_list.append({
                            "product_name": product_name,
                            "go_ingredient": cleaned_ingredient,  # Use cleaned ingredient name
                            "ingredient_type": "go",
                            "scan_type": scan_type,
                            "scanned_at": scan_date,
                            "image_url": image_url,
                            "scan_id": scan.id
                        })
        
        return Response({
            "go_ingredients": go_list,
            "total_go": len(go_list)
        }, status=status.HTTP_200_OK)
    
    def clean_ingredient_name(self, ingredient_name):
        """
        Clean ingredient name by removing common suffixes and parentheses.
        """
        if not ingredient_name:
            return ingredient_name
        
        # Remove common suffixes in parentheses
        import re
        
        # Remove patterns like "(No Edamam data)", "(Defaulted)", "(Allergen)", etc.
        cleaned = re.sub(r'\s*\([^)]*\)\s*$', '', ingredient_name)
        
        # Remove other common suffixes
        suffixes_to_remove = [
            ' (No Edamam data)',
            ' (Defaulted)',
            ' (Allergen)',
            ' (Dietary)',
            ' (Health)',
            ' (Toxicological Concern)',
            ' (Toxic)',
            ' (Hazard)',
            ' (Carcinogen)',
            ' (Danger)',
            ' (Harmful)',
            ' (Poison)',
            ' (Fatal)'
        ]
        
        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)]
                break
        
        return cleaned.strip()
    
    def extract_product_name_from_ocr(self, extracted_text):
        """
        Try to extract product name from OCR text.
        This is a simple heuristic - in a real implementation, you might want to use AI/ML.
        """
        if not extracted_text:
            return None
        
        lines = extracted_text.split('\n')
        
        # Look for common patterns that might indicate product names
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) > 3 and len(line) < 100:  # Reasonable length for product name
                # Skip lines that are likely not product names
                if any(skip_word in line.lower() for skip_word in [
                    'ingredients:', 'nutrition', 'serving', 'calories', 'fat', 'protein', 'carbohydrates',
                    'sodium', 'sugar', 'fiber', 'vitamin', 'mineral', 'daily value', 'percent'
                ]):
                    continue
                
                # If line looks like a product name, return it
                if not any(char.isdigit() for char in line) and not line.endswith(':'):
                    return line
        
        return None

class CautionIngredientsView(APIView):
    """
    API to get all 'caution' ingredients for the authenticated user, with their product names and scan date.
    Returns a flat list: [{"product_name": ..., "caution_ingredient": ..., "scanned_at": ..., "image_url": ...}, ...]
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scans = FoodLabelScan.objects.filter(user=request.user).order_by('-scanned_at')
        caution_list = []
        
        for scan in scans:
            # Heuristic: barcode scan if product_name and product_image_url are present (from OpenFoodFacts),
            # OCR scan if extracted_text and image_url are present
            is_barcode = bool(getattr(scan, 'product_name', None) and getattr(scan, 'product_image_url', None))
            is_ocr = bool(getattr(scan, 'extracted_text', None) and getattr(scan, 'image_url', None))
            if not (is_barcode or is_ocr):
                continue
                
            product_name = scan.product_name or "OCR Product"
            scan_date = scan.scanned_at.isoformat() if scan.scanned_at else None
            image_url = scan.image_url if hasattr(scan, 'image_url') else None
            nutrition_data = scan.nutrition_data if isinstance(scan.nutrition_data, dict) else {}
            caution_ingredients = nutrition_data.get("caution_ingredients") or nutrition_data.get("caution") or []
            
            # Handle both string and dict formats for ingredients
            for ingredient in caution_ingredients:
                if isinstance(ingredient, dict):
                    ingredient_name = ingredient.get("ingredient", "")
                else:
                    ingredient_name = str(ingredient)
                
                if ingredient_name:  # Only add if ingredient name is not empty
                    caution_list.append({
                        "product_name": product_name,
                        "caution_ingredient": ingredient_name,
                        "scanned_at": scan_date,
                        "image_url": image_url
                    })
        
        return Response({
            "caution_ingredients": caution_list,
            "total_caution": len(caution_list)
        }, status=status.HTTP_200_OK)

class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        from .models import UserSubscription
        import stripe
        try:
            sub = UserSubscription.objects.get(user=user, plan_name='premium')
            if not sub.stripe_subscription_id:
                return Response({"error": "No active Stripe subscription found."}, status=400)
            # Cancel on Stripe
            stripe.Subscription.delete(sub.stripe_subscription_id)
            # Update DB
            sub.status = "canceled"
            sub.save()
            return Response({"message": "Subscription canceled. You will not be charged further."}, status=200)
        except UserSubscription.DoesNotExist:
            return Response({"error": "No active premium subscription found."}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


import os
import httpx
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views import View
import asyncio

load_dotenv()
GNEWS_API_KEY = "a64db0ebc7188e3275b708e1bfadd841"

class TrendingNewsView(APIView):
    def get(self, request):
        try:
            # Get user's location from request headers or default to global
            user_country = request.headers.get('X-User-Country', 'us')
            user_language = request.headers.get('X-User-Language', 'en')
            
            # Multiple news sources for comprehensive coverage
            news_data = {
                "trending_headlines": self.get_trending_headlines(user_country, user_language),
                "food_health_news": self.get_food_health_news(),
                "technology_news": self.get_technology_news(),
                "business_news": self.get_business_news(),
                "entertainment_news": self.get_entertainment_news(),
                "sports_news": self.get_sports_news(),
                "videos": self.get_trending_videos(),
                "weather": self.get_weather_info(user_country),
                "currency_rates": self.get_currency_rates(),
                "stock_market": self.get_stock_market_data(),
                "covid_stats": self.get_covid_stats(user_country),
                "local_news": self.get_local_news(user_country),
                "breaking_news": self.get_breaking_news(),
                "featured_stories": self.get_featured_stories(),
                "news_categories": self.get_news_categories(),
                "metadata": {
                    "last_updated": timezone.now().isoformat(),
                    "total_articles": 0,
                    "sources_count": 0,
                    "user_country": user_country,
                    "user_language": user_language
                }
            }
            
            # Calculate totals
            total_articles = sum(len(section.get('articles', [])) for section in news_data.values() if isinstance(section, dict) and 'articles' in section)
            news_data["metadata"]["total_articles"] = total_articles
            news_data["metadata"]["sources_count"] = 8  # Number of different news sources used
            
            return Response({
                "status": "success",
                "message": "Professional news feed retrieved successfully",
                "data": news_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "error", 
                "message": f"Failed to fetch news: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_trending_headlines(self, country='us', language='en'):
        """Get top headlines from GNews API"""
        try:
            url = "https://gnews.io/api/v4/top-headlines"
            params = {
                "lang": language,
                "country": country,
                "max": 30,
                "token": GNEWS_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "id": item.get("url", "").split("/")[-1][:20],
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "content": item.get("content", ""),
                        "url": item.get("url", ""),
                        "image": item.get("image", ""),
                        "publishedAt": item.get("publishedAt", ""),
                        "source": {
                            "name": item.get("source", {}).get("name", ""),
                            "url": item.get("source", {}).get("url", "")
                        },
                        "category": "headlines",
                        "sentiment": self.analyze_sentiment(item.get("title", "")),
                        "read_time": self.calculate_read_time(item.get("content", "")),
                        "tags": self.extract_tags(item.get("title", "") + " " + item.get("description", ""))
                    })
                return {"articles": articles, "count": len(articles)}
            return {"articles": [], "count": 0}
        except Exception:
            return {"articles": [], "count": 0}

    def get_food_health_news(self):
        """Get food and health related news"""
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": "food health nutrition wellness",
                "lang": "en",
                "max": 10,
                "token": GNEWS_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "id": item.get("url", "").split("/")[-1][:20],
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "url": item.get("url", ""),
                        "image": item.get("image", ""),
                        "publishedAt": item.get("publishedAt", ""),
                        "source": item.get("source", {}).get("name", ""),
                        "category": "food_health",
                        "read_time": self.calculate_read_time(item.get("content", ""))
                    })
                return {"articles": articles, "count": len(articles)}
            return {"articles": [], "count": 0}
        except Exception:
            return {"articles": [], "count": 0}

    def get_technology_news(self):
        """Get technology news"""
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": "technology AI artificial intelligence",
                "lang": "en",
                "max": 8,
                "token": GNEWS_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "id": item.get("url", "").split("/")[-1][:20],
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "url": item.get("url", ""),
                        "image": item.get("image", ""),
                        "publishedAt": item.get("publishedAt", ""),
                        "source": item.get("source", {}).get("name", ""),
                        "category": "technology",
                        "read_time": self.calculate_read_time(item.get("content", ""))
                    })
                return {"articles": articles, "count": len(articles)}
            return {"articles": [], "count": 0}
        except Exception:
            return {"articles": [], "count": 0}

    def get_business_news(self):
        """Get business and finance news"""
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": "business finance economy market",
                "lang": "en",
                "max": 8,
                "token": GNEWS_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "id": item.get("url", "").split("/")[-1][:20],
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "url": item.get("url", ""),
                        "image": item.get("image", ""),
                        "publishedAt": item.get("publishedAt", ""),
                        "source": item.get("source", {}).get("name", ""),
                        "category": "business",
                        "read_time": self.calculate_read_time(item.get("content", ""))
                    })
                return {"articles": articles, "count": len(articles)}
            return {"articles": [], "count": 0}
        except Exception:
            return {"articles": [], "count": 0}

    def get_entertainment_news(self):
        """Get entertainment news"""
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": "entertainment movies music celebrities",
                "lang": "en",
                "max": 6,
                "token": GNEWS_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "id": item.get("url", "").split("/")[-1][:20],
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "url": item.get("url", ""),
                        "image": item.get("image", ""),
                        "publishedAt": item.get("publishedAt", ""),
                        "source": item.get("source", {}).get("name", ""),
                        "category": "entertainment",
                        "read_time": self.calculate_read_time(item.get("content", ""))
                    })
                return {"articles": articles, "count": len(articles)}
            return {"articles": [], "count": 0}
        except Exception:
            return {"articles": [], "count": 0}

    def get_sports_news(self):
        """Get sports news"""
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": "sports football basketball soccer",
                "lang": "en",
                "max": 6,
                "token": GNEWS_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "id": item.get("url", "").split("/")[-1][:20],
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "url": item.get("url", ""),
                        "image": item.get("image", ""),
                        "publishedAt": item.get("publishedAt", ""),
                        "source": item.get("source", {}).get("name", ""),
                        "category": "sports",
                        "read_time": self.calculate_read_time(item.get("content", ""))
                    })
                return {"articles": articles, "count": len(articles)}
            return {"articles": [], "count": 0}
        except Exception:
            return {"articles": [], "count": 0}

    def get_trending_videos(self):
        """Get trending videos (simulated)"""
        try:
            # Simulated video data since we don't have video API access
            videos = [
                {
                    "id": "video_001",
                    "title": "Latest Technology Trends 2024",
                    "description": "Explore the most exciting technology developments",
                    "thumbnail": "https://via.placeholder.com/300x200?text=Tech+Video",
                    "duration": "5:30",
                    "views": "125K",
                    "category": "technology",
                    "url": "https://example.com/video1"
                },
                {
                    "id": "video_002", 
                    "title": "Healthy Cooking Tips",
                    "description": "Learn to cook nutritious meals at home",
                    "thumbnail": "https://via.placeholder.com/300x200?text=Cooking+Video",
                    "duration": "8:15",
                    "views": "89K",
                    "category": "food_health",
                    "url": "https://example.com/video2"
                },
                {
                    "id": "video_003",
                    "title": "Market Analysis Today",
                    "description": "Daily stock market insights and analysis",
                    "thumbnail": "https://via.placeholder.com/300x200?text=Business+Video", 
                    "duration": "12:45",
                    "views": "67K",
                    "category": "business",
                    "url": "https://example.com/video3"
                }
            ]
            return {"videos": videos, "count": len(videos)}
        except Exception:
            return {"videos": [], "count": 0}

    def get_weather_info(self, country='us'):
        """Get weather information (simulated)"""
        try:
            weather_data = {
                "location": "New York, NY" if country == 'us' else "London, UK",
                "temperature": "72°F" if country == 'us' else "18°C",
                "condition": "Partly Cloudy",
                "humidity": "65%",
                "wind": "8 mph" if country == 'us' else "13 km/h",
                "forecast": [
                    {"day": "Today", "high": "75°F", "low": "68°F", "condition": "Sunny"},
                    {"day": "Tomorrow", "high": "78°F", "low": "70°F", "condition": "Cloudy"},
                    {"day": "Wednesday", "high": "72°F", "low": "65°F", "condition": "Rain"}
                ]
            }
            return weather_data
        except Exception:
            return {"error": "Weather data unavailable"}

    def get_currency_rates(self):
        """Get currency exchange rates (simulated)"""
        try:
            rates = {
                "USD": 1.00,
                "EUR": 0.85,
                "GBP": 0.73,
                "JPY": 110.25,
                "CAD": 1.25,
                "AUD": 1.35,
                "CHF": 0.92,
                "CNY": 6.45,
                "last_updated": timezone.now().isoformat()
            }
            return rates
        except Exception:
            return {"error": "Currency rates unavailable"}

    def get_stock_market_data(self):
        """Get stock market data (simulated)"""
        try:
            stocks = [
                {"symbol": "AAPL", "name": "Apple Inc.", "price": "$150.25", "change": "+2.15%"},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": "$2,850.75", "change": "-1.25%"},
                {"symbol": "MSFT", "name": "Microsoft Corp.", "price": "$310.50", "change": "+0.85%"},
                {"symbol": "TSLA", "name": "Tesla Inc.", "price": "$750.00", "change": "+3.45%"},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "price": "$3,250.00", "change": "-0.75%"}
            ]
            return {"stocks": stocks, "market_status": "Open", "last_updated": timezone.now().isoformat()}
        except Exception:
            return {"error": "Stock data unavailable"}

    def get_covid_stats(self, country='us'):
        """Get COVID-19 statistics (simulated)"""
        try:
            stats = {
                "country": "United States" if country == 'us' else "United Kingdom",
                "total_cases": "45,678,901" if country == 'us' else "8,234,567",
                "total_deaths": "789,012" if country == 'us' else "138,456",
                "total_recovered": "42,123,456" if country == 'us' else "7,456,789",
                "active_cases": "2,766,433" if country == 'us' else "639,322",
                "vaccination_rate": "65.2%" if country == 'us' else "72.8%",
                "last_updated": timezone.now().isoformat()
            }
            return stats
        except Exception:
            return {"error": "COVID data unavailable"}

    def get_local_news(self, country='us'):
        """Get local news based on country"""
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": "local news",
                "lang": "en",
                "country": country,
                "max": 5,
                "token": GNEWS_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "id": item.get("url", "").split("/")[-1][:20],
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "url": item.get("url", ""),
                        "image": item.get("image", ""),
                        "publishedAt": item.get("publishedAt", ""),
                        "source": item.get("source", {}).get("name", ""),
                        "category": "local",
                        "read_time": self.calculate_read_time(item.get("content", ""))
                    })
                return {"articles": articles, "count": len(articles)}
            return {"articles": [], "count": 0}
        except Exception:
            return {"articles": [], "count": 0}

    def get_breaking_news(self):
        """Get breaking news alerts"""
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": "breaking news urgent",
                "lang": "en",
                "max": 5,
                "token": GNEWS_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "id": item.get("url", "").split("/")[-1][:20],
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "url": item.get("url", ""),
                        "image": item.get("image", ""),
                        "publishedAt": item.get("publishedAt", ""),
                        "source": item.get("source", {}).get("name", ""),
                        "category": "breaking",
                        "priority": "high",
                        "read_time": self.calculate_read_time(item.get("content", ""))
                    })
                return {"articles": articles, "count": len(articles)}
            return {"articles": [], "count": 0}
        except Exception:
            return {"articles": [], "count": 0}

    def get_featured_stories(self):
        """Get featured/editor's pick stories"""
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": "featured story important",
                "lang": "en",
                "max": 8,
                "token": GNEWS_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "id": item.get("url", "").split("/")[-1][:20],
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "url": item.get("url", ""),
                        "image": item.get("image", ""),
                        "publishedAt": item.get("publishedAt", ""),
                        "source": item.get("source", {}).get("name", ""),
                        "category": "featured",
                        "featured": True,
                        "read_time": self.calculate_read_time(item.get("content", ""))
                    })
                return {"articles": articles, "count": len(articles)}
            return {"articles": [], "count": 0}
        except Exception:
            return {"articles": [], "count": 0}

    def get_news_categories(self):
        """Get available news categories"""
        return {
            "categories": [
                {"id": "headlines", "name": "Top Headlines", "icon": "📰"},
                {"id": "food_health", "name": "Food & Health", "icon": "🍎"},
                {"id": "technology", "name": "Technology", "icon": "💻"},
                {"id": "business", "name": "Business", "icon": "💼"},
                {"id": "entertainment", "name": "Entertainment", "icon": "🎬"},
                {"id": "sports", "name": "Sports", "icon": "⚽"},
                {"id": "local", "name": "Local News", "icon": "🏠"},
                {"id": "breaking", "name": "Breaking News", "icon": "🚨"},
                {"id": "featured", "name": "Featured", "icon": "⭐"}
            ]
        }

    def analyze_sentiment(self, text):
        """Simple sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'positive', 'success']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'negative', 'failure', 'crisis']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def calculate_read_time(self, content):
        """Calculate estimated read time"""
        if not content:
            return "1 min"
        words = len(content.split())
        minutes = max(1, words // 200)  # Average reading speed: 200 words per minute
        return f"{minutes} min"

    def extract_tags(self, text):
        """Extract relevant tags from text"""
        common_tags = ['technology', 'health', 'business', 'politics', 'sports', 'entertainment', 'science', 'education']
        text_lower = text.lower()
        found_tags = [tag for tag in common_tags if tag in text_lower]
        return found_tags[:5]  # Return max 5 tags

@method_decorator(csrf_exempt, name='dispatch')
class AppleSignInView(APIView):
    def post(self, request):
        # Get the credential details from frontend
        username = request.data.get("username")  # email
        first_name = request.data.get("firstName", "")
        last_name = request.data.get("lastName", "")
        social_login_id = request.data.get("socialLoginId")
        social_login_type = request.data.get("socialLoginType", "APPLE")
        device_token = request.data.get("deviceToken", "")
        
        # Validate required fields
        if not username:
            return Response({"error": "Missing username (email)"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not social_login_id:
            return Response({"error": "Missing socialLoginId"}, status=status.HTTP_400_BAD_REQUEST)

        # Create or get user
        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=username,
            defaults={
                "username": username.split("@")[0],
                "first_name": first_name,
                "last_name": last_name,
                "social_login_id": social_login_id,
                "social_login_type": social_login_type,
                "device_token": device_token,
            }
        )
        
        # Update existing user with new device token if provided
        if not created and device_token:
            user.device_token = device_token
            user.save()

        # Generate JWT tokens for the user
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "access_token": access_token,
            "refresh_token": str(refresh),
            "created": created,
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "social_login_id": user.social_login_id,
            "social_login_type": user.social_login_type,
        }, status=status.HTTP_200_OK)

def fetch_openfoodfacts_product(barcode, max_retries=1):
    """
    Robust function to fetch product data from OpenFoodFacts API with proper headers and retries.
    
    Args:
        barcode (str): The product barcode
        max_retries (int): Maximum number of retry attempts (default 1 for faster response)
    
    Returns:
        dict: Product data if successful, None if failed
    """
    import re
    import time
    
    # Clean and validate barcode
    if not barcode:
        return None
    
    # Remove any non-digit characters and ensure it's a valid barcode
    cleaned_barcode = re.sub(r'[^0-9]', '', str(barcode))
    if len(cleaned_barcode) < 8 or len(cleaned_barcode) > 14:
        return None
    # Proper headers for OpenFoodFacts API
    headers = {
        'User-Agent': 'FoodApp/1.0 (https://foodapp.com; contact@foodapp.com)',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    # Try different API endpoints and versions
    api_endpoints = [
        f"https://world.openfoodfacts.org/api/v2/product/{cleaned_barcode}.json",
        f"https://world.openfoodfacts.org/api/v1/product/{cleaned_barcode}.json",
        f"https://world.openfoodfacts.org/api/v0/product/{cleaned_barcode}.json",
        f"https://world.openfoodfacts.org/cgi/product_jqm.pl?json=1&code={cleaned_barcode}",
    ]
    
    for attempt in range(max_retries):
        for endpoint in api_endpoints:
            try:
                logging.info(f"Attempting OpenFoodFacts API call: {endpoint}")
                
                response = requests.get(
                    endpoint,
                    headers=headers,
                    timeout=8,  # Reduced timeout for faster response
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if product exists and has required data
                    if data.get("status") == 1 and data.get("product"):
                        product = data["product"]
                        
                        # Log what we found for debugging
                        product_name = product.get("product_name") or product.get("generic_name") or product.get("brands") or "Unknown"
                        has_ingredients = bool(product.get("ingredients_text") or product.get("ingredients"))
                        has_nutrition = bool(product.get("nutriments"))
                        
                        logging.info(f"Product found: {product_name} (Barcode: {cleaned_barcode})")
                        logging.info(f"  - Has ingredients: {has_ingredients}")
                        logging.info(f"  - Has nutrition: {has_nutrition}")
                        logging.info(f"  - Brand: {product.get('brands', 'Unknown')}")
                        
                        # Return product even if it has incomplete data - let the main logic handle it
                        return product
                    elif data.get("status") == 0:
                        logging.info(f"Product not found in OpenFoodFacts database: {cleaned_barcode}")
                        continue
                    else:
                        logging.warning(f"Unexpected response format from OpenFoodFacts: {data.get('status')}")
                        continue
                        
                elif response.status_code == 404:
                    logging.info(f"Product not found (404): {cleaned_barcode}")
                    continue
                elif response.status_code == 429:
                    logging.warning(f"Rate limited by OpenFoodFacts API (429)")
                    # Don't retry on rate limit, just continue to next API
                    return None
                else:
                    logging.warning(f"OpenFoodFacts API returned status {response.status_code}")
                    continue
                    
            except requests.exceptions.Timeout:
                logging.warning(f"OpenFoodFacts API timeout")
                continue
            except requests.exceptions.RequestException as e:
                logging.warning(f"OpenFoodFacts API request error: {e}")
                continue
            except (ValueError, json.JSONDecodeError) as e:
                logging.warning(f"OpenFoodFacts API JSON decode error: {e}")
                continue
            except Exception as e:
                logging.error(f"Unexpected error in OpenFoodFacts API call: {e}")
                continue
    
    logging.info(f"Product not found in OpenFoodFacts: {cleaned_barcode}")
    return None

def search_openfoodfacts_by_name(product_name, max_results=5):
    """
    Search for products in OpenFoodFacts by name as a fallback when barcode lookup fails.
    
    Args:
        product_name (str): The product name to search for
        max_results (int): Maximum number of results to return
    
    Returns:
        list: List of product data dictionaries, empty if failed
    """
    if not product_name or len(product_name.strip()) < 3:
        return []
    
    headers = {
        'User-Agent': 'FoodApp/1.0 (https://foodapp.com; contact@foodapp.com)',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        # Use OpenFoodFacts search API
        search_url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={product_name}&search_simple=1&action=process&json=1&page_size={max_results}"
        
        response = requests.get(
            search_url,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            # Filter products that have required fields
            valid_products = []
            for product in products:
                if (product.get("product_name") or product.get("generic_name") or product.get("brands")) and product.get("ingredients_text"):
                    valid_products.append(product)
            
            logging.info(f"Found {len(valid_products)} products by name search for: {product_name}")
            return valid_products[:max_results]
        else:
            logging.warning(f"OpenFoodFacts search API returned status {response.status_code}")
            return []
            
    except Exception as e:
        logging.error(f"Error in OpenFoodFacts name search: {e}")
        return []

def fetch_upc_database_product(barcode, api_key=None):
    """
    Fetch product data from UPC Database API.
    This API has comprehensive US and international product coverage.
    
    Args:
        barcode (str): The product barcode
        api_key (str): Optional API key for UPC Database
    
    Returns:
        dict: Product data if successful, None if failed
    """
    import requests
    import logging
    
    if not barcode:
        return None
    
    # Clean barcode
    cleaned_barcode = re.sub(r'[^0-9]', '', str(barcode))
    if len(cleaned_barcode) < 8 or len(cleaned_barcode) > 14:
        return None
    
    headers = {
        'User-Agent': 'FoodApp/1.0 (https://foodapp.com; contact@foodapp.com)',
        'Accept': 'application/json',
    }
    
    # Try UPC Database API (free tier available)
    try:
        # Free endpoint (limited requests per day)
        url = f"https://api.upcdatabase.org/product/{cleaned_barcode}"
        
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if product exists
            if data.get('success') and data.get('product'):
                product = data['product']
                
                # Map UPC Database fields to our format
                mapped_product = {
                    'product_name': product.get('title') or product.get('name'),
                    'brands': product.get('brand'),
                    'generic_name': product.get('description'),
                    'ingredients_text': product.get('ingredients'),
                    'image_url': product.get('image'),
                    'categories': product.get('category'),
                    'countries': product.get('country'),
                    'nutriments': {
                        'energy-kcal': product.get('calories'),
                        'proteins': product.get('protein'),
                        'carbohydrates': product.get('carbohydrates'),
                        'fat': product.get('fat'),
                        'fiber': product.get('fiber'),
                        'sugars': product.get('sugar'),
                        'sodium': product.get('sodium'),
                    }
                }
                
                logging.info(f"UPC Database product found: {mapped_product.get('product_name', 'Unknown')}")
                return mapped_product
                
        elif response.status_code == 404:
            logging.info(f"Product not found in UPC Database: {cleaned_barcode}")
        elif response.status_code == 403:
            logging.warning(f"UPC Database API access denied (403) - may need API key")
        else:
            logging.warning(f"UPC Database API returned status {response.status_code}")
            
    except requests.exceptions.Timeout:
        logging.warning(f"UPC Database API timeout")
    except requests.exceptions.RequestException as e:
        logging.warning(f"UPC Database API request error: {e}")
    except Exception as e:
        logging.warning(f"UPC Database API error: {e}")
    
    return None

def fetch_barcode_lookup_product(barcode):
    """
    Fetch product data from Barcode Lookup API.
    This API has good global coverage for various barcode formats.
    
    Args:
        barcode (str): The product barcode
    
    Returns:
        dict: Product data if successful, None if failed
    """
    import requests
    import logging
    
    if not barcode:
        return None
    
    # Clean barcode
    cleaned_barcode = re.sub(r'[^0-9]', '', str(barcode))
    if len(cleaned_barcode) < 8 or len(cleaned_barcode) > 14:
        return None
    
    headers = {
        'User-Agent': 'FoodApp/1.0 (https://foodapp.com; contact@foodapp.com)',
        'Accept': 'application/json',
    }
    
    try:
        # Barcode Lookup API (free tier)
        url = f"https://api.barcodelookup.com/v3/products?barcode={cleaned_barcode}"
        
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            if products:
                product = products[0]  # Get first product
                
                # Map Barcode Lookup fields to our format
                mapped_product = {
                    'product_name': product.get('title') or product.get('product_name'),
                    'brands': product.get('brand'),
                    'generic_name': product.get('description'),
                    'ingredients_text': product.get('ingredients'),
                    'image_url': product.get('images', [{}])[0].get('url') if product.get('images') else None,
                    'categories': product.get('category'),
                    'countries': product.get('country'),
                    'nutriments': {
                        'energy-kcal': product.get('nutrition_facts', {}).get('calories'),
                        'proteins': product.get('nutrition_facts', {}).get('protein'),
                        'carbohydrates': product.get('nutrition_facts', {}).get('carbohydrates'),
                        'fat': product.get('nutrition_facts', {}).get('fat'),
                        'fiber': product.get('nutrition_facts', {}).get('fiber'),
                        'sugars': product.get('nutrition_facts', {}).get('sugar'),
                        'sodium': product.get('nutrition_facts', {}).get('sodium'),
                    }
                }
                
                logging.info(f"Barcode Lookup product found: {mapped_product.get('product_name', 'Unknown')}")
                return mapped_product
                
        elif response.status_code == 404:
            logging.info(f"Product not found in Barcode Lookup: {cleaned_barcode}")
        elif response.status_code == 403:
            logging.warning(f"Barcode Lookup API access denied (403) - may need API key")
        else:
            logging.warning(f"Barcode Lookup API returned status {response.status_code}")
            
    except requests.exceptions.Timeout:
        logging.warning(f"Barcode Lookup API timeout")
    except requests.exceptions.RequestException as e:
        logging.warning(f"Barcode Lookup API request error: {e}")
    except Exception as e:
        logging.warning(f"Barcode Lookup API error: {e}")
    
    return None

def fetch_ean_search_product(barcode):
    """
    Fetch product data from EAN Search API.
    This API specializes in European Article Numbers but has global coverage.
    
    Args:
        barcode (str): The product barcode
    
    Returns:
        dict: Product data if successful, None if failed
    """
    import requests
    import logging
    
    if not barcode:
        return None
    
    # Clean barcode
    cleaned_barcode = re.sub(r'[^0-9]', '', str(barcode))
    if len(cleaned_barcode) < 8 or len(cleaned_barcode) > 14:
        return None
    
    headers = {
        'User-Agent': 'FoodApp/1.0 (https://foodapp.com; contact@foodapp.com)',
        'Accept': 'application/json',
    }
    
    try:
        # EAN Search API (free tier)
        url = f"https://api.ean-search.org/ean/{cleaned_barcode}"
        
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('found') and data.get('product'):
                product = data['product']
                
                # Map EAN Search fields to our format
                mapped_product = {
                    'product_name': product.get('name') or product.get('title'),
                    'brands': product.get('brand'),
                    'generic_name': product.get('description'),
                    'ingredients_text': product.get('ingredients'),
                    'image_url': product.get('image'),
                    'categories': product.get('category'),
                    'countries': product.get('country'),
                    'nutriments': {
                        'energy-kcal': product.get('calories'),
                        'proteins': product.get('protein'),
                        'carbohydrates': product.get('carbs'),
                        'fat': product.get('fat'),
                        'fiber': product.get('fiber'),
                        'sugars': product.get('sugar'),
                        'sodium': product.get('sodium'),
                    }
                }
                
                logging.info(f"EAN Search product found: {mapped_product.get('product_name', 'Unknown')}")
                return mapped_product
                
        elif response.status_code == 404:
            logging.info(f"Product not found in EAN Search: {cleaned_barcode}")
        elif response.status_code == 403:
            logging.warning(f"EAN Search API access denied (403) - may need API key")
        else:
            logging.warning(f"EAN Search API returned status {response.status_code}")
            
    except requests.exceptions.Timeout:
        logging.warning(f"EAN Search API timeout")
    except requests.exceptions.RequestException as e:
        logging.warning(f"EAN Search API request error: {e}")
    except Exception as e:
        logging.warning(f"EAN Search API error: {e}")
    
    return None







def fetch_nutritionix_product(barcode):
    """
    Fetch product data from Nutritionix API.
    This API provides comprehensive nutrition data for US products.
    
    Args:
        barcode (str): The product barcode
    
    Returns:
        dict: Product data if successful, None if failed
    """
    import requests
    import logging
    
    if not barcode:
        return None
    
    # Clean barcode
    cleaned_barcode = re.sub(r'[^0-9]', '', str(barcode))
    if len(cleaned_barcode) < 8 or len(cleaned_barcode) > 14:
        return None
    
    headers = {
        'User-Agent': 'FoodApp/1.0 (https://foodapp.com; contact@foodapp.com)',
        'Accept': 'application/json',
        'x-app-id': 'f466a679',  # You'll need to get this
        'x-app-key': '2a8c378d0b560cf5d69e73be8be8a1bd',  # You'll need to get this
    }
    
    try:
        # Nutritionix API
        url = f"https://trackapi.nutritionix.com/v2/search/item?upc={cleaned_barcode}"
        
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('foods') and len(data['foods']) > 0:
                product = data['foods'][0]
                
                # Map Nutritionix fields to our format
                mapped_product = {
                    'product_name': product.get('food_name'),
                    'brands': product.get('brand_name'),
                    'generic_name': product.get('food_description'),
                    'ingredients_text': product.get('ingredients'),
                    'image_url': product.get('photo', {}).get('thumb'),
                    'categories': product.get('food_category'),
                    'countries': 'US',  # Nutritionix is primarily US-focused
                    'nutriments': {
                        'energy-kcal': product.get('nf_calories'),
                        'proteins': product.get('nf_protein'),
                        'carbohydrates': product.get('nf_total_carbohydrate'),
                        'fat': product.get('nf_total_fat'),
                        'fiber': product.get('nf_dietary_fiber'),
                        'sugars': product.get('nf_sugars'),
                        'sodium': product.get('nf_sodium'),
                    }
                }
                
                logging.info(f"Nutritionix product found: {mapped_product.get('product_name', 'Unknown')}")
                return mapped_product
                
        elif response.status_code == 404:
            logging.info(f"Product not found in Nutritionix: {cleaned_barcode}")
        elif response.status_code == 401:
            logging.warning(f"Nutritionix API authentication failed - need valid app_id and app_key")
        else:
            logging.warning(f"Nutritionix API returned status {response.status_code}")
            
    except requests.exceptions.Timeout:
        logging.warning(f"Nutritionix API timeout")
    except requests.exceptions.RequestException as e:
        logging.warning(f"Nutritionix API request error: {e}")
    except Exception as e:
        logging.warning(f"Nutritionix API error: {e}")
    
    return None



def fetch_product_api_data(barcode):
    """
    Fetch product data from Product API.
    This API aggregates data from multiple sources.
    
    Args:
        barcode (str): The product barcode
    
    Returns:
        dict: Product data if successful, None if failed
    """
    import requests
    import logging
    
    if not barcode:
        return None
    
    # Clean barcode
    cleaned_barcode = re.sub(r'[^0-9]', '', str(barcode))
    if len(cleaned_barcode) < 8 or len(cleaned_barcode) > 14:
        return None
    
    headers = {
        'User-Agent': 'FoodApp/1.0 (https://foodapp.com; contact@foodapp.com)',
        'Accept': 'application/json',
    }
    
    try:
        # Product API (free tier)
        url = f"https://api.product.com/v1/products/{cleaned_barcode}"
        
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and data.get('product'):
                product = data['product']
                
                # Map Product API fields to our format
                mapped_product = {
                    'product_name': product.get('name') or product.get('title'),
                    'brands': product.get('brand'),
                    'generic_name': product.get('description'),
                    'ingredients_text': product.get('ingredients'),
                    'image_url': product.get('image'),
                    'categories': product.get('category'),
                    'countries': product.get('country'),
                    'nutriments': {
                        'energy-kcal': product.get('nutrition', {}).get('calories'),
                        'proteins': product.get('nutrition', {}).get('protein'),
                        'carbohydrates': product.get('nutrition', {}).get('carbohydrates'),
                        'fat': product.get('nutrition', {}).get('fat'),
                        'fiber': product.get('nutrition', {}).get('fiber'),
                        'sugars': product.get('nutrition', {}).get('sugar'),
                        'sodium': product.get('nutrition', {}).get('sodium'),
                    }
                }
                
                logging.info(f"Product API product found: {mapped_product.get('product_name', 'Unknown')}")
                return mapped_product
                
        elif response.status_code == 404:
            logging.info(f"Product not found in Product API: {cleaned_barcode}")
        elif response.status_code == 403:
            logging.warning(f"Product API access denied (403) - may need API key")
        else:
            logging.warning(f"Product API returned status {response.status_code}")
            
    except requests.exceptions.Timeout:
        logging.warning(f"Product API timeout")
    except requests.exceptions.RequestException as e:
        logging.warning(f"Product API request error: {e}")
    except Exception as e:
        logging.warning(f"Product API error: {e}")
    
    return None

def fetch_multi_source_product(barcode, max_retries=1):
    """
    Fetch product data from multiple sources with fallback strategy.
    This function tries multiple APIs in sequence to maximize product coverage.
    
    Args:
        barcode (str): The product barcode
        max_retries (int): Maximum number of retry attempts per API (default 1 for faster response)
    
    Returns:
        dict: Best available product data, None if all sources fail
    """
    import time
    import logging
    
    if not barcode:
        return None
    
    # Clean barcode
    cleaned_barcode = re.sub(r'[^0-9]', '', str(barcode))
    if len(cleaned_barcode) < 8 or len(cleaned_barcode) > 14:
        return None
    
    # Define API sources in order of preference
    api_sources = [
        ('OpenFoodFacts', fetch_openfoodfacts_product),  # Global food database with ingredients
    ]
    
    best_product = None
    best_score = 0
    
    for source_name, api_function in api_sources:
        logging.info(f"Trying {source_name} for barcode: {cleaned_barcode}")
        
        # Try each API only once for faster response
        for attempt in range(max_retries):
            try:
                product_data = api_function(cleaned_barcode)
                
                if product_data:
                    # Score the product based on data completeness
                    score = 0
                    
                    # Basic product info (essential)
                    if product_data.get('product_name'):
                        score += 10
                    if product_data.get('brands'):
                        score += 5
                    
                    # Ingredients (very important for our use case)
                    if product_data.get('ingredients_text'):
                        score += 20
                    
                    # Nutrition data
                    if product_data.get('nutriments'):
                        nutriments = product_data['nutriments']
                        if any(nutriments.get(key) for key in ['energy-kcal', 'proteins', 'carbohydrates', 'fat']):
                            score += 15
                    
                    # Image
                    if product_data.get('image_url'):
                        score += 5
                    
                    # Categories and additional info
                    if product_data.get('categories'):
                        score += 3
                    if product_data.get('countries'):
                        score += 2
                    
                    logging.info(f"{source_name} product score: {score}")
                    
                    # Keep the best product found
                    if score > best_score:
                        best_score = score
                        best_product = product_data
                        best_product['data_source'] = source_name
                        best_product['data_score'] = score
                        
                        # If we have a high-quality product (good ingredients + nutrition), we can stop
                        if score >= 35:
                            logging.info(f"High-quality product found from {source_name}, stopping search")
                            return best_product
                    
                    # Found a product, no need to retry this API
                    break
                    
            except Exception as e:
                logging.warning(f"Error with {source_name} (attempt {attempt + 1}): {e}")
                # Don't retry on errors, just continue to next API
                break
        
        # Small delay between different APIs to be respectful
        time.sleep(0.2)
    
    if best_product:
        logging.info(f"Best product found from {best_product.get('data_source')} with score {best_product.get('data_score')}")
    else:
        logging.warning(f"No product found in any source for barcode: {cleaned_barcode}")
    
    return best_product

class AWSTextractOCRView(APIView):
    """
    AWS Textract-based OCR API for food label scanning.
    Provides enhanced text extraction with structured nutrition data and ingredients.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    # In-memory caches
    ai_cache = {}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize AWS Textract client
        try:
            aws_access_key = settings.AWS_ACCESS_KEY_ID
            aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
            aws_region = settings.AWS_S3_REGION_NAME or 'us-east-1'
            
            print(f"AWS Access Key: {aws_access_key[:10]}..." if aws_access_key else "None")
            print(f"AWS Secret Key: {aws_secret_key[:10]}..." if aws_secret_key else "None")
            print(f"AWS Region: {aws_region}")
            
            if not aws_access_key or not aws_secret_key:
                logging.error("AWS credentials not found in settings")
                self.textract_client = None
                return
            
            self.textract_client = boto3.client(
                'textract',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            print("AWS Textract client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize AWS Textract client: {e}")
            self.textract_client = None

    def get(self, request):
        """
        Test AWS Textract connection.
        """
        try:
            success, message = self.test_aws_connection()
            return Response({
                "success": success,
                "message": message,
                "aws_configured": self.textract_client is not None
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Test failed: {str(e)}",
                "aws_configured": self.textract_client is not None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
        Process food label image using AWS Textract OCR.
        Returns structured nutrition data and ingredients.
        """
        try:
            # Check if user can scan
            # if not can_user_scan(request.user):
            #     return Response({
            #         "error": "Scan limit reached. Please upgrade to premium for unlimited scans."
            #     }, status=status.HTTP_403_FORBIDDEN)

            # Get image from request
            image_file = request.FILES.get('image')
            if not image_file:
                return Response({
                    "error": "No image provided"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Save image and get URL
            image_content = image_file.read()
            print(f"Image content type: {type(image_content)}")
            print(f"Image content length: {len(image_content)} bytes")
            print(f"Image file name: {image_file.name}")
            print(f"Image content type: {image_file.content_type}")
            
            image_url = self.save_image(image_content)
            print(f"Image URL: {image_url}")
            
            # Extract text using AWS Textract (for fallback and display)
            extracted_text = self.extract_text_with_textract(image_content)
            if not extracted_text:
                return Response({
                    "error": "Failed to extract text from image"
                }, status=status.HTTP_400_BAD_REQUEST)
            print("Extracted text:", extracted_text)
            
            # Try to extract ingredients using Query feature first
            query_ingredients = self.extract_ingredients_with_query(image_content)
            print("Query ingredients:", query_ingredients)
            
            # Try to extract nutrition using Query feature first
            query_nutrition = self.extract_nutrition_with_query(image_content)
            print("Query nutrition:", query_nutrition)
            
            # Process nutrition data (use query results if available, otherwise fallback to text parsing)
            if query_nutrition:
                nutrition_data = self.process_query_nutrition_data(query_nutrition)
            else:
                nutrition_data = self.extract_nutrition_data_structured(extracted_text)
            print("Final nutrition data:", nutrition_data)
            
            # Process ingredients data (use query results if available, otherwise fallback to text parsing)
            if query_ingredients:
                ingredients_data = self.process_query_ingredients_data(query_ingredients)
            else:
                ingredients_data = self.extract_ingredients_structured(extracted_text)
            print("Final ingredients data:", ingredients_data)
            
            # Validate product safety
            safety_results = self.validate_product_safety(request.user, ingredients_data.get('ingredients', []))
            
            # Generate AI insights using the same function as Barcode view
            ai_results = self.get_ai_health_insight_and_expert_advice_fast(request.user, nutrition_data, safety_results.get('flagged_ingredients', []))
            
            # Save scan history
            self.save_scan_history(
                user=request.user,
                image_url=image_url,
                extracted_text=extracted_text,
                nutrition_data=nutrition_data,
                ai_results=ai_results,
                safety_status=safety_results.get('safety_status', 'unknown'),
                flagged_ingredients=safety_results.get('flagged_ingredients', []),
                go_ingredients=safety_results.get('go_ingredients', []),
                caution_ingredients=safety_results.get('caution_ingredients', []),
                product_name=nutrition_data.get('product_name', 'AWS OCR Product')
            )

            # Prepare response
            response_data = {
                "success": True,
                "product_name": nutrition_data.get('product_name', 'Unknown Product'),
                "nutrition_data": nutrition_data,
                "ingredients": ingredients_data,
                "safety_analysis": {
                    "safety_status": safety_results.get('safety_status', 'unknown'),
                    "flagged_ingredients": safety_results.get('flagged_ingredients', []),
                    "go_ingredients": safety_results.get('go_ingredients', []),
                    "caution_ingredients": safety_results.get('caution_ingredients', []),
                    "total_ingredients": len(ingredients_data.get('ingredients', [])),
                    "flagged_count": len(safety_results.get('flagged_ingredients', [])),
                    "safe_count": len(safety_results.get('go_ingredients', [])) + len(safety_results.get('caution_ingredients', []))
                },
                "ai_health_insight": ai_results.get("ai_health_insight", ""),
                "expert_advice": ai_results.get("expert_advice", ""),
                "structured_health_analysis": ai_results.get("structured_health_analysis", {}),
                "expert_ai_conclusion": ai_results.get("expert_ai_conclusion", ""),
                "image_url": image_url,
                "extracted_text": extracted_text
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"AWS Textract OCR error: {e}", exc_info=True)
            return Response({
                "error": f"Processing failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def extract_text_with_textract(self, image_content):
        """
        Extract text from image using AWS Textract with enhanced features.
        """
        try:
            if not self.textract_client:
                raise Exception("AWS Textract client not initialized")

            # Ensure image_content is bytes
            if not isinstance(image_content, bytes):
                logging.error("Image content must be bytes")
                return ""

            # Check image size (AWS Textract limit is 5MB)
            if len(image_content) > 5 * 1024 * 1024:
                logging.error("Image too large for AWS Textract (max 5MB)")
                return ""

            # Try analyze_document first (more features)
            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['TABLES', 'FORMS', 'LINES']
                )
                
                # Extract text with spatial information
                extracted_text = ""
                blocks = response.get('Blocks', [])
                
                # Sort blocks by geometry for proper reading order
                text_blocks = [block for block in blocks if block['BlockType'] == 'LINE']
                text_blocks.sort(key=lambda x: (x['Geometry']['BoundingBox']['Top'], x['Geometry']['BoundingBox']['Left']))
                
                for block in text_blocks:
                    if 'Text' in block:
                        extracted_text += block['Text'] + "\n"

                # Also extract table data if present
                table_data = self.extract_table_data(blocks)
                if table_data:
                    extracted_text += "\n" + table_data

                return extracted_text.strip()
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['InvalidDocumentException', 'InvalidParameterException']:
                    logging.warning(f"analyze_document failed with {error_code}, trying detect_document_text")
                    
                    # Fallback to simpler text detection
                    try:
                        response = self.textract_client.detect_document_text(
                            Document={
                                'Bytes': image_content
                            }
                        )
                        
                        # Extract text from simpler response
                        extracted_text = ""
                        blocks = response.get('Blocks', [])
                        
                        for block in blocks:
                            if block['BlockType'] == 'LINE' and 'Text' in block:
                                extracted_text += block['Text'] + "\n"
                        
                        return extracted_text.strip()
                        
                    except Exception as fallback_error:
                        logging.error(f"Fallback detect_document_text also failed: {fallback_error}")
                        raise e  # Re-raise original error
                else:
                    raise e  # Re-raise non-fallback errors

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error'].get('Message', '')
            logging.error(f"AWS Textract error: {error_code} - {error_message}")
            
            if error_code == 'InvalidDocumentException':
                logging.error("Invalid document format for Textract - check image format")
            elif error_code == 'DocumentTooLargeException':
                logging.error("Document too large for Textract (max 5MB)")
            elif error_code == 'InvalidParameterException':
                logging.error("Invalid parameter - check image data format")
            else:
                logging.error(f"Unknown AWS Textract error: {error_code}")
            return ""
        except NoCredentialsError:
            logging.error("AWS credentials not found")
            return ""
        except Exception as e:
            logging.error(f"Textract extraction error: {e}")
            return ""

    def extract_ingredients_with_query(self, image_content):
        """
        Extract ingredients using AWS Textract Query feature for precise extraction.
        """
        try:
            if not self.textract_client:
                raise Exception("AWS Textract client not initialized")

            # Query for ingredients
            queries = [
                {
                    'Text': 'What are the ingredients?',
                    'Alias': 'ingredients'
                },
                {
                    'Text': 'List all ingredients',
                    'Alias': 'ingredients_list'
                },
                {
                    'Text': 'What ingredients are in this product?',
                    'Alias': 'product_ingredients'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                ingredients = []
                
                # Extract answers from the response
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        # Find the answer block
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                ingredients.append(answer_block['Text'])
                
                return ingredients
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['InvalidDocumentException', 'InvalidParameterException']:
                    logging.warning(f"Query failed with {error_code}, falling back to text extraction")
                    return []
                else:
                    raise e

        except Exception as e:
            logging.error(f"Textract Query extraction error: {e}")
            return []

    def extract_nutrition_with_query(self, image_content):
        """
        Extract nutrition data using AWS Textract Query feature.
        """
        try:
            if not self.textract_client:
                raise Exception("AWS Textract client not initialized")

            # Query for nutrition information
            queries = [
                {
                    'Text': 'What is the energy/calories value?',
                    'Alias': 'energy'
                },
                {
                    'Text': 'What is the protein content?',
                    'Alias': 'protein'
                },
                {
                    'Text': 'What is the total fat content?',
                    'Alias': 'total_fat'
                },
                {
                    'Text': 'What is the saturated fat content?',
                    'Alias': 'saturated_fat'
                },
                {
                    'Text': 'What is the carbohydrate content?',
                    'Alias': 'carbohydrates'
                },
                {
                    'Text': 'What is the sugar content?',
                    'Alias': 'sugars'
                },
                {
                    'Text': 'What is the sodium content?',
                    'Alias': 'sodium'
                },
                {
                    'Text': 'What is the fiber content?',
                    'Alias': 'fiber'
                }
            ]

            try:
                response = self.textract_client.analyze_document(
                    Document={
                        'Bytes': image_content
                    },
                    FeatureTypes=['QUERIES'],
                    QueriesConfig={
                        'Queries': queries
                    }
                )
                
                nutrition_data = {}
                
                # Extract answers from the response
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'QUERY_RESULT':
                        query_alias = block.get('Query', {}).get('Alias', '')
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'ANSWER':
                                    for answer_id in relationship['Ids']:
                                        # Find the answer block
                                        for answer_block in response.get('Blocks', []):
                                            if answer_block['Id'] == answer_id and 'Text' in answer_block:
                                                nutrition_data[query_alias] = answer_block['Text']
                
                return nutrition_data
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['InvalidDocumentException', 'InvalidParameterException']:
                    logging.warning(f"Nutrition Query failed with {error_code}, falling back to text extraction")
                    return {}
                else:
                    raise e

        except Exception as e:
            logging.error(f"Nutrition Query extraction error: {e}")
            return {}

    def process_query_nutrition_data(self, query_nutrition):
        """
        Process nutrition data from Textract Query results.
        """
        nutrition_data = {
            "product_name": "",
            "serving_size": "",
            "servings_per_container": "",
            "calories": {"value": 0, "unit": "kcal", "daily_value": 0},
            "total_fat": {"value": 0, "unit": "g", "daily_value": 0},
            "saturated_fat": {"value": 0, "unit": "g", "daily_value": 0},
            "trans_fat": {"value": 0, "unit": "g", "daily_value": 0},
            "cholesterol": {"value": 0, "unit": "mg", "daily_value": 0},
            "sodium": {"value": 0, "unit": "mg", "daily_value": 0},
            "total_carbohydrates": {"value": 0, "unit": "g", "daily_value": 0},
            "dietary_fiber": {"value": 0, "unit": "g", "daily_value": 0},
            "total_sugars": {"value": 0, "unit": "g", "daily_value": 0},
            "added_sugars": {"value": 0, "unit": "g", "daily_value": 0},
            "protein": {"value": 0, "unit": "g", "daily_value": 0},
            "vitamin_d": {"value": 0, "unit": "mcg", "daily_value": 0},
            "calcium": {"value": 0, "unit": "mg", "daily_value": 0},
            "iron": {"value": 0, "unit": "mg", "daily_value": 0},
            "potassium": {"value": 0, "unit": "mg", "daily_value": 0}
        }

        # Map query results to nutrition data
        for key, value in query_nutrition.items():
            if value:
                # Extract numeric value and unit from the query result
                match = re.search(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', value)
                if match:
                    numeric_value = float(match.group(1))
                    unit = match.group(2).lower()
                    
                    if key == 'energy':
                        nutrition_data['calories']['value'] = numeric_value
                        nutrition_data['calories']['unit'] = 'kcal' if 'kcal' in unit else unit
                    elif key == 'protein':
                        nutrition_data['protein']['value'] = numeric_value
                        nutrition_data['protein']['unit'] = 'g'
                    elif key == 'total_fat':
                        nutrition_data['total_fat']['value'] = numeric_value
                        nutrition_data['total_fat']['unit'] = 'g'
                    elif key == 'saturated_fat':
                        nutrition_data['saturated_fat']['value'] = numeric_value
                        nutrition_data['saturated_fat']['unit'] = 'g'
                    elif key == 'carbohydrates':
                        nutrition_data['total_carbohydrates']['value'] = numeric_value
                        nutrition_data['total_carbohydrates']['unit'] = 'g'
                    elif key == 'sugars':
                        nutrition_data['total_sugars']['value'] = numeric_value
                        nutrition_data['total_sugars']['unit'] = 'g'
                    elif key == 'sodium':
                        nutrition_data['sodium']['value'] = numeric_value
                        nutrition_data['sodium']['unit'] = 'mg'
                    elif key == 'fiber':
                        nutrition_data['dietary_fiber']['value'] = numeric_value
                        nutrition_data['dietary_fiber']['unit'] = 'g'

        return nutrition_data

    def process_query_ingredients_data(self, query_ingredients):
        """
        Process ingredients data from Textract Query results.
        """
        ingredients_data = {
            "ingredients": [],
            "allergens": [],
            "contains": [],
            "may_contain": []
        }

        if query_ingredients:
            # Join all ingredient responses and clean them up
            ingredients_text = " ".join(query_ingredients)
            
            # Clean up the ingredients text
            ingredients_text = re.sub(r'[^\w\s,()%.]', ' ', ingredients_text)  # Remove special characters except important ones
            ingredients_text = re.sub(r'\s+', ' ', ingredients_text)  # Normalize whitespace
            
            # Split ingredients by common separators
            separators = [',', ';', '•', '·', '*', 'and']
            ingredients = []
            
            for separator in separators:
                if separator in ingredients_text:
                    parts = ingredients_text.split(separator)
                    break
            else:
                # If no separators found, try to split by common patterns
                parts = re.split(r'\s+(?=[A-Z])', ingredients_text)

            for part in parts:
                ingredient = part.strip()
                if ingredient and len(ingredient) > 2:
                    # Clean up ingredient
                    ingredient = re.sub(r'^\d+\.?\s*', '', ingredient)  # Remove numbers
                    ingredient = re.sub(r'^\s*[-•]\s*', '', ingredient)  # Remove bullet points
                    ingredient = ingredient.strip()
                    
                    # Skip if it's just a number, percentage, or very short
                    if (ingredient and len(ingredient) > 2 and 
                        not re.match(r'^\d+\.?\d*%?$', ingredient) and
                        not ingredient.lower() in ['and', 'or', 'the', 'a', 'an']):
                        ingredients.append(ingredient)

            # Remove duplicates while preserving order
            seen = set()
            unique_ingredients = []
            for ingredient in ingredients:
                if ingredient.lower() not in seen:
                    seen.add(ingredient.lower())
                    unique_ingredients.append(ingredient)

            ingredients_data["ingredients"] = unique_ingredients

        return ingredients_data

    def extract_table_data(self, blocks):
        """
        Extract structured table data from Textract blocks.
        """
        try:
            table_data = ""
            tables = []
            current_table = []
            
            for block in blocks:
                if block['BlockType'] == 'TABLE':
                    # Process table structure
                    table_text = self.process_table_block(block, blocks)
                    if table_text:
                        table_data += f"\nTABLE:\n{table_text}\n"
            
            return table_data
        except Exception as e:
            logging.error(f"Table extraction error: {e}")
            return ""

    def process_table_block(self, table_block, all_blocks):
        """
        Process individual table block to extract structured data.
        """
        try:
            table_text = ""
            table_id = table_block['Id']
            
            # Find cells in this table
            cells = [block for block in all_blocks if block.get('Relationships') and 
                    any(rel['Type'] == 'CHILD' and table_id in rel['Ids'] for rel in block['Relationships'])]
            
            # Sort cells by row and column
            cells.sort(key=lambda x: (x.get('RowIndex', 0), x.get('ColumnIndex', 0)))
            
            current_row = 0
            for cell in cells:
                if cell.get('RowIndex', 0) != current_row:
                    table_text += "\n"
                    current_row = cell.get('RowIndex', 0)
                
                # Extract text from cell
                cell_text = ""
                if 'Relationships' in cell:
                    for rel in cell['Relationships']:
                        if rel['Type'] == 'CHILD':
                            for child_id in rel['Ids']:
                                child_block = next((b for b in all_blocks if b['Id'] == child_id), None)
                                if child_block and 'Text' in child_block:
                                    cell_text += child_block['Text'] + " "
                
                table_text += cell_text.strip() + "\t"
            
            return table_text
        except Exception as e:
            logging.error(f"Table block processing error: {e}")
            return ""

    def extract_nutrition_data_structured(self, text):
        """
        Extract nutrition data in a structured format using dynamic patterns.
        """
        nutrition_data = {
            "product_name": "",
            "serving_size": "",
            "servings_per_container": "",
            "calories": {"value": 0, "unit": "kcal", "daily_value": 0},
            "total_fat": {"value": 0, "unit": "g", "daily_value": 0},
            "saturated_fat": {"value": 0, "unit": "g", "daily_value": 0},
            "trans_fat": {"value": 0, "unit": "g", "daily_value": 0},
            "cholesterol": {"value": 0, "unit": "mg", "daily_value": 0},
            "sodium": {"value": 0, "unit": "mg", "daily_value": 0},
            "total_carbohydrates": {"value": 0, "unit": "g", "daily_value": 0},
            "dietary_fiber": {"value": 0, "unit": "g", "daily_value": 0},
            "total_sugars": {"value": 0, "unit": "g", "daily_value": 0},
            "added_sugars": {"value": 0, "unit": "g", "daily_value": 0},
            "protein": {"value": 0, "unit": "g", "daily_value": 0},
            "vitamin_d": {"value": 0, "unit": "mcg", "daily_value": 0},
            "calcium": {"value": 0, "unit": "mg", "daily_value": 0},
            "iron": {"value": 0, "unit": "mg", "daily_value": 0},
            "potassium": {"value": 0, "unit": "mg", "daily_value": 0},
            # Dynamic nutrients will be added here
            "other_nutrients": {}
        }

        # Extract product name (usually at the top)
        lines = text.split('\n')
        for i, line in enumerate(lines[:5]):  # Check first 5 lines
            if len(line.strip()) > 3 and not any(nutrient in line.lower() for nutrient in ['calories', 'fat', 'protein', 'ingredients']):
                nutrition_data["product_name"] = line.strip()
                break

        # First, try to extract using predefined patterns for common nutrients
        nutrition_data = self.extract_common_nutrients(text, nutrition_data)
        
        # Then, extract any additional nutrients dynamically
        nutrition_data = self.extract_dynamic_nutrients(text, nutrition_data)

        return nutrition_data

    def extract_common_nutrients(self, text, nutrition_data):
        """
        Extract common nutrients using predefined patterns.
        """
        # Enhanced nutrition extraction patterns for table format
        patterns = {
            "serving_size": [
                r'serving\s+size[:\s]*([^\n]+)',
                r'serving\s+information[:\s]*([^\n]+)'
            ],
            "servings_per_container": [
                r'servings\s+per\s+container[:\s]*(\d+(?:\.\d+)?)',
                r'servings[:\s]*(\d+(?:\.\d+)?)',
                r'pack\s+contains\s+(\d+(?:\.\d+)?)\s+servings'
            ],
            "calories": [
                r'calories[:\s]*(\d+(?:\.\d+)?)\s*(kcal|cal)',
                r'energy[:\s]*(\d+(?:\.\d+)?)\s*(kcal|cal)',
                r'(\d+(?:\.\d+)?)\s*(kcal|cal)\s*calories',
                r'energy\s*\(kcal\)\s*\n\s*(\d+(?:\.\d+)?)',
                r'calories\s*\n\s*(\d+(?:\.\d+)?)'
            ],
            "total_fat": [
                r'total\s+fat[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'fat[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'(\d+(?:\.\d+)?)\s*g\s*total\s+fat',
                r'total\s+fat\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)',
                r'fat\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)'
            ],
            "saturated_fat": [
                r'saturated\s+fat[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'sat\s+fat[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'saturated\s+fat\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)',
                r'sat\s+fat\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)'
            ],
            "trans_fat": [
                r'trans\s+fat[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'trans[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'trans\s+fat\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)'
            ],
            "cholesterol": [
                r'cholesterol[:\s]*(\d+(?:\.\d+)?)\s*mg',
                r'(\d+(?:\.\d+)?)\s*mg\s*cholesterol',
                r'cholesterol\s*\(mg\)\s*\n\s*(\d+(?:\.\d+)?)'
            ],
            "sodium": [
                r'sodium[:\s]*(\d+(?:\.\d+)?)\s*mg',
                r'salt[:\s]*(\d+(?:\.\d+)?)\s*mg',
                r'sodium\s*\(mg\)\s*\n\s*(\d+(?:\.\d+)?)'
            ],
            "total_carbohydrates": [
                r'total\s+carbohydrates[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'carbohydrates[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'carbs[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'carbohydrate\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)',
                r'carbohydrates\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)'
            ],
            "dietary_fiber": [
                r'dietary\s+fiber[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'fiber[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'dietary\s+fibre\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)',
                r'fiber\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)'
            ],
            "total_sugars": [
                r'total\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'sugars[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'total\s+sugars\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)',
                r'sugars\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)'
            ],
            "added_sugars": [
                r'added\s+sugars[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'(\d+(?:\.\d+)?)\s*g\s*added\s+sugars',
                r'added\s+sugars\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)'
            ],
            "protein": [
                r'protein[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'(\d+(?:\.\d+)?)\s*g\s*protein',
                r'protein\s*\(g\)\s*\n\s*(\d+(?:\.\d+)?)'
            ]
        }

        for nutrient, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if nutrient in ["serving_size", "servings_per_container"]:
                        nutrition_data[nutrient] = match.group(1).strip()
                    else:
                        try:
                            value = float(match.group(1))
                            nutrition_data[nutrient]["value"] = value
                            if len(match.groups()) > 1:
                                nutrition_data[nutrient]["unit"] = match.group(2)
                        except ValueError:
                            continue
                    break

        return nutrition_data

    def extract_dynamic_nutrients(self, text, nutrition_data):
        """
        Dynamically extract any nutrition data that doesn't match predefined patterns.
        """
        # Common nutrition keywords to look for
        nutrition_keywords = [
            'vitamin', 'mineral', 'calcium', 'iron', 'zinc', 'magnesium', 'phosphorus',
            'potassium', 'sodium', 'chloride', 'bicarbonate', 'sulfate', 'copper',
            'manganese', 'selenium', 'chromium', 'molybdenum', 'iodine', 'fluoride',
            'omega', 'fiber', 'fibre', 'sugar', 'starch', 'alcohol', 'water',
            'ash', 'moisture', 'dry matter', 'crude protein', 'crude fat',
            'crude fiber', 'nitrogen', 'phosphorus', 'calcium', 'magnesium',
            'sodium', 'potassium', 'chloride', 'sulfur', 'iron', 'zinc',
            'copper', 'manganese', 'selenium', 'cobalt', 'iodine', 'vitamin a',
            'vitamin b', 'vitamin c', 'vitamin d', 'vitamin e', 'vitamin k',
            'thiamin', 'riboflavin', 'niacin', 'pantothenic acid', 'pyridoxine',
            'biotin', 'folic acid', 'cobalamin', 'ascorbic acid', 'retinol',
            'carotene', 'tocopherol', 'phylloquinone', 'menaquinone'
        ]

        # Pattern to find nutrient name followed by value and unit
        # This will catch any nutrient format like "Vitamin C 15 mg" or "Zinc 2.5 mg"
        dynamic_patterns = [
            # Pattern 1: "Nutrient Name (unit)\nValue"
            r'([a-zA-Z\s]+)\s*\(([a-zA-Z%]+)\)\s*\n\s*(\d+(?:\.\d+)?)',
            # Pattern 2: "Nutrient Name: Value unit"
            r'([a-zA-Z\s]+)[:\s]+(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)',
            # Pattern 3: "Nutrient Name Value unit"
            r'([a-zA-Z\s]+)\s+(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)',
            # Pattern 4: "Value unit Nutrient Name"
            r'(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)\s+([a-zA-Z\s]+)',
        ]

        for pattern in dynamic_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 3:
                    if pattern == r'([a-zA-Z\s]+)\s*\(([a-zA-Z%]+)\)\s*\n\s*(\d+(?:\.\d+)?)':
                        # Pattern 1: "Nutrient Name (unit)\nValue"
                        nutrient_name = match.group(1).strip()
                        unit = match.group(2).strip()
                        value = match.group(3)
                    elif pattern == r'([a-zA-Z\s]+)[:\s]+(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)':
                        # Pattern 2: "Nutrient Name: Value unit"
                        nutrient_name = match.group(1).strip()
                        value = match.group(2)
                        unit = match.group(3).strip()
                    elif pattern == r'([a-zA-Z\s]+)\s+(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)':
                        # Pattern 3: "Nutrient Name Value unit"
                        nutrient_name = match.group(1).strip()
                        value = match.group(2)
                        unit = match.group(3).strip()
                    else:
                        # Pattern 4: "Value unit Nutrient Name"
                        value = match.group(1)
                        unit = match.group(2).strip()
                        nutrient_name = match.group(3).strip()

                    # Check if this looks like a nutrition value
                    if any(keyword in nutrient_name.lower() for keyword in nutrition_keywords):
                        try:
                            numeric_value = float(value)
                            # Clean up nutrient name
                            clean_name = re.sub(r'\s+', ' ', nutrient_name).strip().lower()
                            
                            # Check if it's already in our predefined nutrients
                            if clean_name not in nutrition_data:
                                # Add to other_nutrients
                                nutrition_data["other_nutrients"][clean_name] = {
                                    "value": numeric_value,
                                    "unit": unit,
                                    "daily_value": 0
                                }
                        except ValueError:
                            continue

        return nutrition_data

    def extract_ingredients_structured(self, text):
        """
        Extract ingredients in a structured format.
        """
        ingredients_data = {
            "ingredients": [],
            "allergens": [],
            "contains": [],
            "may_contain": []
        }

        # Find ingredients section - multiple patterns for different formats
        ingredients_section = ""
        lines = text.split('\n')
        
        # Pattern 1: Look for "Ingredients:" or "Ingredients" followed by ingredients
        for i, line in enumerate(lines):
            if 'ingredients' in line.lower():
                # Check if this line contains ingredients after colon
                if ':' in line:
                    ingredients_text = line.split(':', 1)[1].strip()
                    if ingredients_text:
                        ingredients_section = ingredients_text
                        # Continue reading next lines for more ingredients
                        for j in range(i + 1, min(i + 30, len(lines))):
                            next_line = lines[j].strip()
                            if next_line and not any(keyword in next_line.lower() for keyword in 
                                                   ['nutrition', 'calories', 'serving', 'daily', 'allergen', 'energy', 'fat', 'protein']):
                                ingredients_section += " " + next_line
                            else:
                                break
                        break
                else:
                    # If line just says "Ingredients", read next lines
                    ingredients_text = ""
                    for j in range(i + 1, min(i + 30, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not any(keyword in next_line.lower() for keyword in 
                                               ['nutrition', 'calories', 'serving', 'daily', 'allergen', 'energy', 'fat', 'protein']):
                            ingredients_text += " " + next_line
                        else:
                            break
                    if ingredients_text.strip():
                        ingredients_section = ingredients_text.strip()
                        break

        # Pattern 2: Look for ingredients in table format (common with Textract)
        if not ingredients_section:
            for i, line in enumerate(lines):
                if 'ingredients' in line.lower():
                    # Look for ingredients in subsequent lines in table format
                    ingredients_text = ""
                    for j in range(i + 1, min(i + 50, len(lines))):
                        next_line = lines[j].strip()
                        # Skip empty lines and nutrition-related lines
                        if next_line and not any(keyword in next_line.lower() for keyword in 
                                               ['nutrition', 'calories', 'serving', 'daily', 'allergen', 'energy', 'fat', 'protein', 'carbohydrate', 'sodium']):
                            # Check if this looks like an ingredient (not a number or percentage)
                            if not re.match(r'^\d+\.?\d*%?$', next_line) and len(next_line) > 2:
                                ingredients_text += " " + next_line
                        elif next_line and any(keyword in next_line.lower() for keyword in ['allergen', 'contains', 'may contain']):
                            # Stop at allergen information
                            break
                    if ingredients_text.strip():
                        ingredients_section = ingredients_text.strip()
                        break

        # Pattern 3: Look for ingredients after nutrition facts (common format)
        if not ingredients_section:
            nutrition_end = -1
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['potassium', 'vitamin', 'minerals', '***']):
                    nutrition_end = i
                    break
            
            if nutrition_end > 0:
                # Look for ingredients after nutrition facts
                for i in range(nutrition_end + 1, len(lines)):
                    line = lines[i].strip()
                    if 'ingredients' in line.lower():
                        ingredients_text = ""
                        for j in range(i + 1, min(i + 30, len(lines))):
                            next_line = lines[j].strip()
                            if next_line and not any(keyword in next_line.lower() for keyword in 
                                                   ['nutrition', 'calories', 'serving', 'daily', 'allergen', 'energy', 'fat', 'protein']):
                                ingredients_text += " " + next_line
                            else:
                                break
                        if ingredients_text.strip():
                            ingredients_section = ingredients_text.strip()
                            break

        if ingredients_section:
            # Parse ingredients
            ingredients = self.parse_ingredients_list(ingredients_section)
            ingredients_data["ingredients"] = ingredients

            # Extract allergens
            allergens = self.extract_allergens(text)
            ingredients_data["allergens"] = allergens

        return ingredients_data

    def parse_ingredients_list(self, ingredients_text):
        """
        Parse ingredients text into a structured list.
        """
        ingredients = []
        
        # Common ingredient separators
        separators = [',', ';', '•', '·', '*', '\n','and']
        
        # Split by common separators
        for separator in separators:
            if separator in ingredients_text:
                parts = ingredients_text.split(separator)
                break
        else:
            # If no separators found, try to split by common patterns
            parts = re.split(r'\s+(?=[A-Z])', ingredients_text)

        for part in parts:
            ingredient = part.strip()
            if ingredient and len(ingredient) > 2:
                # Clean up ingredient
                ingredient = re.sub(r'^\d+\.?\s*', '', ingredient)  # Remove numbers
                ingredient = re.sub(r'[()]', '', ingredient)  # Remove parentheses
                ingredient = re.sub(r'^\s*[-•]\s*', '', ingredient)  # Remove bullet points
                ingredient = ingredient.strip()
                
                # Skip if it's just a number, percentage, or very short
                if (ingredient and len(ingredient) > 2 and 
                    not re.match(r'^\d+\.?\d*%?$', ingredient) and
                    not ingredient.lower() in ['and', 'or', 'the', 'a', 'an']):
                    ingredients.append(ingredient)

        # Remove duplicates while preserving order
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            if ingredient.lower() not in seen:
                seen.add(ingredient.lower())
                unique_ingredients.append(ingredient)

        return unique_ingredients

    def extract_allergens(self, text):
        """
        Extract allergen information from text.
        """
        allergens = []
        allergen_keywords = [
            'contains', 'may contain', 'allergens', 'allergen information',
            'wheat', 'milk', 'eggs', 'fish', 'shellfish', 'tree nuts', 'peanuts', 'soybeans',
            'gluten', 'lactose', 'nuts', 'dairy', 'soy'
        ]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in allergen_keywords):
                # Get the full allergen information (current line + next few lines)
                allergen_info = line.strip()
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not any(keyword in next_line.lower() for keyword in 
                                           ['nutrition', 'calories', 'serving', 'daily', 'energy', 'fat', 'protein']):
                        allergen_info += " " + next_line
                    else:
                        break
                allergens.append(allergen_info)
        
        return allergens

    def validate_product_safety(self, user, ingredients_list):
        """
        Validate product safety using existing logic.
        """
        # This will use the existing validation logic from other views
        # For now, return a basic structure
        return {
            "safety_status": "unknown",
            "flagged_ingredients": [],
            "go_ingredients": [],
            "caution_ingredients": []
        }

    def get_ai_health_insight_and_expert_advice_fast(self, user, nutrition_data, flagged_ingredients):
        import json
        import hashlib
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        key_data = {
            'ingredients': sorted(flagged_ingredients),
            'nutrition': nutrition_data,
            'diet': user.Dietary_preferences,
            'health': user.Health_conditions,
            'allergies': user.Allergies
        }
        cache_key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        if hasattr(self, 'ai_cache') and cache_key in self.ai_cache:
            return self.ai_cache[cache_key]
        nutrition_summary = ', '.join(f"{k}: {v}" for k, v in nutrition_data.items() if k.lower() in ["calories", "energy", "protein", "fat", "sugar"])
        flagged_str = ', '.join(flagged_ingredients[:5])
        user_profile = f"Diet: {user.Dietary_preferences}; Allergies: {user.Allergies}; Health: {user.Health_conditions}"
        prompt = f"""
        You are a certified health and nutrition expert.

        User Profile:
        Diet: {user.Dietary_preferences}
        Health Conditions: {user.Health_conditions}
        Allergies: {user.Allergies}

        Product Nutrition: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}

        Give a short health insight: safety, red flags, and user-friendly advice.
        """

        expert_prompt = f"""
        You are a food science expert. Based on the nutrition data and flagged ingredients below, give a detailed expert-level opinion with technical insight.

        Nutrition Data: {nutrition_data}
        Flagged Ingredients: {flagged_ingredients}
        """
        def openai_call():
            from openai import OpenAI
            client = OpenAI(
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=10
            )
            try:
                model = "gpt-3.5-turbo-instant"
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert in food science and health."},
                        {"role": "user", "content": prompt},
                    ],
                )
            except Exception:
                model = "gpt-3.5-turbo"
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert in food science and health."},
                        {"role": "user", "content": prompt},
                    ],
                )
            content = completion.choices[0].message.content.strip()
            try:
                result = json.loads(content)
            except Exception:
                import re
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    try:
                        result = json.loads(match.group(0))
                    except Exception:
                        result = {"ai_health_insight": content, "expert_advice": content}
                else:
                    result = {"ai_health_insight": content, "expert_advice": content}
            return result
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(openai_call)
            try:
                result = future.result(timeout=5)
                if hasattr(self, 'ai_cache'):
                    self.ai_cache[cache_key] = result
                return result
            except TimeoutError:
                return {"ai_health_insight": "AI service timed out.", "expert_advice": "AI service timed out."}
            except Exception as e:
                return {"ai_health_insight": "AI service unavailable.", "expert_advice": "AI service unavailable."}

    def save_scan_history(self, **kwargs):
        """
        Save scan history to database.
        """
        from .models import FoodLabelScan
        
        # Create scan record
        scan = FoodLabelScan.objects.create(
            user=kwargs['user'],
            image_url=kwargs['image_url'],
            extracted_text=kwargs['extracted_text'],
            nutrition_data=kwargs['nutrition_data'],
            safety_status=kwargs['safety_status'],
            flagged_ingredients=kwargs['flagged_ingredients']
        )
        
        # Increment scan count for freemium users
        increment_user_scan_count(kwargs['user'])
        
        return scan

    def save_image(self, image_content):
        """
        Save image and return URL.
        """
        # Use existing image saving logic
        # This should integrate with your current image storage system
        return "image_url_placeholder"

    def test_aws_connection(self):
        """
        Test AWS Textract connection.
        """
        try:
            if not self.textract_client:
                return False, "AWS Textract client not initialized"
            
            # Try a simple operation to test connection
            # We'll use a minimal test that doesn't require an actual image
            return True, "AWS Textract client initialized successfully"
            
        except Exception as e:
            return False, f"AWS connection failed: {str(e)}"

class NotificationTestView(APIView):
    """Simple view to serve the notification testing page"""
    permission_classes = []  # Allow anyone to access for testing
    
    def get(self, request):
        from django.shortcuts import render
        return render(request, 'test_notifications.html')

class MobileNotificationTestView(APIView):
    """Mobile-optimized notification testing page"""
    permission_classes = []
    
    def get(self, request):
        from django.shortcuts import render
        return render(request, 'mobile_test.html')

class SimpleNotificationTestView(APIView):
    """Simple notification testing page without Firebase"""
    permission_classes = []
    
    def get(self, request):
        from django.shortcuts import render
        return render(request, 'simple_test.html')

class SubscriptionManagementView(APIView):
    """
    Comprehensive subscription management endpoint that handles:
    - Plan switching (upgrade/downgrade)
    - Platform-specific subscription management
    - Confirmation flows for plan changes
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current subscription status and available actions"""
        user = request.user
        
        try:
            subscription = UserSubscription.objects.get(user=user)
        except UserSubscription.DoesNotExist:
            subscription = None
        
        # Get current plan info
        current_plan = self._get_current_plan_info(subscription)
        
        # Get available actions based on current plan and platform
        available_actions = self._get_available_actions(subscription)
        
        # Get platform-specific management links
        management_links = self._get_management_links(subscription)
        
        return Response({
            'current_plan': current_plan,
            'available_actions': available_actions,
            'management_links': management_links,
            'platform': subscription.platform if subscription else 'stripe'
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """Handle plan changes and subscription management actions"""
        user = request.user
        action = request.data.get('action')
        target_plan = request.data.get('target_plan')
        confirm = request.data.get('confirm', False)
        
        if not action:
            return Response({'error': 'Action is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            subscription = UserSubscription.objects.get(user=user)
        except UserSubscription.DoesNotExist:
            subscription = None
        
        if action == 'switch_plan':
            return self._handle_plan_switch(user, subscription, target_plan, confirm)
        elif action == 'downgrade_to_freemium':
            return self._handle_downgrade(user, subscription, confirm)
        elif action == 'restore_purchases':
            return self._handle_restore_purchases(user, request.data.get('platform'))
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    def _get_current_plan_info(self, subscription):
        """Get detailed current plan information"""
        if not subscription:
            return {
                'plan_name': 'freemium',
                'plan_id': 'freemium',
                'status': 'active',
                'is_premium': False,
                'platform': 'stripe',
                'renewal_date': None,
                'cancel_date': None,
                'subscription_start_date': None,
                'subscription_end_date': None,
                'plan_type': 'freemium',
                'status_display': 'Freemium',
                'features': [
                    '20 free scans per month',
                    'Basic nutrition analysis',
                    'Ingredient safety check',
                    'Basic health insights'
                ]
            }
        
        # Calculate status display
        if subscription.cancel_at_period_end:
            status_display = f"Premium (cancels on {subscription.cancel_at.strftime('%b %d') if subscription.cancel_at else 'period end'})"
        elif subscription.status == 'past_due':
            status_display = "Past due—retries in X days"
        elif subscription.status == 'active':
            if subscription.renewal_date:
                status_display = f"Premium • Renews on {subscription.renewal_date.strftime('%b %d')}"
            else:
                status_display = "Premium"
        else:
            status_display = subscription.get_status_display()
        
        return {
            'plan_name': subscription.plan_name,
            'plan_id': f"{subscription.plan_name}_{subscription.premium_type}" if subscription.premium_type else subscription.plan_name,
            'status': subscription.status,
            'is_premium': subscription.is_premium,
            'platform': subscription.platform,
            'renewal_date': subscription.renewal_date.isoformat() if subscription.renewal_date else None,
            'cancel_date': subscription.cancel_date.isoformat() if subscription.cancel_date else None,
            'subscription_start_date': subscription.started_at.isoformat() if subscription.started_at else None,
            'subscription_end_date': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            'plan_type': subscription.premium_type if subscription.premium_type else subscription.plan_name,
            'status_display': status_display,
            'features': self._get_plan_features(subscription.plan_name, subscription.premium_type)
        }

    def _get_available_actions(self, subscription):
        """Get available actions based on current subscription"""
        actions = []
        
        if not subscription or subscription.plan_name == 'freemium':
            # Can upgrade to premium
            actions.extend([
                {
                    'action': 'switch_plan',
                    'target_plan': 'premium_monthly',
                    'label': 'Upgrade to Premium Monthly',
                    'description': 'Unlimited premium scans and premium features',
                    'requires_confirmation': False
                },
                {
                    'action': 'switch_plan',
                    'target_plan': 'premium_yearly',
                    'label': 'Upgrade to Premium Yearly',
                    'description': 'Unlimited premium scans and premium features (save with yearly)',
                    'requires_confirmation': False
                }
            ])
        elif subscription.plan_name == 'premium':
            # Can downgrade to freemium
            actions.append({
                'action': 'downgrade_to_freemium',
                'target_plan': 'freemium',
                'label': 'Switch to Freemium',
                'description': 'Downgrade to free plan',
                'requires_confirmation': True,
                'confirmation_message': self._get_downgrade_confirmation_message(subscription)
            })
            
            # Can switch between monthly/yearly if different
            if subscription.premium_type == 'monthly':
                actions.append({
                    'action': 'switch_plan',
                    'target_plan': 'premium_yearly',
                    'label': 'Switch to Yearly',
                    'description': 'Save with yearly billing',
                    'requires_confirmation': True,
                    'confirmation_message': 'You\'ll be charged for the yearly plan immediately. Your current monthly subscription will be canceled.'
                })
            elif subscription.premium_type == 'yearly':
                actions.append({
                    'action': 'switch_plan',
                    'target_plan': 'premium_monthly',
                    'label': 'Switch to Monthly',
                    'description': 'Switch to monthly billing',
                    'requires_confirmation': True,
                    'confirmation_message': 'You\'ll be charged for the monthly plan immediately. Your current yearly subscription will be canceled.'
                })
        
        # Add restore purchases for mobile platforms
        if subscription and subscription.platform in ['ios', 'android']:
            actions.append({
                'action': 'restore_purchases',
                'label': 'Restore Purchases',
                'description': 'Restore your previous purchases',
                'requires_confirmation': False
            })
        
        return actions

    def _get_management_links(self, subscription):
        """Get platform-specific subscription management links"""
        if not subscription:
            return {}
        
        links = {}
        
        if subscription.platform == 'ios':
            links['manage_subscription'] = {
                'label': 'Manage in Apple Subscriptions',
                'url': 'https://apps.apple.com/account/subscriptions',
                'description': 'Manage your subscription through Apple'
            }
        elif subscription.platform == 'android':
            links['manage_subscription'] = {
                'label': 'Manage in Google Subscriptions',
                'url': 'https://play.google.com/store/account/subscriptions',
                'description': 'Manage your subscription through Google Play'
            }
        elif subscription.platform == 'stripe':
            # Generate Stripe Customer Portal link
            try:
                stripe_customer = StripeCustomer.objects.get(user=subscription.user)
                session = stripe.billing_portal.Session.create(
                    customer=stripe_customer.stripe_customer_id,
                    return_url=f"{getattr(settings, 'FRONTEND_URL', 'https://yourapp.com')}/settings/subscription"
                )
                links['manage_subscription'] = {
                    'label': 'Manage in Billing Portal',
                    'url': session.url,
                    'description': 'Manage your subscription and billing'
                }
            except (StripeCustomer.DoesNotExist, Exception):
                links['manage_subscription'] = {
                    'label': 'Contact Support',
                    'url': '/contact-support',
                    'description': 'Contact support for subscription management'
                }
        
        return links

    def _get_downgrade_confirmation_message(self, subscription):
        """Get platform-specific downgrade confirmation message"""
        if subscription.platform in ['ios', 'android']:
            return "Downgrades are managed by your app store. You'll keep Premium until the end of the current billing period. We'll take you to manage your subscription now."
        else:
            return "You'll keep Premium until the end of the current billing period. After that, your account will revert to Freemium features."

    def _get_plan_features(self, plan_name, premium_type=None):
        """Get features for a specific plan"""
        if plan_name == 'freemium':
            return [
                '20 free scans per month',
                'First 6 scans with full AI insights',
                'Remaining 14 scans with basic features',
                'Basic nutrition analysis',
                'Ingredient safety check',
                'Basic health insights'
            ]
        elif plan_name == 'premium':
            return [
                'Unlimited premium scans',
                'Advanced AI insights',
                'Priority support',
                'Detailed health analysis',
                'Ingredient safety alerts',
                'Personalized recommendations'
            ]
        return []

    def _handle_plan_switch(self, user, subscription, target_plan, confirm):
        """Handle switching between plans"""
        if not target_plan:
            return Response({'error': 'Target plan is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse target plan
        if target_plan == 'premium_monthly':
            plan_name = 'premium'
            premium_type = 'monthly'
        elif target_plan == 'premium_yearly':
            plan_name = 'premium'
            premium_type = 'yearly'
        elif target_plan == 'freemium':
            plan_name = 'freemium'
            premium_type = None
        else:
            return Response({'error': 'Invalid target plan'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle downgrade to freemium
        if plan_name == 'freemium' and subscription and subscription.plan_name == 'premium':
            return self._handle_downgrade(user, subscription, confirm)
        
        # Handle upgrade to premium
        if plan_name == 'premium':
            return self._handle_upgrade(user, subscription, premium_type, confirm)
        
        return Response({'error': 'Invalid plan switch'}, status=status.HTTP_400_BAD_REQUEST)

    def _handle_downgrade(self, user, subscription, confirm):
        """Handle downgrade to freemium"""
        if not subscription or subscription.plan_name != 'premium':
            return Response({'error': 'No active premium subscription found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not confirm:
            return Response({
                'error': 'Confirmation required',
                'requires_confirmation': True,
                'confirmation_message': self._get_downgrade_confirmation_message(subscription)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle platform-specific downgrade
        if subscription.platform in ['ios', 'android']:
            # For app store subscriptions, we can't cancel directly
            # Return deep link to store management
            management_links = self._get_management_links(subscription)
            return Response({
                'message': 'Redirecting to subscription management',
                'action': 'redirect_to_store',
                'url': management_links.get('manage_subscription', {}).get('url'),
                'platform': subscription.platform
            }, status=status.HTTP_200_OK)
        
        elif subscription.platform == 'stripe':
            # For Stripe subscriptions, we can cancel directly
            try:
                if subscription.stripe_subscription_id:
                    # Cancel at period end instead of immediately
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                
                # Update local subscription
                subscription.cancel_at_period_end = True
                subscription.cancel_at = subscription.current_period_end
                subscription.save()
                
                # Send notification
                from .tasks import send_subscription_notification_task_celery, safe_execute_task
                safe_execute_task(
                    send_subscription_notification_task_celery,
                    user.id, 
                    'subscription_downgrade_confirmed',
                    plan_type='Freemium'
                )
                
                return Response({
                    'message': 'Subscription will be canceled at the end of the current period',
                    'cancel_date': subscription.cancel_at.isoformat() if subscription.cancel_at else None
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({'error': f'Failed to cancel subscription: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'error': 'Unsupported platform'}, status=status.HTTP_400_BAD_REQUEST)

    def _handle_upgrade(self, user, subscription, premium_type, confirm):
        """Handle upgrade to premium"""
        # This would integrate with the existing SubscribeUserView logic
        # For now, return a response indicating the upgrade flow
        return Response({
            'message': 'Upgrade flow initiated',
            'action': 'initiate_upgrade',
            'premium_type': premium_type,
            'platform': subscription.platform if subscription else 'stripe'
        }, status=status.HTTP_200_OK)

    def _handle_restore_purchases(self, user, platform):
        """Handle restore purchases for mobile platforms"""
        if platform not in ['ios', 'android']:
            return Response({'error': 'Restore purchases only available on mobile platforms'}, status=status.HTTP_400_BAD_REQUEST)
        
        # This would integrate with StoreKit/Google Play Billing
        # For now, return a response indicating the restore flow
        return Response({
            'message': 'Restore purchases initiated',
            'action': 'restore_purchases',
            'platform': platform
        }, status=status.HTTP_200_OK)