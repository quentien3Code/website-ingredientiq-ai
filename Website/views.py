from django.shortcuts import render, get_object_or_404
from django.db import IntegrityError, models
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import (
    DownloadPDF as WebsiteDownloadPDF,
    Stayconnected,
    Contact,
    TermsandConditions,
    PrivacyPolicy,
    Blogs,
    BlogCategory,
    BlogTag,
    BlogAuthor,
    Faqs,
    Testimonials,
    Aboutus,
    Platforms,
    Info,
    Leadership,
    Video,
    relatedposts,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import ModelSerializer
from foodinfo.models import DownloadRequest as DataDownloadRequest
from bs4 import BeautifulSoup
import re

# Create your views here.


# ============================================
# BRITA CMS - SLUG VALIDATION API
# ============================================

@require_GET
def validate_slug(request):
    """
    API endpoint to validate slug uniqueness for Brita CMS.
    Returns JSON: { "exists": true/false, "slug": "...", "existing_id": null|id }
    """
    slug = request.GET.get('slug', '').strip()
    exclude_id = request.GET.get('exclude_id', '').strip()
    
    if not slug:
        return JsonResponse({'exists': False, 'slug': '', 'error': 'No slug provided'})
    
    # Check if slug exists
    qs = Blogs.objects.filter(slug=slug)
    
    # Exclude current post if editing
    if exclude_id and exclude_id.isdigit():
        qs = qs.exclude(id=int(exclude_id))
    
    exists = qs.exists()
    existing_id = qs.values_list('id', flat=True).first() if exists else None
    
    return JsonResponse({
        'exists': exists,
        'slug': slug,
        'existing_id': existing_id
    })

def strip_html_tags(text):
    """
    Utility function to strip HTML tags from text content
    """
    if not text:
        return text
    
    # Use BeautifulSoup to parse and extract text
    soup = BeautifulSoup(text, 'html.parser')
    # Get text content without HTML tags
    clean_text = soup.get_text()
    # Clean up extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

class StayconnectedView(APIView):
    def post(self,request):
        name = request.data.get('name')
        email = request.data.get('email')
        if not email:
            return Response({'error':'Email is required'},status=status.HTTP_400_BAD_REQUEST)
        try:
            user = Stayconnected.objects.create(email=email,name=name)
            return Response({'message':'User created'},status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error':'Email already exists'},status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
    def get(self,request):
        stayconnected = Stayconnected.objects.all()
        data = []
        for user in stayconnected:
            data.append({
                'id': user.id,
                'name':user.name,
                'email': user.email,
                'created_at': user.created_at,
                'updated_at': user.updated_at
            })
        return Response({'stayconnected': data}, status=status.HTTP_200_OK)
    def delete(self,request,id):
        try:
            stayconnected = get_object_or_404(Stayconnected, id=id)
            stayconnected.delete()
            return Response({'message':'Stayconnected deleted'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def patch(self,request,id):
        try:
            stayconnected = get_object_or_404(Stayconnected, id=id)
            stayconnected.email = request.data.get('email', stayconnected.email)
            stayconnected.name = request.data.get('name', stayconnected.name)
            stayconnected.save()
            return Response({'message':'Stayconnected updated'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class ContactView(APIView):
    def post(self,request):
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        phone_number = request.data.get('phone_number')
        enquiry_type = request.data.get('enquiry_type')
        email = request.data.get('email')
        message = request.data.get('message')
        agreed_to_terms = request.data.get('agreed_to_terms')
        try:
            contact = Contact.objects.create(first_name=first_name,last_name=last_name,phone_number=phone_number,enquiry_type=enquiry_type,email=email,message=message,agreed_to_terms=agreed_to_terms)
            return Response({'message':'Contact created'},status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error':'Contact creation failed due to database constraint'},status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
        
    def get(self,request):
        contact = Contact.objects.all()
        data = []
        for contact in contact:
            data.append({
                'id': contact.id,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'phone_number': contact.phone_number,
                'enquiry_type': contact.enquiry_type,
                'email': contact.email,
                'message': contact.message,
                'created_at': contact.created_at,
                'updated_at': contact.updated_at,
                'agreed_to_terms':contact.agreed_to_terms
            })
        return Response({'contact': data}, status=status.HTTP_200_OK)
    # def get(self,request):
    #     contact = Contact.objects.all()
    #     print("----------",contact)
    #     data = {
    #         # 'id': contact.id,
    #         'first_name': Contact.objects.all().first_name,
    #         'last_name': Contact.objects.last_name,
    #         'phone_number': Contact.objects.all().phone_number,
    #         'enquiry_type': Contact.objects.all().enquiry_type,
    #         'email': Contact.objects.all().email,
    #         'message': Contact.objects.message,
    #         'created_at': Contact.objects.created_at,
    #         'updated_at': Contact.objects.updated_at
    #     }
    #     return Response({'contact': data}, status=status.HTTP_200_OK)
    def delete(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            contact = get_object_or_404(Contact, id=id)
            contact.delete()
            return Response({'message':'Contact deleted'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def patch(self,request,id):
        try:
            contact = get_object_or_404(Contact, id=id)
            contact.email = request.data.get('email', contact.email)
            contact.last_name = request.data.get('last_name', contact.last_name)
            contact.phone_number = request.data.get('phone_number', contact.phone_number)
            contact.enquiry_type = request.data.get('enquiry_type', contact.enquiry_type)
            contact.email = request.data.get('email', contact.email)
            contact.message = request.data.get('message', contact.message)
            contact.save()
            return Response({'message':'Contact updated'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class TermsandConditionsView(APIView):
    def get(self,request):
        termsandconditions = TermsandConditions.objects.all()
        data = []
        for term in termsandconditions:
            data.append({
                'id': term.id,
                'terms_and_conditions': term.terms_and_conditions,
                'heading': term.heading,
                'subheading': term.subheading,
                'content': term.content,
                'created_at': term.created_at,
                'updated_at': term.updated_at
            })
        return Response({'termsandconditions': data}, status=status.HTTP_200_OK)
    def post(self,request):
        terms_and_conditions = request.data.get('terms_and_conditions')
        heading = request.data.get('heading')
        subheading = request.data.get('subheading')
        content = request.data.get('content')
        try:
            termsandconditions = TermsandConditions.objects.create(terms_and_conditions=terms_and_conditions,heading=heading,subheading=subheading,content=content)
            return Response({'message':'Terms and conditions created'},status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error':'Terms and conditions creation failed due to database constraint'},status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
    def delete(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            termsandconditions = get_object_or_404(TermsandConditions, id=id)
            termsandconditions.delete()
            return Response({'message':'Terms and conditions deleted'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            termsandconditions = get_object_or_404(TermsandConditions, id=id)
            # termsandconditions.heading = request.data.get('heading', termsandconditions.heading)
            # termsandconditions.subheading = request.data.get('subheading', termsandconditions.subheading)
            termsandconditions.content = request.data.get('content', termsandconditions.content)
            # termsandconditions.terms_and_conditions = request.data.get('terms_and_conditions', termsandconditions.terms_and_conditions)
            termsandconditions.save()
            return Response({'message':'Terms and conditions updated'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PrivacyPolicyView(APIView):
    def get(self,request):
        privacypolicy = PrivacyPolicy.objects.all()
        data = []
        for policy in privacypolicy:
            data.append({
                'id': policy.id,
                'privacy_policy': policy.privacy_policy,
                'heading': policy.heading,
                'subheading': policy.subheading,
                'content': policy.content,
                'created_at': policy.created_at,
                'updated_at': policy.updated_at
            })
        return Response({'privacypolicy': data}, status=status.HTTP_200_OK)
    def post(self,request):
        privacy_policy = request.data.get('privacy_policy')
        heading = request.data.get('heading')
        subheading = request.data.get('subheading')
        content = request.data.get('content')
        try:
            privacypolicy = PrivacyPolicy.objects.create(privacy_policy=privacy_policy,heading=heading,subheading=subheading,content=content)
            return Response({'message':'Privacy policy created'},status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error':'Privacy policy creation failed due to database constraint'},status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, id=None):
        # Support both URL path parameter and query parameter
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        
        if id is None:
            return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            privacypolicy = get_object_or_404(PrivacyPolicy, id=id)
            privacypolicy.delete()
            return Response({'message': 'Privacy policy deleted'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, id=None):
        # Support both URL path parameter and query parameter
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            privacypolicy = get_object_or_404(PrivacyPolicy, id=id)
            # privacypolicy.privacy_policy = request.data.get('privacy_policy', privacypolicy.privacy_policy)
            # privacypolicy.heading = request.data.get('heading', privacypolicy.heading)
            # privacypolicy.subheading = request.data.get('subheading', privacypolicy.subheading)
            privacypolicy.content = request.data.get('content', privacypolicy.content)
            # privacypolicy.privacy_policy = request.data.get('privacy_policy', privacypolicy.privacy_policy)
            privacypolicy.save()
            return Response({'message': 'Privacy policy updated'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class BlogsView(APIView):
    def _html_to_markdown(self, html_content):
        """Convert HTML to markdown format, preserving formatting without HTML tags"""
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Convert common HTML tags to markdown
        # Bold text: <strong> or <b> -> **text**
        for tag in soup.find_all(['strong', 'b']):
            tag.replace_with(f"**{tag.get_text()}**")
        
        # Italic text: <em> or <i> -> *text*
        for tag in soup.find_all(['em', 'i']):
            tag.replace_with(f"*{tag.get_text()}*")
        
        # Paragraphs: <p> -> text with line breaks
        for tag in soup.find_all('p'):
            if tag.get_text().strip():
                tag.replace_with(f"{tag.get_text()}\n\n")
        
        # Line breaks: <br> -> \n
        for tag in soup.find_all('br'):
            tag.replace_with('\n')
        
        # Headers: <h1> -> # text, <h2> -> ## text, etc.
        for i in range(1, 7):
            for tag in soup.find_all(f'h{i}'):
                tag.replace_with(f"{'#' * i} {tag.get_text()}\n\n")
        
        # Lists: <ul> and <li> -> - item
        for ul in soup.find_all('ul'):
            items = []
            for li in ul.find_all('li'):
                items.append(f"- {li.get_text()}")
            ul.replace_with('\n'.join(items) + '\n\n')
        
        # Get the final text and clean up
        text = soup.get_text()
        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def post(self, request):
        """
        Create a new blog post using Brita CMS fields.
        Accepts both new Brita fields and legacy fields for backwards compatibility.
        """
        # Get data - support both new and legacy field names
        title = request.data.get('title', '')
        raw_draft = request.data.get('raw_draft') or request.data.get('body') or request.data.get('description_1', '')
        
        # Handle legacy fields by converting to raw_draft
        if not raw_draft:
            desc1 = request.data.get('description_1', '')
            desc2 = request.data.get('description_2', '')
            if desc1 or desc2:
                raw_draft = self._html_to_markdown(desc1 or '') + '\n\n' + self._html_to_markdown(desc2 or '')
        
        image = request.FILES.get('image')
        image_alt_text = request.data.get('image_alt_text', '')
        excerpt = request.data.get('excerpt', '')
        slug = request.data.get('slug', '')
        status_value = request.data.get('status', 'draft')
        
        # Author - try FK first, fallback to string
        author_id = request.data.get('author_entity_id') or request.data.get('author_id')
        author_name = request.data.get('author', '')  # Legacy string field
        
        # Category - try FK first, fallback to string
        category_id = request.data.get('category_new_id') or request.data.get('category_id')
        category_name = request.data.get('category', '')  # Legacy string field
        
        # Publish date
        publish_date = request.data.get('publish_date') or request.data.get('date')
        
        # Validate image
        if image and not hasattr(image, 'read'):
            return Response({'error': 'Image must be a file upload, not a URL'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create blog with Brita CMS fields
            blog = Blogs(
                title=title,
                raw_draft=raw_draft,
                image=image,
                image_alt_text=image_alt_text,
                excerpt=excerpt,
                slug=slug or None,  # Let model generate if empty
                status=status_value,
                # Legacy fields for backwards compatibility
                author=author_name,
                category=category_name,
            )
            
            # Set FK relations if provided
            if author_id:
                blog.author_entity_id = author_id
            if category_id:
                blog.category_new_id = category_id
            if publish_date:
                from django.utils.dateparse import parse_datetime, parse_date
                if isinstance(publish_date, str):
                    blog.publish_date = parse_datetime(publish_date) or parse_date(publish_date)
                else:
                    blog.publish_date = publish_date
            
            blog.save()  # Triggers Brita pipeline
            
            return Response({
                'message': 'Blog created',
                'blog_id': blog.id,
                'slug': blog.slug,
                'image_url': blog.get_image_url()
            }, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({'error': f'Blog creation failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

    def get(self,request,id=None):
        # If blog id is provided (from path or query), return single blog
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id:
            try:
                blog = get_object_or_404(Blogs, id=id)
                data = self._serialize_blog(blog, detail=True)
                return Response({'blog': data}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # List endpoint with optional category filter
        category_slug = request.query_params.get('category')
        status_filter = request.query_params.get('status', 'published')  # Default to published only
        
        blogs = Blogs.objects.all()
        
        # Filter by status
        if status_filter == 'published':
            blogs = blogs.filter(status='published')
        elif status_filter != 'all':
            blogs = blogs.filter(status=status_filter)
        
        # Filter by category (new FK or legacy)
        if category_slug:
            blogs = blogs.filter(
                models.Q(category_new__slug=category_slug) | 
                models.Q(category=category_slug)
            )

        # Category counts (using new FK)
        from django.db.models import Count
        category_counts = {}
        categories = BlogCategory.objects.annotate(count=Count('blog_posts')).values('slug', 'name', 'count')
        for cat in categories:
            category_counts[cat['slug']] = {'name': cat['name'], 'count': cat['count']}

        data = [self._serialize_blog(blog, detail=False) for blog in blogs]

        return Response({
            'blogs': data,
            'category_counts': category_counts,
            'total_blogs': len(data),
            'filtered_category': category_slug if category_slug else None
        }, status=status.HTTP_200_OK)
    
    def _serialize_blog(self, blog, detail=False):
        """
        Serialize a blog post with Brita CMS fields.
        Returns rich data for detail view, compact for list view.
        """
        # Author info
        author_data = None
        if blog.author_entity:
            author_data = {
                'id': blog.author_entity.id,
                'name': blog.author_entity.name,
                'slug': blog.author_entity.slug,
                'bio': blog.author_entity.bio if detail else None,
                'avatar': blog.author_entity.get_avatar_url(),
                'job_title': blog.author_entity.job_title,
            }
        
        # Category info
        category_data = None
        if blog.category_new:
            category_data = {
                'id': blog.category_new.id,
                'name': blog.category_new.name,
                'slug': blog.category_new.slug,
            }
        
        # Tags
        tags_data = list(blog.tags.values('id', 'name', 'slug')) if detail else []
        
        # Base data (for list views)
        author_name = (
            blog.author_entity.name
            if blog.author_entity and getattr(blog.author_entity, 'name', None)
            else (blog.author or 'Anonymous')
        )
        category_name = (
            blog.category_new.name
            if blog.category_new and getattr(blog.category_new, 'name', None)
            else (blog.category or 'Uncategorized')
        )

        data = {
            'id': blog.id,
            'title': blog.title,
            'slug': blog.slug,
            'excerpt': blog.excerpt,
            'image': blog.get_image_url(),
            'image_alt_text': blog.image_alt_text,
            
            # Dates - use publish_date, fallback to date, then created_at
            'publish_date': blog.publish_date.isoformat() if blog.publish_date else (
                blog.date.isoformat() if blog.date else blog.created_at.isoformat()
            ),
            'date': blog.publish_date.isoformat() if blog.publish_date else (
                blog.date.isoformat() if blog.date else blog.created_at.isoformat()
            ),  # Legacy field for backwards compatibility
            
            # Reading time (auto-calculated)
            'reading_time_minutes': blog.reading_time_minutes or 1,
            'time_to_read': blog.get_reading_time_display(),  # "X min read" format
            
            # Author & Category
            # IMPORTANT: keep these as strings for React rendering.
            # (React will crash if you try to render an object as a node.)
            'author': author_name,
            'category': category_name,
            # Preserve rich info separately.
            'author_entity': author_data,
            'category_entity': category_data,
            
            # Status
            'status': blog.status,
            'is_featured': blog.is_featured,
            
            # Timestamps
            'created_at': blog.created_at.isoformat(),
            'updated_at': blog.updated_at.isoformat(),
            
            # Legacy fields for backwards compatibility
            'description_1': blog.description_1 or strip_html_tags(blog.excerpt),
            'quote': blog.pull_quote or blog.quote,
        }
        
        # Extended data for detail views
        if detail:
            data.update({
                # Main content
                'body': blog.body_html or blog.body,
                'body_html': blog.body_html,
                'description_2': blog.description_2 or blog.body_html or blog.body,  # Legacy
                
                # Key takeaways
                'key_takeaways': blog.key_takeaways or [],
                
                # SEO
                'meta_title': blog.meta_title or blog.title,
                'meta_description': blog.meta_description or blog.excerpt,
                'canonical_url': blog.canonical_url,
                
                # Social
                'og_title': blog.og_title or blog.title,
                'og_description': blog.og_description or blog.excerpt,
                'og_image': blog.og_image.url if blog.og_image else blog.get_image_url(),
                
                # Structure
                'toc': blog.toc_json or [],
                'word_count': blog.word_count or 0,
                
                # Related
                'tags': tags_data,
                'related_posts': [
                    {'id': rp.id, 'title': rp.title, 'slug': rp.slug, 'image': rp.get_image_url()}
                    for rp in blog.related_posts.all()[:3]
                ] if detail else [],
                
                # Image details
                'image_caption': blog.image_caption,
                'image_credit': blog.image_credit,
                
                # Pull quote
                'pull_quote': blog.pull_quote,
            })
        
        return data

    def put(self, request, id=None):
        """
        Update a blog post using Brita CMS fields.
        Accepts both new Brita fields and legacy fields for backwards compatibility.
        """
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            blog = get_object_or_404(Blogs, id=id)
            
            # Title
            if 'title' in request.data:
                blog.title = request.data['title']
                blog.title_locked = True  # Lock since manually edited
            
            # Raw draft / body content
            if 'raw_draft' in request.data:
                blog.raw_draft = request.data['raw_draft']
            elif 'body' in request.data:
                blog.raw_draft = self._html_to_markdown(request.data['body'])
            elif 'description_1' in request.data or 'description_2' in request.data:
                # Legacy: combine description fields
                desc1 = self._html_to_markdown(request.data.get('description_1', '') or '')
                desc2 = self._html_to_markdown(request.data.get('description_2', '') or '')
                blog.raw_draft = (desc1 + '\n\n' + desc2).strip()
            
            # Image handling
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                if not hasattr(image_file, 'read'):
                    return Response({'error': 'Image must be a file upload, not a URL'}, status=status.HTTP_400_BAD_REQUEST)
                blog.image = image_file
            if 'image_alt_text' in request.data:
                blog.image_alt_text = request.data['image_alt_text']
            
            # Excerpt
            if 'excerpt' in request.data:
                blog.excerpt = request.data['excerpt']
                blog.excerpt_locked = True
            
            # Slug
            if 'slug' in request.data:
                blog.slug = request.data['slug']
                blog.slug_locked = True
            
            # Status
            if 'status' in request.data:
                blog.status = request.data['status']
            
            # Publish date
            if 'publish_date' in request.data or 'date' in request.data:
                from django.utils.dateparse import parse_datetime, parse_date
                date_value = request.data.get('publish_date') or request.data.get('date')
                if date_value:
                    if isinstance(date_value, str):
                        blog.publish_date = parse_datetime(date_value) or parse_date(date_value)
                    else:
                        blog.publish_date = date_value
            
            # Author - support FK or legacy string
            if 'author_entity_id' in request.data or 'author_id' in request.data:
                blog.author_entity_id = request.data.get('author_entity_id') or request.data.get('author_id')
            if 'author' in request.data:
                blog.author = request.data['author']  # Legacy field
            
            # Category - support FK or legacy string
            if 'category_new_id' in request.data or 'category_id' in request.data:
                blog.category_new_id = request.data.get('category_new_id') or request.data.get('category_id')
            if 'category' in request.data:
                blog.category = request.data['category']  # Legacy field
            
            # Pull quote
            if 'pull_quote' in request.data or 'quote' in request.data:
                blog.pull_quote = request.data.get('pull_quote') or request.data.get('quote')
            
            blog.save()  # Triggers Brita pipeline
            
            return Response({
                'message': 'Blog updated',
                'blog_id': blog.id,
                'slug': blog.slug,
                'image_url': blog.get_image_url()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            blog = get_object_or_404(Blogs, id=id)
            blog.delete()
            return Response({'message':'Blog deleted'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BlogBySlugView(APIView):
    """
    API endpoint to retrieve a blog post by its slug.
    Used by the React frontend to fetch blog content for rendering.
    """
    
    def get(self, request, slug=None):
        """Get a blog post by its slug"""
        if not slug:
            slug = request.query_params.get('slug')
        
        if not slug:
            return Response({'error': 'Slug is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            blog = get_object_or_404(Blogs, slug=slug)
            
            # Check if blog is published (or allow preview with token)
            preview_token = request.query_params.get('preview_token')
            if blog.status != 'published' and str(blog.preview_token) != preview_token:
                return Response({'error': 'Blog not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Reuse the serialization logic from BlogsView
            data = self._serialize_blog(blog)
            return Response({'blog': data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def _serialize_blog(self, blog):
        """Serialize a blog post with full details"""
        # Author info
        author_data = None
        if blog.author_entity:
            author_data = {
                'id': blog.author_entity.id,
                'name': blog.author_entity.name,
                'slug': blog.author_entity.slug,
                'bio': blog.author_entity.bio,
                'avatar': blog.author_entity.get_avatar_url(),
                'job_title': blog.author_entity.job_title,
            }
        
        # Category info
        category_data = None
        if blog.category_new:
            category_data = {
                'id': blog.category_new.id,
                'name': blog.category_new.name,
                'slug': blog.category_new.slug,
            }
        
        # Tags
        tags_data = list(blog.tags.values('id', 'name', 'slug'))

        author_name = (
            blog.author_entity.name
            if blog.author_entity and getattr(blog.author_entity, 'name', None)
            else (blog.author or 'Anonymous')
        )
        category_name = (
            blog.category_new.name
            if blog.category_new and getattr(blog.category_new, 'name', None)
            else (blog.category or 'Uncategorized')
        )
        
        return {
            'id': blog.id,
            'title': blog.title,
            'slug': blog.slug,
            'excerpt': blog.excerpt,
            'image': blog.get_image_url(),
            'image_alt_text': blog.image_alt_text,
            'image_caption': blog.image_caption,
            'image_credit': blog.image_credit,
            
            # Main content
            'body': blog.body_html or blog.body,
            'body_html': blog.body_html,
            
            # Dates
            'publish_date': blog.publish_date.isoformat() if blog.publish_date else (
                blog.date.isoformat() if blog.date else blog.created_at.isoformat()
            ),
            'date': blog.publish_date.isoformat() if blog.publish_date else (
                blog.date.isoformat() if blog.date else blog.created_at.isoformat()
            ),
            
            # Reading time
            'reading_time_minutes': blog.reading_time_minutes or 1,
            'time_to_read': blog.get_reading_time_display(),
            'word_count': blog.word_count or 0,
            
            # Author & Category
            'author': author_name,
            'category': category_name,
            'author_entity': author_data,
            'category_entity': category_data,
            
            # Status
            'status': blog.status,
            'is_featured': blog.is_featured,
            
            # Key takeaways
            'key_takeaways': blog.key_takeaways or [],
            
            # SEO
            'meta_title': blog.meta_title or blog.title,
            'meta_description': blog.meta_description or blog.excerpt,
            'canonical_url': blog.canonical_url or blog.get_full_url(),
            
            # Social
            'og_title': blog.og_title or blog.title,
            'og_description': blog.og_description or blog.excerpt,
            'og_image': blog.og_image.url if blog.og_image else blog.get_image_url(),
            
            # Structure
            'toc': blog.toc_json or [],
            
            # Related
            'tags': tags_data,
            'related_posts': [
                {'id': rp.id, 'title': rp.title, 'slug': rp.slug, 'image': rp.get_image_url()}
                for rp in blog.related_posts.all()[:3]
            ],
            
            # Sources (for LLM/citation)
            'sources': blog.sources_json or [],
            
            # Pull quote
            'pull_quote': blog.pull_quote,
            
            # Timestamps
            'created_at': blog.created_at.isoformat(),
            'updated_at': blog.updated_at.isoformat(),
            
            # Legacy fields
            'description_1': blog.description_1 or strip_html_tags(blog.excerpt),
            'description_2': blog.description_2 or blog.body_html or blog.body,
            'quote': blog.pull_quote or blog.quote,
        }


class FaqsView(APIView):
    def post(self,request):
        category = request.data.get('category')
        question = request.data.get('question')
        answer = request.data.get('answer')
        try:
            faq = Faqs.objects.create(category=category,question=question,answer=answer)
            return Response({'message':'Faq created'},status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error':'FAQ creation failed due to database constraint'},status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
    
    def get(self,request):
        faqs = Faqs.objects.all()
        data = []
        for faq in faqs:
            data.append({
                'id': faq.id,
                'category': faq.category,
                'question': faq.question,
                'answer': faq.answer,
                'created_at': faq.created_at,
                'updated_at': faq.updated_at
            })
        return Response({'faqs': data}, status=status.HTTP_200_OK)
    
    def put(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            faq = get_object_or_404(Faqs, id=id)
            faq.category = request.data.get('category', faq.category)
            faq.question = request.data.get('question', faq.question)
            faq.answer = request.data.get('answer', faq.answer)
            faq.save()
            return Response({'message':'Faq updated'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            faq = get_object_or_404(Faqs, id=id)
            faq.delete()
            return Response({'message':'Faq deleted'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
class TestimonialsView(APIView):
    def post(self,request):
        name = request.data.get('name')
        role = request.data.get('role')
        rating = request.data.get('rating')
        image = request.FILES.get('image')  # Handle file upload
        content = request.data.get('content')
        
        # Debug: Print image info
        print(f"Image type: {type(image)}")
        print(f"Image content: {image}")
        
        # Validate that image is a file, not a URL string
        if image and not hasattr(image, 'read'):
            return Response({'error': 'Image must be a file upload, not a URL'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Additional validation for file upload
        if image and hasattr(image, 'content_type') and not image.content_type.startswith('image/'):
            return Response({'error': 'Uploaded file must be an image'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            testimonial = Testimonials.objects.create(name=name,role=role,rating=rating,image=image,content=content)
            return Response({
                'message':'Testimonial created',
                'testimonial_id': testimonial.id,
                'image_url': testimonial.get_image_url()
            },status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error':'Testimonial creation failed due to database constraint'},status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
        
    def get(self,request):
        testimonials = Testimonials.objects.all()
        data = []
        for testimonial in testimonials:
            data.append({
                'id': testimonial.id,
                'name': testimonial.name,
                'role': testimonial.role,
                'rating': testimonial.rating,
                'image': testimonial.get_image_url(),
                'content': testimonial.content,
                'created_at': testimonial.created_at,
                'updated_at': testimonial.updated_at
            })
        return Response({'testimonials': data}, status=status.HTTP_200_OK)
    
    def put(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            testimonial = get_object_or_404(Testimonials, id=id)
            testimonial.category = request.data.get('category', testimonial.category)
            testimonial.name = request.data.get('name', testimonial.name)
            testimonial.role = request.data.get('role', testimonial.role)
            testimonial.rating = request.data.get('rating', testimonial.rating)
            # Handle file upload for image
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                # Validate that image is a file, not a URL string
                if not hasattr(image_file, 'read'):
                    return Response({'error': 'Image must be a file upload, not a URL'}, status=status.HTTP_400_BAD_REQUEST)
                testimonial.image = image_file
            testimonial.content = request.data.get('content', testimonial.content)
            testimonial.save()
            return Response({
                'message':'Testimonial updated',
                'image_url': testimonial.get_image_url()
            },status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            testimonial = get_object_or_404(Testimonials, id=id)
            testimonial.delete()
            return Response({'message':'Testimonial deleted'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
class AboutusView(APIView):
    def post(self,request):
        title = request.data.get('title')
        image = request.FILES.get('image')  # Handle file upload
        content = request.data.get('content')
        
        # Validate that image is a file, not a URL string
        if image and not hasattr(image, 'read'):
            return Response({'error': 'Image must be a file upload, not a URL'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            aboutus = Aboutus.objects.create(title=title,image=image,content=content)
            return Response({
                'message':'Aboutus created',
                'aboutus_id': aboutus.id,
                'image_url': aboutus.get_image_url()
            },status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error':'About us creation failed due to database constraint'},status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
        
    def get(self,request):
        aboutus = Aboutus.objects.all()
        data = []
        for about in aboutus:
            data.append({
                'id': about.id,
                'title': about.title,
                'image': about.get_image_url(),
                'content': about.content,
                'created_at': about.created_at,
                'updated_at': about.updated_at
            })
        return Response({'aboutus': data}, status=status.HTTP_200_OK)
    
    def put(self, request, id=None):
        # Support both URL path parameter and query parameter
        
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        
        print("-------------id:", id)
        
        try:
            aboutus = Aboutus.objects.get(pk=id)
            aboutus.title = request.data.get('title', aboutus.title)
            aboutus.content = request.data.get('content', aboutus.content)
            aboutus.save()
            return Response({'message': 'Aboutus updated'}, status=status.HTTP_200_OK)
        except Aboutus.DoesNotExist:
            return Response({'error': 'Aboutus not found'}, status=status.HTTP_404_NOT_FOUND)
        
    
    def delete(self, request, id=None):
        # Support both URL path parameter and query parameter
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        
        if id is None:
            return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            aboutus = Aboutus.objects.get(pk=id)
            aboutus.delete()
            return Response({'message': 'Aboutus deleted'}, status=status.HTTP_200_OK)
        except Aboutus.DoesNotExist:
            return Response({'error': 'Aboutus not found'}, status=status.HTTP_404_NOT_FOUND)
    
class PlatformsView(APIView):
    def post(self,request):
        # name = request.data.get('name')
        content = request.data.get('content')
        TikTok = request.data.get('twitter')
        Instagram = request.data.get('instagram')
        Facebook = request.data.get('facebook')
        LinkedIn = request.data.get('pinterest')
        # image = request.data.get('image')
        try:
            platforms = Platforms.objects.create(content=content,TikTok=TikTok,Instagram=Instagram,Facebook=Facebook,LinkedIn=LinkedIn)
            return Response({'message':'Platforms created'},status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error':'Platforms creation failed due to database constraint'},status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
        
    def get(self,request):
        platforms = Platforms.objects.all()
        data = []
        for platform in platforms:
            data.append({
                'id': platform.id,
                'content': platform.content,
                'twitter': platform.TikTok,
                'instagram': platform.Instagram,
                'facebook': platform.Facebook,
                'pinterest': platform.LinkedIn,
                'created_at': platform.created_at,
                'updated_at': platform.updated_at
            })
        return Response({'platforms': data}, status=status.HTTP_200_OK)
    
    def put(self, request, id=None):
        # Support both URL path parameter and query parameter
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            platforms = Platforms.objects.get(pk=id)
            platforms.content = request.data.get('content', platforms.content)
            platforms.twitter = request.data.get('twitter', platforms.TikTok)
            platforms.instagram = request.data.get('instagram', platforms.Instagram)
            platforms.facebook = request.data.get('facebook', platforms.Facebook)
            platforms.pinterest = request.data.get('pinterest', platforms.LinkedIn)
            platforms.save()
            return Response({'message': 'Platforms updated'}, status=status.HTTP_200_OK)
        except Platforms.DoesNotExist:
            return Response({'error': 'Platform not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, id=None):
        # Support both URL path parameter and query parameter
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        
        if id is None:
            return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            platforms = Platforms.objects.get(pk=id)
            platforms.delete()
            return Response({'message': 'Platforms deleted'}, status=status.HTTP_200_OK)
        except Platforms.DoesNotExist:
            return Response({'error': 'Platform not found'}, status=status.HTTP_404_NOT_FOUND)
    
class InfoView(APIView):
    def post(self,request):
        office_address = request.data.get('office_address')
        call_us = request.data.get('call_us')
        working_hours = request.data.get('working_hours')
        partnership_and_support = request.data.get('partnership_and_support')
        try:
            info = Info.objects.create(office_address=office_address,call_us=call_us,working_hours=working_hours,partnership_and_support=partnership_and_support)
            return Response({'message':'Info created'},status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error':'Info creation failed due to database constraint'},status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
    def get(self,request):
        info = Info.objects.all()
        data = []
        for info_item in info:
            data.append({
                'id': info_item.id,
                'office_address': info_item.office_address,
                'call_us': info_item.call_us,
                'working_hours': info_item.working_hours,
                'partnership_and_support': info_item.partnership_and_support,
                'created_at': info_item.created_at,
                'updated_at': info_item.updated_at
            })
        return Response({'info': data}, status=status.HTTP_200_OK)
    
    def put(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            info = get_object_or_404(Info, id=id)
            info.office_address = request.data.get('office_address', info.office_address)
            info.call_us = request.data.get('call_us', info.call_us)
            info.working_hours = request.data.get('working_hours', info.working_hours)
            info.partnership_and_support = request.data.get('partnership_and_support', info.partnership_and_support)
            info.save()
            return Response({'message':'Info updated'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            info = get_object_or_404(Info, id=id)
            info.delete()
            return Response({'message':'Info deleted'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LeadershipView(APIView):
    permission_classes = []
    
    
    def get(self, request):
        """
        Get all active leadership members
        """
        def profile_picture(url):
            if url:
                return url.replace('https://https://', 'https://')
            return None
        
        try:
            leadership_members = Leadership.objects.filter(is_active=True)
            data = []
            
            for member in leadership_members:
                print("member", member)
                data.append({
                    'id': member.id,
                    'name': member.name,
                    'position': member.position,
                    'experience': member.experience,
                    'instagram_link': member.instagram_link,
                    'facebook_link': member.facebook_link,
                    'profile_picture_url': profile_picture(member.profile_picture.url) if member.profile_picture else None,
                    # 'profile_picture_url': profile_picture(member.profile_picture.url) if member.profile_picture else None,
                    # 'profile_picture': self.profile_picture(member.profile_picture.url) if member.profile_picture else None,
                    'bio': member.bio,
                    'order': member.order,
                    'created_at': member.created_at,
                    'updated_at': member.updated_at
                })
                # print("profile_picture_url", profile_picture(member.profile_picture.url))

            
            return Response({
                'success': True,
                'data': data,
                'count': len(data)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        print("id", id)
        try:
            leadership = get_object_or_404(Leadership, id=id)
            leadership.name = request.data.get('name', leadership.name)
            leadership.position = request.data.get('position', leadership.position)
            leadership.experience = request.data.get('experience', leadership.experience)
            leadership.instagram_link = request.data.get('instagram_link', leadership.instagram_link)
            leadership.facebook_link = request.data.get('facebook_link', leadership.facebook_link)
            leadership.profile_picture = request.FILES.get('profile_picture', leadership.profile_picture)
            leadership.bio = request.data.get('bio', leadership.bio)
            leadership.order = request.data.get('order', leadership.order)
            leadership.save()
            return Response({'message':'Leadership member updated'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)
        print("id", id)
        try:
            leadership = get_object_or_404(Leadership, id=id)
            leadership.delete()
            return Response({'message':'Leadership member deleted'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        print("id", id)
        try:
            leadership = get_object_or_404(Leadership, id=id)
            leadership.name = request.data.get('name', leadership.name)
            leadership.position = request.data.get('position', leadership.position)
            leadership.experience = request.data.get('experience', leadership.experience)
            leadership.instagram_link = request.data.get('instagram_link', leadership.instagram_link)
            leadership.facebook_link = request.data.get('facebook_link', leadership.facebook_link)
            leadership.profile_picture = request.FILES.get('profile_picture', leadership.profile_picture)
            leadership.bio = request.data.get('bio', leadership.bio)
            leadership.order = request.data.get('order', leadership.order)
            leadership.save()
            return Response({'message':'Leadership member updated'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        """
        Create a new leadership member (Admin only)
        """
        try:
            name = request.data.get('name')
            position = request.data.get('position')
            experience = request.data.get('experience')
            instagram_link = request.data.get('instagram_link')
            profile_picture = request.FILES.get('profile_picture')
            facebook_link = request.data.get('facebook_link')
            bio = request.data.get('bio')
            order = request.data.get('order', 0)
            
            if not name or not position:
                return Response({
                    'success': False,
                    'error': 'Name and position are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            leadership = Leadership.objects.create(
                name=name,
                position=position,
                experience=experience or '',
                instagram_link=instagram_link,
                facebook_link=facebook_link,
                profile_picture=profile_picture,
                bio=bio,
                order=order
            )
            
            return Response({
                'success': True,
                'message': 'Leadership member created successfully',
                'data': {
                    'id': leadership.id,
                    'name': leadership.name,
                    'position': leadership.position,
                    'experience': leadership.experience,
                    'instagram_link': leadership.instagram_link,
                    'facebook_link': leadership.facebook_link,
                    'profile_picture': leadership.profile_picture.url if leadership.profile_picture else None,
                    'bio': leadership.bio,
                    'order': leadership.order
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RelatedPostsView(APIView):
    def get(self,request):
        category = request.query_params.get('category')
        blogs = relatedposts.objects.all()
        if not blogs:
            return Response({'message': 'No blogs found'}, status=status.HTTP_200_OK)
        data = []
        for blog in blogs:
            data.append({
                'id': blog.id,
                'title': blog.title,
                'image': blog.get_image_url(),  # Changed from blog.image.url
                'description_1': blog.description_1,
                'description_2': blog.description_2,
                'quote': blog.quote,
                'author': blog.author,
                'date': blog.date,
                'time_to_read': blog.time_to_read,
                'category': blog.category,
                'created_at': blog.created_at,
                'updated_at': blog.updated_at
            })
        return Response({'related_posts': data}, status=status.HTTP_200_OK)
    
    def post(self,request):
        title = request.data.get('title')
        image = request.FILES.get('image')
        description_1 = request.data.get('description_1')
        description_2 = request.data.get('description_2')
        quote = request.data.get('quote')
        author = request.data.get('author')
        date = request.data.get('date')
        time_to_read = request.data.get('time_to_read')
        category = request.data.get('category')
        if not title or not image or not time_to_read or not description_1 or not description_2 or not quote or not author or not date or not category:
            return Response({'error':'All fields are required'},status=status.HTTP_400_BAD_REQUEST)
        related_post = relatedposts.objects.create(title=title,image=image,description_1=description_1,description_2=description_2,quote=quote,author=author,date=date,time_to_read=time_to_read,category=category)
        return Response({'message':'Related posts created',
            'relatedposts_id': related_post.id,
            'image_url': related_post.get_image_url()
        },status=status.HTTP_201_CREATED)
    
    def put(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            related_post = get_object_or_404(relatedposts, id=id)
            related_post.title = request.data.get('title', related_post.title)
            related_post.image = request.FILES.get('image', related_post.image)
            related_post.description_1 = request.data.get('description_1', related_post.description_1)
            related_post.description_2 = request.data.get('description_2', related_post.description_2)
            related_post.quote = request.data.get('quote', related_post.quote)
            related_post.author = request.data.get('author', related_post.author)
            related_post.date = request.data.get('date', related_post.date)
            related_post.time_to_read = request.data.get('time_to_read', related_post.time_to_read)
            related_post.category = request.data.get('category', related_post.category)
            related_post.save()
            return Response({'message':'Related posts updated',
                'image_url': related_post.get_image_url()
            },status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            related_post = get_object_or_404(relatedposts, id=id)
            related_post.delete()
            return Response({'message':'Related posts deleted'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DownloadPDFView(APIView):
    def get(self,request):
        downloadpdf = WebsiteDownloadPDF.objects.all()
        data = []
        for pdf in downloadpdf:
            data.append({
                'id': pdf.id,
                'email': pdf.email,
                'name': pdf.name,
                'pdf_url': pdf.pdf.url if getattr(pdf, 'pdf', None) else None,
                'created_at': pdf.created_at,
                'updated_at': pdf.updated_at
            })
        return Response({'downloadpdf': data},status=status.HTTP_200_OK)
    def post(self,request):
        email = request.data.get('email')
        name = request.data.get('name')
        # pdf = request.FILES.get('pdf') if request.FILES.get('pdf') else None
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        downloadpdf = WebsiteDownloadPDF.objects.create(email=email,name=name)
        # Here you can add logic to handle the email (e.g., store it, trigger PDF download, etc.)
        return Response({'message' : 'PDF is downloading shortly',
            'downloadpdf_id': downloadpdf.id,
            # 'pdf_url': downloadpdf.pdf.url if downloadpdf.pdf else None
        },status=status.HTTP_200_OK)

class VideoView(APIView):
    def get(self,request):
        videos = Video.objects.all()
        data = []
        for video in videos:
            def replace_https_https(url):
                if url:
                    # Handle both https://https:// and https//https:// patterns
                    url = url.replace('https://https://', 'https://')
                    url = url.replace('https//https://', 'https://')
                    return url
                return None
            video_url = replace_https_https(video.video.url if video.video else None)
            data.append({
                'id': video.id,
                'title': video.title,
                'video': video_url,
                'created_at': video.created_at,
                'updated_at': video.updated_at
            })
        return Response({'video': data},status=status.HTTP_200_OK)
    def post(self,request):
        title = request.data.get('title')
        video = request.FILES.get('video') if request.FILES.get('video') else None
        if not title:
            return Response({'error': 'Title is required'}, status=status.HTTP_400_BAD_REQUEST)
        video_obj = Video.objects.create(title=title,video=video)
        def replace_https_https(url):
            if url:
                # Handle both https://https:// and https//https:// patterns
                url = url.replace('https://https://', 'https://')
                url = url.replace('https//https://', 'https://')
                return url
            return None
        video_url = replace_https_https(video_obj.video.url if video_obj.video else None)
        
        return Response({'message':'Video created',
            'video_id': video_obj.id,
            'video_url': video_url
        },status=status.HTTP_200_OK)

    def put(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            video = get_object_or_404(Video, id=id)
            video.title = request.data.get('title', video.title)
            video.video = request.FILES.get('video', video.video)
            video.save()
            return Response({'message':'Video updated',
                'video_url': video.video.url
            },status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,id=None):
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')


class DownloadRequestView(APIView):
    """
    API to request data export
    """
    permission_classes = []
    
    def post(self, request):
        """Request data export"""
        # serializer = DownloadRequestSerializer(data=request.data)
        name = request.data.get('name')
        email = request.data.get('email')
        if not name or not email:
            return Response({'error': 'Name and email are required'}, status=status.HTTP_400_BAD_REQUEST)
        DataDownloadRequest.objects.create(name=name, email=email)
        return Response({'message': 'Download request created successfully'}, status=status.HTTP_200_OK)

    def get(self, request):
        downloadrequest = DataDownloadRequest.objects.all()
        data = []
        for download_req in downloadrequest:
            data.append({
                'id': download_req.id,
                'name': download_req.name,
                'email': download_req.email,
                'created_at': download_req.created_at,
                'updated_at': download_req.updated_at
            })
        return Response({'downloadrequest': data}, status=status.HTTP_200_OK)