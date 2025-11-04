from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from foodinfo.models import User,UserManager

    


class SuperAdmin(User):
    is_super_admin = models.BooleanField(default=True)
    admin_permissions = models.JSONField(
        default=dict,
        help_text="Stores admin-specific permissions"
    )

    class Meta:
        verbose_name = "Super Admin"
        verbose_name_plural = "Super Admins"

    def has_permission(self, permission):
        return self.is_super_admin or permission in self.admin_permissions

    def __str__(self):
        return f"Super Admin: {self.email}"
    
class OnboardingQuestion(models.Model):
    SINGLE = 'single'
    MULTIPLE = 'multiple'
    ANSWER_TYPE_CHOICES = [
        (SINGLE, 'Single Choice'),
        (MULTIPLE, 'Multiple Choice'),
    ]

    QUESTION_CATEGORIES = [
        # Static categories as per client requirements
        ('profile_demographics', 'Profile & Demographics'),
        ('motivation_cognitive', 'Motivation & Cognitive Profile'),
        ('medical_clinical', 'Medical & Clinical History'),
        ('medications_supplements', 'Medications & Supplements'),
        ('allergies_sensitivities', 'Allergies & Sensitivities'),
        ('lifestyle_dietary', 'Lifestyle & Dietary Preferences'),
        ('behavioral_rhythm', 'Behavioral Rhythm & Feedback Cadence'),
        # Legacy categories for backward compatibility
        ('diet', 'Dietary Preference'),
        ('health', 'Health Condition'),
        ('allergy', 'Allergy'),
        ('primary health goals', 'Health Goals'),
        ('Parental status', 'Parental status'),
        ('safer meal planning','Family_Health_Awareness'),
        ('quality and safety of ingredients','Emotional_Conection'),
        ('negative health symptoms','Health_impact_awareness'),
        ('achive by using IngredientIQ','Desired_outcome'),
        ('ready to take control of health','Motivation'),
        ('other', 'Other'),
    ]

    question_text = models.TextField()
    answer_type = models.CharField(max_length=100, choices=ANSWER_TYPE_CHOICES, default=SINGLE)
    category = models.CharField(max_length=100, choices=QUESTION_CATEGORIES, default='other')  # 👈 new field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text


class OnboardingChoice(models.Model):
    question = models.ForeignKey(OnboardingQuestion, related_name='choices', on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.question.question_text} - {self.choice_text}"
    
class OnboardingAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the user
    question = models.ForeignKey(OnboardingQuestion, on_delete=models.CASCADE)  # Link to the question
    answer = models.TextField()  # Store the answer provided by the user

    def __str__(self):
        return f"{self.user}'s answer to {self.question}"


class OnboardingCategory(models.Model):
    """
    Static model to store the 6 core onboarding categories with their descriptions
    """
    CATEGORY_CHOICES = [
        ('profile_demographics', 'Profile & Demographics'),
        ('motivation_cognitive', 'Motivation & Cognitive Profile'),
        ('medical_clinical', 'Medical & Clinical History'),
        ('medications_supplements', 'Medications & Supplements'),
        ('allergies_sensitivities', 'Allergies & Sensitivities'),
        ('lifestyle_dietary', 'Lifestyle & Dietary Preferences'),
        ('behavioral_rhythm', 'Behavioral Rhythm & Feedback Cadence'),
    ]
    
    category_key = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    category_name = models.CharField(max_length=100)
    description = models.TextField()
    purpose = models.TextField(help_text="What this category feeds into the AI system")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'category_name']
        verbose_name = "Onboarding Category"
        verbose_name_plural = "Onboarding Categories"

    def __str__(self):
        return self.category_name