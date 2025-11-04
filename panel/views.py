from django.shortcuts import render
import io
import random
import ssl
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from fuzzywuzzy import fuzz
from django.contrib.auth import login
from rest_framework.pagination import PageNumberPagination
from foodinfo.models import User,privacypolicy,Termandcondition,FAQ,AboutUS
from foodinfo.serializers import userGetSerializer,userPatchSerializer,privacypolicySerializer,termsandconditionSerializer,AboutSerializer,FAQSerializer
from .serializers import AdminLoginSerializer,AdminSignupSerializer, AdminpatchSerializer, OnboardingQuestionSerializer, OnboardingCategorySerializer
from .models import OnboardingAnswer, OnboardingQuestion, OnboardingCategory, SuperAdmin, OnboardingChoice
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from foodinfo.permissions import IsSuperAdmin
import re
from django.http import HttpResponse
from .utils.response import success_response, error_response
from django.db import transaction


# Create your views here.
# @method_decorator(csrf_exempt, name='dispatch')
class AdminSignupAPIView(APIView):
    def post(self, request):
        serializer = AdminSignupSerializer(data=request.data)
        if serializer.is_valid():
            admin = serializer.save()
            # refresh = RefreshToken.for_user(admin)
            return success_response("Admin created successfully.", serializer.data, status_code=201)

        return error_response("Sign-up failed",serializer.errors)


@method_decorator(csrf_exempt, name='dispatch')
class AdminLoginAPIView(APIView):
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            admin = serializer.validated_data['admin']
            refresh = RefreshToken.for_user(admin)
            data = {
                # "id": admin.id,
                # "firstName": admin.first_name,
                # "lastName": admin.last_name,
                # "email": admin.email,
                # "role": "Admin",
                "token": str(refresh.access_token),
                "refresh_token": str(refresh)
            }
            return success_response("Admin login successful", data)
        return error_response("Login failed", serializer.errors)

