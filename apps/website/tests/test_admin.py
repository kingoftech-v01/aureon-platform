"""
Tests for website app admin configuration.

Covers: Admin registration, custom display methods, actions, permissions,
and fieldsets for all website models.
"""
import pytest
from unittest.mock import MagicMock

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone

from apps.website.admin import (
    BlogCategoryAdmin,
    BlogTagAdmin,
    BlogPostAdmin,
    ProductAdmin,
    ContactSubmissionAdmin,
    NewsletterSubscriberAdmin,
    SiteSettingsAdmin,
    CaseStudyCategoryAdmin,
    CaseStudyAdmin,
    ServiceAdmin,
    TeamMemberAdmin,
    FAQAdmin,
    TestimonialAdmin,
)
from apps.website.models import (
    BlogCategory,
    BlogTag,
    BlogPost,
    Product,
    ContactSubmission,
    NewsletterSubscriber,
    SiteSettings,
    CaseStudyCategory,
    CaseStudy,
    Service,
    TeamMember,
    FAQ,
    Testimonial,
)

User = get_user_model()


@pytest.fixture
def rf():
    """Request factory."""
    return RequestFactory()


@pytest.fixture
def admin_site():
    """Return the default admin site."""
    return admin.site


# ============================================================================
# Model Registration Tests
# ============================================================================


class TestAdminRegistration:
    """Test that all models are registered with the admin site."""

    def test_blog_category_registered(self, admin_site):
        assert BlogCategory in admin_site._registry

    def test_blog_tag_registered(self, admin_site):
        assert BlogTag in admin_site._registry

    def test_blog_post_registered(self, admin_site):
        assert BlogPost in admin_site._registry

    def test_product_registered(self, admin_site):
        assert Product in admin_site._registry

    def test_contact_submission_registered(self, admin_site):
        assert ContactSubmission in admin_site._registry

    def test_newsletter_subscriber_registered(self, admin_site):
        assert NewsletterSubscriber in admin_site._registry

    def test_site_settings_registered(self, admin_site):
        assert SiteSettings in admin_site._registry

    def test_case_study_category_registered(self, admin_site):
        assert CaseStudyCategory in admin_site._registry

    def test_case_study_registered(self, admin_site):
        assert CaseStudy in admin_site._registry

    def test_service_registered(self, admin_site):
        assert Service in admin_site._registry

    def test_team_member_registered(self, admin_site):
        assert TeamMember in admin_site._registry

    def test_faq_registered(self, admin_site):
        assert FAQ in admin_site._registry

    def test_testimonial_registered(self, admin_site):
        assert Testimonial in admin_site._registry

    def test_blog_category_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[BlogCategory], BlogCategoryAdmin)

    def test_blog_tag_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[BlogTag], BlogTagAdmin)

    def test_blog_post_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[BlogPost], BlogPostAdmin)

    def test_product_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[Product], ProductAdmin)

    def test_contact_submission_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[ContactSubmission], ContactSubmissionAdmin)

    def test_newsletter_subscriber_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[NewsletterSubscriber], NewsletterSubscriberAdmin)

    def test_site_settings_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[SiteSettings], SiteSettingsAdmin)

    def test_case_study_category_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[CaseStudyCategory], CaseStudyCategoryAdmin)

    def test_case_study_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[CaseStudy], CaseStudyAdmin)

    def test_service_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[Service], ServiceAdmin)

    def test_team_member_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[TeamMember], TeamMemberAdmin)

    def test_faq_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[FAQ], FAQAdmin)

    def test_testimonial_admin_class(self, admin_site):
        assert isinstance(admin_site._registry[Testimonial], TestimonialAdmin)


# ============================================================================
# BlogCategoryAdmin Tests
# ============================================================================


@pytest.mark.django_db
class TestBlogCategoryAdmin:
    """Tests for BlogCategoryAdmin."""

    def test_list_display(self):
        model_admin = BlogCategoryAdmin(BlogCategory, admin.site)
        assert "name" in model_admin.list_display
        assert "slug" in model_admin.list_display
        assert "post_count" in model_admin.list_display

    def test_post_count_method(self):
        category = BlogCategory.objects.create(name="Test")
        model_admin = BlogCategoryAdmin(BlogCategory, admin.site)
        result = model_admin.post_count(category)
        assert "0" in str(result)

    def test_prepopulated_fields(self):
        model_admin = BlogCategoryAdmin(BlogCategory, admin.site)
        assert "slug" in model_admin.prepopulated_fields


