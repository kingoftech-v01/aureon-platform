from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import stripe
import json

from .models import (
    BlogPost, BlogCategory, BlogTag, Product,
    ContactSubmission, NewsletterSubscriber, SiteSettings,
    CaseStudyCategory, CaseStudy, Service, TeamMember, FAQ, Testimonial
)
from .forms import ContactForm, NewsletterForm, SalesInquiryForm, QuickContactForm

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_LIVE_SECRET_KEY', '') or getattr(settings, 'STRIPE_TEST_SECRET_KEY', '')


# Homepage View
class HomeView(TemplateView):
    """Homepage with hero, features, testimonials, and CTA sections"""
    template_name = 'website/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['featured_posts'] = BlogPost.objects.filter(
            status='published',
            featured=True
        )[:3]
        context['featured_products'] = Product.objects.filter(
            is_active=True,
            is_featured=True
        )[:3]
        context['services'] = Service.objects.filter(is_active=True).order_by('order')[:6]
        context['testimonials'] = Testimonial.objects.filter(is_active=True, is_featured=True).order_by('order')[:6]
        context['case_studies'] = CaseStudy.objects.filter(status='published', is_featured=True).order_by('-published_at')[:3]
        context['team_members'] = TeamMember.objects.filter(is_active=True, is_leadership=True).order_by('order')[:4]
        return context


# About Page
class AboutView(TemplateView):
    """About Us page with company story, mission, values"""
    template_name = 'website/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['page_title'] = 'About Aureon'
        context['meta_description'] = 'Learn about Aureon by Rhematek Solutions - automating business workflows for growth.'
        context['team_members'] = TeamMember.objects.filter(is_active=True).order_by('order')
        context['testimonials'] = Testimonial.objects.filter(is_active=True).order_by('order')[:6]
        return context


# Team Page
class TeamView(TemplateView):
    """Team page with team members"""
    template_name = 'website/team.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['page_title'] = 'Our Team'
        context['meta_description'] = 'Meet the team behind Aureon - experts in SaaS, automation, and business growth.'
        context['leadership'] = TeamMember.objects.filter(is_active=True, is_leadership=True).order_by('order')
        context['team_members'] = TeamMember.objects.filter(is_active=True, is_leadership=False).order_by('order')
        return context


# Services Page
class ServicesView(TemplateView):
    """Services overview page"""
    template_name = 'website/services.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['page_title'] = 'Our Services'
        context['meta_description'] = 'Comprehensive SaaS solutions for contract management, invoicing, payments, and more.'
        context['services'] = Service.objects.filter(is_active=True).order_by('order')
        context['testimonials'] = Testimonial.objects.filter(is_active=True, is_featured=True).order_by('order')[:3]
        return context


# Service Detail Page
class ServiceDetailView(DetailView):
    """Individual service detail page"""
    model = Service
    template_name = 'website/service-detail.html'
    context_object_name = 'service'
    slug_field = 'slug'

    def get_queryset(self):
        return Service.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        service = self.get_object()
        context['page_title'] = service.meta_title or service.name
        context['meta_description'] = service.meta_description or service.short_description
        context['other_services'] = Service.objects.filter(is_active=True).exclude(id=service.id).order_by('order')[:4]
        context['testimonials'] = Testimonial.objects.filter(is_active=True, is_featured=True).order_by('order')[:2]
        return context


