from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, full_name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    otp = models.CharField(max_length=100, null=True, blank=True)
    Dietary_preferences = models.TextField(blank=True, null=True, help_text="Dietary preferences (e.g., vegan, keto).")
    Health_conditions = models.TextField(blank=True, null=True, help_text="Medical conditions (e.g., diabetes, hypertension).")
    Allergies = models.TextField(blank=True, null=True, help_text="Medical conditions (e.g., vegan, gluten).")
    Health_Goals = models.TextField(blank=True,null=True)
    Parental_status = models.TextField(blank=True,null=True)
    Family_Health_Awareness = models.TextField(blank=True,null=True)
    Emotional_Conection = models.TextField(blank=True,null=True)
    Health_impact_awareness = models.TextField(blank=True,null=True)
    Desired_outcome = models.TextField(blank=True,null=True)
    Motivation = models.TextField(blank=True,null=True)
    # New fields for static onboarding categories
    Demographics = models.TextField(blank=True, null=True, help_text="Profile & Demographics data (age, sex, height, region)")
    Medications = models.TextField(blank=True, null=True, help_text="Medications and supplements information")
    Behavioral_patterns = models.TextField(blank=True, null=True, help_text="Behavioral rhythm and feedback cadence data")
    is_active = models.BooleanField(default=True)
    is_2fa_enabled = models.BooleanField(default=False,null=True,blank=True)  # Add this field
    is_staff = models.BooleanField(default=True)
    is_terms = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)  # Fixed: use callable, not evaluated value
    notifications_enabled = models.BooleanField(default=True)
    subscription_notifications_enabled = models.BooleanField(default=True)  # Toggle for subscription notifications
    dark_mode = models.BooleanField(default=False)
    language = models.CharField(max_length=20, default="English")
    subscription_plan = models.CharField(max_length=100, default="Free")
    has_answered_onboarding = models.BooleanField(default=False)  # <-- Add this
    privacy_settings_enabled = models.BooleanField(default=True)
    loves_app = models.BooleanField(default=False)  # New field for "Love the app" feature
    device_token = models.CharField(blank=True,null=True,max_length=200)
    first_name = models.CharField(null=True,blank=True, max_length=50)
    last_name = models.CharField(null=True,blank=True, max_length=50)
    social_login_id = models.CharField(null=True,blank=True,max_length=200)
    social_login_type = models.CharField(null=True,blank=True,max_length=200)
    username = models.CharField(max_length=200,null=True,blank=True)
    account_deactivation_date = models.OneToOneField('AccountDeletionRequest', on_delete=models.CASCADE, null=True, blank=True, related_name='user_deactivation')
    download_data = models.OneToOneField('DownloadPDF', on_delete=models.CASCADE, related_name='user_download', null=True, blank=True)


    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email


class UserHealthPreference(models.Model):
    """
    A generic model for storing health-related preferences with a compulsory threshold.
    If the user doesn't provide a threshold, it will be treated as zero.
    """
    
    ALLERGY = 'allergy'
    DIETARY = 'dietary'
    MEDICAL = 'medical'
    PREFERENCE_TYPE_CHOICES = [
        (ALLERGY, 'Allergy'),
        (DIETARY, 'Dietary Preference'),
        (MEDICAL, 'Medical History'),
    ]
    
    user = models.ForeignKey(User, related_name="health_preferences", on_delete=models.CASCADE)
    preference_type = models.CharField(
        max_length=10,
        choices=PREFERENCE_TYPE_CHOICES,
        help_text="Type of health preference."
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the allergen, dietary preference, or medical condition (e.g., peanuts, vegan, diabetes)."
    )
    # Make threshold required by setting blank=False. In your serializer or view, treat empty as zero.
    threshold = models.CharField(
        max_length=50,
        blank=False,
        null=False,
        help_text="Compulsory threshold value (with units) that the user can tolerate. Enter 0 (or 0 with unit, e.g., 0mg) if none."
    )
    
    def __str__(self):
        return f"{self.name} ({self.get_preference_type_display()})" + (f" - Threshold: {self.threshold}" if self.threshold else "")
    
    
# Optionally, create an OTP model for forgot password flow.
# class OTP(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     code = models.CharField(max_length=6)
#     created_at = models.DateTimeField(auto_now_add=True)
#     is_verified = models.BooleanField(default=False)