# ============================================================================
# BlogTagAdmin Tests
# ============================================================================


@pytest.mark.django_db
class TestBlogTagAdmin:
    """Tests for BlogTagAdmin."""

    def test_list_display(self):
        model_admin = BlogTagAdmin(BlogTag, admin.site)
        assert "name" in model_admin.list_display
        assert "slug" in model_admin.list_display

    def test_post_count_method(self):
        tag = BlogTag.objects.create(name="Python")
        model_admin = BlogTagAdmin(BlogTag, admin.site)
        result = model_admin.post_count(tag)
        assert "0" in str(result)


# ============================================================================
# BlogPostAdmin Tests
# ============================================================================


@pytest.mark.django_db
class TestBlogPostAdmin:
    """Tests for BlogPostAdmin."""

    @pytest.fixture
    def author(self, db):
        return User.objects.create_user(
            email="blogadmin@example.com",
            password="TestPass123!",
            first_name="Blog",
            last_name="Admin",
        )

    def test_list_display(self):
        model_admin = BlogPostAdmin(BlogPost, admin.site)
        assert "title" in model_admin.list_display
        assert "status" in model_admin.list_display
        assert "views_count" in model_admin.list_display

    def test_featured_badge_featured(self, author):
        post = BlogPost.objects.create(
            title="Featured",
            author=author,
            excerpt="E",
            content="C",
            featured=True,
        )
        model_admin = BlogPostAdmin(BlogPost, admin.site)
        result = model_admin.featured_badge(post)
        assert "Featured" in str(result)

    def test_featured_badge_not_featured(self, author):
        post = BlogPost.objects.create(
            title="Not Featured",
            author=author,
            excerpt="E",
            content="C",
            featured=False,
        )
        model_admin = BlogPostAdmin(BlogPost, admin.site)
        result = model_admin.featured_badge(post)
        assert result == "-"

    def test_save_model_sets_author(self, rf, author):
        model_admin = BlogPostAdmin(BlogPost, admin.site)
        post = BlogPost(
            title="No Author",
            excerpt="E",
            content="C",
        )
        request = rf.get("/admin/")
        request.user = author
        form = MagicMock()
        model_admin.save_model(request, post, form, change=False)
        assert post.author == author

    def test_save_model_preserves_existing_author(self, rf, author):
        other_user = User.objects.create_user(
            email="other@example.com",
            password="TestPass123!",
        )
        model_admin = BlogPostAdmin(BlogPost, admin.site)
        post = BlogPost(
            title="With Author",
            author=other_user,
            excerpt="E",
            content="C",
        )
        request = rf.get("/admin/")
        request.user = author
        form = MagicMock()
        model_admin.save_model(request, post, form, change=True)
        assert post.author == other_user

    def test_publish_posts_action(self, rf, author):
        model_admin = BlogPostAdmin(BlogPost, admin.site)
        post = BlogPost.objects.create(
            title="Draft",
            author=author,
            excerpt="E",
            content="C",
            status="draft",
        )
        request = rf.get("/admin/")
        request.user = author
        # Mock message_user
        model_admin.message_user = MagicMock()
        model_admin.publish_posts(request, BlogPost.objects.filter(pk=post.pk))
        post.refresh_from_db()
        assert post.status == "published"

    def test_unpublish_posts_action(self, rf, author):
        model_admin = BlogPostAdmin(BlogPost, admin.site)
        post = BlogPost.objects.create(
            title="Published",
            author=author,
            excerpt="E",
            content="C",
            status="published",
            published_at=timezone.now(),
        )
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.unpublish_posts(request, BlogPost.objects.filter(pk=post.pk))
        post.refresh_from_db()
        assert post.status == "draft"

    def test_feature_posts_action(self, rf, author):
        model_admin = BlogPostAdmin(BlogPost, admin.site)
        post = BlogPost.objects.create(
            title="Unfeatured",
            author=author,
            excerpt="E",
            content="C",
            featured=False,
        )
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.feature_posts(request, BlogPost.objects.filter(pk=post.pk))
        post.refresh_from_db()
        assert post.featured is True

    def test_unfeature_posts_action(self, rf, author):
        model_admin = BlogPostAdmin(BlogPost, admin.site)
        post = BlogPost.objects.create(
            title="Featured",
            author=author,
            excerpt="E",
            content="C",
            featured=True,
        )
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.unfeature_posts(request, BlogPost.objects.filter(pk=post.pk))
        post.refresh_from_db()
        assert post.featured is False

    def test_actions_defined(self):
        model_admin = BlogPostAdmin(BlogPost, admin.site)
        assert "publish_posts" in model_admin.actions
        assert "unpublish_posts" in model_admin.actions
        assert "feature_posts" in model_admin.actions
        assert "unfeature_posts" in model_admin.actions


