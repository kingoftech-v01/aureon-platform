"""
Tests for website app URL configuration.

Covers: URL resolution, naming, and reverse lookups for all website URLs
including marketing pages, blog, products, newsletter, stripe, and SEO files.
"""
import pytest

from django.urls import resolve, reverse


class TestWebsiteUrls:
    """Test URL resolution and reverse lookups for the website app."""

    # ============================================================
    # Homepage
    # ============================================================

    def test_home_url_resolves(self):
        match = resolve("/")
        assert match.url_name == "home"

    def test_home_url_reverse(self):
        url = reverse("website:home")
        assert url == "/"

    # ============================================================
    # Company pages
    # ============================================================

    def test_about_url_resolves(self):
        match = resolve("/about/")
        assert match.url_name == "about"

    def test_about_url_reverse(self):
        assert reverse("website:about") == "/about/"

    def test_team_url_resolves(self):
        match = resolve("/team/")
        assert match.url_name == "team"

    def test_team_url_reverse(self):
        assert reverse("website:team") == "/team/"

    def test_pricing_url_resolves(self):
        match = resolve("/pricing/")
        assert match.url_name == "pricing"

    def test_pricing_url_reverse(self):
        assert reverse("website:pricing") == "/pricing/"

    def test_contact_url_resolves(self):
        match = resolve("/contact/")
        assert match.url_name == "contact"

    def test_contact_url_reverse(self):
        assert reverse("website:contact") == "/contact/"

    def test_contact_success_url_resolves(self):
        match = resolve("/contact/success/")
        assert match.url_name == "contact_success"

    def test_contact_success_url_reverse(self):
        assert reverse("website:contact_success") == "/contact/success/"

    def test_contact_submit_url_resolves(self):
        match = resolve("/contact/submit/")
        assert match.url_name == "contact_submit"

    def test_contact_submit_url_reverse(self):
        assert reverse("website:contact_submit") == "/contact/submit/"

    # ============================================================
    # Services
    # ============================================================

    def test_services_url_resolves(self):
        match = resolve("/services/")
        assert match.url_name == "services"

    def test_services_url_reverse(self):
        assert reverse("website:services") == "/services/"

    def test_service_detail_url_resolves(self):
        match = resolve("/services/invoicing/")
        assert match.url_name == "service_detail"
        assert match.kwargs["slug"] == "invoicing"

    def test_service_detail_url_reverse(self):
        url = reverse("website:service_detail", kwargs={"slug": "invoicing"})
        assert url == "/services/invoicing/"

    # ============================================================
    # Case Studies
    # ============================================================

    def test_case_studies_url_resolves(self):
        match = resolve("/case-studies/")
        assert match.url_name == "case_studies"

    def test_case_studies_url_reverse(self):
        assert reverse("website:case_studies") == "/case-studies/"

    def test_case_study_category_url_resolves(self):
        match = resolve("/case-studies/category/tech/")
        assert match.url_name == "case_study_category"
        assert match.kwargs["slug"] == "tech"

    def test_case_study_category_url_reverse(self):
        url = reverse("website:case_study_category", kwargs={"slug": "tech"})
        assert url == "/case-studies/category/tech/"

    def test_case_study_detail_url_resolves(self):
        match = resolve("/case-studies/acme-success/")
        assert match.url_name == "case_study_detail"
        assert match.kwargs["slug"] == "acme-success"

    def test_case_study_detail_url_reverse(self):
        url = reverse("website:case_study_detail", kwargs={"slug": "acme-success"})
        assert url == "/case-studies/acme-success/"

    # ============================================================
    # Blog
    # ============================================================

    def test_blog_url_resolves(self):
        match = resolve("/blog/")
        assert match.url_name == "blog"

    def test_blog_url_reverse(self):
        assert reverse("website:blog") == "/blog/"

    def test_blog_category_url_resolves(self):
        match = resolve("/blog/category/python/")
        assert match.url_name == "blog_category"
        assert match.kwargs["slug"] == "python"

    def test_blog_category_url_reverse(self):
        url = reverse("website:blog_category", kwargs={"slug": "python"})
        assert url == "/blog/category/python/"

    def test_blog_tag_url_resolves(self):
        match = resolve("/blog/tag/django/")
        assert match.url_name == "blog_tag"
        assert match.kwargs["slug"] == "django"

    def test_blog_tag_url_reverse(self):
        url = reverse("website:blog_tag", kwargs={"slug": "django"})
        assert url == "/blog/tag/django/"

    def test_blog_detail_url_resolves(self):
        match = resolve("/blog/my-post/")
        assert match.url_name == "blog_detail"
        assert match.kwargs["slug"] == "my-post"

    def test_blog_detail_url_reverse(self):
        url = reverse("website:blog_detail", kwargs={"slug": "my-post"})
        assert url == "/blog/my-post/"

    # ============================================================
    # Products
    # ============================================================

    def test_products_url_resolves(self):
        match = resolve("/products/")
        assert match.url_name == "products"

    def test_products_url_reverse(self):
        assert reverse("website:products") == "/products/"

    def test_product_detail_url_resolves(self):
        match = resolve("/products/template-pack/")
        assert match.url_name == "product_detail"
        assert match.kwargs["slug"] == "template-pack"

    def test_product_detail_url_reverse(self):
        url = reverse("website:product_detail", kwargs={"slug": "template-pack"})
        assert url == "/products/template-pack/"

    # ============================================================
    # Newsletter
    # ============================================================

    def test_newsletter_subscribe_url_resolves(self):
        match = resolve("/newsletter/subscribe/")
        assert match.url_name == "newsletter_subscribe"

    def test_newsletter_subscribe_url_reverse(self):
        assert reverse("website:newsletter_subscribe") == "/newsletter/subscribe/"

    def test_newsletter_confirm_url_resolves(self):
        match = resolve("/newsletter/confirm/abc123token/")
        assert match.url_name == "newsletter_confirm"
        assert match.kwargs["token"] == "abc123token"

    def test_newsletter_confirm_url_reverse(self):
        url = reverse("website:newsletter_confirm", kwargs={"token": "mytoken"})
        assert url == "/newsletter/confirm/mytoken/"

    def test_newsletter_unsubscribe_url_resolves(self):
        match = resolve("/newsletter/unsubscribe/abc123token/")
        assert match.url_name == "newsletter_unsubscribe"
        assert match.kwargs["token"] == "abc123token"

    def test_newsletter_unsubscribe_url_reverse(self):
        url = reverse("website:newsletter_unsubscribe", kwargs={"token": "mytoken"})
        assert url == "/newsletter/unsubscribe/mytoken/"

    # ============================================================
    # Stripe / Payment
    # ============================================================

    def test_create_checkout_session_url_resolves(self):
        match = resolve("/create-checkout-session/")
        assert match.url_name == "create_checkout_session"

    def test_create_checkout_session_url_reverse(self):
        assert reverse("website:create_checkout_session") == "/create-checkout-session/"

    def test_payment_success_url_resolves(self):
        match = resolve("/payment/success/")
        assert match.url_name == "payment_success"

    def test_payment_success_url_reverse(self):
        assert reverse("website:payment_success") == "/payment/success/"

    # ============================================================
    # Legal / Support
    # ============================================================

    def test_faq_url_resolves(self):
        match = resolve("/faq/")
        assert match.url_name == "faq"

    def test_faq_url_reverse(self):
        assert reverse("website:faq") == "/faq/"

    def test_privacy_policy_url_resolves(self):
        match = resolve("/privacy-policy/")
        assert match.url_name == "privacy_policy"

    def test_privacy_policy_url_reverse(self):
        assert reverse("website:privacy_policy") == "/privacy-policy/"

    def test_terms_of_service_url_resolves(self):
        match = resolve("/terms-of-service/")
        assert match.url_name == "terms_of_service"

    def test_terms_of_service_url_reverse(self):
        assert reverse("website:terms_of_service") == "/terms-of-service/"

    # ============================================================
    # Auth pages (served by Next.js)
    # ============================================================

    def test_login_url_resolves(self):
        match = resolve("/login/")
        assert match.url_name == "login"

    def test_login_url_reverse(self):
        assert reverse("website:login") == "/login/"

    def test_signup_url_resolves(self):
        match = resolve("/signup/")
        assert match.url_name == "signup"

    def test_signup_url_reverse(self):
        assert reverse("website:signup") == "/signup/"

    # ============================================================
    # SEO Files
    # ============================================================

    def test_sitemap_url_resolves(self):
        match = resolve("/sitemap.xml")
        assert match.url_name == "sitemap"

    def test_sitemap_url_reverse(self):
        assert reverse("website:sitemap") == "/sitemap.xml"

    def test_robots_url_resolves(self):
        match = resolve("/robots.txt")
        assert match.url_name == "robots"

    def test_robots_url_reverse(self):
        assert reverse("website:robots") == "/robots.txt"

    # ============================================================
    # App namespace
    # ============================================================

    def test_app_name_is_website(self):
        match = resolve("/")
        assert match.app_name == "website"


