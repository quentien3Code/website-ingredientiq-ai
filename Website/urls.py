from django.urls import path
from .views import LeadershipView, StayconnectedView, ContactView, TermsandConditionsView, PrivacyPolicyView, BlogsView, BlogBySlugView, FaqsView, TestimonialsView, AboutusView, PlatformsView, InfoView, RelatedPostsView, DownloadPDFView, VideoView, DownloadRequestView, validate_slug, download_smart_label_decoder_pdf

urlpatterns = [
    # Brita CMS API endpoints
    path('api/validate-slug/', validate_slug, name='validate-slug'),
    
    path('stayconnected/', StayconnectedView.as_view(), name='stayconnected'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('termsandconditions/', TermsandConditionsView.as_view(), name='termsandconditions'),
    path('privacypolicy/', PrivacyPolicyView.as_view(), name='privacypolicy'),
    path('blogs/', BlogsView.as_view(), name='blogs'),
    path('blogs/<int:id>/', BlogsView.as_view(), name='blog-detail'),
    path('blogs/slug/<slug:slug>/', BlogBySlugView.as_view(), name='blog-by-slug'),
    path('faqs/', FaqsView.as_view(), name='faqs'),
    path('faqs/<int:id>/', FaqsView.as_view(), name='faq-detail'),
    path('testimonials/', TestimonialsView.as_view(), name='testimonials'),
    path('testimonials/<int:id>/', TestimonialsView.as_view(), name='testimonial-detail'),
    path('aboutus/', AboutusView.as_view(), name='aboutus'),
    path('aboutus/<int:id>/', AboutusView.as_view(), name='aboutus-detail'),
    path('platforms/', PlatformsView.as_view(), name='platforms'),
    path('platforms/<int:id>/', PlatformsView.as_view(), name='platform-detail'),
    path('info/', InfoView.as_view(), name='info'),
    path('info/<int:id>/', InfoView.as_view(), name='info-detail'),
    path('leadership/',LeadershipView.as_view(),name='leadership'),
    path('related-posts/', RelatedPostsView.as_view(), name='related-posts'),
    path('downloadpdf/', DownloadPDFView.as_view(), name='downloadpdf'),
    path('downloadpdf/file/', download_smart_label_decoder_pdf, name='downloadpdf-file'),
    path('video/', VideoView.as_view(), name='video'),
    path('downloadrequest/', DownloadRequestView.as_view(), name='downloadrequest'),
]