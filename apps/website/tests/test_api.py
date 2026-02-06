"""
Tests for website app API endpoints.

Covers: api_site_settings, api_services, api_service_detail, api_pricing,
api_testimonials, api_faqs, api_blog_posts, api_blog_post_detail,
api_blog_categories, api_case_studies, api_case_study_detail,
api_team, api_contact, api_newsletter, api_response helper.
"""
import json
import pytest
from unittest.mock import patch
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.website.models import (
    BlogCategory,
    BlogPost,
    BlogTag,
    CaseStudy,
    CaseStudyCategory,
    ContactSubmission,
    FAQ,
    NewsletterSubscriber,
    Service,
    SiteSettings,
    TeamMember,
    Testimonial,
)
from apps.website.api import api_response

User = get_user_model()


@pytest.fixture
def api_client():
    """Django test client for API calls."""
    return Client()


@pytest.fixture
def site_settings(db):
    """Create site settings for tests."""
    return SiteSettings.objects.create(
        pk=1,
        company_name="Aureon Test",
        tagline="Test Tagline",
        contact_email="test@aureon.io",
        phone="+1234567890",
        address="123 Test St",
        twitter_url="https://twitter.com/test",
        linkedin_url="https://linkedin.com/test",
        github_url="https://github.com/test",
        facebook_url="https://facebook.com/test",
    )


# ============================================================================
# api_response helper Tests
# ============================================================================


class TestApiResponse:
    """Tests for the api_response helper function."""

    def test_success_response(self):
        response = api_response({"key": "value"})
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] == "success"
        assert data["data"] == {"key": "value"}

    def test_error_response(self):
        response = api_response({"error": "Something went wrong"}, status=400)
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["status"] == "error"

    def test_cors_headers(self):
        response = api_response({})
        assert response["Access-Control-Allow-Origin"] == "*"
        assert "GET" in response["Access-Control-Allow-Methods"]
        assert "POST" in response["Access-Control-Allow-Methods"]
        assert "Content-Type" in response["Access-Control-Allow-Headers"]

    def test_success_response_with_list(self):
        response = api_response([1, 2, 3])
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["data"] == [1, 2, 3]

    def test_500_error_response(self):
        response = api_response("Internal error", status=500)
        assert response.status_code == 500
        data = json.loads(response.content)
        assert data["status"] == "error"

    def test_404_error_response(self):
        response = api_response({"error": "Not found"}, status=404)
        assert response.status_code == 404


# ============================================================================
# api_site_settings Tests
# ============================================================================