#     def __str__(self):
#         return f"{self.user.email} - {self.code}"

class Termandcondition(models.Model):
    description = models.TextField()

    def __str__(self):
        return str(self.id)
    
class privacypolicy(models.Model):
    description = models.TextField()
    def __str__(self):
        return str(self.id)

class FAQ(models.Model):
    # description = models.TextField()
    question = models.CharField(max_length=500)
    category = models.CharField(max_length=500,null=True,blank=True)
    answer = models.CharField(max_length=500)
    def __str__(self):
        return str(self.category)
    
class AboutUS(models.Model):
    description = models.TextField()
    def __str__(self):
        return str(self.id)
    
class FoodLabelScan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255, null=True, blank=True)
    product_image_url = models.URLField(null=True, blank=True)
    image_url = models.URLField()  # Store S3 Image URL
    extracted_text = models.TextField()
    nutrition_data = models.JSONField()
    safety_status = models.CharField(max_length=20)
    flagged_ingredients = models.JSONField(default=list,null=True,blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)
    is_favorite = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Scan by {self.user.email} at {self.scanned_at}"
    
class StripeCustomer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.stripe_customer_id}"

class UserSubscription(models.Model):
    PLAN_CHOICES = [
        # Keep legacy DB values but present user-facing names.
        ('freemium', 'Free'),
        ('premium', 'Premium'),
        ('family', 'Family/Team'),
        ('team', 'Family/Team'),
        ('enterprise', 'Enterprise'),
    ]
    PREMIUM_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        (None, 'None'),
    ]
    PLATFORM_CHOICES = [
        ('stripe', 'Stripe/Web'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('pending_cancel', 'Pending Cancel'),
        ('inactive', 'Inactive'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=50, choices=PLAN_CHOICES)
    premium_type = models.CharField(max_length=20, choices=PREMIUM_TYPE_CHOICES, null=True, blank=True, default=None)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='stripe')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="inactive")
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    cancel_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.plan_name} - {self.premium_type} ({self.platform})"
    
    @property
    def is_active(self):
        return self.status == 'active' and not self.cancel_at_period_end
    
    @property
    def is_premium(self):
        # Publicly treated as a paid plan. Keep legacy 'premium' while supporting future tiers.
        return self.plan_name in {'premium', 'family', 'team', 'enterprise'} and self.is_active

    @property
    def public_plan_label(self) -> str:
        """User-facing plan label.

        Must not expose internal billing cadence or entitlement mechanics.
        """
        if not self.is_active:
            return 'Free'

        plan = (self.plan_name or '').lower().strip()
        if plan in {'premium'}:
            return 'Premium'
        if plan in {'family', 'team'}:
            return 'Family/Team'
        if plan in {'enterprise'}:
            return 'Enterprise'
        return 'Free'
    
    @property
    def renewal_date(self):
        if self.current_period_end:
            return self.current_period_end
        return None
    
    @property
    def cancel_date(self):
        if self.cancel_at_period_end and self.current_period_end:
            return self.current_period_end
        return self.cancel_at


class MonthlyScanUsage(models.Model):
    """
    Track monthly scan usage for freemium users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    scan_count = models.IntegerField(default=0)
    premium_scans_used = models.IntegerField(default=0)  # First 6 scans with AI insights
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'year', 'month']
        indexes = [
            models.Index(fields=['user', 'year', 'month']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.year}/{self.month} - {self.scan_count} scans"

    @classmethod
    def get_or_create_current_month(cls, user):
        """Get or create current month's usage record"""
        from datetime import datetime
        now = datetime.now()
        usage, created = cls.objects.get_or_create(
            user=user,
            year=now.year,
            month=now.month,
            defaults={'scan_count': 0, 'premium_scans_used': 0}
        )
        return usage

    def increment_scan(self, is_premium_scan=False):
        """Increment scan count and optionally premium scan count"""
        self.scan_count += 1
        if is_premium_scan:
            self.premium_scans_used += 1
        self.save()

    def can_scan(self):
        """Check if user can still scan this month"""
        return self.scan_count < 20

    def can_get_ai_insights(self):
        """Check if user can get AI insights (first 6 scans)"""
        return self.premium_scans_used < 6

    def get_remaining_scans(self):
        """Get remaining scans for this month"""
        return max(0, 20 - self.scan_count)

    def get_remaining_premium_scans(self):
        """Get remaining premium scans (with AI insights) for this month"""
        return max(0, 6 - self.premium_scans_used)

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 star rating
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback from {self.user.email} - {self.rating} stars"

