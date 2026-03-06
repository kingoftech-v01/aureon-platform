"""
API views for the marketing website React frontend.
These endpoints provide JSON data for the Plax React template.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import json

from .models import (
    BlogPost, BlogCategory, BlogTag, Service,
    Testimonial, FAQ, CaseStudy, CaseStudyCategory,
    SiteSettings, TeamMember, NewsletterSubscriber, ContactSubmission
)


def api_response(data, status=200):
    """Helper to create consistent API responses"""
    wrapped = {'data': data, 'status': 'success'} if status == 200 else {'error': data, 'status': 'error'}
    response = JsonResponse(wrapped, safe=False, status=status)
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@require_GET
def api_site_settings(request):
    """Get site-wide settings like contact info, social links"""
    settings_obj = SiteSettings.get_settings()
    data = {
        'site_name': settings_obj.company_name if settings_obj else 'Aureon',
        'site_tagline': settings_obj.tagline if settings_obj else 'Financial Automation Platform',
        'contact_email': settings_obj.contact_email if settings_obj else 'support@aureon.io',
        'contact_phone': settings_obj.phone if settings_obj else '+1 (555) 123-4567',
        'address': settings_obj.address if settings_obj else 'Rhematek Solutions, Tech City',
        'twitter_url': settings_obj.twitter_url if settings_obj else '',
        'linkedin_url': settings_obj.linkedin_url if settings_obj else '',
        'github_url': settings_obj.github_url if settings_obj else '',
        'facebook_url': settings_obj.facebook_url if settings_obj else '',
    }
    return api_response(data)


@require_GET
def api_services(request):
    """Get all active services"""
    services = Service.objects.filter(is_active=True).order_by('order')
    data = [{
        'id': s.id,
        'name': s.name,
        'slug': s.slug,
        'short_description': s.short_description,
        'description': s.description,
        'icon': s.icon.url if s.icon else None,
        'image': s.image.url if s.image else None,
        'features': s.features if hasattr(s, 'features') else [],
    } for s in services]
    return api_response(data)


@require_GET
def api_service_detail(request, slug):
    """Get single service by slug"""
    try:
        s = Service.objects.get(slug=slug, is_active=True)
        data = {
            'id': s.id,
            'name': s.name,
            'slug': s.slug,
            'short_description': s.short_description,
            'description': s.description,
            'icon': s.icon.url if s.icon else None,
            'image': s.image.url if s.image else None,
            'features': s.features if hasattr(s, 'features') else [],
        }
        return api_response(data)
    except Service.DoesNotExist:
        return api_response({'error': 'Service not found'}, status=404)


@require_GET
def api_pricing(request):
    """Get pricing plans - static for now, can be made dynamic"""
    data = [
        {
            'id': 1,
            'name': 'Starter',
            'description': 'Perfect for freelancers',
            'price_monthly': 0,
            'price_yearly': 0,
            'popular': False,
            'features': [
                '5 contracts/month',
                '3 clients',
                'Basic invoicing',
                'Email support',
            ],
            'limitations': [
                'No e-signatures',
                'No payment processing',
            ],
            'cta': 'Get Started Free',
            'cta_url': '/register/',
        },
        {
            'id': 2,
            'name': 'Pro',
            'description': 'For growing businesses',
            'price_monthly': 49,
            'price_yearly': 490,
            'popular': True,
            'features': [
                'Unlimited contracts',
                'Unlimited clients',
                'E-signatures',
                'Stripe payments',
                'Priority support',
            ],
            'limitations': [],
            'cta': 'Start Free Trial',
            'stripe_price_monthly': 'price_pro_monthly',
            'stripe_price_yearly': 'price_pro_yearly',
        },
        {
            'id': 3,
            'name': 'Business',
            'description': 'For agencies & teams',
            'price_monthly': 149,
            'price_yearly': 1490,
            'popular': False,
            'features': [
                'Everything in Pro',
                'Multi-user access',
                'Custom branding',
                'API access',
                'Dedicated support',
                'Analytics dashboard',
            ],
            'limitations': [],
            'cta': 'Start Free Trial',
            'stripe_price_monthly': 'price_business_monthly',
            'stripe_price_yearly': 'price_business_yearly',
        },
        {
            'id': 4,
            'name': 'Enterprise',
            'description': 'Custom solutions',
            'price_monthly': None,
            'price_yearly': None,
            'popular': False,
            'features': [
                'Everything in Business',
                'Custom integrations',
                'SLA guarantee',
                'On-premise option',
                'Training & onboarding',
            ],
            'limitations': [],
            'cta': 'Contact Sales',
            'cta_url': '/contact/',
        },
    ]
    return api_response(data)


@require_GET
def api_testimonials(request):
    """Get active testimonials"""
    testimonials = Testimonial.objects.filter(is_active=True).order_by('order')[:10]
    data = [{
        'id': t.id,
        'content': t.content,
        'client_name': t.client_name,
        'client_role': t.client_role,
        'client_company': t.client_company,
        'client_photo': t.client_photo.url if t.client_photo else None,
        'rating': t.rating,
    } for t in testimonials]
    return api_response(data)


@require_GET
def api_faqs(request):
    """Get FAQs grouped by category"""
    faqs = FAQ.objects.filter(is_active=True).order_by('order')

    # Group by category
    categories = {}
    for faq in faqs:
        cat = faq.category or 'general'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            'id': faq.id,
            'question': faq.question,
            'answer': faq.answer,
        })

    data = {
        'categories': categories,
        'all': [{
            'id': f.id,
            'question': f.question,
            'answer': f.answer,
            'category': f.category or 'general',
        } for f in faqs]
    }
    return api_response(data)


@require_GET
def api_blog_posts(request):
    """Get published blog posts"""
    posts = BlogPost.objects.filter(status='published').order_by('-published_at')[:20]
    data = [{
        'id': p.id,
        'title': p.title,
        'slug': p.slug,
        'excerpt': p.excerpt,
        'featured_image': p.featured_image.url if p.featured_image else None,
        'category': {
            'name': p.category.name,
            'slug': p.category.slug,
        } if p.category else None,
        'author': p.author.get_full_name() if p.author else 'Aureon Team',
        'published_at': p.published_at.isoformat() if p.published_at else None,
        'read_time': p.read_time if hasattr(p, 'read_time') else 5,
        'views': p.views if hasattr(p, 'views') else 0,
        'featured': p.featured,
    } for p in posts]
    return api_response(data)


@require_GET
def api_blog_post_detail(request, slug):
    """Get single blog post by slug"""
    try:
        p = BlogPost.objects.get(slug=slug, status='published')
        data = {
            'id': p.id,
            'title': p.title,
            'slug': p.slug,
            'content': p.content,
            'excerpt': p.excerpt,
            'featured_image': p.featured_image.url if p.featured_image else None,
            'category': {
                'name': p.category.name,
                'slug': p.category.slug,
            } if p.category else None,
            'tags': [{'name': t.name, 'slug': t.slug} for t in p.tags.all()],
            'author': p.author.get_full_name() if p.author else 'Aureon Team',
            'published_at': p.published_at.isoformat() if p.published_at else None,
            'read_time': p.read_time if hasattr(p, 'read_time') else 5,
        }
        return api_response(data)
    except BlogPost.DoesNotExist:
        return api_response({'error': 'Post not found'}, status=404)


@require_GET
def api_blog_categories(request):
    """Get blog categories with post counts"""
    categories = BlogCategory.objects.annotate(
        post_count=models.Count('posts', filter=models.Q(posts__status='published'))
    ).order_by('name')
    data = [{
        'id': c.id,
        'name': c.name,
        'slug': c.slug,
        'post_count': c.post_count,
    } for c in categories]
    return api_response(data)


@require_GET
def api_case_studies(request):
    """Get published case studies"""
    studies = CaseStudy.objects.filter(status='published').order_by('-published_at')[:10]
    data = [{
        'id': s.id,
        'title': s.title,
        'slug': s.slug,
        'excerpt': s.excerpt,
        'featured_image': s.featured_image.url if s.featured_image else None,
        'client_name': s.client_name,
        'client_industry': s.client_industry,
        'results': s.results if hasattr(s, 'results') else [],
        'featured': s.is_featured,
    } for s in studies]
    return api_response(data)


@require_GET
def api_case_study_detail(request, slug):
    """Get single case study by slug"""
    try:
        s = CaseStudy.objects.get(slug=slug, status='published')
        data = {
            'id': s.id,
            'title': s.title,
            'slug': s.slug,
            'content': s.content,
            'excerpt': s.excerpt,
            'featured_image': s.featured_image.url if s.featured_image else None,
            'client_name': s.client_name,
            'client_industry': s.client_industry,
            'challenge': s.challenge if hasattr(s, 'challenge') else '',
            'solution': s.solution if hasattr(s, 'solution') else '',
            'results': s.results if hasattr(s, 'results') else [],
            'testimonial': s.testimonial if hasattr(s, 'testimonial') else '',
        }
        return api_response(data)
    except CaseStudy.DoesNotExist:
        return api_response({'error': 'Case study not found'}, status=404)


@require_GET
def api_team(request):
    """Get team members"""
    members = TeamMember.objects.filter(is_active=True).order_by('order')
    data = [{
        'id': m.id,
        'name': m.name,
        'position': m.position,
        'bio': m.bio,
        'photo': m.photo.url if m.photo else None,
        'linkedin': m.linkedin,
        'twitter': m.twitter,
        'is_leadership': m.is_leadership,
    } for m in members]
    return api_response(data)


@csrf_exempt
@require_POST
def api_contact(request):
    """Handle contact form submission"""
    try:
        data = json.loads(request.body)

        # Validate required fields
        required = ['name', 'email', 'message']
        for field in required:
            if not data.get(field):
                return api_response({'error': f'{field} is required'}, status=400)

        # Save to database
        submission = ContactSubmission.objects.create(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', ''),
            company=data.get('company', ''),
            subject=data.get('subject', 'General Inquiry'),
            message=data['message'],
        )

        # Send email notification
        try:
            send_mail(
                subject=f"New Contact Form: {data.get('subject', 'General Inquiry')}",
                message=f"Name: {data['name']}\nEmail: {data['email']}\nPhone: {data.get('phone', 'N/A')}\nCompany: {data.get('company', 'N/A')}\n\nMessage:\n{data['message']}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL or 'support@aureon.io'],
                fail_silently=True,
            )
        except Exception as e:
            pass  # Don't fail the request if email fails

        return api_response({'success': True, 'message': 'Thank you for your message. We will get back to you soon.'})
    except json.JSONDecodeError:
        return api_response({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return api_response({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def api_newsletter(request):
    """Handle newsletter subscription"""
    try:
        data = json.loads(request.body)
        email = data.get('email')

        if not email:
            return api_response({'error': 'Email is required'}, status=400)

        # Check if already subscribed
        if NewsletterSubscriber.objects.filter(email=email).exists():
            return api_response({'success': True, 'message': 'You are already subscribed!'})

        # Create subscription
        from django.utils import timezone as tz
        NewsletterSubscriber.objects.create(email=email, confirmed_at=tz.now())

        return api_response({'success': True, 'message': 'Thank you for subscribing!'})
    except json.JSONDecodeError:
        return api_response({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return api_response({'error': str(e)}, status=500)


# Import models for annotations
from django.db import models