@method_decorator(csrf_exempt, name='dispatch')
class AdminUserManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all users"""
        users = User.objects.filter(is_superuser=False).order_by('-created_at')
        # print("-=0-0users",users)
        serializer = userGetSerializer(users, many=True)
        
        # Add accurate subscription data for each user
        from foodinfo.models import UserSubscription
        updated_data = []
        for user_data in serializer.data:
            user_id = user_data['id']
            user = User.objects.get(id=user_id)
            
            # Get accurate subscription status
            payment_status = 'freemium'
            premium_type = None
            subscription_plan = "Freemium plan"
            
            try:
                sub = UserSubscription.objects.get(user=user)
                if sub.is_premium:  # This checks both plan_name == 'premium' AND is_active
                    payment_status = 'premium'
                    premium_type = getattr(sub, 'premium_type', None)
                    subscription_plan = f"{premium_type.capitalize()} Premium" if premium_type else "Premium"
            except UserSubscription.DoesNotExist:
                pass
            
            # Override subscription data with accurate information
            user_data['payment_status'] = payment_status
            user_data['premium_type'] = premium_type
            user_data['subscription_plan'] = subscription_plan
            
            updated_data.append(user_data)
        
        return success_response("User details fetch successfully", updated_data)

    def patch(self, request):
        """Update any user"""
        try:
            # print("9-09-0")
            user_id = request.query_params.get('id')
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response("User not found")

        serializer = userPatchSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response("User updated successfully")
        return error_response(serializer.errors)
    def delete(self, request):
        """Delete any user"""
        try:
            user_id = request.query_params.get("id")
            user = User.objects.get(id=user_id)
            
            # Handle foreign key constraints by manually deleting related records
            from django.db import connection
            with connection.cursor() as cursor:
                # Set foreign key references to NULL first
                cursor.execute("UPDATE foodinfo_user SET account_deactivation_date_id = NULL, download_data_id = NULL WHERE id = %s", [user_id])
                
                # Delete related records with correct column names
                delete_queries = [
                    ("DELETE FROM foodinfo_userhealthpreference WHERE user_id = %s", [user_id]),
                    ("DELETE FROM foodinfo_stripecustomer WHERE user_id = %s", [user_id]), 
                    ("DELETE FROM foodinfo_foodlabelscan WHERE user_id = %s", [user_id]),
                    ("DELETE FROM foodinfo_feedback WHERE user_id = %s", [user_id]),
                    ("DELETE FROM foodinfo_monthlyscanusage WHERE user_id = %s", [user_id]),
                    ("DELETE FROM foodinfo_pushnotification WHERE user_id = %s", [user_id]),
                    ("DELETE FROM foodinfo_devicetoken WHERE user_id = %s", [user_id]),
                    ("DELETE FROM foodinfo_usersubscription WHERE user_id = %s", [user_id]),
                    ("DELETE FROM foodinfo_accountdeletionrequest WHERE user_id = %s", [user_id]),
                    ("DELETE FROM panel_onboardinganswer WHERE user_id = %s", [user_id]),
                    ("DELETE FROM panel_superadmin WHERE user_ptr_id = %s", [user_id]),
                    ("DELETE FROM foodinfo_user_groups WHERE user_id = %s", [user_id]),
                    ("DELETE FROM foodinfo_user_user_permissions WHERE user_id = %s", [user_id])
                ]
                
                for query, params in delete_queries:
                    try:
                        cursor.execute(query, params)
                    except Exception as e:
                        print(f"Warning: Could not delete from query {query}: {e}")
                
                # Finally delete the user
                cursor.execute("DELETE FROM foodinfo_user WHERE id = %s", [user_id])
            
            return success_response("User deleted successfully")
        except User.DoesNotExist:
            return error_response("User not found")
        except Exception as e:
            return error_response(f"Error deleting user: {str(e)}")
        except User.DoesNotExist:
            return error_response("User not found")
        except Exception as e:
            return error_response(f"Error deleting user: {str(e)}")
@method_decorator(csrf_exempt, name='dispatch')
class AdminForgotPasswordAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return error_response("Email is required")

        try:
            admin = SuperAdmin.objects.get(email=email)
        except SuperAdmin.DoesNotExist:
            return error_response("Admin not found")

        # Create OTP (for now: simple code logic)
        otp = str(random.randint(100000, 999999))
        print("---------",otp)
        admin.otp = otp
        admin.save()

        # Send OTP (for real-world: send email)
        send_mail(
            'Admin OTP Code',
            f'Your OTP is {otp}',
            'admin@yourapp.com',
            [email],
            fail_silently=False,
        )

        return success_response("OTP sent to email")
    
class AdminChangePasswordAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        if not all([email, otp, new_password]):
            return error_response("All fields are required")

        try:
            admin = SuperAdmin.objects.get(email=email)
        except SuperAdmin.DoesNotExist:
            return error_response("Admin not found")

        if admin.otp != otp:
            return error_response("Invalid OTP")

        admin.set_password(new_password)
        admin.otp = None  # Reset OTP
        admin.save()

        return success_response("Password changed successfully")
    
@method_decorator(csrf_exempt, name='dispatch')
class AdminProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = AdminSignupSerializer(request.user)
        return success_response("Admin profile fetched successfully",serializer.data)

    def patch(self, request):
        serializer = AdminpatchSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response("Profile updated successfully")
        return error_response("Profile is not updated",serializer.errors)
    
    def delete(self,request):
        user = request.user
        user.delete()
        return success_response("Admin profile deleted successfully.")

        

class PrivacyPolicyView(APIView):
    def get(self, request):
        policies = privacypolicy.objects.all()
        serializer = privacypolicySerializer(policies, many=True)
        return success_response("Privacy policy fetched",serializer.data)

    def post(self, request):
        serializer = privacypolicySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response("Privacy policy created successfully.")
        return error_response(serializer.errors)

    def put(self, request):
        try:
            pk = request.query_params.get('pk')
            policy = privacypolicy.objects.get(pk=pk)
        except privacypolicy.DoesNotExist:
            return error_response("Privacy policy not found")

        serializer = privacypolicySerializer(policy, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response("Privacy policy updated successfully.")
        return error_response(serializer.errors)

    def delete(self, request):
        try:
            pk = request.query_params.get('pk')
            policy = privacypolicy.objects.get(pk=pk)
            policy.delete()
            return success_response("Privacy policy deleted successfully.")
        except privacypolicy.DoesNotExist:
            return error_response("Privacy policy not found")

# Terms and Conditions View
class TermsAndConditionsView(APIView):
    def get(self, request):
        terms = Termandcondition.objects.all()
        serializer = termsandconditionSerializer(terms, many=True)
        return success_response("Terms and Condition fetched successfully",serializer.data)

    def post(self, request):
        serializer = termsandconditionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response("Terms and Conditions created successfully.")
        return error_response(serializer.errors)

    def put(self, request):
        try:
            pk = request.query_params.get('pk')
            term = Termandcondition.objects.get(pk=pk)
        except Termandcondition.DoesNotExist:
            return error_response("Terms and Conditions not found")

        serializer = termsandconditionSerializer(term, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response("Terms and Conditions updated successfully.")
        return error_response(serializer.errors)

    def delete(self, request):
        try:
            pk = request.query_params.get('pk')
            term = Termandcondition.objects.get(pk=pk)
            term.delete()
            return success_response("Terms and Conditions deleted successfully.")
        except Termandcondition.DoesNotExist:
            return error_response("Terms and Conditions not found")

# About Us View
class AboutUsView(APIView):
    def get(self, request):
        about = AboutUS.objects.all()
        serializer = AboutSerializer(about, many=True)
        return success_response("About US fetched successfully",serializer.data)

    def post(self, request):
        serializer = AboutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response("About Us content created successfully.")
        return error_response(serializer.errors)

    def put(self, request):
        try:
            pk = request.query_params.get('pk')
            about = AboutUS.objects.get(pk=pk)
        except AboutUS.DoesNotExist:
            return error_response("About Us content not found")

        serializer = AboutSerializer(about, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response("About Us updated successfully.")
        return error_response("Not updated",serializer.errors)

    def delete(self, request):
        try:
            pk = request.query_params.get('pk')
            about = AboutUS.objects.get(pk=pk)
            about.delete()
            return success_response("About Us deleted successfully.")
        except AboutUS.DoesNotExist:
            return error_response("About Us content not found")

# FAQ View
class FAQView(APIView):
    def get(self, request):
        faqs = FAQ.objects.all()
        serializer = FAQSerializer(faqs, many=True)
        return success_response("FAQ fetched successfully",serializer.data)

    def post(self, request):
        serializer = FAQSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response("FAQ created successfully.")
        return error_response(serializer.errors)

    def put(self, request):
        try:
            pk = request.query_params.get('pk')
            faq = FAQ.objects.get(pk=pk)
        except FAQ.DoesNotExist:
            return error_response("FAQ not found")

        serializer = FAQSerializer(faq, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response("FAQ updated successfully.")
        return error_response("FAQ not updated",serializer.errors)

    def delete(self, request):
        try:
            pk = request.query_params.get('pk')
            faq = FAQ.objects.get(pk=pk)
            faq.delete()
            return success_response("FAQ deleted successfully.")
        except FAQ.DoesNotExist:
            return error_response("FAQ not found")

class passwordreset(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.user.email
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not old_password or not new_password or not confirm_password:
            message="Please provide all the fields -> old_password, new_password, confirm_password"
            return error_response("Please provide all the fields -> old_password, new_password, confirm_password")
        user = SuperAdmin.objects.get(email=email.lower())
        if not user.check_password(old_password):
            return error_response("Old password is incorrect")
        if new_password != confirm_password:
            return error_response({'message': 'Passwords do not match'}, status=400)
        user.set_password(new_password)
        user.save()
        return success_response("Password changed successfully")
    
# class OnboardingQuestionPagination(PageNumberPagination):
#     page_size = 1  # Set page size to 1 to return one question per page
#     page_size_query_param = 'page_size'  # Optional: allows clients to specify the page size
#     max_page_size = 1  # Limits the max page size to 1

class OnboardingQuestionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            try:
                question = OnboardingQuestion.objects.get(pk=pk)
                
                # Check if this is a request for choices only
                if request.path.endswith('/choices/'):
                    return self.get_question_choices(request, pk)
                
                serializer = OnboardingQuestionSerializer(question)
                return success_response(data=serializer.data, message="Single question fetched successfully.")
            except OnboardingQuestion.DoesNotExist:
                return error_response({"message": "Question not found"}, status=status.HTTP_404_NOT_FOUND)

        questions = OnboardingQuestion.objects.all()
        serializer = OnboardingQuestionSerializer(questions, many=True)
        return success_response(data=serializer.data, message="All questions fetched successfully.")

    
    def post(self, request):
        serializer = OnboardingQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response({"message": "Question added successfully", "data": serializer.data})
        return error_response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            pk = request.query_params.get('pk')
            question = OnboardingQuestion.objects.get(pk=pk)
        except OnboardingQuestion.DoesNotExist:
            return error_response("Question not found")

        # Handle choices update if provided
        choices_data = request.data.get('choices', [])
        
        # Debug logging
        print(f"🔍 DEBUG - Question ID: {pk}")
        print(f"🔍 DEBUG - Choices data received: {choices_data}")
        print(f"🔍 DEBUG - Current choices count: {question.choices.count()}")
        
        # Remove choices from request data to avoid serializer validation issues
        request_data_without_choices = request.data.copy()
        if 'choices' in request_data_without_choices:
            del request_data_without_choices['choices']
        
        # Update question fields (without choices)
        print(f"🔍 DEBUG - Request data (without choices): {request_data_without_choices}")
        serializer = OnboardingQuestionSerializer(question, data=request_data_without_choices, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Update choices if provided
            if choices_data:
                # Clear existing choices to avoid ID conflicts
                print(f"🗑️ Clearing {question.choices.count()} existing choices")
                question.choices.all().delete()
                
                # Create all choices fresh
                created_choices = []
                errors = []
                
                for i, choice_data in enumerate(choices_data):
                    # Handle both 'id' and 'choice_id' fields from frontend
                    choice_id = choice_data.get('id') or choice_data.get('choice_id')
                    choice_text = choice_data.get('choice_text', '').strip()
                    
                    print(f"🔍 Processing choice {i+1}: ID={choice_id}, Text='{choice_text}'")
                    
                    # Skip empty choices
                    if not choice_text:
                        print(f"⚠️ Skipping empty choice {i+1}")
                        continue
                    
                    # Create new choice (ignore old IDs since we cleared all choices)
                    try:
                        new_choice = OnboardingChoice.objects.create(
                            question=question,
                            choice_text=choice_text
                        )
                        created_choices.append({
                            'id': new_choice.id,
                            'choice_text': new_choice.choice_text,
                            'action': 'created'
                        })
                        print(f"✅ Created choice: {choice_text}")
                    except Exception as e:
                        errors.append(f"Error creating choice '{choice_text}': {str(e)}")
                        print(f"❌ Error creating choice '{choice_text}': {str(e)}")
                
                # If there are errors, return them
                if errors:
                    return error_response({
                        "message": "Some choices could not be updated",
                        "errors": errors,
                        "question_id": pk,
                        "available_choices": [
                            {"id": choice.id, "choice_text": choice.choice_text}
                            for choice in question.choices.all()
                        ]
                    })
                
                # Refresh the question data to include updated choices
                updated_question = OnboardingQuestion.objects.get(pk=pk)
                updated_serializer = OnboardingQuestionSerializer(updated_question)
                
                print(f"✅ Final result: {updated_question.choices.count()} total choices")
                print(f"✅ Created: {len(created_choices)}")
                
                return success_response({
                    "message": f"Question updated successfully. {len(created_choices)} choices created.",
                    "data": updated_serializer.data,
                    "choices_summary": {
                        "created": created_choices
                    }
                })
            
            return success_response("Question updated successfully")
        else:
            print(f"❌ Serializer validation failed: {serializer.errors}")
            return error_response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            pk = request.query_params.get('pk')
            question = OnboardingQuestion.objects.get(pk=pk)
            question.delete()
            return success_response("Question deleted successfully")
        except OnboardingQuestion.DoesNotExist:
            return error_response("Question not found")

    def patch(self, request):
        """Update specific choices by ID without affecting other choices"""
        try:
            pk = request.query_params.get('pk')
            question = OnboardingQuestion.objects.get(pk=pk)
        except OnboardingQuestion.DoesNotExist:
            return error_response("Question not found")

        choices_data = request.data.get('choices', [])
        
        if not choices_data:
            return error_response("choices data is required")
        
        updated_choices = []
        errors = []
        
        for choice_data in choices_data:
            choice_id = choice_data.get('id')
            choice_text = choice_data.get('choice_text')
            
            if not choice_id:
                errors.append("choice_id is required for each choice")
                continue
                
            if not choice_text:
                errors.append(f"choice_text is required for choice {choice_id}")
                continue
            
            try:
                choice = OnboardingChoice.objects.get(pk=choice_id, question=question)
                choice.choice_text = choice_text
                choice.save()
                updated_choices.append({
                    'id': choice.id,
                    'choice_text': choice.choice_text,
                    'action': 'updated'
                })
            except OnboardingChoice.DoesNotExist:
                # Check if choice exists but belongs to different question
                try:
                    choice_exists = OnboardingChoice.objects.get(pk=choice_id)
                    errors.append(f"Choice with ID {choice_id} exists but belongs to question ID {choice_exists.question.id}, not question ID {pk}")
                except OnboardingChoice.DoesNotExist:
                    errors.append(f"Choice with ID {choice_id} does not exist")
        
        if errors:
            return error_response({
                "message": "Some choices could not be updated",
                "errors": errors,
                "question_id": pk,
                "available_choices": [
                    {"id": choice.id, "choice_text": choice.choice_text}
                    for choice in question.choices.all()
                ]
            })
        
        # Refresh the question data
        updated_question = OnboardingQuestion.objects.get(pk=pk)
        updated_serializer = OnboardingQuestionSerializer(updated_question)
        
        return success_response({
            "message": f"Successfully updated {len(updated_choices)} choices",
            "data": updated_serializer.data,
            "updated_choices": updated_choices
        })

    def get_question_choices(self, request, pk):
        """Helper method to get all choices for a specific question"""
        try:
            question = OnboardingQuestion.objects.get(pk=pk)
            choices = question.choices.all()
            choices_data = [
                {"id": choice.id, "choice_text": choice.choice_text}
                for choice in choices
            ]
            return success_response({
                "question_id": pk,
                "question_text": question.question_text,
                "choices": choices_data,
                "total_choices": len(choices_data)
            })
        except OnboardingQuestion.DoesNotExist:
            return error_response("Question not found")


class OnboardingChoiceAPIView(APIView):
    """
    Separate API view for managing choices of existing questions
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Add new choices to an existing question"""
        question_id = request.data.get('question_id')
        choices_data = request.data.get('choices', [])
        
        if not question_id:
            return error_response("question_id is required")
        
        if not choices_data:
            return error_response("choices data is required")
        
        try:
            question = OnboardingQuestion.objects.get(pk=question_id)
        except OnboardingQuestion.DoesNotExist:
            return error_response("Question not found")
        
        # Create new choices
        created_choices = []
        for choice_data in choices_data:
            choice = OnboardingChoice.objects.create(
                question=question,
                choice_text=choice_data.get('choice_text')
            )
            created_choices.append({
                'id': choice.id,
                'choice_text': choice.choice_text
            })
        
        return success_response({
            "message": f"Added {len(created_choices)} new choices successfully",
            "choices": created_choices
        })

    def put(self, request):
        """Update existing choices"""
        choice_id = request.data.get('choice_id')
        choice_text = request.data.get('choice_text')
        
        if not choice_id or not choice_text:
            return error_response("choice_id and choice_text are required")
        
        try:
            choice = OnboardingChoice.objects.get(pk=choice_id)
            choice.choice_text = choice_text
            choice.save()
            
            return success_response({
                "message": "Choice updated successfully",
                "choice": {
                    'id': choice.id,
                    'choice_text': choice.choice_text
                }
            })
        except OnboardingChoice.DoesNotExist:
            return error_response("Choice not found")

    def delete(self, request):
        """Delete a specific choice"""
        choice_id = request.query_params.get('choice_id')
        
        if not choice_id:
            return error_response("choice_id is required")
        
        try:
            choice = OnboardingChoice.objects.get(pk=choice_id)
            choice.delete()
            return success_response("Choice deleted successfully")
        except OnboardingChoice.DoesNotExist:
            return error_response("Choice not found")
        
class OnboardingQuestionPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = 'page_size'
    max_page_size = 1

class OnboardingAnswerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        # Admin can manage, users can only view their answers
        if pk:
            try:
                question = OnboardingQuestion.objects.get(pk=pk)
                serializer = OnboardingQuestionSerializer(question)
                return success_response(serializer.data)
            except OnboardingQuestion.DoesNotExist:
                return error_response("Question not found")
        else:
            # Get the next question for the user
            questions = OnboardingQuestion.objects.all()
            paginator = OnboardingQuestionPagination()
            paginated_questions = paginator.paginate_queryset(questions, request)
            serializer = OnboardingQuestionSerializer(paginated_questions, many=True)
            return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        user = request.user
        answers_data = request.data  # Expecting a list of dicts

        if not isinstance(answers_data, list):
            return error_response("Invalid data format.")

        for item in answers_data:
            question_id = item.get('questionId')
            answers = item.get('answers', [])

            if not question_id or not isinstance(answers, list):
                continue  # skip invalid entries

            try:
                question = OnboardingQuestion.objects.get(pk=question_id)
            except OnboardingQuestion.DoesNotExist:
                continue  # skip if question not found

            # Save or update onboarding answer
            answer_text = ", ".join(answers)  # Join multiple answers into a comma-separated string
            OnboardingAnswer.objects.update_or_create(
                user=user,
                question=question,
                defaults={'answer': answer_text}
            )

            # Helper function to combine answers for same category
            def combine_answers(existing_text, new_text):
                if not existing_text:
                    return new_text
                if not new_text:
                    return existing_text
                # Combine and remove duplicates
                existing_items = [item.strip() for item in existing_text.split(',') if item.strip()]
                new_items = [item.strip() for item in new_text.split(',') if item.strip()]
                combined = existing_items + [item for item in new_items if item not in existing_items]
                return ', '.join(combined)
            
            # Legacy category mappings (for backward compatibility)
            if question.category == 'health':
                user.Health_conditions = combine_answers(user.Health_conditions, answer_text)
            elif question.category == 'allergy':
                user.Allergies = combine_answers(user.Allergies, answer_text)
            elif question.category == 'diet':
                user.Dietary_preferences = combine_answers(user.Dietary_preferences, answer_text)
            elif question.category == 'primary health goals':
                user.Health_Goals = combine_answers(user.Health_Goals, answer_text)
            elif question.category in ['Parental status', 'parent or caregiver']:
                user.Parental_status = combine_answers(user.Parental_status, answer_text)
            elif question.category in ['safer meal planning', 'Family_Health_Awareness']:
                user.Family_Health_Awareness = combine_answers(user.Family_Health_Awareness, answer_text)
            elif question.category == 'quality and safety of ingredients':
                user.Emotional_Conection = combine_answers(user.Emotional_Conection, answer_text)
            elif question.category == 'negative health symptoms':
                user.Health_impact_awareness = combine_answers(user.Health_impact_awareness, answer_text)
            elif question.category == 'achive by using IngredientIQ':
                user.Desired_outcome = combine_answers(user.Desired_outcome, answer_text)
            elif question.category == 'ready to take control of health':
                user.Motivation = combine_answers(user.Motivation, answer_text)
            
            # New static category mappings
            elif question.category == 'profile_demographics':
                user.Demographics = combine_answers(user.Demographics, answer_text)
            elif question.category == 'motivation_cognitive':
                user.Motivation = combine_answers(user.Motivation, answer_text)
            elif question.category == 'medical_clinical':
                user.Health_conditions = combine_answers(user.Health_conditions, answer_text)
            elif question.category == 'medications_supplements':
                user.Medications = combine_answers(user.Medications, answer_text)
            elif question.category == 'allergies_sensitivities':
                user.Allergies = combine_answers(user.Allergies, answer_text)
            elif question.category == 'lifestyle_dietary':
                user.Dietary_preferences = combine_answers(user.Dietary_preferences, answer_text)
            elif question.category == 'behavioral_rhythm':
                user.Behavioral_patterns = combine_answers(user.Behavioral_patterns, answer_text)

        user.has_answered_onboarding = True  # <-- Mark that user has finished onboarding
        user.save()

        return success_response("Onboarding answers saved successfully.")

    def patch(self, request):
        user = request.user
        answers_data = request.data  # Expecting a list of dicts

        if not isinstance(answers_data, list):
            return error_response("Invalid data format.")

        skipped_questions = []
        try:
            with transaction.atomic():
                for item in answers_data:
                    question_id = item.get('questionId')
                    answers = item.get('answers', [])

                    if not question_id or not isinstance(answers, list):
                        skipped_questions.append(f"Invalid format for question {question_id}")
                        continue

                    try:
                        question = OnboardingQuestion.objects.get(pk=question_id)
                    except OnboardingQuestion.DoesNotExist:
                        # Create the missing question
                        question = OnboardingQuestion.objects.create(
                            id=question_id,
                            question_text=f"Question {question_id}",
                            answer_type='multiple',
                            category='other'  # Default category
                        )
                        print(f"Created missing question with ID {question_id}")

                    answer, created = OnboardingAnswer.objects.get_or_create(
                        user=user,
                        question=question,
                        defaults={'answer': ', '.join(answers)}
                    )
                    
                    if not created:
                        answer.answer = ', '.join(answers)
                        answer.save()

                    # Update user profile fields based on question category
                    answer_text = ', '.join(answers)
                    
                    # Helper function to combine answers for same category
                    def combine_answers(existing_text, new_text):
                        if not existing_text:
                            return new_text
                        if not new_text:
                            return existing_text
                        # Combine and remove duplicates
                        existing_items = [item.strip() for item in existing_text.split(',') if item.strip()]
                        new_items = [item.strip() for item in new_text.split(',') if item.strip()]
                        combined = existing_items + [item for item in new_items if item not in existing_items]
                        return ', '.join(combined)
                    
                    # Legacy category mappings (for backward compatibility)
                    if question.category == 'health':
                        user.Health_conditions = combine_answers(user.Health_conditions, answer_text)
                    elif question.category == 'allergy':
                        user.Allergies = combine_answers(user.Allergies, answer_text)
                    elif question.category == 'diet':
                        user.Dietary_preferences = combine_answers(user.Dietary_preferences, answer_text)
                    elif question.category == 'primary health goals':
                        user.Health_Goals = combine_answers(user.Health_Goals, answer_text)
                    elif question.category in ['Parental status', 'parent or caregiver']:
                        user.Parental_status = combine_answers(user.Parental_status, answer_text)
                    elif question.category in ['safer meal planning', 'Family_Health_Awareness']:
                        user.Family_Health_Awareness = combine_answers(user.Family_Health_Awareness, answer_text)
                    elif question.category == 'quality and safety of ingredients':
                        user.Emotional_Conection = combine_answers(user.Emotional_Conection, answer_text)
                    elif question.category == 'negative health symptoms':
                        user.Health_impact_awareness = combine_answers(user.Health_impact_awareness, answer_text)
                    elif question.category == 'achive by using IngredientIQ':
                        user.Desired_outcome = combine_answers(user.Desired_outcome, answer_text)
                    elif question.category == 'ready to take control of health':
                        user.Motivation = combine_answers(user.Motivation, answer_text)
                    
                    # New static category mappings
                    elif question.category == 'profile_demographics':
                        user.Demographics = combine_answers(user.Demographics, answer_text)
                    elif question.category == 'motivation_cognitive':
                        user.Motivation = combine_answers(user.Motivation, answer_text)
                    elif question.category == 'medical_clinical':
                        user.Health_conditions = combine_answers(user.Health_conditions, answer_text)
                    elif question.category == 'medications_supplements':
                        user.Medications = combine_answers(user.Medications, answer_text)
                    elif question.category == 'allergies_sensitivities':
                        user.Allergies = combine_answers(user.Allergies, answer_text)
                    elif question.category == 'lifestyle_dietary':
                        user.Dietary_preferences = combine_answers(user.Dietary_preferences, answer_text)
                    elif question.category == 'behavioral_rhythm':
                        user.Behavioral_patterns = combine_answers(user.Behavioral_patterns, answer_text)
                    else:
                        print(f"Warning: Unknown question category: {question.category}")

                # Mark that user has finished onboarding
                user.has_answered_onboarding = True
                # Save all user field updates at once
                user.save()
                # Force refresh from database
                user.refresh_from_db()

                # Verify the data was saved
                print(f"Updated user fields:")
                print(f"Health_conditions: {user.Health_conditions}")
                print(f"Allergies: {user.Allergies}")
                print(f"Dietary_preferences: {user.Dietary_preferences}")
                print(f"Health_Goals: {user.Health_Goals}")
                print(f"Parental_status: {user.Parental_status}")
                print(f"Family_Health_Awareness: {user.Family_Health_Awareness}")
                print(f"Emotional_Conection: {user.Emotional_Conection}")
                print(f"Health_impact_awareness: {user.Health_impact_awareness}")
                print(f"Desired_outcome: {user.Desired_outcome}")
                print(f"Motivation: {user.Motivation}")
                print(f"Demographics: {user.Demographics}")
                print(f"Medications: {user.Medications}")
                print(f"Behavioral_patterns: {user.Behavioral_patterns}")

            if skipped_questions:
                return success_response(
                    "Onboarding answers updated successfully. Some questions were skipped: " + 
                    ", ".join(skipped_questions)
                )
            return success_response("Onboarding answers updated successfully.")
        except Exception as e:
            print(f"Error in patch method: {str(e)}")
            return error_response(f"Error updating answers: {str(e)}")


class OnboardingCategoryAPIView(APIView):
    """
    API view to manage onboarding categories
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all active onboarding categories"""
        categories = OnboardingCategory.objects.filter(is_active=True).order_by('order')
        serializer = OnboardingCategorySerializer(categories, many=True)
        return success_response("Categories fetched successfully", serializer.data)

    def post(self, request):
        """Create a new onboarding category (Admin only)"""
        serializer = OnboardingCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response("Category created successfully", serializer.data)
        return error_response("Failed to create category", serializer.errors)

    def put(self, request):
        """Update an existing category (Admin only)"""
        try:
            category_id = request.query_params.get('id')
            category = OnboardingCategory.objects.get(pk=category_id)
        except OnboardingCategory.DoesNotExist:
            return error_response("Category not found")

        serializer = OnboardingCategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response("Category updated successfully", serializer.data)
        return error_response("Failed to update category", serializer.errors)

    def delete(self, request):
        """Soft delete a category (Admin only)"""
        try:
            category_id = request.query_params.get('id')
            category = OnboardingCategory.objects.get(pk=category_id)
            category.is_active = False
            category.save()
            return success_response("Category deactivated successfully")
        except OnboardingCategory.DoesNotExist:
            return error_response("Category not found")
        