class DepartmentContact(models.Model):
    DEPARTMENT_CHOICES = [
        ('customer_support', 'Customer Support'),
        ('technical_support', 'Technical Support'),
        ('billing', 'Billing'),
        ('general', 'General Inquiries'),
        ('partnership', 'Partnership'),
        ('media', 'Media Relations'),
    ]
    
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, unique=True)
    contact_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    available_hours = models.CharField(max_length=100, default="Monday-Friday, 9 AM - 6 PM")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_department_display()} - {self.contact_name}"

# Mobile-specific models removed (DeviceToken, NotificationTemplate, PushNotification, AppVersion)
# These were for push notifications in the mobile app which is now discontinued


# Django signals to automatically sync scan counts
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=FoodLabelScan)
def sync_scan_count_on_save(sender, instance, created, **kwargs):
    """
    Automatically sync scan count when a new scan is created
    """
    if created:
        try:
            usage = MonthlyScanUsage.get_or_create_current_month(instance.user)
            # Get actual count of scans for this user
            actual_count = FoodLabelScan.objects.filter(user=instance.user).count()
            if usage.scan_count != actual_count:
                usage.scan_count = actual_count
                usage.save()
        except Exception as e:
            print(f"Error syncing scan count on save: {e}")

@receiver(post_delete, sender=FoodLabelScan)
def sync_scan_count_on_delete(sender, instance, **kwargs):
    """
    Automatically sync scan count when a scan is deleted
    """
    try:
        # Check if user still exists (not being deleted)
        if not hasattr(instance.user, '_state') or instance.user._state.adding or not instance.user.pk:
            # User is being deleted, skip sync to avoid constraint errors
            return
            
        # Check if user exists in database
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            if not User.objects.filter(pk=instance.user.pk).exists():
                # User has been deleted, skip sync
                return
        except Exception:
            # If there's any error checking user existence, skip sync
            return
            
        usage = MonthlyScanUsage.get_or_create_current_month(instance.user)
        # Get actual count of scans for this user
        actual_count = FoodLabelScan.objects.filter(user=instance.user).count()
        if usage.scan_count != actual_count:
            usage.scan_count = actual_count
            usage.save()
    except Exception as e:
        # Silently ignore errors during user deletion
        print(f"Error syncing scan count on delete: {e}")


class AccountDeletionRequest(models.Model):
    """
    Track account deletion requests for premium users
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Deletion'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='deletion_request')
    requested_at = models.DateTimeField(auto_now_add=True)
    scheduled_deletion_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Deletion request for {self.user.email} - {self.status}"
    
    @property
    def is_cancelled(self):
        return self.status == 'cancelled'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def days_remaining(self):
        if self.status != 'pending':
            return 0
        delta = self.scheduled_deletion_date - timezone.now()
        return max(0, delta.days)
    
    def is_ready_for_deletion(self):
        """Check if the account is ready for deletion (past scheduled date)"""
        return (self.status == 'pending' and 
                self.scheduled_deletion_date <= timezone.now())
    
    def execute_deletion(self):
        """Execute the account deletion"""
        if not self.is_ready_for_deletion():
            return False, "Account is not ready for deletion"
        
        try:
            # Update status before deletion
            self.status = 'completed'
            self.save()
            
            # Delete the user (cascades to related objects)
            # The AccountDeletionRequest will be automatically deleted due to CASCADE
            self.user.delete()
            
            return True, "Account deleted successfully"
        except Exception as e:
            return False, f"Error deleting account: {str(e)}"
        
class DownloadPDF(models.Model):
    email = models.EmailField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    download_requested = models.ForeignKey('DownloadRequest', on_delete=models.CASCADE, related_name='download_pdfs', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} - Data Download Requested: {self.download_requested}"
    
    class Meta:
        verbose_name = "Data Download Request"
        verbose_name_plural = "Data Download Requests"
    

class DownloadRequest(models.Model):
    email = models.EmailField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} - Data Download Requested: {self.name}"