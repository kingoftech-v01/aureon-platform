"""
Tests for website app views.

Covers: MarketingPageView subclasses (HomeView, AboutView, etc.),
contact_submit, newsletter_subscribe/confirm/unsubscribe,
create_checkout_session, robots_txt, sitemap_xml.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from django.test import RequestFactory, Client
from django.http import HttpResponse
from django.urls import reverse

from apps.website.models import (
    ContactSubmission,
    NewsletterSubscriber,
    SiteSettings,
)
from apps.website.views import (
    HomeView,
    AboutView,
    TeamView,
    ServicesView,
    ServiceDetailView,
    PricingView,
    ContactView,
    ContactSuccessView,
    BlogListView,
    BlogDetailView,
    BlogCategoryView,
    BlogTagView,
    ProductListView,
    ProductDetailView,
    FAQView,
    PrivacyPolicyView,
    TermsOfServiceView,
    CaseStudyListView,
    CaseStudyDetailView,
    CaseStudyCategoryView,
    PaymentSuccessView,
    LoginView,
    SignupView,
    MarketingPageView,
    contact_submit,
    newsletter_subscribe,
    newsletter_confirm,
    newsletter_unsubscribe,
    create_checkout_session,
    send_contact_notification,
    send_contact_confirmation,
    send_newsletter_confirmation,
)


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def rf():
    """Django request factory."""
    return RequestFactory()


# ============================================================================
# Marketing Page View Tests (all delegate to serve_marketing_site)
# ============================================================================


@pytest.mark.django_db
class TestMarketingPageViews:
    """Test that all marketing page views delegate to serve_marketing_site."""

    @patch("apps.website.views.serve_marketing_site")
    def test_home_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Home", status=200)
        request = rf.get("/")
        response = HomeView.as_view()(request)
        mock_serve.assert_called_once_with(request, "")
        assert response.status_code == 200

    @patch("apps.website.views.serve_marketing_site")
    def test_about_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("About", status=200)
        request = rf.get("/about/")
        response = AboutView.as_view()(request)
        mock_serve.assert_called_once_with(request, "about")

    @patch("apps.website.views.serve_marketing_site")
    def test_team_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Team", status=200)
        request = rf.get("/team/")
        response = TeamView.as_view()(request)
        mock_serve.assert_called_once_with(request, "team")

    @patch("apps.website.views.serve_marketing_site")
    def test_services_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Services", status=200)
        request = rf.get("/services/")
        response = ServicesView.as_view()(request)
        mock_serve.assert_called_once_with(request, "services")

    @patch("apps.website.views.serve_marketing_site")
    def test_service_detail_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Service Detail", status=200)
        request = rf.get("/services/invoicing/")
        response = ServiceDetailView.as_view()(request, slug="invoicing")
        mock_serve.assert_called_once_with(request, "services/invoicing")

    @patch("apps.website.views.serve_marketing_site")
    def test_service_detail_view_empty_slug(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Service Detail", status=200)
        request = rf.get("/services/")
        response = ServiceDetailView.as_view()(request)
        mock_serve.assert_called_once_with(request, "services/")

    @patch("apps.website.views.serve_marketing_site")
    def test_pricing_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Pricing", status=200)
        request = rf.get("/pricing/")
        response = PricingView.as_view()(request)
        mock_serve.assert_called_once_with(request, "pricing")

    @patch("apps.website.views.serve_marketing_site")
    def test_contact_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Contact", status=200)
        request = rf.get("/contact/")
        response = ContactView.as_view()(request)
        mock_serve.assert_called_once_with(request, "contact")

    @patch("apps.website.views.serve_marketing_site")
    def test_contact_success_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Success", status=200)
        request = rf.get("/contact/success/")
        response = ContactSuccessView.as_view()(request)
        mock_serve.assert_called_once_with(request, "contact/success")

    @patch("apps.website.views.serve_marketing_site")
    def test_blog_list_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Blog", status=200)
        request = rf.get("/blog/")
        response = BlogListView.as_view()(request)
        mock_serve.assert_called_once_with(request, "blog")

    @patch("apps.website.views.serve_marketing_site")
    def test_blog_detail_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Blog Detail", status=200)
        request = rf.get("/blog/my-post/")
        response = BlogDetailView.as_view()(request, slug="my-post")
        mock_serve.assert_called_once_with(request, "blog/my-post")

    @patch("apps.website.views.serve_marketing_site")
    def test_blog_detail_view_empty_slug(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Blog", status=200)
        request = rf.get("/blog/")
        response = BlogDetailView.as_view()(request)
        mock_serve.assert_called_once_with(request, "blog/")

    @patch("apps.website.views.serve_marketing_site")
    def test_blog_category_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Category", status=200)
        request = rf.get("/blog/category/tech/")
        response = BlogCategoryView.as_view()(request, slug="tech")
        mock_serve.assert_called_once_with(request, "blog/category/tech")

    @patch("apps.website.views.serve_marketing_site")
    def test_blog_category_view_empty_slug(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Category", status=200)
        request = rf.get("/blog/category/")
        response = BlogCategoryView.as_view()(request)
        mock_serve.assert_called_once_with(request, "blog/category/")

    @patch("apps.website.views.serve_marketing_site")
    def test_blog_tag_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Tag", status=200)
        request = rf.get("/blog/tag/django/")
        response = BlogTagView.as_view()(request, slug="django")
        mock_serve.assert_called_once_with(request, "blog/tag/django")

    @patch("apps.website.views.serve_marketing_site")
    def test_blog_tag_view_empty_slug(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Tag", status=200)
        request = rf.get("/blog/tag/")
        response = BlogTagView.as_view()(request)
        mock_serve.assert_called_once_with(request, "blog/tag/")

    @patch("apps.website.views.serve_marketing_site")
    def test_product_list_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Products", status=200)
        request = rf.get("/products/")
        response = ProductListView.as_view()(request)
        mock_serve.assert_called_once_with(request, "products")

    @patch("apps.website.views.serve_marketing_site")
    def test_product_detail_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Product", status=200)
        request = rf.get("/products/template-pack/")
        response = ProductDetailView.as_view()(request, slug="template-pack")
        mock_serve.assert_called_once_with(request, "products/template-pack")

    @patch("apps.website.views.serve_marketing_site")
    def test_product_detail_view_empty_slug(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Products", status=200)
        request = rf.get("/products/")
        response = ProductDetailView.as_view()(request)
        mock_serve.assert_called_once_with(request, "products/")

    @patch("apps.website.views.serve_marketing_site")
    def test_faq_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("FAQ", status=200)
        request = rf.get("/faq/")
        response = FAQView.as_view()(request)
        mock_serve.assert_called_once_with(request, "faq")

    @patch("apps.website.views.serve_marketing_site")
    def test_privacy_policy_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Privacy", status=200)
        request = rf.get("/privacy-policy/")
        response = PrivacyPolicyView.as_view()(request)
        mock_serve.assert_called_once_with(request, "privacy-policy")

    @patch("apps.website.views.serve_marketing_site")
    def test_terms_of_service_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Terms", status=200)
        request = rf.get("/terms-of-service/")
        response = TermsOfServiceView.as_view()(request)
        mock_serve.assert_called_once_with(request, "terms-of-service")

    @patch("apps.website.views.serve_marketing_site")
    def test_case_study_list_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Case Studies", status=200)
        request = rf.get("/case-studies/")
        response = CaseStudyListView.as_view()(request)
        mock_serve.assert_called_once_with(request, "case-studies")

    @patch("apps.website.views.serve_marketing_site")
    def test_case_study_detail_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Case Study", status=200)
        request = rf.get("/case-studies/acme/")
        response = CaseStudyDetailView.as_view()(request, slug="acme")
        mock_serve.assert_called_once_with(request, "case-studies/acme")

    @patch("apps.website.views.serve_marketing_site")
    def test_case_study_detail_view_empty_slug(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Case Studies", status=200)
        request = rf.get("/case-studies/")
        response = CaseStudyDetailView.as_view()(request)
        mock_serve.assert_called_once_with(request, "case-studies/")

    @patch("apps.website.views.serve_marketing_site")
    def test_case_study_category_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Category", status=200)
        request = rf.get("/case-studies/category/tech/")
        response = CaseStudyCategoryView.as_view()(request, slug="tech")
        mock_serve.assert_called_once_with(request, "case-studies/category/tech")

    @patch("apps.website.views.serve_marketing_site")
    def test_case_study_category_view_empty_slug(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Category", status=200)
        request = rf.get("/case-studies/category/")
        response = CaseStudyCategoryView.as_view()(request)
        mock_serve.assert_called_once_with(request, "case-studies/category/")

    @patch("apps.website.views.serve_marketing_site")
    def test_payment_success_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Success", status=200)
        request = rf.get("/payment/success/")
        response = PaymentSuccessView.as_view()(request)
        mock_serve.assert_called_once_with(request, "payment/success")

    @patch("apps.website.views.serve_marketing_site")
    def test_login_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Login", status=200)
        request = rf.get("/login/")
        response = LoginView.as_view()(request)
        mock_serve.assert_called_once_with(request, "login")

    @patch("apps.website.views.serve_marketing_site")
    def test_signup_view(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Signup", status=200)
        request = rf.get("/signup/")
        response = SignupView.as_view()(request)
        mock_serve.assert_called_once_with(request, "signup")

    @patch("apps.website.views.serve_marketing_site")
    def test_marketing_page_view_base_with_slug_kwarg(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Page", status=200)
        request = rf.get("/some-page/")
        response = MarketingPageView.as_view()(request, slug="some-page")
        mock_serve.assert_called_once_with(request, "some-page")

    @patch("apps.website.views.serve_marketing_site")
    def test_marketing_page_view_base_with_path_kwarg(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Page", status=200)
        request = rf.get("/some/path/")
        response = MarketingPageView.as_view()(request, path="some/path")
        mock_serve.assert_called_once_with(request, "some/path")

    @patch("apps.website.views.serve_marketing_site")
    def test_marketing_page_view_base_no_kwargs(self, mock_serve, rf):
        mock_serve.return_value = HttpResponse("Page", status=200)
        request = rf.get("/")
        response = MarketingPageView.as_view()(request)
        mock_serve.assert_called_once_with(request, "")


# ============================================================================
# contact_submit view Tests
# ============================================================================


@pytest.mark.django_db
class TestContactSubmitView:
    """Tests for the contact_submit function-based view."""

    @patch("apps.website.views.send_contact_notification")
    @patch("apps.website.views.send_contact_confirmation")
    def test_successful_submission(self, mock_confirm, mock_notify, client):
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "company": "Test Inc",
            "inquiry_type": "general",
            "subject": "Test Subject",
            "message": "This is a test message with enough content.",
        }
        response = client.post(
            reverse("website:contact_submit"),
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "Thank you" in result["message"]
        assert ContactSubmission.objects.count() == 1
        mock_notify.assert_called_once()
        mock_confirm.assert_called_once()

    @patch("apps.website.views.send_contact_notification")
    @patch("apps.website.views.send_contact_confirmation")
    def test_captures_ip_from_forwarded_for(self, mock_confirm, mock_notify, client):
        data = {
            "name": "Jane",
            "email": "jane@example.com",
            "subject": "IP Test",
            "message": "Testing IP capture from forwarded header.",
        }
        response = client.post(
            reverse("website:contact_submit"),
            data=json.dumps(data),
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8",
        )
        assert response.status_code == 200
        contact = ContactSubmission.objects.first()
        assert contact.ip_address == "1.2.3.4"

    @patch("apps.website.views.send_contact_notification")
    @patch("apps.website.views.send_contact_confirmation")
    def test_captures_remote_addr(self, mock_confirm, mock_notify, rf):
        data = {
            "name": "Bob",
            "email": "bob@example.com",
            "subject": "Remote Addr",
            "message": "Testing remote addr capture for IP.",
        }
        request = rf.post(
            reverse("website:contact_submit"),
            data=json.dumps(data),
            content_type="application/json",
        )
        response = contact_submit(request)
        assert response.status_code == 200
        contact = ContactSubmission.objects.first()
        assert contact.ip_address == "127.0.0.1"

    @patch("apps.website.views.send_contact_notification")
    @patch("apps.website.views.send_contact_confirmation")
    def test_captures_user_agent(self, mock_confirm, mock_notify, client):
        data = {
            "name": "Agent",
            "email": "agent@example.com",
            "subject": "UA Test",
            "message": "Testing user agent capture field.",
        }
        response = client.post(
            reverse("website:contact_submit"),
            data=json.dumps(data),
            content_type="application/json",
            HTTP_USER_AGENT="TestBrowser/1.0",
        )
        assert response.status_code == 200
        contact = ContactSubmission.objects.first()
        assert contact.user_agent == "TestBrowser/1.0"

    def test_invalid_form_returns_400(self, client):
        data = {
            "name": "",
            "email": "invalid-email",
            "subject": "",
            "message": "short",
        }
        response = client.post(
            reverse("website:contact_submit"),
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False
        assert "errors" in result

    def test_get_method_not_allowed(self, client):
        response = client.get(reverse("website:contact_submit"))
        assert response.status_code == 405

    def test_exception_returns_500(self, client):
        # Send invalid JSON to trigger an exception
        response = client.post(
            reverse("website:contact_submit"),
            data="not valid json{{{",
            content_type="application/json",
        )
        assert response.status_code == 500
        result = response.json()
        assert result["success"] is False
        assert "error" in result


# ============================================================================
# send_contact_notification / send_contact_confirmation Tests
# ============================================================================


@pytest.mark.django_db
class TestSendContactEmails:
    """Test the email-sending helper functions for contact submissions."""

    @patch("apps.website.views.render_to_string", return_value="<html>Notification</html>")
    @patch("apps.website.views.EmailMultiAlternatives")
    def test_send_contact_notification(self, mock_email_cls, mock_render):
        SiteSettings.objects.create(pk=1, contact_email="admin@test.com")
        contact = ContactSubmission.objects.create(
            name="Test",
            email="test@example.com",
            subject="Test Subject",
            message="Test message content.",
        )
        send_contact_notification(contact)
        mock_render.assert_called_once()
        mock_email_cls.assert_called_once()
        mock_email_cls.return_value.attach_alternative.assert_called_once_with(
            "<html>Notification</html>", "text/html"
        )
        mock_email_cls.return_value.send.assert_called_once()

    @patch("apps.website.views.render_to_string", return_value="<html>Confirm</html>")
    @patch("apps.website.views.EmailMultiAlternatives")
    def test_send_contact_confirmation(self, mock_email_cls, mock_render):
        SiteSettings.objects.create(pk=1)
        contact = ContactSubmission.objects.create(
            name="Test",
            email="test@example.com",
            subject="Test Subject",
            message="Test message content.",
        )
        send_contact_confirmation(contact)
        mock_render.assert_called_once()
        mock_email_cls.assert_called_once()
        mock_email_cls.return_value.send.assert_called_once()


# ============================================================================
# newsletter_subscribe view Tests
# ============================================================================


@pytest.mark.django_db
class TestNewsletterSubscribeView:
    """Tests for the newsletter_subscribe function-based view."""

    @patch("apps.website.views.send_newsletter_confirmation")
    def test_successful_subscription_json(self, mock_send, client):
        data = {"email": "new@example.com", "name": "Subscriber"}
        response = client.post(
            reverse("website:newsletter_subscribe"),
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "Thank you" in result["message"]
        assert NewsletterSubscriber.objects.count() == 1
        mock_send.assert_called_once()

    @patch("apps.website.views.send_newsletter_confirmation")
    def test_captures_source(self, mock_send, client):
        data = {"email": "source@example.com", "source": "footer"}
        response = client.post(
            reverse("website:newsletter_subscribe"),
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        sub = NewsletterSubscriber.objects.first()
        assert sub.source == "footer"

    @patch("apps.website.views.send_newsletter_confirmation")
    def test_captures_ip_from_forwarded(self, mock_send, client):
        data = {"email": "ip@example.com"}
        response = client.post(
            reverse("website:newsletter_subscribe"),
            data=json.dumps(data),
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="10.0.0.1, 10.0.0.2",
        )
        assert response.status_code == 200
        sub = NewsletterSubscriber.objects.first()
        assert sub.ip_address == "10.0.0.1"

    @patch("apps.website.views.send_newsletter_confirmation")
    def test_captures_ip_from_remote_addr(self, mock_send, rf):
        data = {"email": "remote@example.com"}
        request = rf.post(
            reverse("website:newsletter_subscribe"),
            data=json.dumps(data),
            content_type="application/json",
        )
        response = newsletter_subscribe(request)
        assert response.status_code == 200
        sub = NewsletterSubscriber.objects.first()
        assert sub.ip_address == "127.0.0.1"

    def test_invalid_form_returns_400(self, client):
        data = {"email": "not-an-email"}
        response = client.post(
            reverse("website:newsletter_subscribe"),
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False
        assert "errors" in result

    def test_get_method_not_allowed(self, client):
        response = client.get(reverse("website:newsletter_subscribe"))
        assert response.status_code == 405

    def test_exception_returns_500(self, client):
        response = client.post(
            reverse("website:newsletter_subscribe"),
            data="bad json{",
            content_type="application/json",
        )
        assert response.status_code == 500
        result = response.json()
        assert result["success"] is False

    @patch("apps.website.views.send_newsletter_confirmation")
    def test_default_source_website(self, mock_send, client):
        data = {"email": "defaultsource@example.com"}
        response = client.post(
            reverse("website:newsletter_subscribe"),
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        sub = NewsletterSubscriber.objects.first()
        assert sub.source == "website"


# ============================================================================
# send_newsletter_confirmation Tests
# ============================================================================


@pytest.mark.django_db
class TestSendNewsletterConfirmation:
    """Test the newsletter confirmation email helper."""

    @patch("apps.website.views.render_to_string", return_value="<html>Confirm</html>")
    @patch("apps.website.views.EmailMultiAlternatives")
    def test_send_newsletter_confirmation(self, mock_email_cls, mock_render):
        SiteSettings.objects.create(pk=1)
        sub = NewsletterSubscriber.objects.create(email="sub@example.com")
        send_newsletter_confirmation(sub)
        mock_render.assert_called_once()
        template_context = mock_render.call_args[0][1]
        assert "confirmation_url" in template_context
        assert sub.confirmation_token in template_context["confirmation_url"]
        mock_email_cls.return_value.send.assert_called_once()


# ============================================================================
# newsletter_confirm view Tests
# ============================================================================


@pytest.mark.django_db
class TestNewsletterConfirmView:
    """Tests for the newsletter_confirm function-based view."""

    def test_confirm_valid_token(self, client):
        sub = NewsletterSubscriber.objects.create(email="confirm@example.com")
        response = client.get(
            reverse("website:newsletter_confirm", kwargs={"token": sub.confirmation_token})
        )
        assert response.status_code == 302  # redirect
        sub.refresh_from_db()
        assert sub.confirmed_at is not None
        assert sub.status == "active"

    def test_confirm_invalid_token_returns_404(self, client):
        response = client.get(
            reverse("website:newsletter_confirm", kwargs={"token": "invalid-token"})
        )
        assert response.status_code == 404


# ============================================================================
# newsletter_unsubscribe view Tests
# ============================================================================


@pytest.mark.django_db
class TestNewsletterUnsubscribeView:
    """Tests for the newsletter_unsubscribe function-based view."""

    def test_unsubscribe_valid_token(self, client):
        sub = NewsletterSubscriber.objects.create(email="unsub@example.com")
        sub.confirm_subscription()
        response = client.get(
            reverse("website:newsletter_unsubscribe", kwargs={"token": sub.confirmation_token})
        )
        assert response.status_code == 302  # redirect
        sub.refresh_from_db()
        assert sub.status == "unsubscribed"
        assert sub.unsubscribed_at is not None

    def test_unsubscribe_invalid_token_returns_404(self, client):
        response = client.get(
            reverse("website:newsletter_unsubscribe", kwargs={"token": "nonexistent"})
        )
        assert response.status_code == 404


# ============================================================================
# create_checkout_session view Tests
# ============================================================================


@pytest.mark.django_db
class TestCreateCheckoutSessionView:
    """Tests for the create_checkout_session function-based view."""

    @patch("apps.website.views.stripe.checkout.Session.create")
    def test_successful_checkout_session(self, mock_stripe, client):
        mock_stripe.return_value = MagicMock(id="cs_test_123")
        data = {"price_id": "price_abc123"}
        response = client.post(
            reverse("website:create_checkout_session"),
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["sessionId"] == "cs_test_123"

    def test_missing_price_id_returns_400(self, client):
        data = {}
        response = client.post(
            reverse("website:create_checkout_session"),
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "Price ID is required" in result["error"]

    @patch("apps.website.views.stripe.checkout.Session.create")
    def test_stripe_exception_returns_400(self, mock_stripe, client):
        mock_stripe.side_effect = Exception("Stripe error")
        data = {"price_id": "price_invalid"}
        response = client.post(
            reverse("website:create_checkout_session"),
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        result = response.json()
        assert "error" in result

    def test_get_method_not_allowed(self, client):
        response = client.get(reverse("website:create_checkout_session"))
        assert response.status_code == 405

    @patch("apps.website.views.stripe.checkout.Session.create")
    def test_authenticated_user_passes_email(self, mock_stripe, rf):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        mock_stripe.return_value = MagicMock(id="cs_auth_123")
        user = User(email="user@example.com", is_authenticated=True)

        request = rf.post(
            reverse("website:create_checkout_session"),
            data=json.dumps({"price_id": "price_test"}),
            content_type="application/json",
        )
        request.user = user
        response = create_checkout_session(request)
        assert response.status_code == 200
        # Verify Stripe was called with customer_email
        call_kwargs = mock_stripe.call_args[1]
        assert call_kwargs["customer_email"] == "user@example.com"


# ============================================================================
# robots.txt and sitemap.xml Tests
# ============================================================================


@pytest.mark.django_db
class TestSEOFiles:
    """Tests for robots.txt and sitemap.xml views."""

    def test_robots_txt(self, client):
        response = client.get(reverse("website:robots"))
        assert response.status_code == 200
        assert response["Content-Type"] == "text/plain"
        content = response.content.decode()
        assert "User-agent: *" in content
        assert "Allow: /" in content
        assert "Sitemap:" in content

    def test_sitemap_xml(self, client):
        response = client.get(reverse("website:sitemap"))
        assert response.status_code == 200
        assert response["Content-Type"] == "application/xml"
        content = response.content.decode()
        assert '<?xml version="1.0"' in content
        assert "<urlset" in content
        assert "<loc>" in content
        assert "aureon.rhematek-solutions.com" in content