# Pricing Page
class PricingView(TemplateView):
    """Pricing page with Stripe integration"""
    template_name = 'website/pricing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['stripe_publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY

        # Define pricing plans
        context['plans'] = [
            {
                'name': 'Free',
                'price': 0,
                'price_annual': 0,
                'stripe_price_id_monthly': None,
                'stripe_price_id_annual': None,
                'description': 'Perfect for trying out Aureon',
                'features': [
                    'Up to 3 active contracts',
                    '5 invoices per month',
                    'Basic templates',
                    'Email support',
                    'Single user',
                ],
                'limitations': [
                    'No e-signature',
                    'No Stripe integration',
                    'Limited storage (500MB)',
                ],
                'cta': 'Get Started Free',
                'cta_url': reverse_lazy('account_signup'),
                'popular': False,
            },
            {
                'name': 'Starter',
                'price': 19,
                'price_annual': 190,  # ~$15.83/month
                'stripe_price_id_monthly': settings.STRIPE_PRICE_ID_STARTER_MONTHLY if hasattr(settings, 'STRIPE_PRICE_ID_STARTER_MONTHLY') else None,
                'stripe_price_id_annual': settings.STRIPE_PRICE_ID_STARTER_ANNUAL if hasattr(settings, 'STRIPE_PRICE_ID_STARTER_ANNUAL') else None,
                'description': 'For freelancers and small teams',
                'features': [
                    'Up to 25 active contracts',
                    'Unlimited invoices',
                    'E-signature (DocuSign)',
                    'Stripe payment integration',
                    'Premium templates',
                    'Up to 3 users',
                    'Priority email support',
                    '5GB storage',
                ],
                'cta': 'Start 14-Day Trial',
                'popular': False,
            },
            {
                'name': 'Pro',
                'price': 49,
                'price_annual': 490,  # ~$40.83/month
                'stripe_price_id_monthly': settings.STRIPE_PRICE_ID_PRO_MONTHLY if hasattr(settings, 'STRIPE_PRICE_ID_PRO_MONTHLY') else None,
                'stripe_price_id_annual': settings.STRIPE_PRICE_ID_PRO_ANNUAL if hasattr(settings, 'STRIPE_PRICE_ID_PRO_ANNUAL') else None,
                'description': 'For growing businesses',
                'features': [
                    'Unlimited contracts',
                    'Unlimited invoices',
                    'Advanced e-signature workflows',
                    'Stripe + PayPal integration',
                    'Multi-currency support',
                    'Automated workflows',
                    'Up to 10 users',
                    'Custom branding',
                    'API access',
                    'Phone & chat support',
                    '50GB storage',
                ],
                'cta': 'Start 14-Day Trial',
                'popular': True,
            },
            {
                'name': 'Business',
                'price': 99,
                'price_annual': 990,  # ~$82.50/month
                'stripe_price_id_monthly': settings.STRIPE_PRICE_ID_BUSINESS_MONTHLY if hasattr(settings, 'STRIPE_PRICE_ID_BUSINESS_MONTHLY') else None,
                'stripe_price_id_annual': settings.STRIPE_PRICE_ID_BUSINESS_ANNUAL if hasattr(settings, 'STRIPE_PRICE_ID_BUSINESS_ANNUAL') else None,
                'description': 'For established companies',
                'features': [
                    'Everything in Pro',
                    'Unlimited users',
                    'Advanced analytics & reporting',
                    'White-label options',
                    'Dedicated account manager',
                    'Custom integrations',
                    'SLA guarantee (99.9% uptime)',
                    'SSO/SAML support',
                    'Audit trail & compliance tools',
                    '500GB storage',
                    'Priority phone support',
                ],
                'cta': 'Start 14-Day Trial',
                'popular': False,
            },
        ]

        context['page_title'] = 'Pricing Plans'
        context['meta_description'] = 'Flexible pricing for businesses of all sizes. Start free or choose a plan that fits your needs.'
        return context


# Contact Page
class ContactView(FormView):
    """Contact page with contact form"""
    template_name = 'website/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('website:contact_success')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['page_title'] = 'Contact Us'
        context['meta_description'] = 'Get in touch with Aureon. We\'re here to help with any questions about our platform.'
        return context

    def form_valid(self, form):
        # Save the contact submission
        contact = form.save(commit=False)

        # Capture metadata
        contact.ip_address = self.get_client_ip()
        contact.user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        contact.referrer = self.request.META.get('HTTP_REFERER', '')

        contact.save()

        # Send notification email to admin
        self.send_notification_email(contact)

        # Send confirmation email to user
        self.send_confirmation_email(contact)

        messages.success(
            self.request,
            'Thank you for contacting us! We\'ll get back to you within 24 hours.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'There was an error with your submission. Please check the form and try again.'
        )
        return super().form_invalid(form)

    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def send_notification_email(self, contact):
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

    def send_confirmation_email(self, contact):
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


class ContactSuccessView(TemplateView):
    """Contact form success page"""
    template_name = 'website/contact-success.html'


# Blog List View
class BlogListView(ListView):
    """Blog listing page with pagination and filtering"""
    model = BlogPost
    template_name = 'website/blog.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        queryset = BlogPost.objects.filter(status='published')

        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(excerpt__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        # Category filter
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Tag filter
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        return queryset.select_related('author', 'category').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['categories'] = BlogCategory.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        )
        context['tags'] = BlogTag.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        )
        context['featured_posts'] = BlogPost.objects.filter(
            status='published',
            featured=True
        )[:3]
        context['search_query'] = self.request.GET.get('q', '')
        context['page_title'] = 'Blog'
        context['meta_description'] = 'Insights, tips, and news about business automation, SaaS, and growth strategies.'
        return context


