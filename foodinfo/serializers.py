"""
Minimal serializers for foodinfo app.
Mobile app terminated - only serializers used by panel/admin remain.
"""
from rest_framework import serializers
from panel.models import OnboardingQuestion
from .models import FAQ, AboutUS, Termandcondition, User, privacypolicy


class userPatchSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    phone_number = serializers.IntegerField(required=False, allow_null=True)
    full_name = serializers.CharField(required=False) 
    Dietary_preferences = serializers.CharField(required=False) 
    Health_conditions = serializers.CharField(required=False)
    Allergies = serializers.CharField(required=False)
    Health_Goals = serializers.CharField(required=False)
    Parental_status = serializers.CharField(required=False)
    Family_Health_Awareness = serializers.CharField(required=False)
    Emotional_Conection = serializers.CharField(required=False)
    Health_impact_awareness = serializers.CharField(required=False)
    Desired_outcome = serializers.CharField(required=False)
    Motivation = serializers.CharField(required=False)
    
    class Meta:
        model = User
        fields = [
            'full_name', 'phone_number', 'profile_picture', 'Dietary_preferences',
            'Health_conditions', 'Allergies', 'Health_Goals', 'Parental_status',
            'Family_Health_Awareness', 'Emotional_Conection', 'Health_impact_awareness',
            'Desired_outcome', 'Motivation'
        ]
    
    def validate_phone_number(self, value):
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return value


class userGetSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    questions_and_answers = serializers.SerializerMethodField()
    computed_full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'first_name', 'last_name', 'computed_full_name',
            'phone_number', 'profile_picture', 'questions_and_answers', 'date_joined',
            'language', 'subscription_plan', 'notifications_enabled', 'dark_mode',
            'privacy_settings_enabled', 'has_answered_onboarding', 'loves_app',
            'subscription_notifications_enabled', 'account_deactivation_date',
        ]

    def get_profile_picture(self, obj):
        if obj.profile_picture:
            profile_picture_url = obj.profile_picture.url
            profile_picture_url = profile_picture_url.replace("https//", "")
            return profile_picture_url
        return None

    def get_computed_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        elif obj.first_name:
            return obj.first_name
        elif obj.last_name:
            return obj.last_name
        elif obj.full_name:
            return obj.full_name
        else:
            return "User"

    def get_questions_and_answers(self, obj):
        user_answers = {
            'health': obj.Health_conditions,
            'allergy': obj.Allergies,
            'diet': obj.Dietary_preferences,
            'primary health goals': obj.Health_Goals,
            'parental status': obj.Parental_status,
            'family health awareness': obj.Family_Health_Awareness,
            'quality and safety of ingredients': obj.Emotional_Conection,
            'negative health symptoms': obj.Health_impact_awareness,
            'achive by using ingredientiq': obj.Desired_outcome,
            'ready to take control of health': obj.Motivation,
        }

        category_map = {
            'parent or caregiver': 'parental status',
            'Parental status': 'parental status',
            'safer meal planning': 'family health awareness',
            'Family_Health_Awareness': 'family health awareness',
        }

        questions = OnboardingQuestion.objects.prefetch_related('choices').all()
        data = []

        for question in questions:
            normalized_category = category_map.get(
                question.category.strip().lower(), 
                question.category.strip().lower()
            )
            user_answer_raw = user_answers.get(normalized_category, "")
            
            if user_answer_raw:
                if ',' in user_answer_raw and not any(
                    choice.choice_text.strip().lower() == user_answer_raw.strip().lower()
                    for q in OnboardingQuestion.objects.all()
                    for choice in q.choices.all()
                ):
                    user_selected = {ans.strip().lower() for ans in user_answer_raw.split(',')}
                else:
                    user_selected = {user_answer_raw.strip().lower()}
            else:
                user_selected = set()

            choices_data = []
            for choice in question.choices.all():
                choice_clean = choice.choice_text.strip().lower()
                is_selected = choice_clean in user_selected
                choices_data.append({
                    "choice_text": choice.choice_text,
                    "is_selected": is_selected
                })

            data.append({
                "questionId": question.id,
                "question_text": question.question_text,
                "choices": choices_data
            })

        return data


class termsandconditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Termandcondition
        fields = '__all__'


class privacypolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = privacypolicy
        fields = '__all__'


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'


class AboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUS
        fields = '__all__'
