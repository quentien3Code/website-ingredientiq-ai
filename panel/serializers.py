from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import OnboardingAnswer, OnboardingChoice, OnboardingQuestion, OnboardingCategory, SuperAdmin

class AdminSignupSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = SuperAdmin
        fields = (
            'email', 
            'full_name',  
            'password', 
            'profile_picture',
            'confirm_password',
        )
    
    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError("Passwords do not match.")
        data.pop('confirm_password')
        return data
    
    def create(self, validated_data):
        admin = SuperAdmin.objects.create_user(**validated_data)
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        return admin

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        try:
            admin = SuperAdmin.objects.get(email=email)
            if not admin.check_password(password):
                raise serializers.ValidationError("Invalid password")
            if not admin.is_super_admin:
                raise serializers.ValidationError("Not an admin account")
        except SuperAdmin.DoesNotExist:
            raise serializers.ValidationError("Admin account not found")
        
        data['admin'] = admin
        return data
        
class AdminpatchSerializer(serializers.ModelSerializer):
    # confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = SuperAdmin
        fields = (
            # 'email', 
            'full_name',  
            # 'password', 
            'profile_picture',
            # 'confirm_password',
        )
    
    # def validate(self, data):
    #     if data.get('password') != data.get('confirm_password'):
    #         raise serializers.ValidationError("Passwords do not match.")
    #     data.pop('confirm_password')
    #     return data
    
    def create(self, validated_data):
        admin = SuperAdmin.objects.create_user(**validated_data)
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        return admin
    
class OnboardingChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingChoice
        fields = ['id', 'choice_text']

class OnboardingQuestionSerializer(serializers.ModelSerializer):
    choices = OnboardingChoiceSerializer(many=True)

    class Meta:
        model = OnboardingQuestion
        fields = ['id', 'question_text', 'answer_type','category', 'choices']

    def create(self, validated_data):
        choices_data = validated_data.pop('choices')
        question = OnboardingQuestion.objects.create(**validated_data)
        for choice_data in choices_data:
            OnboardingChoice.objects.create(question=question, **choice_data)
        return question
    
    def update(self, instance, validated_data):
        # Update question fields
        choices_data = validated_data.pop('choices', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle choices update if provided
        if choices_data is not None:
            # Clear existing choices
            instance.choices.all().delete()
            
            # Create new choices
            for choice_data in choices_data:
                OnboardingChoice.objects.create(question=instance, **choice_data)
        
        return instance

# class OnboardingputSerializer(serializers.ModelSerializer):
#     class meta:
#         model = OnboardingQuestion
#         fields = ['question_text']
class OnboardingAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingAnswer
        fields = ['user', 'question', 'answer']


class OnboardingCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingCategory
        fields = ['id', 'category_key', 'category_name', 'description', 'purpose', 'order', 'is_active', 'created_at', 'updated_at']