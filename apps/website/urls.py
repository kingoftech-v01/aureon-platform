from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'website'

urlpatterns = [
    # Homepage
    path('', views.HomeView.as_view(), name='home'),

    # Company Pages
    path('about/', views.AboutView.as_view(), name='about'),
    path('team/', views.TeamView.as_view(), name='team'),
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/success/', views.ContactSuccessView.as_view(), name='contact_success'),

    # Services
    path('services/', views.ServicesView.as_view(), name='services'),
    path('services/<slug:slug>/', views.ServiceDetailView.as_view(), name='service_detail'),

    # Case Studies
    path('case-studies/', views.CaseStudyListView.as_view(), name='case_studies'),
    path('case-studies/category/<slug:slug>/', views.CaseStudyCategoryView.as_view(), name='case_study_category'),
    path('case-studies/<slug:slug>/', views.CaseStudyDetailView.as_view(), name='case_study_detail'),

    # Blog
    path('blog/', views.BlogListView.as_view(), name='blog'),
    path('blog/category/<slug:slug>/', views.BlogCategoryView.as_view(), name='blog_category'),
    path('blog/tag/<slug:slug>/', views.BlogTagView.as_view(), name='blog_tag'),
    path('blog/<slug:slug>/', views.BlogDetailView.as_view(), name='blog_detail'),

    # Products/Store
    path('products/', views.ProductListView.as_view(), name='products'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # Newsletter
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('newsletter/confirm/<str:token>/', views.newsletter_confirm, name='newsletter_confirm'),
    path('newsletter/unsubscribe/<str:token>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),

    # Stripe Payment
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('payment/success/', views.PaymentSuccessView.as_view(), name='payment_success'),

    # Legal & Support
    path('faq/', views.FAQView.as_view(), name='faq'),
    path('privacy-policy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('terms-of-service/', views.TermsOfServiceView.as_view(), name='terms_of_service'),

    # SEO Files (will be handled by Django views)
    path('sitemap.xml', TemplateView.as_view(template_name='website/sitemap.xml', content_type='text/xml'), name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='website/robots.txt', content_type='text/plain'), name='robots'),
]
