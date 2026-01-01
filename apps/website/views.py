"""
Website views for Aureon SaaS Platform.

All frontend rendering is now handled by Next.js (marketing) or React (dashboard).
Marketing pages are served from Next.js static export.
"""
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.http import require_POST
import stripe
import json

from .models import (
    BlogPost, BlogCategory, BlogTag, Product,
    ContactSubmission, NewsletterSubscriber, SiteSettings,
    CaseStudyCategory, CaseStudy, Service, TeamMember, FAQ, Testimonial
)
from .forms import ContactForm, NewsletterForm

from config.views import serve_marketing_site

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_LIVE_SECRET_KEY', '') or getattr(settings, 'STRIPE_TEST_SECRET_KEY', '')


class MarketingPageView(View):
    """Base view that serves Next.js marketing site for all public pages."""
    page_path = ''  # Override in subclasses for specific routes

    def get(self, request, *args, **kwargs):
        # Get the path from the URL or use the class-defined path
        path = kwargs.get('slug', '') or kwargs.get('path', '') or self.page_path
        return serve_marketing_site(request, path)


# All marketing page views now serve Next.js static export
class HomeView(MarketingPageView):
    """Homepage - served by Next.js"""
    page_path = ''


class AboutView(MarketingPageView):
    """About page - served by Next.js"""
    page_path = 'about'


class TeamView(MarketingPageView):
    """Team page - served by Next.js"""
    page_path = 'team'


class ServicesView(MarketingPageView):
    """Services page - served by Next.js"""
    page_path = 'services'


class ServiceDetailView(MarketingPageView):
    """Service detail page - served by Next.js"""

    def get(self, request, slug=''):
        return serve_marketing_site(request, f'services/{slug}')


class PricingView(MarketingPageView):
    """Pricing page - served by Next.js"""
    page_path = 'pricing'


class ContactView(MarketingPageView):
    """Contact page - served by Next.js"""
    page_path = 'contact'


class ContactSuccessView(MarketingPageView):
    """Contact success page - served by Next.js"""
    page_path = 'contact/success'


class BlogListView(MarketingPageView):
    """Blog listing - served by Next.js"""
    page_path = 'blog'


class BlogDetailView(MarketingPageView):
    """Blog post detail - served by Next.js"""

    def get(self, request, slug=''):
        return serve_marketing_site(request, f'blog/{slug}')


class BlogCategoryView(MarketingPageView):
    """Blog category - served by Next.js"""

    def get(self, request, slug=''):
        return serve_marketing_site(request, f'blog/category/{slug}')


class BlogTagView(MarketingPageView):
    """Blog tag - served by Next.js"""

    def get(self, request, slug=''):
        return serve_marketing_site(request, f'blog/tag/{slug}')


class ProductListView(MarketingPageView):
    """Products listing - served by Next.js"""
    page_path = 'products'


class ProductDetailView(MarketingPageView):
    """Product detail - served by Next.js"""

    def get(self, request, slug=''):
        return serve_marketing_site(request, f'products/{slug}')


class FAQView(MarketingPageView):
    """FAQ page - served by Next.js"""
    page_path = 'faq'


class PrivacyPolicyView(MarketingPageView):
    """Privacy policy - served by Next.js"""
    page_path = 'privacy-policy'


class TermsOfServiceView(MarketingPageView):
    """Terms of service - served by Next.js"""
    page_path = 'terms-of-service'


class CaseStudyListView(MarketingPageView):
    """Case studies listing - served by Next.js"""
    page_path = 'case-studies'


class CaseStudyDetailView(MarketingPageView):
    """Case study detail - served by Next.js"""

    def get(self, request, slug=''):
        return serve_marketing_site(request, f'case-studies/{slug}')


class CaseStudyCategoryView(MarketingPageView):
    """Case study category - served by Next.js"""

    def get(self, request, slug=''):
        return serve_marketing_site(request, f'case-studies/category/{slug}')


class PaymentSuccessView(MarketingPageView):
    """Payment success - served by Next.js"""
    page_path = 'payment/success'