# Blog Detail View
class BlogDetailView(DetailView):
    """Individual blog post page"""
    model = BlogPost
    template_name = 'website/blog-detail.html'
    context_object_name = 'post'
    slug_field = 'slug'

    def get_queryset(self):
        return BlogPost.objects.filter(status='published').select_related('author', 'category').prefetch_related('tags')

    def get_object(self):
        obj = super().get_object()
        # Increment view count
        obj.increment_views()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()

        # Related posts
        post = self.get_object()
        related_posts = BlogPost.objects.filter(
            status='published'
        ).exclude(id=post.id)

        if post.category:
            related_posts = related_posts.filter(category=post.category)

        context['related_posts'] = related_posts[:3]

        # SEO meta tags
        context['page_title'] = post.meta_title or post.title
        context['meta_description'] = post.meta_description or post.excerpt
        context['meta_keywords'] = post.meta_keywords
        context['canonical_url'] = post.canonical_url or self.request.build_absolute_uri()
        context['og_image'] = post.featured_image.url if post.featured_image else None

        return context


# Blog Category View
class BlogCategoryView(ListView):
    """Blog posts filtered by category"""
    model = BlogPost
    template_name = 'website/blog-category.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        self.category = get_object_or_404(BlogCategory, slug=self.kwargs['slug'])
        return BlogPost.objects.filter(
            status='published',
            category=self.category
        ).select_related('author', 'category').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['category'] = self.category
        context['page_title'] = f'{self.category.name} - Blog'
        context['meta_description'] = self.category.description or f'Blog posts about {self.category.name}'
        return context


# Blog Tag View
class BlogTagView(ListView):
    """Blog posts filtered by tag"""
    model = BlogPost
    template_name = 'website/blog-tag.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        self.tag = get_object_or_404(BlogTag, slug=self.kwargs['slug'])
        return BlogPost.objects.filter(
            status='published',
            tags=self.tag
        ).select_related('author', 'category').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['tag'] = self.tag
        context['page_title'] = f'{self.tag.name} - Blog'
        context['meta_description'] = f'Blog posts tagged with {self.tag.name}'
        return context


# Product List View
class ProductListView(ListView):
    """Product listing page"""
    model = Product
    template_name = 'website/products.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['featured_products'] = Product.objects.filter(
            is_active=True,
            is_featured=True
        )[:4]
        context['page_title'] = 'Products & Add-ons'
        context['meta_description'] = 'Explore our products, templates, and add-ons to enhance your Aureon experience.'
        return context


