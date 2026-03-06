"""
Tests for website app context processors.

Covers: site_settings, navigation, seo_defaults, analytics_ids,
feature_flags, current_year.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from django.test import RequestFactory

from apps.website.context_processors import (
    site_settings,
    navigation,
    seo_defaults,
    analytics_ids,
    feature_flags,
    current_year,
)
from apps.website.models import SiteSettings, BlogCategory


@pytest.fixture
def rf():
    """Django request factory."""
    return RequestFactory()


@pytest.fixture
def settings_obj(db):
    """Create site settings."""
    return SiteSettings.objects.create(
        pk=1,
        company_name="Aureon Test",
        tagline="Test Tagline",
        default_meta_title="Test Meta Title",
        default_meta_description="Test Meta Description",
        default_meta_keywords="test, keywords",
        google_analytics_id="G-TEST123",
        google_tag_manager_id="GTM-TEST456",
        facebook_pixel_id="FB-789",
        maintenance_mode=False,
        show_blog=True,
        show_store=True,
        allow_newsletter_signup=True,
    )


# ============================================================================
# site_settings context processor Tests
# ============================================================================


@pytest.mark.django_db
class TestSiteSettingsContextProcessor:
    """Tests for the site_settings context processor."""

    def test_returns_site_settings(self, rf, settings_obj):
        request = rf.get("/")
        context = site_settings(request)
        assert "site_settings" in context
        assert context["site_settings"].pk == settings_obj.pk

    def test_auto_creates_settings_if_none(self, rf):
        request = rf.get("/")
        context = site_settings(request)
        assert "site_settings" in context
        assert context["site_settings"] is not None

    def test_returns_same_settings_instance(self, rf, settings_obj):
        request = rf.get("/")
        context1 = site_settings(request)
        context2 = site_settings(request)
        assert context1["site_settings"].pk == context2["site_settings"].pk


# ============================================================================
# navigation context processor Tests
# ============================================================================


@pytest.mark.django_db
class TestNavigationContextProcessor:
    """Tests for the navigation context processor."""

    def test_returns_main_menu(self, rf, settings_obj):
        request = rf.get("/")
        context = navigation(request)
        assert "main_menu" in context
        assert isinstance(context["main_menu"], list)

    def test_main_menu_items(self, rf, settings_obj):
        request = rf.get("/")
        context = navigation(request)
        menu = context["main_menu"]
        titles = [item["title"] for item in menu]
        assert "Home" in titles
        assert "About" in titles
        assert "Services" in titles
        assert "Pricing" in titles
        assert "Blog" in titles
        assert "Contact" in titles

    def test_home_active_on_root(self, rf, settings_obj):
        request = rf.get("/")
        context = navigation(request)
        menu = context["main_menu"]
        home = [item for item in menu if item["title"] == "Home"][0]
        assert home["active"] is True

    def test_about_active_on_about_page(self, rf, settings_obj):
        request = rf.get("/about/")
        context = navigation(request)
        menu = context["main_menu"]
        about = [item for item in menu if item["title"] == "About"][0]
        assert about["active"] is True

    def test_services_active_on_services_page(self, rf, settings_obj):
        request = rf.get("/services/invoicing/")
        context = navigation(request)
        menu = context["main_menu"]
        services = [item for item in menu if item["title"] == "Services"][0]
        assert services["active"] is True

    def test_pricing_active_on_pricing_page(self, rf, settings_obj):
        request = rf.get("/pricing/")
        context = navigation(request)
        menu = context["main_menu"]
        pricing = [item for item in menu if item["title"] == "Pricing"][0]
        assert pricing["active"] is True

    def test_blog_active_on_blog_page(self, rf, settings_obj):
        request = rf.get("/blog/my-post/")
        context = navigation(request)
        menu = context["main_menu"]
        blog = [item for item in menu if item["title"] == "Blog"][0]
        assert blog["active"] is True

    def test_contact_active_on_contact_page(self, rf, settings_obj):
        request = rf.get("/contact/")
        context = navigation(request)
        menu = context["main_menu"]
        contact = [item for item in menu if item["title"] == "Contact"][0]
        assert contact["active"] is True

    def test_services_has_submenu(self, rf, settings_obj):
        request = rf.get("/")
        context = navigation(request)
        menu = context["main_menu"]
        services = [item for item in menu if item["title"] == "Services"][0]
        assert "submenu" in services
        assert len(services["submenu"]) > 0

    def test_returns_blog_categories(self, rf, settings_obj):
        BlogCategory.objects.create(name="Tech")
        BlogCategory.objects.create(name="Business")
        request = rf.get("/")
        context = navigation(request)
        assert "blog_categories" in context

    def test_home_not_active_on_other_pages(self, rf, settings_obj):
        request = rf.get("/about/")
        context = navigation(request)
        menu = context["main_menu"]
        home = [item for item in menu if item["title"] == "Home"][0]
        assert home["active"] is False


# ============================================================================
# seo_defaults context processor Tests
# ============================================================================


@pytest.mark.django_db
class TestSeoDefaultsContextProcessor:
    """Tests for the seo_defaults context processor."""

    def test_returns_seo_data(self, rf, settings_obj):
        request = rf.get("/")
        context = seo_defaults(request)
        assert "seo_title" in context
        assert "seo_description" in context
        assert "seo_keywords" in context
        assert "canonical_url" in context
        assert "og_url" in context

    def test_uses_settings_values(self, rf, settings_obj):
        request = rf.get("/")
        context = seo_defaults(request)
        assert context["seo_title"] == "Test Meta Title"
        assert context["seo_description"] == "Test Meta Description"
        assert context["seo_keywords"] == "test, keywords"

    def test_fallback_values_when_empty(self, rf):
        SiteSettings.objects.create(pk=1)  # empty settings
        request = rf.get("/")
        context = seo_defaults(request)
        assert "Aureon" in context["seo_title"]
        assert context["seo_description"] != ""

    def test_canonical_url_includes_request_uri(self, rf, settings_obj):
        request = rf.get("/about/")
        context = seo_defaults(request)
        assert "/about/" in context["canonical_url"]

    def test_og_url_matches_canonical(self, rf, settings_obj):
        request = rf.get("/pricing/")
        context = seo_defaults(request)
        assert context["og_url"] == context["canonical_url"]

    def test_og_type_is_website(self, rf, settings_obj):
        request = rf.get("/")
        context = seo_defaults(request)
        assert context["og_type"] == "website"

    def test_og_site_name(self, rf, settings_obj):
        request = rf.get("/")
        context = seo_defaults(request)
        assert context["og_site_name"] == "Aureon Test"

    def test_twitter_card_type(self, rf, settings_obj):
        request = rf.get("/")
        context = seo_defaults(request)
        assert context["twitter_card"] == "summary_large_image"

    def test_twitter_site_handle(self, rf, settings_obj):
        request = rf.get("/")
        context = seo_defaults(request)
        assert context["twitter_site"] == "@aureonapp"

    def test_og_image_is_absolute_url(self, rf, settings_obj):
        request = rf.get("/")
        context = seo_defaults(request)
        assert context["og_image"].startswith("http")


# ============================================================================
# analytics_ids context processor Tests
# ============================================================================


@pytest.mark.django_db
class TestAnalyticsIdsContextProcessor:
    """Tests for the analytics_ids context processor."""

    def test_returns_analytics_ids(self, rf, settings_obj):
        request = rf.get("/")
        context = analytics_ids(request)
        assert "google_analytics_id" in context
        assert "google_tag_manager_id" in context
        assert "facebook_pixel_id" in context

    def test_returns_correct_values(self, rf, settings_obj):
        request = rf.get("/")
        context = analytics_ids(request)
        assert context["google_analytics_id"] == "G-TEST123"
        assert context["google_tag_manager_id"] == "GTM-TEST456"
        assert context["facebook_pixel_id"] == "FB-789"

    def test_empty_values_when_not_set(self, rf):
        SiteSettings.objects.create(pk=1)
        request = rf.get("/")
        context = analytics_ids(request)
        assert context["google_analytics_id"] == ""
        assert context["google_tag_manager_id"] == ""
        assert context["facebook_pixel_id"] == ""


# ============================================================================
# feature_flags context processor Tests
# ============================================================================


@pytest.mark.django_db
class TestFeatureFlagsContextProcessor:
    """Tests for the feature_flags context processor."""

    def test_returns_feature_flags(self, rf, settings_obj):
        request = rf.get("/")
        context = feature_flags(request)
        assert "maintenance_mode" in context
        assert "show_blog" in context
        assert "show_store" in context
        assert "allow_newsletter_signup" in context

    def test_returns_correct_values(self, rf, settings_obj):
        request = rf.get("/")
        context = feature_flags(request)
        assert context["maintenance_mode"] is False
        assert context["show_blog"] is True
        assert context["show_store"] is True
        assert context["allow_newsletter_signup"] is True

    def test_maintenance_mode_enabled(self, rf):
        SiteSettings.objects.create(pk=1, maintenance_mode=True)
        request = rf.get("/")
        context = feature_flags(request)
        assert context["maintenance_mode"] is True

    def test_blog_disabled(self, rf):
        SiteSettings.objects.create(pk=1, show_blog=False)
        request = rf.get("/")
        context = feature_flags(request)
        assert context["show_blog"] is False

    def test_store_disabled(self, rf):
        SiteSettings.objects.create(pk=1, show_store=False)
        request = rf.get("/")
        context = feature_flags(request)
        assert context["show_store"] is False

    def test_newsletter_disabled(self, rf):
        SiteSettings.objects.create(pk=1, allow_newsletter_signup=False)
        request = rf.get("/")
        context = feature_flags(request)
        assert context["allow_newsletter_signup"] is False


# ============================================================================
# current_year context processor Tests
# ============================================================================


class TestCurrentYearContextProcessor:
    """Tests for the current_year context processor."""

    def test_returns_current_year(self, rf):
        request = rf.get("/")
        context = current_year(request)
        assert "current_year" in context
        assert context["current_year"] == datetime.now().year

    def test_year_is_integer(self, rf):
        request = rf.get("/")
        context = current_year(request)
        assert isinstance(context["current_year"], int)

    def test_year_is_reasonable(self, rf):
        request = rf.get("/")
        context = current_year(request)
        assert context["current_year"] >= 2024
        assert context["current_year"] <= 2100
