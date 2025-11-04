from django.contrib import admin
from .models import SuperAdmin,OnboardingAnswer,OnboardingChoice,OnboardingQuestion
# Register your models here.
admin.site.register(SuperAdmin)
admin.site.register(OnboardingAnswer)
admin.site.register(OnboardingQuestion)
admin.site.register(OnboardingChoice)