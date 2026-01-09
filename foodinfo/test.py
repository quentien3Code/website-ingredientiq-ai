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
from .models import FoodLabelScan, Termandcondition, User, UserSubscription, privacypolicy, AboutUS, FAQ,StripeCustomer, Feedback, DepartmentContact
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
from .utils import send_sms
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
# openai.api_key = os.getenv("OPENAI_API_KEY")
# import feedparser  # For Medium RSS feeds
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
BASE_URL = "https://api.spoonacular.com"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
OPEN_FOOD_FACTS_API = "https://world.openfoodfacts.org/api/v0/product/"
USDA_API_KEY = os.getenv("USDA_API_KEY")
API_KEY = os.getenv("foursquare_api_key")
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WORDPRESS_API_URL = "https://public-api.wordpress.com/rest/v1.1/sites/example.wordpress.com/posts/"
WORDPRESS_BLOG_URL = "https://public-api.wordpress.com/rest/v1.1/sites/example.wordpress.com/posts"
SPOONACULAR_KEY = "c01bfdfb4ccd4d8097b5110f789e0618"
WIKIPEDIA_SEARCH_API_URL = "https://en.wikipedia.org/w/api.php"
WHO_SEARCH_URL = "https://www.who.int/search?q="
WIKIPEDIA_LINKS_API = "https://en.wikipedia.org/w/api.php"
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Set to True for instant local safety check, False to use OpenAI
USE_STATIC_INGREDIENT_SAFETY = False

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
                "OCR Product",  # product_name
                actual_ingredients  # actual_ingredients - SAME AS BARCODE
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
        Generate fully dynamic AI health insights and expert advice based on user's specific health profile.
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
            'allergies': user.Allergies,
            'health_conditions': user.Health_conditions
        }
        cache_key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        if cache_key in self.openai_cache:
            return self.openai_cache[cache_key]
        
        # Prepare comprehensive user profile data
        nutrition_summary = ', '.join(f"{k}: {v}" for k, v in list(nutrition_data.items())[:5])
        flagged_str = ', '.join(flagged_ingredients[:3])  # Only top 3
        
        # Clean and prepare user health data
        health_conditions = [h.strip() for h in user.Health_conditions.split(',') if h.strip()] if user.Health_conditions else []
        dietary_preferences = [d.strip() for d in user.Dietary_preferences.split(',') if d.strip()] if user.Dietary_preferences else []
        allergies = [a.strip() for a in user.Allergies.split(',') if a.strip()] if user.Allergies else []
        
        # Analyze nutrition data for specific concerns
        nutrition_analysis = self._analyze_nutrition_for_health_conditions(nutrition_data, health_conditions)
        
        # Determine risk level dynamically
        risk_level = self._calculate_dynamic_risk_level(health_conditions, dietary_preferences, allergies, flagged_ingredients, nutrition_data)
        
        def openai_call():
            from openai import OpenAI
            import os
            
            try:
                client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    timeout=5.0  # Increased timeout for more complex analysis
                )
                
                # Create comprehensive prompt for dynamic analysis
                prompt = f"""
                As a certified nutritionist and medical expert, analyze this food product for a specific user with the following profile:

                USER HEALTH PROFILE:
                - Health Conditions: {', '.join(health_conditions) if health_conditions else 'None specified'}
                - Dietary Preferences: {', '.join(dietary_preferences) if dietary_preferences else 'None specified'}
                - Allergies: {', '.join(allergies) if allergies else 'None specified'}

                PRODUCT ANALYSIS:
                - Nutrition Data: {nutrition_summary}
                - Flagged Ingredients: {flagged_str}
                - Nutrition Analysis: {nutrition_analysis}

                Generate a comprehensive analysis in the EXACT JSON format below. Make it highly personalized based on the user's specific health conditions, dietary preferences, and allergies:

                {{
                    "ai_health_insight": {{
                        "bluf_insight": "Brief, direct insight focusing on the most critical concern for this specific user's health conditions and allergies. Mention specific values and potential health impacts.",
                        "main_insight": "Detailed analysis explaining how this product affects the user's specific health conditions, dietary preferences, and allergies. Include specific recommendations and guidelines.",
                        "deeper_reference": "Scientific backing with references to WHO, EFSA, PubMed studies, SNOMED CT, and ICD-10 guidelines relevant to the user's specific health conditions. Include specific recommendations for their dietary preferences.",
                        "disclaimer": "Informational, not diagnostic. Consult healthcare providers for medical advice."
                    }},
                    "expert_advice": "Specific, actionable recommendations tailored to the user's health conditions, dietary preferences, and allergies. Include portion control, alternatives, and specific guidance.",
                    "expert_ai_conclusion": {{
                        "prognosis": "Detailed prognosis explaining how regular consumption would affect the user's specific health conditions, considering their dietary preferences and allergies.",
                        "patient_counseling": "Personalized counseling with specific steps the user can take based on their health conditions and dietary preferences. Include specific food alternatives and lifestyle recommendations.",
                        "total_words": 0,
                        "risk_level": "{risk_level}",
                        "evidence_sources": ["SNOMED CT & ICD-10 Clinical Guidelines", "WHO Guidelines", "EFSA Recommendations", "PubMed Research"]
                    }}
                }}

                IMPORTANT GUIDELINES:
                1. Make EVERYTHING specific to the user's actual health conditions, dietary preferences, and allergies
                2. If user has diabetes, focus on sugar/carbohydrate content and blood glucose impact
                3. If user has hypertension, focus on sodium content and blood pressure impact
                4. If user has allergies, highlight specific allergen risks
                5. If user is vegan/vegetarian, check for animal-derived ingredients
                6. If user has heart conditions, focus on saturated fat, cholesterol, and sodium
                7. If user has kidney disease, focus on protein, phosphorus, and potassium
                8. Always provide specific, actionable advice based on their profile
                9. Include specific nutrient values and their implications
                10. Reference appropriate medical guidelines for their conditions

                Return ONLY valid JSON, no additional text.
                """
                
                completion = client.chat.completions.create(
                    model="gpt-4",  # Use GPT-4 for better analysis
                    messages=[
                        {"role": "system", "content": "You are a certified nutritionist and medical expert specializing in personalized dietary analysis. Always provide specific, evidence-based recommendations tailored to individual health profiles. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,  # Increased for comprehensive analysis
                    temperature=0.2,  # Lower temperature for more consistent medical advice
                )
                
                content = completion.choices[0].message.content.strip()
                
                # Clean up the response to ensure it's valid JSON
                content = content.replace('```json', '').replace('```', '').strip()
                
                # Parse JSON
                result = json.loads(content)
                
                # Calculate total words
                total_text = result["ai_health_insight"]["bluf_insight"] + " " + result["ai_health_insight"]["main_insight"] + " " + result["expert_advice"] + " " + result["expert_ai_conclusion"]["prognosis"] + " " + result["expert_ai_conclusion"]["patient_counseling"]
                result["expert_ai_conclusion"]["total_words"] = len(total_text.split())
                
                return result
                
            except Exception as e:
                print(f"OpenAI error: {e}")
                # Fallback to dynamic structured response
                return self._generate_dynamic_fallback_response(health_conditions, dietary_preferences, allergies, nutrition_data, flagged_ingredients, risk_level)
        
        # Execute with timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(openai_call)
            try:
                result = future.result(timeout=6.0)  # 6 second total timeout
                self.openai_cache[cache_key] = result
                return result
            except TimeoutError:
                print("OpenAI timeout - using dynamic fallback")
                return self._generate_dynamic_fallback_response(health_conditions, dietary_preferences, allergies, nutrition_data, flagged_ingredients, risk_level)
            except Exception as e:
                print(f"OpenAI outer error: {e}")
                return self._generate_dynamic_fallback_response(health_conditions, dietary_preferences, allergies, nutrition_data, flagged_ingredients, risk_level)
    
    def _analyze_nutrition_for_health_conditions(self, nutrition_data, health_conditions):
        """Analyze nutrition data specifically for user's health conditions."""
        analysis = []
        
        for condition in health_conditions:
            condition_lower = condition.lower()
            
            if 'diabetes' in condition_lower:
                # Check for sugar and carbohydrate content
                for key, value in nutrition_data.items():
                    if 'sugar' in key.lower() or 'carbohydrate' in key.lower():
                        try:
                            amount = float(value.split()[0])
                            if 'sugar' in key.lower():
                                analysis.append(f"High sugar content ({amount}g) may cause blood glucose spikes for diabetes management")
                            elif 'carbohydrate' in key.lower():
                                analysis.append(f"Carbohydrate content ({amount}g) requires careful monitoring for diabetes control")
                        except:
                            pass
            
            elif 'hypertension' in condition_lower or 'high blood pressure' in condition_lower:
                # Check for sodium content
                for key, value in nutrition_data.items():
                    if 'sodium' in key.lower() or 'salt' in key.lower():
                        try:
                            amount = float(value.split()[0])
                            if amount > 200:  # High sodium threshold
                                analysis.append(f"High sodium content ({amount}mg) may elevate blood pressure")
                        except:
                            pass
            
            elif 'heart' in condition_lower or 'cardiovascular' in condition_lower:
                # Check for saturated fat and cholesterol
                for key, value in nutrition_data.items():
                    if 'saturated' in key.lower() or 'cholesterol' in key.lower():
                        try:
                            amount = float(value.split()[0])
                            if 'saturated' in key.lower() and amount > 3:
                                analysis.append(f"High saturated fat ({amount}g) may impact cardiovascular health")
                            elif 'cholesterol' in key.lower() and amount > 20:
                                analysis.append(f"Cholesterol content ({amount}mg) requires consideration for heart health")
                        except:
                            pass
            
            elif 'kidney' in condition_lower or 'renal' in condition_lower:
                # Check for protein, phosphorus, potassium
                for key, value in nutrition_data.items():
                    if 'protein' in key.lower() or 'phosphorus' in key.lower() or 'potassium' in key.lower():
                        try:
                            amount = float(value.split()[0])
                            if 'protein' in key.lower() and amount > 15:
                                analysis.append(f"High protein content ({amount}g) may stress kidney function")
                        except:
                            pass
        
        return '; '.join(analysis) if analysis else "No specific nutritional concerns identified for your health conditions"
    
    def _calculate_dynamic_risk_level(self, health_conditions, dietary_preferences, allergies, flagged_ingredients, nutrition_data):
        """Calculate risk level based on user's specific health profile."""
        risk_score = 0
        
        # Check for allergen conflicts
        if allergies:
            for ingredient in flagged_ingredients:
                for allergy in allergies:
                    if allergy.lower() in ingredient.lower():
                        risk_score += 3  # High risk for allergens
        
        # Check for dietary preference conflicts
        if dietary_preferences:
            for pref in dietary_preferences:
                pref_lower = pref.lower()
                if 'vegan' in pref_lower:
                    for ingredient in flagged_ingredients:
                        if any(animal in ingredient.lower() for animal in ['milk', 'egg', 'meat', 'fish', 'gelatin', 'honey', 'whey', 'casein']):
                            risk_score += 2
                elif 'vegetarian' in pref_lower:
                    for ingredient in flagged_ingredients:
                        if any(animal in ingredient.lower() for animal in ['meat', 'fish', 'gelatin']):
                            risk_score += 2
                elif 'gluten' in pref_lower or 'celiac' in pref_lower:
                    for ingredient in flagged_ingredients:
                        if 'gluten' in ingredient.lower() or 'wheat' in ingredient.lower():
                            risk_score += 3
        
        # Check for health condition conflicts
        for condition in health_conditions:
            condition_lower = condition.lower()
            
            if 'diabetes' in condition_lower:
                for key, value in nutrition_data.items():
                    if 'sugar' in key.lower():
                        try:
                            amount = float(value.split()[0])
                            if amount > 10:  # High sugar threshold
                                risk_score += 2
                        except:
                            pass
            
            elif 'hypertension' in condition_lower:
                for key, value in nutrition_data.items():
                    if 'sodium' in key.lower():
                        try:
                            amount = float(value.split()[0])
                            if amount > 200:  # High sodium threshold
                                risk_score += 2
                        except:
                            pass
        
        # Determine risk level
        if risk_score >= 5:
            return "high"
        elif risk_score >= 2:
            return "moderate"
        else:
            return "low"
    
    def _generate_dynamic_fallback_response(self, health_conditions, dietary_preferences, allergies, nutrition_data, flagged_ingredients, risk_level):
        """Generate dynamic fallback response based on user's specific profile."""
        
        # Generate personalized BLUF insight
        bluf_insight = self._generate_personalized_bluf(health_conditions, dietary_preferences, allergies, nutrition_data, flagged_ingredients)
        
        # Generate personalized main insight
        main_insight = self._generate_personalized_main_insight(health_conditions, dietary_preferences, allergies, nutrition_data, flagged_ingredients)
        
        # Generate personalized deeper reference
        deeper_reference = self._generate_personalized_reference(health_conditions, dietary_preferences, allergies)
        
        # Generate personalized expert advice
        expert_advice = self._generate_personalized_expert_advice(health_conditions, dietary_preferences, allergies, nutrition_data, flagged_ingredients)
        
        # Generate personalized expert conclusion
        expert_conclusion = self._generate_personalized_expert_conclusion(health_conditions, dietary_preferences, allergies, risk_level, flagged_ingredients)
        
        return {
            "ai_health_insight": {
                "bluf_insight": bluf_insight,
                "main_insight": main_insight,
                "deeper_reference": deeper_reference,
                "disclaimer": "Informational, not diagnostic. Consult healthcare providers for medical advice."
            },
            "expert_advice": expert_advice,
            "expert_ai_conclusion": expert_conclusion
        }
    
    def _generate_personalized_bluf(self, health_conditions, dietary_preferences, allergies, nutrition_data, flagged_ingredients):
        """Generate personalized BLUF insight based on user's specific profile."""
        concerns = []
        
        # Check for allergen conflicts
        if allergies:
            for ingredient in flagged_ingredients:
                for allergy in allergies:
                    if allergy.lower() in ingredient.lower():
                        concerns.append(f"Contains {allergy} allergen")
        
        # Check for dietary preference conflicts
        if dietary_preferences:
            for pref in dietary_preferences:
                pref_lower = pref.lower()
                if 'vegan' in pref_lower:
                    for ingredient in flagged_ingredients:
                        if any(animal in ingredient.lower() for animal in ['milk', 'egg', 'meat', 'fish', 'gelatin', 'honey']):
                            concerns.append("Contains non-vegan ingredients")
                elif 'vegetarian' in pref_lower:
                    for ingredient in flagged_ingredients:
                        if any(animal in ingredient.lower() for animal in ['meat', 'fish', 'gelatin']):
                            concerns.append("Contains non-vegetarian ingredients")
        
        # Check for health condition concerns
        for condition in health_conditions:
            condition_lower = condition.lower()
            if 'diabetes' in condition_lower:
                for key, value in nutrition_data.items():
                    if 'sugar' in key.lower():
                        try:
                            amount = float(value.split()[0])
                            if amount > 10:
                                concerns.append(f"High sugar content ({amount}g) may affect blood glucose")
                        except:
                            pass
        
        if concerns:
            return f"Product analysis reveals: {'; '.join(concerns[:3])}. These components may conflict with your health profile and require careful consideration before consumption."
        else:
            return "Product appears compatible with your health profile. No immediate conflicts identified with your health conditions, dietary preferences, or allergies."
    
    def _generate_personalized_main_insight(self, health_conditions, dietary_preferences, allergies, nutrition_data, flagged_ingredients):
        """Generate personalized main insight based on user's specific profile."""
        insights = []
        
        # Health condition analysis
        for condition in health_conditions:
            condition_lower = condition.lower()
            if 'diabetes' in condition_lower:
                insights.append("For diabetes management, monitor carbohydrate and sugar content carefully")
            elif 'hypertension' in condition_lower:
                insights.append("For blood pressure control, limit sodium intake and monitor salt content")
            elif 'heart' in condition_lower:
                insights.append("For cardiovascular health, consider saturated fat and cholesterol levels")
        
        # Dietary preference analysis
        if dietary_preferences:
            insights.append(f"Your dietary preferences ({', '.join(dietary_preferences)}) should be respected for optimal health outcomes")
        
        # Allergy analysis
        if allergies:
            insights.append(f"Allergy considerations for {', '.join(allergies)} require careful ingredient review")
        
        if insights:
            return f"Personalized analysis: {'; '.join(insights)}. Product compatibility with your specific health profile requires consideration of these factors for safe consumption."
        else:
            return "Product analysis indicates general compatibility with your health profile. Consider your individual health goals and consult healthcare providers for personalized guidance."
    
    def _generate_personalized_reference(self, health_conditions, dietary_preferences, allergies):
        """Generate personalized scientific reference based on user's profile."""
        references = []
        
        for condition in health_conditions:
            condition_lower = condition.lower()
            if 'diabetes' in condition_lower:
                references.append("WHO and ADA guidelines recommend <10% total energy from free sugars for diabetes management")
            elif 'hypertension' in condition_lower:
                references.append("AHA recommends <2,300mg sodium daily for blood pressure control")
            elif 'heart' in condition_lower:
                references.append("AHA guidelines recommend <7% saturated fat for cardiovascular health")
        
        if dietary_preferences:
            references.append(f"Dietary preferences ({', '.join(dietary_preferences)}) align with evidence-based nutritional guidelines")
        
        references.append("This analysis is informational only and not a substitute for professional medical advice")
        
        return " ".join(references)
    
    def _generate_personalized_expert_advice(self, health_conditions, dietary_preferences, allergies, nutrition_data, flagged_ingredients):
        """Generate personalized expert advice based on user's specific profile."""
        advice = []
        
        # Health condition specific advice
        for condition in health_conditions:
            condition_lower = condition.lower()
            if 'diabetes' in condition_lower:
                advice.append("Monitor blood glucose levels and consider carbohydrate counting")
            elif 'hypertension' in condition_lower:
                advice.append("Limit sodium intake and monitor blood pressure regularly")
            elif 'heart' in condition_lower:
                advice.append("Focus on heart-healthy fats and limit saturated fat intake")
        
        # Dietary preference advice
        if dietary_preferences:
            advice.append(f"Choose alternatives that align with your {', '.join(dietary_preferences)} preferences")
        
        # Allergy advice
        if allergies:
            advice.append(f"Always check ingredient lists for {', '.join(allergies)} allergens")
        
        if advice:
            return f"Personalized recommendations: {'; '.join(advice)}. Consult your healthcare provider for specific guidance tailored to your health conditions."
        else:
            return "Consider portion control and incorporate this product as part of a balanced diet. Consult healthcare providers for personalized nutritional guidance."
    
    def _generate_personalized_expert_conclusion(self, health_conditions, dietary_preferences, allergies, risk_level, flagged_ingredients):
        """Generate personalized expert conclusion based on user's specific profile."""
        
        # Personalized prognosis
        prognosis_parts = []
        prognosis_parts.append(f"Regular consumption of this product may {'exacerbate' if risk_level == 'high' else 'moderately impact' if risk_level == 'moderate' else 'be compatible with'} your health conditions")
        
        for condition in health_conditions:
            condition_lower = condition.lower()
            if 'diabetes' in condition_lower:
                prognosis_parts.append("Blood glucose management requires careful monitoring")
            elif 'hypertension' in condition_lower:
                prognosis_parts.append("Blood pressure control may be affected by sodium content")
        
        if dietary_preferences:
            prognosis_parts.append(f"Your {', '.join(dietary_preferences)} preferences should be maintained for optimal health")
        
        prognosis = ". ".join(prognosis_parts) + "."
        
        # Personalized counseling
        counseling_parts = []
        counseling_parts.append("Take these personalized steps for your health:")
        
        if health_conditions:
            counseling_parts.append(f"Monitor your {', '.join(health_conditions)} regularly")
        
        if allergies:
            counseling_parts.append(f"Always verify ingredients for {', '.join(allergies)} safety")
        
        if dietary_preferences:
            counseling_parts.append(f"Choose foods that support your {', '.join(dietary_preferences)} lifestyle")
        
        counseling_parts.append("Consult healthcare providers for personalized medical advice")
        
        counseling = " ".join(counseling_parts)
        
        # Calculate total words
        total_text = prognosis + " " + counseling
        total_words = len(total_text.split())
        
        return {
            "prognosis": prognosis,
            "patient_counseling": counseling,
            "total_words": total_words,
            "risk_level": risk_level,
            "evidence_sources": ["SNOMED CT & ICD-10 Clinical Guidelines", "WHO Guidelines", "ADA/AHA Recommendations"]
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

