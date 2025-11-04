from django.shortcuts import render, get_object_or_404
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from .models import DownloadPDF, Stayconnected, Contact, TermsandConditions, PrivacyPolicy, Blogs, Faqs, Testimonials, Aboutus, Platforms, Info,Leadership, Video, relatedposts, DownloadPDF
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import ModelSerializer
from foodinfo.models import DownloadRequest,DownloadPDF
from bs4 import BeautifulSoup
import re

# Create your views here.

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
    
    def post(self,request):
        from bs4 import BeautifulSoup
        
        title = request.data.get('title')
        image = request.FILES.get('image')  # Handle file upload
        description_1 = request.data.get('description_1')
        description_2 = request.data.get('description_2')
        quote = request.data.get('quote')
        author = request.data.get('author')
        date = request.data.get('date')
        time_to_read = request.data.get('time_to_read')
        category = request.data.get('category')
        
        # Convert HTML to markdown format (preserves formatting without HTML tags)
        if description_1:
            description_1 = self._html_to_markdown(description_1)
        if description_2:
            description_2 = self._html_to_markdown(description_2)
        if quote:
            quote = self._html_to_markdown(quote)
        # Validate that image is a file, not a URL string
        if image and not hasattr(image, 'read'):
            return Response({'error': 'Image must be a file upload, not a URL'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            blog = Blogs.objects.create(title=title,image=image,description_1=description_1,description_2=description_2,quote=quote,author=author,date=date,time_to_read=time_to_read,category=category)
            return Response({
                'message':'Blog created',
                'blog_id': blog.id,
                'image_url': blog.get_image_url()
            },status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error':'Blog creation failed due to database constraint'},status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
        

    def get(self,request,id=None):
        # If blog id is provided (from path or query), return single blog
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id:
            try:
                blog = get_object_or_404(Blogs, id=id)
                data = {
                    'id': blog.id,
                    'title': blog.title,
                    'image': blog.get_image_url(),
                    'description_1': blog.description_1,
                    'description_2': blog.description_2,
                    'quote': blog.quote,
                    'author': blog.author,
                    'date': blog.date,
                    'time_to_read': blog.time_to_read,
                    'category': blog.category,
                    'created_at': blog.created_at,
                    'updated_at': blog.updated_at
                }
                return Response({'blog': data}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # List endpoint with optional category filter
        category = request.query_params.get('category')
        blogs = Blogs.objects.all()
        if category:
            blogs = blogs.filter(category=category)

        # Category counts
        category_counts = {}
        all_categories = Blogs.objects.values_list('category', flat=True).distinct()
        for cat in all_categories:
            category_counts[cat] = Blogs.objects.filter(category=cat).count()

        data = []
        for blog in blogs:
            data.append({
                'id': blog.id,
                'title': blog.title,
                'image': blog.get_image_url(),
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

        return Response({
            'blogs': data,
            'category_counts': category_counts,
            'total_blogs': len(data),
            'filtered_category': category if category else None
        }, status=status.HTTP_200_OK)

    def put(self,request,id=None):
        from bs4 import BeautifulSoup
        
        if id is None:
            id = request.query_params.get('pk') or request.query_params.get('id')
        if id is None:
            return Response({'error': 'ID is required for update'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            blog = get_object_or_404(Blogs, id=id)
            blog.title = request.data.get('title', blog.title)
            # Handle file upload for image
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                # Validate that image is a file, not a URL string
                if not hasattr(image_file, 'read'):
                    return Response({'error': 'Image must be a file upload, not a URL'}, status=status.HTTP_400_BAD_REQUEST)
                blog.image = image_file
            
            # Convert HTML to markdown format before saving
            description_1 = request.data.get('description_1', blog.description_1)
            if description_1:
                description_1 = self._html_to_markdown(description_1)
            blog.description_1 = description_1
            
            description_2 = request.data.get('description_2', blog.description_2)
            if description_2:
                description_2 = self._html_to_markdown(description_2)
            blog.description_2 = description_2
            
            quote = request.data.get('quote', blog.quote)
            if quote:
                quote = self._html_to_markdown(quote)
            blog.quote = quote
            blog.author = request.data.get('author', blog.author)
            blog.date = request.data.get('date', blog.date)
            blog.time_to_read = request.data.get('time_to_read', blog.time_to_read)
            blog.category = request.data.get('category', blog.category)
            blog.save()
            return Response({
                'message':'Blog updated',
                'image_url': blog.get_image_url()
            },status=status.HTTP_200_OK)
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
        downloadpdf = DownloadPDF.objects.all()
        data = []
        for pdf in downloadpdf:
            data.append({
                'id': pdf.id,
                'email': pdf.email,
                'name': pdf.name,
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
        downloadpdf = DownloadPDF.objects.create(email=email,name=name)
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
        downloadpdf = DownloadPDF.objects.create(name=name, email=email)
        return Response({'message': 'Download request created successfully'}, status=status.HTTP_200_OK)

    def get(self, request):
        downloadrequest = DownloadPDF.objects.all()
        print("downloadrequest", downloadrequest)
        data = []
        for download_req in downloadrequest:
            print("download_req", download_req)
            data.append({
                'id': download_req.id,
                'name': download_req.name,
                'email': download_req.email,
                'created_at': download_req.created_at,
                'updated_at': download_req.updated_at
            })
        return Response({'downloadrequest': data}, status=status.HTTP_200_OK)