# ============================================================================
# ProductAdmin Tests
# ============================================================================


@pytest.mark.django_db
class TestProductAdmin:
    """Tests for ProductAdmin."""

    def test_list_display(self):
        model_admin = ProductAdmin(Product, admin.site)
        assert "name" in model_admin.list_display
        assert "price" in model_admin.list_display

    def test_discount_badge_with_discount(self):
        product = Product.objects.create(
            name="Discounted",
            short_description="D",
            description="F",
            price=50,
            compare_at_price=100,
        )
        model_admin = ProductAdmin(Product, admin.site)
        result = model_admin.discount_badge(product)
        assert "50% OFF" in str(result)

    def test_discount_badge_without_discount(self):
        product = Product.objects.create(
            name="Full Price",
            short_description="D",
            description="F",
            price=100,
        )
        model_admin = ProductAdmin(Product, admin.site)
        assert model_admin.discount_badge(product) == "-"

    def test_stripe_status_linked(self):
        product = Product.objects.create(
            name="Linked",
            short_description="D",
            description="F",
            price=100,
            stripe_price_id="price_123",
            stripe_product_id="prod_123",
        )
        model_admin = ProductAdmin(Product, admin.site)
        result = model_admin.stripe_status(product)
        assert "Linked" in str(result)

    def test_stripe_status_partial(self):
        product = Product.objects.create(
            name="Partial",
            short_description="D",
            description="F",
            price=100,
            stripe_product_id="prod_123",
        )
        model_admin = ProductAdmin(Product, admin.site)
        result = model_admin.stripe_status(product)
        assert "Partial" in str(result)

    def test_stripe_status_not_linked(self):
        product = Product.objects.create(
            name="Not Linked",
            short_description="D",
            description="F",
            price=100,
        )
        model_admin = ProductAdmin(Product, admin.site)
        result = model_admin.stripe_status(product)
        assert "Not Linked" in str(result)

    def test_activate_products_action(self, rf):
        product = Product.objects.create(
            name="Inactive",
            short_description="D",
            description="F",
            price=100,
            is_active=False,
        )
        model_admin = ProductAdmin(Product, admin.site)
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.activate_products(request, Product.objects.filter(pk=product.pk))
        product.refresh_from_db()
        assert product.is_active is True

    def test_deactivate_products_action(self, rf):
        product = Product.objects.create(
            name="Active",
            short_description="D",
            description="F",
            price=100,
            is_active=True,
        )
        model_admin = ProductAdmin(Product, admin.site)
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.deactivate_products(request, Product.objects.filter(pk=product.pk))
        product.refresh_from_db()
        assert product.is_active is False

    def test_feature_products_action(self, rf):
        product = Product.objects.create(
            name="Not Featured",
            short_description="D",
            description="F",
            price=100,
            is_featured=False,
        )
        model_admin = ProductAdmin(Product, admin.site)
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.feature_products(request, Product.objects.filter(pk=product.pk))
        product.refresh_from_db()
        assert product.is_featured is True


# ============================================================================
# ContactSubmissionAdmin Tests
# ============================================================================