@pytest.mark.django_db
class TestApiSiteSettings:
    """Tests for the api_site_settings endpoint."""

    def test_get_site_settings(self, api_client, site_settings):
        response = api_client.get("/api/v1/website/settings/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_site_settings_returns_expected_keys(self, api_client, site_settings):
        response = api_client.get("/api/v1/website/settings/")
        data = response.json()["data"]
        expected_keys = [
            "site_name", "site_tagline", "contact_email",
            "contact_phone", "address", "twitter_url",
            "linkedin_url", "github_url", "facebook_url",
        ]
        for key in expected_keys:
            assert key in data

    def test_post_not_allowed(self, api_client, site_settings):
        response = api_client.post("/api/v1/website/settings/")
        assert response.status_code == 405

    def test_settings_fallback_values(self, api_client, db):
        """Test that settings endpoint works even without explicit settings."""
        # get_settings will auto-create
        response = api_client.get("/api/v1/website/settings/")
        assert response.status_code == 200


# ============================================================================
# api_services Tests
# ============================================================================


@pytest.mark.django_db
class TestApiServices:
    """Tests for the api_services endpoint."""

    def test_empty_services(self, api_client):
        response = api_client.get("/api/v1/website/services/")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

    def test_returns_active_services_only(self, api_client):
        Service.objects.create(
            name="Active Service",
            short_description="Desc",
            description="Full",
            is_active=True,
            order=1,
        )
        Service.objects.create(
            name="Inactive Service",
            short_description="Desc",
            description="Full",
            is_active=False,
            order=2,
        )
        response = api_client.get("/api/v1/website/services/")
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Active Service"

    def test_services_ordered_by_order(self, api_client):
        Service.objects.create(
            name="Second",
            short_description="D",
            description="F",
            is_active=True,
            order=2,
        )
        Service.objects.create(
            name="First",
            short_description="D",
            description="F",
            is_active=True,
            order=1,
        )
        response = api_client.get("/api/v1/website/services/")
        data = response.json()["data"]
        assert data[0]["name"] == "First"
        assert data[1]["name"] == "Second"

    def test_service_data_structure(self, api_client):
        Service.objects.create(
            name="Test Service",
            short_description="Short",
            description="Full description",
            is_active=True,
        )
        response = api_client.get("/api/v1/website/services/")
        data = response.json()["data"][0]
        assert "id" in data
        assert "name" in data
        assert "slug" in data
        assert "short_description" in data
        assert "description" in data

    def test_post_not_allowed(self, api_client):
        response = api_client.post("/api/v1/website/services/")
        assert response.status_code == 405


# ============================================================================
# api_service_detail Tests
# ============================================================================


@pytest.mark.django_db
class TestApiServiceDetail:
    """Tests for the api_service_detail endpoint."""

    def test_get_existing_service(self, api_client):
        service = Service.objects.create(
            name="Invoicing",
            short_description="Invoice management",
            description="Full invoicing",
            is_active=True,
        )
        response = api_client.get(f"/api/v1/website/services/{service.slug}/")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "Invoicing"

    def test_inactive_service_returns_404(self, api_client):
        service = Service.objects.create(
            name="Hidden",
            short_description="D",
            description="F",
            is_active=False,
        )
        response = api_client.get(f"/api/v1/website/services/{service.slug}/")
        assert response.status_code == 404

    def test_nonexistent_service_returns_404(self, api_client):
        response = api_client.get("/api/v1/website/services/does-not-exist/")
        assert response.status_code == 404


# ============================================================================
# api_pricing Tests
# ============================================================================


@pytest.mark.django_db
class TestApiPricing:
    """Tests for the api_pricing endpoint."""

    def test_returns_pricing_plans(self, api_client):
        response = api_client.get("/api/v1/website/pricing/")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 4  # Starter, Pro, Business, Enterprise

    def test_pricing_plan_names(self, api_client):
        response = api_client.get("/api/v1/website/pricing/")
        data = response.json()["data"]
        names = [p["name"] for p in data]
        assert "Starter" in names
        assert "Pro" in names
        assert "Business" in names
        assert "Enterprise" in names

    def test_popular_plan_marked(self, api_client):
        response = api_client.get("/api/v1/website/pricing/")
        data = response.json()["data"]
        popular_plans = [p for p in data if p.get("popular")]
        assert len(popular_plans) == 1
        assert popular_plans[0]["name"] == "Pro"

    def test_starter_plan_is_free(self, api_client):
        response = api_client.get("/api/v1/website/pricing/")
        data = response.json()["data"]
        starter = [p for p in data if p["name"] == "Starter"][0]
        assert starter["price_monthly"] == 0
        assert starter["price_yearly"] == 0

    def test_enterprise_plan_no_price(self, api_client):
        response = api_client.get("/api/v1/website/pricing/")
        data = response.json()["data"]
        enterprise = [p for p in data if p["name"] == "Enterprise"][0]
        assert enterprise["price_monthly"] is None
        assert enterprise["price_yearly"] is None

    def test_plan_has_features(self, api_client):
        response = api_client.get("/api/v1/website/pricing/")
        data = response.json()["data"]
        for plan in data:
            assert "features" in plan
            assert len(plan["features"]) > 0

    def test_post_not_allowed(self, api_client):
        response = api_client.post("/api/v1/website/pricing/")
        assert response.status_code == 405


# ============================================================================
# api_testimonials Tests
# ============================================================================


@pytest.mark.django_db
class TestApiTestimonials:
    """Tests for the api_testimonials endpoint."""

    def test_empty_testimonials(self, api_client):
        response = api_client.get("/api/v1/website/testimonials/")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_returns_active_testimonials_only(self, api_client):
        Testimonial.objects.create(
            client_name="Active",
            client_role="CEO",
            content="Great!",
            is_active=True,
        )
        Testimonial.objects.create(
            client_name="Inactive",
            client_role="CTO",
            content="Hidden",
            is_active=False,
        )
        response = api_client.get("/api/v1/website/testimonials/")
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["client_name"] == "Active"

    def test_testimonial_data_structure(self, api_client):
        Testimonial.objects.create(
            client_name="John",
            client_role="Manager",
            client_company="Test Inc",
            content="Amazing platform!",
            rating=4,
            is_active=True,
        )
        response = api_client.get("/api/v1/website/testimonials/")
        data = response.json()["data"][0]
        assert data["client_name"] == "John"
        assert data["client_role"] == "Manager"
        assert data["client_company"] == "Test Inc"
        assert data["content"] == "Amazing platform!"
        assert data["rating"] == 4

    def test_max_10_testimonials(self, api_client):
        for i in range(15):
            Testimonial.objects.create(
                client_name=f"Client {i}",
                client_role="Role",
                content="Content",
                is_active=True,
                order=i,
            )
        response = api_client.get("/api/v1/website/testimonials/")
        data = response.json()["data"]
        assert len(data) == 10

    def test_ordered_by_order_field(self, api_client):
        Testimonial.objects.create(
            client_name="Second",
            client_role="R",
            content="C",
            is_active=True,
            order=2,
        )
        Testimonial.objects.create(
            client_name="First",
            client_role="R",
            content="C",
            is_active=True,
            order=1,
        )
        response = api_client.get("/api/v1/website/testimonials/")
        data = response.json()["data"]
        assert data[0]["client_name"] == "First"


# ============================================================================
# api_faqs Tests
# ============================================================================


@pytest.mark.django_db
class TestApiFaqs:
    """Tests for the api_faqs endpoint."""

    def test_empty_faqs(self, api_client):
        response = api_client.get("/api/v1/website/faqs/")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["categories"] == {}
        assert data["all"] == []

    def test_returns_active_faqs_only(self, api_client):
        FAQ.objects.create(
            question="Active?",
            answer="Yes",
            is_active=True,
        )
        FAQ.objects.create(
            question="Inactive?",
            answer="No",
            is_active=False,
        )
        response = api_client.get("/api/v1/website/faqs/")
        data = response.json()["data"]
        assert len(data["all"]) == 1

    def test_faqs_grouped_by_category(self, api_client):
        FAQ.objects.create(
            question="General Q?",
            answer="A",
            category="general",
            is_active=True,
        )
        FAQ.objects.create(
            question="Pricing Q?",
            answer="A",
            category="pricing",
            is_active=True,
        )
        response = api_client.get("/api/v1/website/faqs/")
        data = response.json()["data"]
        assert "general" in data["categories"]
        assert "pricing" in data["categories"]
        assert len(data["categories"]["general"]) == 1
        assert len(data["categories"]["pricing"]) == 1

    def test_faq_data_structure(self, api_client):
        FAQ.objects.create(
            question="What is Aureon?",
            answer="A platform.",
            category="general",
            is_active=True,
        )
        response = api_client.get("/api/v1/website/faqs/")
        faq = response.json()["data"]["all"][0]
        assert "id" in faq
        assert "question" in faq
        assert "answer" in faq
        assert "category" in faq

    def test_post_not_allowed(self, api_client):
        response = api_client.post("/api/v1/website/faqs/")
        assert response.status_code == 405


# ============================================================================
# api_blog_posts Tests
# ============================================================================


@pytest.mark.django_db
class TestApiBlogPosts:
    """Tests for the api_blog_posts endpoint."""

    @pytest.fixture
    def author(self, db):
        return User.objects.create_user(
            email="blogauthor@example.com",
            password="TestPass123!",
            first_name="Blog",
            last_name="Author",
        )

    def test_empty_blog_posts(self, api_client):
        response = api_client.get("/api/v1/website/posts/")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_returns_published_only(self, api_client, author):
        now = timezone.now()
        BlogPost.objects.create(
            title="Published Post",
            author=author,
            excerpt="Excerpt",
            content="Content",
            status="published",
            published_at=now - timedelta(hours=1),
        )
        BlogPost.objects.create(
            title="Draft Post",
            author=author,
            excerpt="Excerpt",
            content="Content",
            status="draft",
        )
        response = api_client.get("/api/v1/website/posts/")
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["title"] == "Published Post"

    def test_post_data_structure(self, api_client, author):
        category = BlogCategory.objects.create(name="Tech")
        now = timezone.now()
        BlogPost.objects.create(
            title="Test Post",
            author=author,
            category=category,
            excerpt="Test excerpt",
            content="Test content",
            status="published",
            published_at=now,
        )
        response = api_client.get("/api/v1/website/posts/")
        post = response.json()["data"][0]
        assert "id" in post
        assert "title" in post
        assert "slug" in post
        assert "excerpt" in post
        assert "category" in post
        assert "author" in post
        assert "published_at" in post
        assert "featured" in post

    def test_post_without_author(self, api_client, author):
        now = timezone.now()
        post = BlogPost.objects.create(
            title="No Author Post",
            excerpt="E",
            content="C",
            status="published",
            published_at=now,
            author=None,
        )
        response = api_client.get("/api/v1/website/posts/")
        data = response.json()["data"][0]
        assert data["author"] == "Aureon Team"

    def test_post_without_category(self, api_client, author):
        now = timezone.now()
        BlogPost.objects.create(
            title="No Cat Post",
            author=author,
            excerpt="E",
            content="C",
            status="published",
            published_at=now,
            category=None,
        )
        response = api_client.get("/api/v1/website/posts/")
        data = response.json()["data"][0]
        assert data["category"] is None

    def test_max_20_posts(self, api_client, author):
        now = timezone.now()
        for i in range(25):
            BlogPost.objects.create(
                title=f"Post {i}",
                author=author,
                excerpt="E",
                content="C",
                status="published",
                published_at=now - timedelta(hours=i),
            )
        response = api_client.get("/api/v1/website/posts/")
        assert len(response.json()["data"]) == 20


# ============================================================================
# api_blog_post_detail Tests
# ============================================================================


@pytest.mark.django_db
class TestApiBlogPostDetail:
    """Tests for the api_blog_post_detail endpoint."""

    @pytest.fixture
    def author(self, db):
        return User.objects.create_user(
            email="detailauthor@example.com",
            password="TestPass123!",
            first_name="Detail",
            last_name="Author",
        )

    def test_get_published_post(self, api_client, author):
        now = timezone.now()
        post = BlogPost.objects.create(
            title="Detail Post",
            author=author,
            excerpt="Excerpt",
            content="<p>Content</p>",
            status="published",
            published_at=now,
        )
        response = api_client.get(f"/api/v1/website/posts/{post.slug}/")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["title"] == "Detail Post"
        assert data["content"] == "<p>Content</p>"

    def test_draft_post_returns_404(self, api_client, author):
        post = BlogPost.objects.create(
            title="Draft",
            author=author,
            excerpt="E",
            content="C",
            status="draft",
        )
        response = api_client.get(f"/api/v1/website/posts/{post.slug}/")
        assert response.status_code == 404

    def test_nonexistent_post_returns_404(self, api_client):
        response = api_client.get("/api/v1/website/posts/nonexistent-slug/")
        assert response.status_code == 404

    def test_post_detail_includes_tags(self, api_client, author):
        now = timezone.now()
        post = BlogPost.objects.create(
            title="Tagged Post",
            author=author,
            excerpt="E",
            content="C",
            status="published",
            published_at=now,
        )
        tag = BlogTag.objects.create(name="Python")
        post.tags.add(tag)
        response = api_client.get(f"/api/v1/website/posts/{post.slug}/")
        data = response.json()["data"]
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "Python"

    def test_post_detail_without_author(self, api_client):
        now = timezone.now()
        post = BlogPost.objects.create(
            title="Orphan Post",
            excerpt="E",
            content="C",
            status="published",
            published_at=now,
            author=None,
        )
        response = api_client.get(f"/api/v1/website/posts/{post.slug}/")
        data = response.json()["data"]
        assert data["author"] == "Aureon Team"


# ============================================================================
# api_blog_categories Tests
# ============================================================================


@pytest.mark.django_db
class TestApiBlogCategories:
    """Tests for the api_blog_categories endpoint."""

    def test_empty_categories(self, api_client):
        response = api_client.get("/api/v1/website/categories/")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_returns_categories(self, api_client):
        BlogCategory.objects.create(name="Tech")
        BlogCategory.objects.create(name="Business")
        response = api_client.get("/api/v1/website/categories/")
        data = response.json()["data"]
        assert len(data) == 2

    def test_category_data_structure(self, api_client):
        BlogCategory.objects.create(name="Technology")
        response = api_client.get("/api/v1/website/categories/")
        cat = response.json()["data"][0]
        assert "id" in cat
        assert "name" in cat
        assert "slug" in cat
        assert "post_count" in cat


# ============================================================================
# api_case_studies Tests
# ============================================================================


@pytest.mark.django_db
class TestApiCaseStudies:
    """Tests for the api_case_studies endpoint."""

    def test_empty_case_studies(self, api_client):
        response = api_client.get("/api/v1/website/case-studies/")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_returns_published_only(self, api_client):
        now = timezone.now()
        CaseStudy.objects.create(
            title="Published Study",
            client_name="Client",
            excerpt="Excerpt",
            challenge="C",
            solution="S",
            results="R",
            status="published",
            published_at=now,
        )
        CaseStudy.objects.create(
            title="Draft Study",
            client_name="Client2",
            excerpt="Excerpt",
            challenge="C",
            solution="S",
            results="R",
            status="draft",
        )
        response = api_client.get("/api/v1/website/case-studies/")
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["title"] == "Published Study"

    def test_case_study_data_structure(self, api_client):
        now = timezone.now()
        CaseStudy.objects.create(
            title="Test Study",
            client_name="Test Client",
            excerpt="Test excerpt",
            challenge="Challenge",
            solution="Solution",
            results="Results",
            status="published",
            published_at=now,
        )
        response = api_client.get("/api/v1/website/case-studies/")
        cs = response.json()["data"][0]
        assert "id" in cs
        assert "title" in cs
        assert "slug" in cs
        assert "excerpt" in cs
        assert "client_name" in cs
        assert "featured" in cs

    def test_max_10_case_studies(self, api_client):
        now = timezone.now()
        for i in range(15):
            CaseStudy.objects.create(
                title=f"Study {i}",
                client_name=f"Client {i}",
                excerpt="E",
                challenge="C",
                solution="S",
                results="R",
                status="published",
                published_at=now - timedelta(hours=i),
            )
        response = api_client.get("/api/v1/website/case-studies/")
        assert len(response.json()["data"]) == 10


# ============================================================================
# api_case_study_detail Tests
# ============================================================================


@pytest.mark.django_db
class TestApiCaseStudyDetail:
    """Tests for the api_case_study_detail endpoint."""

    def test_get_published_case_study(self, api_client):
        now = timezone.now()
        cs = CaseStudy.objects.create(
            title="Detail Study",
            client_name="Client",
            excerpt="Excerpt",
            challenge="Challenge desc",
            solution="Solution desc",
            results="Results desc",
            testimonial="Great work!",
            status="published",
            published_at=now,
        )
        response = api_client.get(f"/api/v1/website/case-studies/{cs.slug}/")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["title"] == "Detail Study"

    def test_draft_returns_404(self, api_client):
        cs = CaseStudy.objects.create(
            title="Draft Study",
            client_name="Client",
            excerpt="E",
            challenge="C",
            solution="S",
            results="R",
            status="draft",
        )
        response = api_client.get(f"/api/v1/website/case-studies/{cs.slug}/")
        assert response.status_code == 404

    def test_nonexistent_returns_404(self, api_client):
        response = api_client.get("/api/v1/website/case-studies/nonexistent/")
        assert response.status_code == 404


# ============================================================================
# api_team Tests
# ============================================================================


@pytest.mark.django_db
class TestApiTeam:
    """Tests for the api_team endpoint."""

    def test_empty_team(self, api_client):
        response = api_client.get("/api/v1/website/team/")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_returns_active_members_only(self, api_client):
        TeamMember.objects.create(
            name="Active Member",
            role="CEO",
            bio="Bio",
            is_active=True,
        )
        TeamMember.objects.create(
            name="Inactive Member",
            role="CTO",
            bio="Bio",
            is_active=False,
        )
        response = api_client.get("/api/v1/website/team/")
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Active Member"

    def test_team_data_structure(self, api_client):
        TeamMember.objects.create(
            name="John",
            role="Developer",
            bio="A developer",
            is_active=True,
            is_leadership=True,
        )
        response = api_client.get("/api/v1/website/team/")
        member = response.json()["data"][0]
        assert "id" in member
        assert "name" in member
        assert "bio" in member
        assert "is_leadership" in member

    def test_ordered_by_order_field(self, api_client):
        TeamMember.objects.create(
            name="Second",
            role="R",
            bio="B",
            is_active=True,
            order=2,
        )
        TeamMember.objects.create(
            name="First",
            role="R",
            bio="B",
            is_active=True,
            order=1,
        )
        response = api_client.get("/api/v1/website/team/")
        data = response.json()["data"]
        assert data[0]["name"] == "First"


# ============================================================================
# api_contact Tests
# ============================================================================


@pytest.mark.django_db
class TestApiContact:
    """Tests for the api_contact endpoint."""

    @patch("apps.website.api.send_mail")
    def test_successful_contact(self, mock_send, api_client):
        data = {
            "name": "John",
            "email": "john@example.com",
            "message": "Hello, I have a question.",
            "subject": "Question",
        }
        response = api_client.post(
            "/api/v1/website/contact/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()["data"]
        assert result["success"] is True
        assert ContactSubmission.objects.count() == 1

    @patch("apps.website.api.send_mail")
    def test_contact_with_optional_fields(self, mock_send, api_client):
        data = {
            "name": "Jane",
            "email": "jane@example.com",
            "message": "Question here.",
            "phone": "+123",
            "company": "Test Inc",
            "subject": "Sales Question",
        }
        response = api_client.post(
            "/api/v1/website/contact/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        submission = ContactSubmission.objects.first()
        assert submission.phone == "+123"
        assert submission.company == "Test Inc"

    def test_missing_required_name(self, api_client):
        data = {"email": "test@example.com", "message": "Msg"}
        response = api_client.post(
            "/api/v1/website/contact/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_missing_required_email(self, api_client):
        data = {"name": "John", "message": "Msg"}
        response = api_client.post(
            "/api/v1/website/contact/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_missing_required_message(self, api_client):
        data = {"name": "John", "email": "john@example.com"}
        response = api_client.post(
            "/api/v1/website/contact/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_invalid_json(self, api_client):
        response = api_client.post(
            "/api/v1/website/contact/",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_get_not_allowed(self, api_client):
        response = api_client.get("/api/v1/website/contact/")
        assert response.status_code == 405

    @patch("apps.website.api.send_mail", side_effect=Exception("SMTP Error"))
    def test_email_failure_does_not_fail_request(self, mock_send, api_client):
        data = {
            "name": "Test",
            "email": "test@example.com",
            "message": "Test msg",
        }
        response = api_client.post(
            "/api/v1/website/contact/",
            data=json.dumps(data),
            content_type="application/json",
        )
        # Should still succeed since email failure is caught
        assert response.status_code == 200

    @patch("apps.website.api.send_mail")
    def test_default_subject_when_not_provided(self, mock_send, api_client):
        data = {
            "name": "Test",
            "email": "test@example.com",
            "message": "Test msg",
        }
        response = api_client.post(
            "/api/v1/website/contact/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        submission = ContactSubmission.objects.first()
        assert submission.subject == "General Inquiry"


# ============================================================================
# api_newsletter Tests
# ============================================================================


@pytest.mark.django_db
class TestApiNewsletter:
    """Tests for the api_newsletter endpoint."""

    def test_successful_subscription(self, api_client):
        data = {"email": "new@example.com"}
        response = api_client.post(
            "/api/v1/website/newsletter/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()["data"]
        assert result["success"] is True
        assert "subscribing" in result["message"] or "subscribed" in result["message"]

    def test_already_subscribed(self, api_client):
        NewsletterSubscriber.objects.create(email="existing@example.com")
        data = {"email": "existing@example.com"}
        response = api_client.post(
            "/api/v1/website/newsletter/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()["data"]
        assert "already subscribed" in result["message"]

    def test_missing_email(self, api_client):
        data = {}
        response = api_client.post(
            "/api/v1/website/newsletter/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_invalid_json(self, api_client):
        response = api_client.post(
            "/api/v1/website/newsletter/",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_get_not_allowed(self, api_client):
        response = api_client.get("/api/v1/website/newsletter/")
        assert response.status_code == 405
