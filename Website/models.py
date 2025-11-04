from django.db import models
from django.conf import settings

# Create your models here.
class Stayconnected(models.Model):
    name = models.CharField(max_length=100,null=True,blank=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
    
class Contact(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    # name = models.CharField(max_length=255)   
    phone_number = models.CharField(max_length=255)
    enquiry_type = models.CharField(max_length=255,choices=[('support','Support'),('feedback','Feedback'),('partnership','Partnership'),('press','Press'),('security','Security')])
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    agreed_to_terms = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name
    
class TermsandConditions(models.Model):
    terms_and_conditions = models.TextField(null=True,blank=True)
    heading = models.CharField(max_length=255,null=True,blank=True)
    subheading = models.CharField(max_length=255,null=True,blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content
    
class PrivacyPolicy(models.Model):
    privacy_policy = models.TextField(null=True,blank=True)
    heading = models.CharField(max_length=255,null=True,blank=True)
    subheading = models.CharField(max_length=255,null=True,blank=True)
    content = models.TextField(max_length=10000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content
    
class Blogs(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='website/blogs/')
    description_1 = models.TextField(max_length=10000)
    description_2 = models.TextField(max_length=10000,null=True,blank=True)
    quote = models.TextField(max_length=10000)
    # content = models.TextField(max_length=10000)
    author = models.CharField(max_length=255)
    date = models.DateField()
    time_to_read = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def get_image_url(self):
        """Get the S3 URL for the image"""
        if self.image:
            # Ensure we're getting a clean URL
            if hasattr(self.image, 'url'):
                url = self.image.url
                # Fix malformed URLs with double https://
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
            elif isinstance(self.image, str):
                # If it's already a string, fix malformed URLs
                url = self.image
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
        return None
    
    def get_description_1_html(self):
        """Get description_1 as safe HTML"""
        from django.utils.safestring import mark_safe
        return mark_safe(self.description_1)
    
    def get_description_2_html(self):
        """Get description_2 as safe HTML"""
        from django.utils.safestring import mark_safe
        return mark_safe(self.description_2 or '')
    
    def get_quote_html(self):
        """Get quote as safe HTML"""
        from django.utils.safestring import mark_safe
        return mark_safe(self.quote)

class Faqs(models.Model):
    category = models.CharField(max_length=255,null=True,blank=True)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question
    
class Testimonials(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    image = models.ImageField(upload_to='website/testimonials/')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - Rating: {self.rating}"
    
    def get_image_url(self):
        """Get the S3 URL for the image"""
        if self.image:
            # Ensure we're getting a clean URL
            if hasattr(self.image, 'url'):
                url = self.image.url
                # Fix malformed URLs with double https://
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
            elif isinstance(self.image, str):
                # If it's already a string, fix malformed URLs
                url = self.image
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
        return None
    
class Aboutus(models.Model):
    title = models.CharField(max_length=255,null=True,blank=True)
    image = models.ImageField(upload_to='website/aboutus/',null=True,blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def get_image_url(self):
        """Get the S3 URL for the image"""
        if self.image:
            # Ensure we're getting a clean URL
            if hasattr(self.image, 'url'):
                url = self.image.url
                # Fix malformed URLs with double https://
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
            elif isinstance(self.image, str):
                # If it's already a string, fix malformed URLs
                url = self.image
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
        return None
    
class Platforms(models.Model):
    # name = models.CharField(max_length=255)
    content = models.TextField()
    TikTok = models.URLField(null=True,blank=True)
    Instagram = models.URLField(null=True,blank=True)
    Facebook = models.URLField(null=True,blank=True)
    LinkedIn = models.URLField(null=True,blank=True)
    # image = models.ImageField(upload_to='platforms/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content
    
class Info(models.Model):
    office_address = models.TextField()
    call_us = models.CharField(max_length=255)
    working_hours = models.CharField(max_length=255)
    partnership_and_support = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.office_address
    
class Leadership(models.Model):
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    experience = models.CharField(max_length=255, help_text="Years of experience or experience description")
    instagram_link = models.URLField(blank=True, null=True, help_text="Instagram profile URL")
    facebook_link = models.URLField(blank=True, null=True, help_text="Facebook profile URL")
    profile_picture = models.ImageField(upload_to='leadership/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True, help_text="Brief biography")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of display")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Leadership"

    def __str__(self):
        return f"{self.name} - {self.position}"
    
class relatedposts(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='relatedposts/')
    description_1 = models.TextField(max_length=10000)
    description_2 = models.TextField(max_length=10000,null=True,blank=True)
    quote = models.TextField(max_length=10000)
    author = models.CharField(max_length=255,null=True,blank=True)
    date = models.DateField(null=True,blank=True)
    time_to_read = models.CharField(max_length=255,null=True,blank=True)
    category = models.CharField(max_length=255,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def get_image_url(self):
        """Get the S3 URL for the image"""
        if self.image:
            # Ensure we're getting a clean URL
            if hasattr(self.image, 'url'):
                url = self.image.url
                # Fix malformed URLs with double https://
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
            elif isinstance(self.image, str):
                # If it's already a string, fix malformed URLs
                url = self.image
                if url.startswith('https//https://'):
                    url = url.replace('https//https://', 'https://')
                elif url.startswith('https://https://'):
                    url = url.replace('https://https://', 'https://')
                return url
        return None
    
class DownloadPDF(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=255,null=True,blank=True)
    # pdf = models.FileField(upload_to='website/pdfs/',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
    
class Video(models.Model):
    title = models.CharField(max_length=255)
    video = models.FileField(upload_to='website/videos/',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    