@pytest.mark.django_db
class TestContactSubmissionAdmin:
    """Tests for ContactSubmissionAdmin."""

    def test_list_display(self):
        model_admin = ContactSubmissionAdmin(ContactSubmission, admin.site)
        assert "name" in model_admin.list_display
        assert "email" in model_admin.list_display
        assert "status_badge" in model_admin.list_display

    def test_status_badge_new(self):
        contact = ContactSubmission.objects.create(
            name="Test",
            email="test@example.com",
            subject="Subject",
            message="Message",
            status="new",
        )
        model_admin = ContactSubmissionAdmin(ContactSubmission, admin.site)
        result = model_admin.status_badge(contact)
        assert "New" in str(result)

    def test_status_badge_in_progress(self):
        contact = ContactSubmission.objects.create(
            name="Test",
            email="test@example.com",
            subject="Subject",
            message="Message",
            status="in_progress",
        )
        model_admin = ContactSubmissionAdmin(ContactSubmission, admin.site)
        result = model_admin.status_badge(contact)
        assert "In Progress" in str(result)

    def test_status_badge_resolved(self):
        contact = ContactSubmission.objects.create(
            name="Test",
            email="test@example.com",
            subject="Subject",
            message="Message",
            status="resolved",
        )
        model_admin = ContactSubmissionAdmin(ContactSubmission, admin.site)
        result = model_admin.status_badge(contact)
        assert "Resolved" in str(result)

    def test_status_badge_spam(self):
        contact = ContactSubmission.objects.create(
            name="Test",
            email="test@example.com",
            subject="Subject",
            message="Message",
            status="spam",
        )
        model_admin = ContactSubmissionAdmin(ContactSubmission, admin.site)
        result = model_admin.status_badge(contact)
        assert "Spam" in str(result)

    def test_mark_as_in_progress_action(self, rf):
        contact = ContactSubmission.objects.create(
            name="Test",
            email="test@example.com",
            subject="Subject",
            message="Message",
            status="new",
        )
        model_admin = ContactSubmissionAdmin(ContactSubmission, admin.site)
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.mark_as_in_progress(
            request, ContactSubmission.objects.filter(pk=contact.pk)
        )
        contact.refresh_from_db()
        assert contact.status == "in_progress"

    def test_mark_as_resolved_action(self, rf):
        contact = ContactSubmission.objects.create(
            name="Test",
            email="test@example.com",
            subject="Subject",
            message="Message",
            status="new",
        )
        model_admin = ContactSubmissionAdmin(ContactSubmission, admin.site)
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.mark_as_resolved(
            request, ContactSubmission.objects.filter(pk=contact.pk)
        )
        contact.refresh_from_db()
        assert contact.status == "resolved"
        assert contact.responded_at is not None

    def test_mark_as_spam_action(self, rf):
        contact = ContactSubmission.objects.create(
            name="Test",
            email="test@example.com",
            subject="Subject",
            message="Message",
            status="new",
        )
        model_admin = ContactSubmissionAdmin(ContactSubmission, admin.site)
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.mark_as_spam(
            request, ContactSubmission.objects.filter(pk=contact.pk)
        )
        contact.refresh_from_db()
        assert contact.status == "spam"


# ============================================================================
# NewsletterSubscriberAdmin Tests
# ============================================================================


@pytest.mark.django_db
class TestNewsletterSubscriberAdmin:
    """Tests for NewsletterSubscriberAdmin."""

    def test_list_display(self):
        model_admin = NewsletterSubscriberAdmin(NewsletterSubscriber, admin.site)
        assert "email" in model_admin.list_display
        assert "status_badge" in model_admin.list_display
        assert "confirmed_badge" in model_admin.list_display

    def test_status_badge_active(self):
        sub = NewsletterSubscriber.objects.create(
            email="active@example.com",
            status="active",
        )
        model_admin = NewsletterSubscriberAdmin(NewsletterSubscriber, admin.site)
        result = model_admin.status_badge(sub)
        assert "Active" in str(result)

    def test_status_badge_unsubscribed(self):
        sub = NewsletterSubscriber.objects.create(
            email="unsub@example.com",
            status="unsubscribed",
        )
        model_admin = NewsletterSubscriberAdmin(NewsletterSubscriber, admin.site)
        result = model_admin.status_badge(sub)
        assert "Unsubscribed" in str(result)

    def test_status_badge_bounced(self):
        sub = NewsletterSubscriber.objects.create(
            email="bounced@example.com",
            status="bounced",
        )
        model_admin = NewsletterSubscriberAdmin(NewsletterSubscriber, admin.site)
        result = model_admin.status_badge(sub)
        assert "Bounced" in str(result)

    def test_confirmed_badge_confirmed(self):
        sub = NewsletterSubscriber.objects.create(
            email="confirmed@example.com",
        )
        sub.confirm_subscription()
        model_admin = NewsletterSubscriberAdmin(NewsletterSubscriber, admin.site)
        result = model_admin.confirmed_badge(sub)
        assert "Confirmed" in str(result)

    def test_confirmed_badge_pending(self):
        sub = NewsletterSubscriber.objects.create(
            email="pending@example.com",
        )
        model_admin = NewsletterSubscriberAdmin(NewsletterSubscriber, admin.site)
        result = model_admin.confirmed_badge(sub)
        assert "Pending" in str(result)

    def test_confirm_subscriptions_action(self, rf):
        sub = NewsletterSubscriber.objects.create(
            email="toconfirm@example.com",
        )
        model_admin = NewsletterSubscriberAdmin(NewsletterSubscriber, admin.site)
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.confirm_subscriptions(
            request, NewsletterSubscriber.objects.filter(pk=sub.pk)
        )
        sub.refresh_from_db()
        assert sub.confirmed_at is not None

    def test_unsubscribe_selected_action(self, rf):
        sub = NewsletterSubscriber.objects.create(
            email="tounsub@example.com",
        )
        sub.confirm_subscription()
        model_admin = NewsletterSubscriberAdmin(NewsletterSubscriber, admin.site)
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.unsubscribe_selected(
            request, NewsletterSubscriber.objects.filter(pk=sub.pk)
        )
        sub.refresh_from_db()
        assert sub.status == "unsubscribed"