class TestApiUrls:
    """Test URL resolution for the website API endpoints."""

    def test_api_settings_url(self):
        match = resolve("/api/v1/website/settings/")
        assert match.url_name == "api_site_settings"

    def test_api_services_url(self):
        match = resolve("/api/v1/website/services/")
        assert match.url_name == "api_services"

    def test_api_service_detail_url(self):
        match = resolve("/api/v1/website/services/invoicing/")
        assert match.url_name == "api_service_detail"
        assert match.kwargs["slug"] == "invoicing"

    def test_api_pricing_url(self):
        match = resolve("/api/v1/website/pricing/")
        assert match.url_name == "api_pricing"

    def test_api_testimonials_url(self):
        match = resolve("/api/v1/website/testimonials/")
        assert match.url_name == "api_testimonials"

    def test_api_faqs_url(self):
        match = resolve("/api/v1/website/faqs/")
        assert match.url_name == "api_faqs"

    def test_api_blog_posts_url(self):
        match = resolve("/api/v1/website/posts/")
        assert match.url_name == "api_blog_posts"

    def test_api_blog_post_detail_url(self):
        match = resolve("/api/v1/website/posts/my-post/")
        assert match.url_name == "api_blog_post_detail"
        assert match.kwargs["slug"] == "my-post"

    def test_api_categories_url(self):
        match = resolve("/api/v1/website/categories/")
        assert match.url_name == "api_blog_categories"

    def test_api_case_studies_url(self):
        match = resolve("/api/v1/website/case-studies/")
        assert match.url_name == "api_case_studies"

    def test_api_case_study_detail_url(self):
        match = resolve("/api/v1/website/case-studies/acme/")
        assert match.url_name == "api_case_study_detail"
        assert match.kwargs["slug"] == "acme"

    def test_api_team_url(self):
        match = resolve("/api/v1/website/team/")
        assert match.url_name == "api_team"

    def test_api_contact_url(self):
        match = resolve("/api/v1/website/contact/")
        assert match.url_name == "api_contact"

    def test_api_newsletter_url(self):
        match = resolve("/api/v1/website/newsletter/")
        assert match.url_name == "api_newsletter"