# Product Detail View
class ProductDetailView(DetailView):
    """Individual product page"""
    model = Product
    template_name = 'website/product-detail.html'
    context_object_name = 'product'
    slug_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['stripe_publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY

        product = self.get_object()
        context['page_title'] = product.meta_title or product.name
        context['meta_description'] = product.meta_description or product.short_description
        context['meta_keywords'] = product.meta_keywords

        # Related products
        context['related_products'] = Product.objects.filter(
            is_active=True
        ).exclude(id=product.id)[:4]

        return context


# Newsletter Subscription
@require_POST
def newsletter_subscribe(request):
    """Handle newsletter subscription via AJAX"""
    form = NewsletterForm(request.POST)

    if form.is_valid():
        subscriber = form.save(commit=False)

        # Capture metadata
        subscriber.source = request.POST.get('source', 'website')
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            subscriber.ip_address = x_forwarded_for.split(',')[0]
        else:
            subscriber.ip_address = request.META.get('REMOTE_ADDR')

        subscriber.save()

        # Send confirmation email
        send_confirmation_email(subscriber)

        return JsonResponse({
            'success': True,
            'message': 'Thank you for subscribing! Please check your email to confirm your subscription.'
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


def send_confirmation_email(subscriber):
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
    return redirect('website:home')


def newsletter_unsubscribe(request, token):
    """Unsubscribe from newsletter"""
    subscriber = get_object_or_404(NewsletterSubscriber, confirmation_token=token)
    subscriber.unsubscribe()

    messages.info(request, 'You have been unsubscribed from our newsletter.')
    return redirect('website:home')


# Stripe Checkout Session Creation
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
            success_url=request.build_absolute_uri(reverse('website:payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('website:pricing')),
            customer_email=request.user.email if request.user.is_authenticated else None,
        )

        return JsonResponse({
            'sessionId': checkout_session.id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# Payment Success Page
class PaymentSuccessView(TemplateView):
    """Payment success page after Stripe checkout"""
    template_name = 'website/payment-success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        session_id = self.request.GET.get('session_id')

        if session_id:
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                context['session'] = session
            except Exception as e:
                context['error'] = str(e)

        return context


# FAQ Page
class FAQView(TemplateView):
    """FAQ page"""
    template_name = 'website/faq.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['page_title'] = 'Frequently Asked Questions'
        context['meta_description'] = 'Find answers to common questions about Aureon platform, pricing, features, and support.'

        # Group FAQs by category
        context['general_faqs'] = FAQ.objects.filter(is_active=True, category='general').order_by('order')
        context['pricing_faqs'] = FAQ.objects.filter(is_active=True, category='pricing').order_by('order')
        context['features_faqs'] = FAQ.objects.filter(is_active=True, category='features').order_by('order')
        context['security_faqs'] = FAQ.objects.filter(is_active=True, category='security').order_by('order')
        context['support_faqs'] = FAQ.objects.filter(is_active=True, category='support').order_by('order')
        context['technical_faqs'] = FAQ.objects.filter(is_active=True, category='technical').order_by('order')
        context['featured_faqs'] = FAQ.objects.filter(is_active=True, is_featured=True).order_by('order')
        return context


# Privacy Policy
class PrivacyPolicyView(TemplateView):
    """Privacy policy page"""
    template_name = 'website/privacy-policy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['page_title'] = 'Privacy Policy'
        return context


# Terms of Service
class TermsOfServiceView(TemplateView):
    """Terms of service page"""
    template_name = 'website/terms-of-service.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['page_title'] = 'Terms of Service'
        return context


# ============================================================
# CASE STUDY VIEWS
# ============================================================

class CaseStudyListView(ListView):
    """Case studies listing page"""
    model = CaseStudy
    template_name = 'website/case-studies.html'
    context_object_name = 'case_studies'
    paginate_by = 9

    def get_queryset(self):
        queryset = CaseStudy.objects.filter(status='published')

        # Category filter
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset.select_related('category').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['categories'] = CaseStudyCategory.objects.annotate(
            case_study_count=Count('case_studies', filter=Q(case_studies__status='published'))
        )
        context['featured_case_studies'] = CaseStudy.objects.filter(
            status='published',
            is_featured=True
        )[:3]
        context['page_title'] = 'Case Studies'
        context['meta_description'] = 'Discover how businesses have transformed their operations with Aureon. Read our success stories and case studies.'
        return context


class CaseStudyDetailView(DetailView):
    """Individual case study page"""
    model = CaseStudy
    template_name = 'website/case-study-detail.html'
    context_object_name = 'case_study'
    slug_field = 'slug'

    def get_queryset(self):
        return CaseStudy.objects.filter(status='published').select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()

        case_study = self.get_object()

        # Related case studies
        related_case_studies = CaseStudy.objects.filter(
            status='published'
        ).exclude(id=case_study.id)

        if case_study.category:
            related_case_studies = related_case_studies.filter(category=case_study.category)

        context['related_case_studies'] = related_case_studies[:3]

        # SEO meta tags
        context['page_title'] = case_study.meta_title or case_study.title
        context['meta_description'] = case_study.meta_description or case_study.excerpt
        context['meta_keywords'] = case_study.meta_keywords
        context['og_image'] = case_study.featured_image.url if case_study.featured_image else None

        return context


class CaseStudyCategoryView(ListView):
    """Case studies filtered by category"""
    model = CaseStudy
    template_name = 'website/case-study-category.html'
    context_object_name = 'case_studies'
    paginate_by = 9

    def get_queryset(self):
        self.category = get_object_or_404(CaseStudyCategory, slug=self.kwargs['slug'])
        return CaseStudy.objects.filter(
            status='published',
            category=self.category
        ).order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['category'] = self.category
        context['categories'] = CaseStudyCategory.objects.annotate(
            case_study_count=Count('case_studies', filter=Q(case_studies__status='published'))
        )
        context['page_title'] = f'{self.category.name} Case Studies'
        context['meta_description'] = self.category.description or f'Case studies in {self.category.name}'
        return context