# ============================================================================
# SiteSettingsAdmin Tests
# ============================================================================


@pytest.mark.django_db
class TestSiteSettingsAdmin:
    """Tests for SiteSettingsAdmin."""

    def test_has_add_permission_true_when_empty(self, rf):
        model_admin = SiteSettingsAdmin(SiteSettings, admin.site)
        request = rf.get("/admin/")
        assert model_admin.has_add_permission(request) is True

    def test_has_add_permission_false_when_exists(self, rf):
        SiteSettings.objects.create(pk=1)
        model_admin = SiteSettingsAdmin(SiteSettings, admin.site)
        request = rf.get("/admin/")
        assert model_admin.has_add_permission(request) is False

    def test_has_delete_permission_always_false(self, rf):
        model_admin = SiteSettingsAdmin(SiteSettings, admin.site)
        request = rf.get("/admin/")
        assert model_admin.has_delete_permission(request) is False
        settings = SiteSettings.objects.create(pk=1)
        assert model_admin.has_delete_permission(request, obj=settings) is False


# ============================================================================
# CaseStudyCategoryAdmin Tests
# ============================================================================


@pytest.mark.django_db
class TestCaseStudyCategoryAdmin:
    """Tests for CaseStudyCategoryAdmin."""

    def test_list_display(self):
        model_admin = CaseStudyCategoryAdmin(CaseStudyCategory, admin.site)
        assert "name" in model_admin.list_display
        assert "case_study_count" in model_admin.list_display

    def test_case_study_count_method(self):
        category = CaseStudyCategory.objects.create(name="Tech")
        model_admin = CaseStudyCategoryAdmin(CaseStudyCategory, admin.site)
        result = model_admin.case_study_count(category)
        assert "0" in str(result)


# ============================================================================
# CaseStudyAdmin Tests
# ============================================================================


