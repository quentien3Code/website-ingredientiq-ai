from django.contrib import admin
from .models import Stayconnected, Contact, TermsandConditions, PrivacyPolicy, Blogs, Faqs, Testimonials, Aboutus, Platforms, Info,Leadership,relatedposts,DownloadPDF,Video
from foodinfo.models import DownloadRequest
# Register your models here.
admin.site.register(Stayconnected)
admin.site.register(Contact)
admin.site.register(TermsandConditions)
admin.site.register(PrivacyPolicy)
admin.site.register(Blogs)
admin.site.register(Faqs)
admin.site.register(Testimonials)
admin.site.register(Aboutus)
admin.site.register(Platforms)
admin.site.register(Info)
admin.site.register(Leadership)
admin.site.register(relatedposts)
admin.site.register(DownloadPDF)
admin.site.register(Video)
admin.site.register(DownloadRequest)
# admin.site.register(AccountDeletionRequest)