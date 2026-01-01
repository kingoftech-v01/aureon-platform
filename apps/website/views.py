"""
Website views for Aureon SaaS Platform.

All frontend rendering is now handled by React/Next.js.
These views now serve the React SPA or provide API endpoints.
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

from config.views import serve_react_app

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_LIVE_SECRET_KEY', '') or getattr(settings, 'STRIPE_TEST_SECRET_KEY', '')


class ReactPageView(View):
    """Base view that serves React SPA for all page routes."""

    def get(self, request, *args, **kwargs):
        return serve_react_app(request)


# All page views now serve React SPA
class HomeView(ReactPageView):
    """Homepage - served by React/Next.js"""
    pass


class AboutView(ReactPageView):
    """About page - served by React/Next.js"""
    pass


class TeamView(ReactPageView):
    """Team page - served by React/Next.js"""
    pass


class ServicesView(ReactPageView):
    """Services page - served by React/Next.js"""
    pass


class ServiceDetailView(ReactPageView):
    """Service detail page - served by React/Next.js"""
    pass


class PricingView(ReactPageView):
    """Pricing page - served by React/Next.js"""
    pass


class ContactView(ReactPageView):
    """Contact page - served by React/Next.js"""
    pass


class ContactSuccessView(ReactPageView):
    """Contact success page - served by React/Next.js"""
    pass


class BlogListView(ReactPageView):
    """Blog listing - served by React/Next.js"""
    pass


class BlogDetailView(ReactPageView):
    """Blog post detail - served by React/Next.js"""
    pass


class BlogCategoryView(ReactPageView):
    """Blog category - served by React/Next.js"""
    pass


class BlogTagView(ReactPageView):
    """Blog tag - served by React/Next.js"""
    pass


class ProductListView(ReactPageView):
    """Products listing - served by React/Next.js"""
    pass


class ProductDetailView(ReactPageView):
    """Product detail - served by React/Next.js"""
    pass


class FAQView(ReactPageView):
    """FAQ page - served by React/Next.js"""
    pass


class PrivacyPolicyView(ReactPageView):
    """Privacy policy - served by React/Next.js"""
    pass


class TermsOfServiceView(ReactPageView):
    """Terms of service - served by React/Next.js"""
    pass


class CaseStudyListView(ReactPageView):
    """Case studies listing - served by React/Next.js"""
    pass


class CaseStudyDetailView(ReactPageView):
    """Case study detail - served by React/Next.js"""
    pass


class CaseStudyCategoryView(ReactPageView):
    """Case study category - served by React/Next.js"""
    pass


class PaymentSuccessView(ReactPageView):
    """Payment success - served by React/Next.js"""
    pass


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