@pytest.mark.django_db
class TestCaseStudyAdmin:
    """Tests for CaseStudyAdmin."""

    def test_list_display(self):
        model_admin = CaseStudyAdmin(CaseStudy, admin.site)
        assert "title" in model_admin.list_display
        assert "client_name" in model_admin.list_display

    def test_featured_badge_featured(self):
        cs = CaseStudy.objects.create(
            title="Featured CS",
            client_name="Client",
            excerpt="E",
            challenge="C",
            solution="S",
            results="R",
            featured=True,
        )
        model_admin = CaseStudyAdmin(CaseStudy, admin.site)
        result = model_admin.featured_badge(cs)
        assert "Featured" in str(result)

    def test_featured_badge_not_featured(self):
        cs = CaseStudy.objects.create(
            title="Not Featured CS",
            client_name="Client",
            excerpt="E",
            challenge="C",
            solution="S",
            results="R",
            featured=False,
        )
        model_admin = CaseStudyAdmin(CaseStudy, admin.site)
        assert model_admin.featured_badge(cs) == "-"

    def test_publish_case_studies_action(self, rf):
        cs = CaseStudy.objects.create(
            title="Draft CS",
            client_name="Client",
            excerpt="E",
            challenge="C",
            solution="S",
            results="R",
            status="draft",
        )
        model_admin = CaseStudyAdmin(CaseStudy, admin.site)
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.publish_case_studies(
            request, CaseStudy.objects.filter(pk=cs.pk)
        )
        cs.refresh_from_db()
        assert cs.status == "published"

    def test_unpublish_case_studies_action(self, rf):
        cs = CaseStudy.objects.create(
            title="Published CS",
            client_name="Client",
            excerpt="E",
            challenge="C",
            solution="S",
            results="R",
            status="published",
            published_at=timezone.now(),
        )
        model_admin = CaseStudyAdmin(CaseStudy, admin.site)
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.unpublish_case_studies(
            request, CaseStudy.objects.filter(pk=cs.pk)
        )
        cs.refresh_from_db()
        assert cs.status == "draft"

    def test_feature_case_studies_action(self, rf):
        cs = CaseStudy.objects.create(
            title="Not Featured",
            client_name="Client",
            excerpt="E",
            challenge="C",
            solution="S",
            results="R",
            featured=False,
        )
        model_admin = CaseStudyAdmin(CaseStudy, admin.site)
        request = rf.get("/admin/")
        model_admin.message_user = MagicMock()
        model_admin.feature_case_studies(
            request, CaseStudy.objects.filter(pk=cs.pk)
        )
        cs.refresh_from_db()
        assert cs.featured is True

    def test_actions_defined(self):
        model_admin = CaseStudyAdmin(CaseStudy, admin.site)
        assert "publish_case_studies" in model_admin.actions
        assert "unpublish_case_studies" in model_admin.actions
        assert "feature_case_studies" in model_admin.actions


# ============================================================================
# ServiceAdmin Tests
# ============================================================================


class TestServiceAdmin:
    """Tests for ServiceAdmin."""

    def test_list_display(self):
        model_admin = ServiceAdmin(Service, admin.site)
        assert "name" in model_admin.list_display
        assert "is_active" in model_admin.list_display
        assert "order" in model_admin.list_display

    def test_list_editable(self):
        model_admin = ServiceAdmin(Service, admin.site)
        assert "order" in model_admin.list_editable
        assert "is_active" in model_admin.list_editable
        assert "is_featured" in model_admin.list_editable


# ============================================================================
# TeamMemberAdmin Tests
# ============================================================================


class TestTeamMemberAdmin:
    """Tests for TeamMemberAdmin."""

    def test_list_display(self):
        model_admin = TeamMemberAdmin(TeamMember, admin.site)
        assert "name" in model_admin.list_display
        assert "role" in model_admin.list_display

    def test_list_editable(self):
        model_admin = TeamMemberAdmin(TeamMember, admin.site)
        assert "order" in model_admin.list_editable
        assert "is_active" in model_admin.list_editable
        assert "is_leadership" in model_admin.list_editable


# ============================================================================
# FAQAdmin Tests
# ============================================================================


class TestFAQAdmin:
    """Tests for FAQAdmin."""

    def test_list_display(self):
        model_admin = FAQAdmin(FAQ, admin.site)
        assert "question" in model_admin.list_display
        assert "category" in model_admin.list_display

    def test_list_editable(self):
        model_admin = FAQAdmin(FAQ, admin.site)
        assert "order" in model_admin.list_editable
        assert "is_active" in model_admin.list_editable
        assert "is_featured" in model_admin.list_editable
        assert "category" in model_admin.list_editable


# ============================================================================
# TestimonialAdmin Tests
# ============================================================================


class TestTestimonialAdmin:
    """Tests for TestimonialAdmin."""

    def test_list_display(self):
        model_admin = TestimonialAdmin(Testimonial, admin.site)
        assert "client_name" in model_admin.list_display
        assert "rating" in model_admin.list_display

    def test_list_editable(self):
        model_admin = TestimonialAdmin(Testimonial, admin.site)
        assert "order" in model_admin.list_editable
        assert "is_active" in model_admin.list_editable
        assert "is_featured" in model_admin.list_editable
