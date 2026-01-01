"""
API URL routes for the marketing website.
These endpoints serve JSON data for the Plax React frontend.
"""
from django.urls import path
from . import api

urlpatterns = [
    # Site Settings
    path('settings/', api.api_site_settings, name='api_site_settings'),

    # Services
    path('services/', api.api_services, name='api_services'),
    path('services/<slug:slug>/', api.api_service_detail, name='api_service_detail'),

    # Pricing
    path('pricing/', api.api_pricing, name='api_pricing'),

    # Testimonials
    path('testimonials/', api.api_testimonials, name='api_testimonials'),

    # FAQs
    path('faqs/', api.api_faqs, name='api_faqs'),

    # Blog
    path('posts/', api.api_blog_posts, name='api_blog_posts'),
    path('posts/<slug:slug>/', api.api_blog_post_detail, name='api_blog_post_detail'),
    path('categories/', api.api_blog_categories, name='api_blog_categories'),

    # Case Studies
    path('case-studies/', api.api_case_studies, name='api_case_studies'),
    path('case-studies/<slug:slug>/', api.api_case_study_detail, name='api_case_study_detail'),

    # Team
    path('team/', api.api_team, name='api_team'),

    # Contact & Newsletter
    path('contact/', api.api_contact, name='api_contact'),
    path('newsletter/', api.api_newsletter, name='api_newsletter'),
]