class LoginView(MarketingPageView):
    """Login page - served by Next.js"""
    page_path = 'login'


class SignupView(MarketingPageView):
    """Signup page - served by Next.js"""
    page_path = 'signup'


# ============================================================
# API/FORM HANDLING VIEWS (These still work server-side)
# ============================================================

@require_POST
def contact_submit(request):
    """Handle contact form submission via AJAX"""
    try:
        data = json.loads(request.body)
        form = ContactForm(data)

        if form.is_valid():
            contact = form.save(commit=False)

            # Capture metadata
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                contact.ip_address = x_forwarded_for.split(',')[0]
            else:
                contact.ip_address = request.META.get('REMOTE_ADDR')
            contact.user_agent = request.META.get('HTTP_USER_AGENT', '')
            contact.referrer = request.META.get('HTTP_REFERER', '')

            contact.save()

            # Send notification email to admin
            send_contact_notification(contact)

            # Send confirmation email to user
            send_contact_confirmation(contact)

            return JsonResponse({
                'success': True,
                'message': 'Thank you for contacting us! We\'ll get back to you within 24 hours.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def send_contact_notification(contact):
    """Send notification to admin"""
    subject = f'New Contact Form Submission: {contact.subject}'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [SiteSettings.get_settings().contact_email]

    html_content = render_to_string('website/emails/contact_notification.html', {
        'contact': contact,
    })

    msg = EmailMultiAlternatives(subject, '', from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_contact_confirmation(contact):
    """Send confirmation to user"""
    subject = 'Thank you for contacting Aureon'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [contact.email]

    html_content = render_to_string('website/emails/contact_confirmation.html', {
        'contact': contact,
        'site_settings': SiteSettings.get_settings(),
    })

    msg = EmailMultiAlternatives(subject, '', from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


@require_POST
def newsletter_subscribe(request):
    """Handle newsletter subscription via AJAX"""
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        form = NewsletterForm(data)

        if form.is_valid():
            subscriber = form.save(commit=False)

            # Capture metadata
            subscriber.source = data.get('source', 'website')
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                subscriber.ip_address = x_forwarded_for.split(',')[0]
            else:
                subscriber.ip_address = request.META.get('REMOTE_ADDR')

            subscriber.save()

            # Send confirmation email
            send_newsletter_confirmation(subscriber)

            return JsonResponse({
                'success': True,
                'message': 'Thank you for subscribing! Please check your email to confirm your subscription.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def send_newsletter_confirmation(subscriber):
    """Send newsletter confirmation email"""
    subject = 'Confirm your newsletter subscription'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [subscriber.email]

    confirmation_url = settings.SITE_URL + reverse('website:newsletter_confirm',
                                                   kwargs={'token': subscriber.confirmation_token})

    html_content = render_to_string('website/emails/newsletter_confirmation.html', {
        'subscriber': subscriber,
        'confirmation_url': confirmation_url,
        'site_settings': SiteSettings.get_settings(),
    })

    msg = EmailMultiAlternatives(subject, '', from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def newsletter_confirm(request, token):
    """Confirm newsletter subscription"""
    subscriber = get_object_or_404(NewsletterSubscriber, confirmation_token=token)
    subscriber.confirm_subscription()

    messages.success(request, 'Your subscription has been confirmed! Thank you for subscribing.')
    return redirect('/')


def newsletter_unsubscribe(request, token):
    """Unsubscribe from newsletter"""
    subscriber = get_object_or_404(NewsletterSubscriber, confirmation_token=token)
    subscriber.unsubscribe()

    messages.info(request, 'You have been unsubscribed from our newsletter.')
    return redirect('/')


@require_POST
def create_checkout_session(request):
    """Create Stripe Checkout session for subscription"""
    try:
        data = json.loads(request.body)
        price_id = data.get('price_id')

        if not price_id:
            return JsonResponse({'error': 'Price ID is required'}, status=400)

        # Create Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.build_absolute_uri('/payment-success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/pricing'),
            customer_email=request.user.email if request.user.is_authenticated else None,
        )

        return JsonResponse({
            'sessionId': checkout_session.id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
