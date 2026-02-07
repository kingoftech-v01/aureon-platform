"""
Tests for website app models.

Covers: BlogCategory, BlogTag, BlogPost, Product, ContactSubmission,
NewsletterSubscriber, CaseStudyCategory, CaseStudy, Service, TeamMember,
FAQ, Testimonial, SiteSettings.
"""
import pytest
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify

from apps.website.models import (
    BlogCategory,
    BlogTag,
    BlogPost,
    Product,
    ContactSubmission,
    NewsletterSubscriber,
    CaseStudyCategory,
    CaseStudy,
    Service,
    TeamMember,
    FAQ,
    Testimonial,
    SiteSettings,
)

User = get_user_model()


# ============================================================================
# BlogCategory Tests
# ============================================================================


@pytest.mark.django_db
class TestBlogCategory:
    """Tests for the BlogCategory model."""

    def test_str_representation(self):
        category = BlogCategory.objects.create(name="Technology")
        assert str(category) == "Technology"

    def test_auto_slug_generation(self):
        category = BlogCategory.objects.create(name="Web Development")
        assert category.slug == "web-development"

    def test_slug_not_overwritten_if_provided(self):
        category = BlogCategory.objects.create(
            name="Web Development", slug="custom-slug"
        )
        assert category.slug == "custom-slug"

    def test_slug_not_overwritten_on_save(self):
        category = BlogCategory.objects.create(name="Technology")
        assert category.slug == "technology"
        category.name = "Updated Technology"
        category.save()
        # Slug should remain the same since it was already set
        assert category.slug == "technology"

    def test_get_absolute_url(self):
        category = BlogCategory.objects.create(name="Finance")
        url = category.get_absolute_url()
        assert url == "/blog/category/finance/"

    def test_ordering_by_name(self):
        BlogCategory.objects.create(name="Zebra")
        BlogCategory.objects.create(name="Alpha")
        BlogCategory.objects.create(name="Middle")
        categories = list(BlogCategory.objects.values_list("name", flat=True))
        assert categories == ["Alpha", "Middle", "Zebra"]

    def test_meta_verbose_names(self):
        assert BlogCategory._meta.verbose_name == "Blog Category"
        assert BlogCategory._meta.verbose_name_plural == "Blog Categories"

    def test_name_unique_constraint(self):
        BlogCategory.objects.create(name="Unique Category")
        with pytest.raises(Exception):
            BlogCategory.objects.create(name="Unique Category")

    def test_description_blank_allowed(self):
        category = BlogCategory.objects.create(name="No Description")
        assert category.description == ""

    def test_description_with_content(self):
        category = BlogCategory.objects.create(
            name="Described", description="A category with description."
        )
        assert category.description == "A category with description."

    def test_created_at_auto_set(self):
        category = BlogCategory.objects.create(name="Timestamped")
        assert category.created_at is not None


# ============================================================================
# BlogTag Tests
# ============================================================================


@pytest.mark.django_db
class TestBlogTag:
    """Tests for the BlogTag model."""

    def test_str_representation(self):
        tag = BlogTag.objects.create(name="Python")
        assert str(tag) == "Python"

    def test_auto_slug_generation(self):
        tag = BlogTag.objects.create(name="Machine Learning")
        assert tag.slug == "machine-learning"

    def test_slug_not_overwritten_if_provided(self):
        tag = BlogTag.objects.create(name="Test Tag", slug="my-custom-slug")
        assert tag.slug == "my-custom-slug"

    def test_slug_preserved_on_update(self):
        tag = BlogTag.objects.create(name="Initial")
        assert tag.slug == "initial"
        tag.name = "Updated"
        tag.save()
        assert tag.slug == "initial"

    def test_get_absolute_url(self):
        tag = BlogTag.objects.create(name="Django")
        url = tag.get_absolute_url()
        assert url == "/blog/tag/django/"

    def test_ordering_by_name(self):
        BlogTag.objects.create(name="Zeta")
        BlogTag.objects.create(name="Alpha")
        tags = list(BlogTag.objects.values_list("name", flat=True))
        assert tags == ["Alpha", "Zeta"]

    def test_meta_verbose_names(self):
        assert BlogTag._meta.verbose_name == "Blog Tag"
        assert BlogTag._meta.verbose_name_plural == "Blog Tags"

    def test_name_unique_constraint(self):
        BlogTag.objects.create(name="Unique")
        with pytest.raises(Exception):
            BlogTag.objects.create(name="Unique")

    def test_created_at_auto_set(self):
        tag = BlogTag.objects.create(name="Timestamped")
        assert tag.created_at is not None


# ============================================================================
# BlogPost Tests
# ============================================================================


@pytest.mark.django_db
class TestBlogPost:
    """Tests for the BlogPost model."""

    @pytest.fixture
    def author(self, db):
        return User.objects.create_user(
            username="author",
            email="author@example.com",
            password="TestPass123!",
            first_name="Blog",
            last_name="Author",
        )

    @pytest.fixture
    def category(self, db):
        return BlogCategory.objects.create(name="Tech")

    @pytest.fixture
    def blog_post(self, author, category):
        return BlogPost.objects.create(
            title="Test Blog Post",
            author=author,
            category=category,
            excerpt="A short excerpt for testing.",
            content="This is the content of the blog post with enough words " * 20,
            status="draft",
        )

    def test_str_representation(self, blog_post):
        assert str(blog_post) == "Test Blog Post"

    def test_auto_slug_generation(self, blog_post):
        assert blog_post.slug == "test-blog-post"

    def test_slug_not_overwritten_if_provided(self, author):
        post = BlogPost.objects.create(
            title="My Post",
            slug="custom-post-slug",
            author=author,
            excerpt="Excerpt",
            content="Content",
        )
        assert post.slug == "custom-post-slug"

    def test_slug_preserved_on_update(self, blog_post):
        original_slug = blog_post.slug
        blog_post.title = "Updated Title"
        blog_post.save()
        assert blog_post.slug == original_slug

    def test_auto_published_at_on_publish(self, blog_post):
        assert blog_post.published_at is None
        blog_post.status = "published"
        blog_post.save()
        assert blog_post.published_at is not None

    def test_published_at_not_overwritten_if_already_set(self, blog_post):
        fixed_time = timezone.now() - timedelta(days=7)
        blog_post.published_at = fixed_time
        blog_post.status = "published"
        blog_post.save()
        assert blog_post.published_at == fixed_time

    def test_reading_time_calculated_from_content(self, author):
        # 400 words => 400/200 = 2 minutes
        content = " ".join(["word"] * 400)
        post = BlogPost.objects.create(
            title="Long Post",
            author=author,
            excerpt="Excerpt",
            content=content,
        )
        assert post.reading_time == 2

    def test_reading_time_minimum_one_minute(self, author):
        post = BlogPost.objects.create(
            title="Short Post",
            author=author,
            excerpt="Excerpt",
            content="short",
        )
        assert post.reading_time == 1

    def test_reading_time_empty_content(self, author):
        # If content is empty string (falsy), reading_time stays default
        post = BlogPost.objects.create(
            title="Empty Content Post",
            author=author,
            excerpt="Excerpt",
            content="",
        )
        assert post.reading_time == 5  # default

    def test_meta_title_auto_from_title(self, blog_post):
        assert blog_post.meta_title == blog_post.title[:70]

    def test_meta_title_not_overwritten_if_provided(self, author):
        post = BlogPost.objects.create(
            title="My Post",
            author=author,
            excerpt="Excerpt",
            content="Content",
            meta_title="Custom Meta Title",
        )
        assert post.meta_title == "Custom Meta Title"

    def test_meta_description_auto_from_excerpt(self, author):
        post = BlogPost.objects.create(
            title="My Post",
            author=author,
            excerpt="This is a test excerpt for meta description.",
            content="Content",
        )
        assert post.meta_description == "This is a test excerpt for meta description."

    def test_meta_description_not_overwritten_if_provided(self, author):
        post = BlogPost.objects.create(
            title="My Post",
            author=author,
            excerpt="Excerpt",
            content="Content",
            meta_description="Custom meta description",
        )
        assert post.meta_description == "Custom meta description"

    def test_meta_description_truncated_at_160(self, author):
        long_excerpt = "A" * 300
        post = BlogPost.objects.create(
            title="My Post",
            author=author,
            excerpt=long_excerpt,
            content="Content",
        )
        assert len(post.meta_description) == 160

    def test_get_absolute_url(self, blog_post):
        url = blog_post.get_absolute_url()
        assert url == "/blog/test-blog-post/"

    def test_increment_views(self, blog_post):
        assert blog_post.views_count == 0
        blog_post.increment_views()
        blog_post.refresh_from_db()
        assert blog_post.views_count == 1

    def test_increment_views_multiple(self, blog_post):
        blog_post.increment_views()
        blog_post.increment_views()
        blog_post.increment_views()
        blog_post.refresh_from_db()
        assert blog_post.views_count == 3

    def test_is_published_true(self, blog_post):
        blog_post.status = "published"
        blog_post.published_at = timezone.now() - timedelta(hours=1)
        blog_post.save()
        assert blog_post.is_published is True

    def test_is_published_false_draft(self, blog_post):
        assert blog_post.is_published is False

    def test_is_published_false_future_date(self, blog_post):
        blog_post.status = "published"
        blog_post.published_at = timezone.now() + timedelta(days=1)
        assert blog_post.is_published is False

    def test_is_published_false_no_published_at(self, author):
        post = BlogPost(
            title="Test",
            author=author,
            excerpt="Excerpt",
            content="Content",
            status="published",
            published_at=None,
        )
        assert post.is_published is False

    def test_is_published_archived(self, blog_post):
        blog_post.status = "archived"
        blog_post.published_at = timezone.now() - timedelta(hours=1)
        assert blog_post.is_published is False

    def test_default_status_is_draft(self, blog_post):
        assert blog_post.status == "draft"

    def test_tags_many_to_many(self, blog_post):
        tag1 = BlogTag.objects.create(name="Python")
        tag2 = BlogTag.objects.create(name="Django")
        blog_post.tags.add(tag1, tag2)
        assert blog_post.tags.count() == 2

    def test_featured_default_false(self, blog_post):
        assert blog_post.featured is False

    def test_author_set_null_on_delete(self, blog_post, author):
        author.delete()
        blog_post.refresh_from_db()
        assert blog_post.author is None

    def test_category_set_null_on_delete(self, blog_post, category):
        category.delete()
        blog_post.refresh_from_db()
        assert blog_post.category is None

    def test_ordering(self, author):
        now = timezone.now()
        post1 = BlogPost.objects.create(
            title="Post 1",
            author=author,
            excerpt="E",
            content="C",
            status="published",
            published_at=now - timedelta(days=2),
        )
        post2 = BlogPost.objects.create(
            title="Post 2",
            author=author,
            excerpt="E",
            content="C",
            status="published",
            published_at=now - timedelta(days=1),
        )
        posts = list(
            BlogPost.objects.filter(author=author).values_list("title", flat=True)
        )
        assert posts[0] == "Post 2"
        assert posts[1] == "Post 1"

    def test_meta_verbose_names(self):
        assert BlogPost._meta.verbose_name == "Blog Post"
        assert BlogPost._meta.verbose_name_plural == "Blog Posts"


# ============================================================================
# Product Tests
# ============================================================================


@pytest.mark.django_db
class TestProduct:
    """Tests for the Product model."""

    @pytest.fixture
    def product(self):
        return Product.objects.create(
            name="Template Pack",
            short_description="A collection of templates.",
            description="Full description of the template pack.",
            price=Decimal("29.99"),
        )

    def test_str_representation(self, product):
        assert str(product) == "Template Pack"

    def test_auto_slug_generation(self, product):
        assert product.slug == "template-pack"

    def test_slug_not_overwritten_if_provided(self):
        product = Product.objects.create(
            name="Test",
            slug="custom-slug",
            short_description="Desc",
            description="Full",
            price=Decimal("10.00"),
        )
        assert product.slug == "custom-slug"

    def test_auto_sku_generation(self, product):
        assert product.sku.startswith("PROD-")
        assert len(product.sku) == 13  # "PROD-" + 8 hex chars

    def test_sku_not_overwritten_if_provided(self):
        product = Product.objects.create(
            name="Test",
            sku="CUSTOM-SKU-123",
            short_description="Desc",
            description="Full",
            price=Decimal("10.00"),
        )
        assert product.sku == "CUSTOM-SKU-123"

    def test_meta_title_auto_from_name(self, product):
        assert product.meta_title == "Template Pack"

    def test_meta_title_not_overwritten_if_provided(self):
        product = Product.objects.create(
            name="Test",
            short_description="Desc",
            description="Full",
            price=Decimal("10.00"),
            meta_title="Custom Meta",
        )
        assert product.meta_title == "Custom Meta"

    def test_meta_description_auto_from_short_description(self, product):
        assert product.meta_description == "A collection of templates."

    def test_meta_description_not_overwritten_if_provided(self):
        product = Product.objects.create(
            name="Test",
            short_description="Desc",
            description="Full",
            price=Decimal("10.00"),
            meta_description="Custom meta desc",
        )
        assert product.meta_description == "Custom meta desc"

    def test_get_absolute_url(self, product):
        assert product.get_absolute_url() == "/products/template-pack/"

    def test_discount_percentage_with_compare_at_price(self):
        product = Product.objects.create(
            name="Discounted",
            short_description="Desc",
            description="Full",
            price=Decimal("75.00"),
            compare_at_price=Decimal("100.00"),
        )
        assert product.discount_percentage == 25

    def test_discount_percentage_no_compare_at_price(self, product):
        assert product.discount_percentage == 0

    def test_discount_percentage_compare_at_price_lower(self):
        product = Product.objects.create(
            name="No Discount",
            short_description="Desc",
            description="Full",
            price=Decimal("100.00"),
            compare_at_price=Decimal("50.00"),
        )
        assert product.discount_percentage == 0

    def test_discount_percentage_same_prices(self):
        product = Product.objects.create(
            name="Same Prices",
            short_description="Desc",
            description="Full",
            price=Decimal("100.00"),
            compare_at_price=Decimal("100.00"),
        )
        assert product.discount_percentage == 0

    def test_has_discount_true(self):
        product = Product.objects.create(
            name="Has Discount",
            short_description="Desc",
            description="Full",
            price=Decimal("50.00"),
            compare_at_price=Decimal("100.00"),
        )
        assert product.has_discount is True

    def test_has_discount_false(self, product):
        assert product.has_discount is False

    def test_default_product_type(self, product):
        assert product.product_type == "digital"

    def test_default_is_active(self, product):
        assert product.is_active is True

    def test_default_is_featured(self, product):
        assert product.is_featured is False

    def test_default_in_stock(self, product):
        assert product.in_stock is True

    def test_meta_verbose_names(self):
        assert Product._meta.verbose_name == "Product"
        assert Product._meta.verbose_name_plural == "Products"

    def test_ordering(self):
        p1 = Product.objects.create(
            name="Old Product",
            short_description="D",
            description="F",
            price=Decimal("10.00"),
        )
        p2 = Product.objects.create(
            name="New Product",
            short_description="D",
            description="F",
            price=Decimal("20.00"),
        )
        products = list(Product.objects.values_list("name", flat=True))
        # Ordering is ['-created_at'], newest first
        assert products[0] == "New Product"


# ============================================================================
# ContactSubmission Tests
# ============================================================================


@pytest.mark.django_db
class TestContactSubmission:
    """Tests for the ContactSubmission model."""

    @pytest.fixture
    def contact(self):
        return ContactSubmission.objects.create(
            name="John Doe",
            email="john@example.com",
            inquiry_type="general",
            subject="Test Inquiry",
            message="This is a test message.",
        )

    def test_str_representation(self, contact):
        assert str(contact) == "John Doe - Test Inquiry"

    def test_is_new_property_true(self, contact):
        assert contact.is_new is True

    def test_is_new_property_false(self, contact):
        contact.status = "in_progress"
        contact.save()
        assert contact.is_new is False

    def test_default_status(self, contact):
        assert contact.status == "new"

    def test_default_inquiry_type(self, contact):
        assert contact.inquiry_type == "general"

    def test_optional_fields_blank(self, contact):
        assert contact.phone == ""
        assert contact.company == ""
        assert contact.notes == ""

    def test_assigned_to_nullable(self, contact):
        assert contact.assigned_to is None

    def test_responded_at_nullable(self, contact):
        assert contact.responded_at is None

    def test_created_at_auto_set(self, contact):
        assert contact.created_at is not None

    def test_meta_verbose_names(self):
        assert ContactSubmission._meta.verbose_name == "Contact Submission"
        assert ContactSubmission._meta.verbose_name_plural == "Contact Submissions"

    def test_ordering(self):
        c1 = ContactSubmission.objects.create(
            name="First",
            email="first@example.com",
            subject="First",
            message="Msg",
        )
        c2 = ContactSubmission.objects.create(
            name="Second",
            email="second@example.com",
            subject="Second",
            message="Msg",
        )
        submissions = list(
            ContactSubmission.objects.values_list("name", flat=True)
        )
        assert submissions[0] == "Second"  # newest first

    def test_all_inquiry_types(self):
        types = ["general", "sales", "support", "partnership", "media", "other"]
        for i, inquiry_type in enumerate(types):
            cs = ContactSubmission.objects.create(
                name=f"Test {i}",
                email=f"test{i}@example.com",
                subject="Subject",
                message="Message",
                inquiry_type=inquiry_type,
            )
            assert cs.inquiry_type == inquiry_type

    def test_all_status_types(self):
        statuses = ["new", "in_progress", "resolved", "spam"]
        for i, status in enumerate(statuses):
            cs = ContactSubmission.objects.create(
                name=f"Status {i}",
                email=f"status{i}@example.com",
                subject="Subject",
                message="Message",
                status=status,
            )
            assert cs.status == status

    def test_ip_address_field(self):
        contact = ContactSubmission.objects.create(
            name="IP Test",
            email="ip@example.com",
            subject="Subject",
            message="Message",
            ip_address="192.168.1.1",
        )
        assert contact.ip_address == "192.168.1.1"

    def test_user_agent_field(self):
        contact = ContactSubmission.objects.create(
            name="UA Test",
            email="ua@example.com",
            subject="Subject",
            message="Message",
            user_agent="Mozilla/5.0",
        )
        assert contact.user_agent == "Mozilla/5.0"


# ============================================================================
# NewsletterSubscriber Tests
# ============================================================================


@pytest.mark.django_db
class TestNewsletterSubscriber:
    """Tests for the NewsletterSubscriber model."""

    @pytest.fixture
    def subscriber(self):
        return NewsletterSubscriber.objects.create(
            email="subscriber@example.com",
            name="Test Subscriber",
        )

    def test_str_representation(self, subscriber):
        assert str(subscriber) == "subscriber@example.com"

    def test_auto_confirmation_token_generation(self, subscriber):
        assert subscriber.confirmation_token is not None
        assert len(subscriber.confirmation_token) == 32  # uuid4().hex

    def test_confirmation_token_not_overwritten_if_set(self):
        sub = NewsletterSubscriber.objects.create(
            email="token@example.com",
            confirmation_token="custom-token-value-1234567890abcdef",
        )
        assert sub.confirmation_token == "custom-token-value-1234567890abcdef"

    def test_confirm_subscription(self, subscriber):
        assert subscriber.confirmed_at is None
        subscriber.confirm_subscription()
        subscriber.refresh_from_db()
        assert subscriber.confirmed_at is not None
        assert subscriber.status == "active"

    def test_unsubscribe(self, subscriber):
        subscriber.confirm_subscription()
        subscriber.unsubscribe()
        subscriber.refresh_from_db()
        assert subscriber.status == "unsubscribed"
        assert subscriber.unsubscribed_at is not None

    def test_is_confirmed_true(self, subscriber):
        subscriber.confirm_subscription()
        assert subscriber.is_confirmed is True

    def test_is_confirmed_false(self, subscriber):
        assert subscriber.is_confirmed is False

    def test_is_active_true(self, subscriber):
        subscriber.confirm_subscription()
        assert subscriber.is_active is True

    def test_is_active_false_unconfirmed(self, subscriber):
        assert subscriber.is_active is False

    def test_is_active_false_unsubscribed(self, subscriber):
        subscriber.confirm_subscription()
        subscriber.unsubscribe()
        assert subscriber.is_active is False

    def test_default_status(self, subscriber):
        assert subscriber.status == "active"

    def test_default_interests(self, subscriber):
        assert subscriber.interests == {}

    def test_email_unique(self, subscriber):
        with pytest.raises(Exception):
            NewsletterSubscriber.objects.create(email="subscriber@example.com")

    def test_name_optional(self):
        sub = NewsletterSubscriber.objects.create(email="noname@example.com")
        assert sub.name == ""

    def test_source_optional(self, subscriber):
        assert subscriber.source == ""

    def test_meta_verbose_names(self):
        assert NewsletterSubscriber._meta.verbose_name == "Newsletter Subscriber"
        assert (
            NewsletterSubscriber._meta.verbose_name_plural == "Newsletter Subscribers"
        )

    def test_ordering(self):
        s1 = NewsletterSubscriber.objects.create(email="first@example.com")
        s2 = NewsletterSubscriber.objects.create(email="second@example.com")
        subs = list(
            NewsletterSubscriber.objects.values_list("email", flat=True)
        )
        assert subs[0] == "second@example.com"  # newest first

    def test_all_status_types(self):
        statuses = ["active", "unsubscribed", "bounced"]
        for i, status in enumerate(statuses):
            sub = NewsletterSubscriber.objects.create(
                email=f"status{i}@example.com",
                status=status,
            )
            assert sub.status == status

    def test_confirmation_token_unique(self):
        s1 = NewsletterSubscriber.objects.create(email="one@example.com")
        s2 = NewsletterSubscriber.objects.create(email="two@example.com")
        assert s1.confirmation_token != s2.confirmation_token


# ============================================================================
# CaseStudyCategory Tests
# ============================================================================


@pytest.mark.django_db
class TestCaseStudyCategory:
    """Tests for the CaseStudyCategory model."""

    def test_str_representation(self):
        category = CaseStudyCategory.objects.create(name="Fintech")
        assert str(category) == "Fintech"

    def test_auto_slug_generation(self):
        category = CaseStudyCategory.objects.create(name="Financial Services")
        assert category.slug == "financial-services"

    def test_slug_not_overwritten_if_provided(self):
        category = CaseStudyCategory.objects.create(
            name="Test", slug="custom"
        )
        assert category.slug == "custom"

    def test_slug_preserved_on_update(self):
        category = CaseStudyCategory.objects.create(name="Original")
        original_slug = category.slug
        category.name = "Updated"
        category.save()
        assert category.slug == original_slug

    def test_get_absolute_url(self):
        category = CaseStudyCategory.objects.create(name="Healthcare")
        url = category.get_absolute_url()
        assert url == "/case-studies/category/healthcare/"

    def test_icon_field_optional(self):
        category = CaseStudyCategory.objects.create(name="No Icon")
        assert category.icon == ""

    def test_icon_field_with_value(self):
        category = CaseStudyCategory.objects.create(
            name="With Icon", icon="fa-chart-line"
        )
        assert category.icon == "fa-chart-line"

    def test_meta_verbose_names(self):
        assert CaseStudyCategory._meta.verbose_name == "Case Study Category"
        assert (
            CaseStudyCategory._meta.verbose_name_plural == "Case Study Categories"
        )

    def test_ordering_by_name(self):
        CaseStudyCategory.objects.create(name="Zebra")
        CaseStudyCategory.objects.create(name="Alpha")
        categories = list(
            CaseStudyCategory.objects.values_list("name", flat=True)
        )
        assert categories == ["Alpha", "Zebra"]


# ============================================================================
# CaseStudy Tests
# ============================================================================


@pytest.mark.django_db
class TestCaseStudy:
    """Tests for the CaseStudy model."""

    @pytest.fixture
    def cs_category(self):
        return CaseStudyCategory.objects.create(name="Technology")

    @pytest.fixture
    def case_study(self, cs_category):
        return CaseStudy.objects.create(
            title="Success Story",
            client_name="Acme Corp",
            category=cs_category,
            excerpt="A brief summary of the case study.",
            challenge="The challenge faced.",
            solution="The solution provided.",
            results="The results achieved.",
            status="draft",
        )

    def test_str_representation(self, case_study):
        assert str(case_study) == "Success Story - Acme Corp"

    def test_auto_slug_generation(self, case_study):
        assert case_study.slug == "success-story"

    def test_slug_not_overwritten_if_provided(self):
        cs = CaseStudy.objects.create(
            title="Test",
            slug="custom-slug",
            client_name="Client",
            excerpt="Excerpt",
            challenge="Challenge",
            solution="Solution",
            results="Results",
        )
        assert cs.slug == "custom-slug"

    def test_slug_preserved_on_update(self, case_study):
        original_slug = case_study.slug
        case_study.title = "Updated Title"
        case_study.save()
        assert case_study.slug == original_slug

    def test_auto_published_at_on_publish(self, case_study):
        assert case_study.published_at is None
        case_study.status = "published"
        case_study.save()
        assert case_study.published_at is not None

    def test_published_at_not_overwritten_if_set(self, case_study):
        fixed_time = timezone.now() - timedelta(days=30)
        case_study.published_at = fixed_time
        case_study.status = "published"
        case_study.save()
        assert case_study.published_at == fixed_time

    def test_meta_title_auto_from_title(self, case_study):
        assert case_study.meta_title == "Success Story"

    def test_meta_title_not_overwritten_if_provided(self):
        cs = CaseStudy.objects.create(
            title="Test",
            client_name="Client",
            excerpt="Excerpt",
            challenge="C",
            solution="S",
            results="R",
            meta_title="Custom Meta",
        )
        assert cs.meta_title == "Custom Meta"

    def test_meta_description_auto_from_excerpt(self, case_study):
        assert case_study.meta_description == "A brief summary of the case study."

    def test_meta_description_not_overwritten_if_provided(self):
        cs = CaseStudy.objects.create(
            title="Test",
            client_name="Client",
            excerpt="Excerpt",
            challenge="C",
            solution="S",
            results="R",
            meta_description="Custom desc",
        )
        assert cs.meta_description == "Custom desc"

    def test_get_absolute_url(self, case_study):
        assert case_study.get_absolute_url() == "/case-studies/success-story/"

    def test_increment_views(self, case_study):
        assert case_study.views_count == 0
        case_study.increment_views()
        case_study.refresh_from_db()
        assert case_study.views_count == 1

    def test_increment_views_multiple(self, case_study):
        for _ in range(5):
            case_study.increment_views()
        case_study.refresh_from_db()
        assert case_study.views_count == 5

    def test_is_published_true(self, case_study):
        case_study.status = "published"
        case_study.published_at = timezone.now() - timedelta(hours=1)
        case_study.save()
        assert case_study.is_published is True

    def test_is_published_false_draft(self, case_study):
        assert case_study.is_published is False

    def test_is_published_false_future(self, case_study):
        case_study.status = "published"
        case_study.published_at = timezone.now() + timedelta(days=1)
        assert case_study.is_published is False

    def test_is_published_false_no_published_at(self):
        cs = CaseStudy(
            title="Test",
            client_name="Client",
            excerpt="E",
            challenge="C",
            solution="S",
            results="R",
            status="published",
            published_at=None,
        )
        assert cs.is_published is False

    def test_featured_default_false(self, case_study):
        assert case_study.featured is False

    def test_default_status(self, case_study):
        assert case_study.status == "draft"

    def test_category_set_null_on_delete(self, case_study, cs_category):
        cs_category.delete()
        case_study.refresh_from_db()
        assert case_study.category is None

    def test_metric_fields_optional(self, case_study):
        assert case_study.metric_1_value == ""
        assert case_study.metric_1_label == ""

    def test_meta_verbose_names(self):
        assert CaseStudy._meta.verbose_name == "Case Study"
        assert CaseStudy._meta.verbose_name_plural == "Case Studies"

    def test_testimonial_fields_optional(self, case_study):
        assert case_study.testimonial == ""
        assert case_study.testimonial_author == ""
        assert case_study.testimonial_role == ""


# ============================================================================
# Service Tests
# ============================================================================


@pytest.mark.django_db
class TestService:
    """Tests for the Service model."""

    @pytest.fixture
    def service(self):
        return Service.objects.create(
            name="Contract Management",
            short_description="Manage your contracts efficiently.",
            description="Full description of contract management service.",
            feature_1="Feature one",
            feature_2="Feature two",
            feature_3="Feature three",
        )

    def test_str_representation(self, service):
        assert str(service) == "Contract Management"

    def test_auto_slug_generation(self, service):
        assert service.slug == "contract-management"

    def test_slug_not_overwritten_if_provided(self):
        svc = Service.objects.create(
            name="Test",
            slug="custom-slug",
            short_description="Desc",
            description="Full",
        )
        assert svc.slug == "custom-slug"

    def test_slug_preserved_on_update(self, service):
        original_slug = service.slug
        service.name = "Updated Name"
        service.save()
        assert service.slug == original_slug

    def test_meta_title_auto_from_name(self, service):
        assert service.meta_title == "Contract Management"

    def test_meta_title_not_overwritten_if_provided(self):
        svc = Service.objects.create(
            name="Test",
            short_description="Desc",
            description="Full",
            meta_title="Custom Meta Title",
        )
        assert svc.meta_title == "Custom Meta Title"

    def test_get_absolute_url(self, service):
        assert service.get_absolute_url() == "/services/contract-management/"

    def test_features_list_all_populated(self, service):
        features = service.features_list
        assert features == ["Feature one", "Feature two", "Feature three"]

    def test_features_list_partial(self):
        svc = Service.objects.create(
            name="Partial",
            short_description="Desc",
            description="Full",
            feature_1="Only one feature",
        )
        assert svc.features_list == ["Only one feature"]

    def test_features_list_empty(self):
        svc = Service.objects.create(
            name="Empty Features",
            short_description="Desc",
            description="Full",
        )
        assert svc.features_list == []

    def test_features_list_all_five(self):
        svc = Service.objects.create(
            name="All Features",
            short_description="Desc",
            description="Full",
            feature_1="F1",
            feature_2="F2",
            feature_3="F3",
            feature_4="F4",
            feature_5="F5",
        )
        assert len(svc.features_list) == 5

    def test_default_order(self, service):
        assert service.order == 0

    def test_default_is_active(self, service):
        assert service.is_active is True

    def test_default_is_featured(self, service):
        assert service.is_featured is False

    def test_ordering(self):
        s1 = Service.objects.create(
            name="B Service",
            short_description="D",
            description="F",
            order=2,
        )
        s2 = Service.objects.create(
            name="A Service",
            short_description="D",
            description="F",
            order=1,
        )
        services = list(Service.objects.values_list("name", flat=True))
        assert services[0] == "A Service"  # order=1 comes first

    def test_meta_verbose_names(self):
        assert Service._meta.verbose_name == "Service"
        assert Service._meta.verbose_name_plural == "Services"


# ============================================================================
# TeamMember Tests
# ============================================================================


@pytest.mark.django_db
class TestTeamMember:
    """Tests for the TeamMember model."""

    @pytest.fixture
    def member(self):
        return TeamMember.objects.create(
            name="Jane Doe",
            role="CEO",
            bio="Experienced leader in tech.",
        )

    def test_str_representation(self, member):
        assert str(member) == "Jane Doe - CEO"

    def test_auto_slug_generation(self, member):
        assert member.slug == "jane-doe"

    def test_slug_not_overwritten_if_provided(self):
        member = TeamMember.objects.create(
            name="Test Member",
            slug="custom-slug",
            role="CTO",
            bio="Bio",
        )
        assert member.slug == "custom-slug"

    def test_slug_preserved_on_update(self, member):
        original_slug = member.slug
        member.name = "Updated Name"
        member.save()
        assert member.slug == original_slug

    def test_social_links_optional(self, member):
        assert member.linkedin_url == ""
        assert member.twitter_url == ""
        assert member.github_url == ""
        assert member.email == ""

    def test_default_order(self, member):
        assert member.order == 0

    def test_default_is_active(self, member):
        assert member.is_active is True

    def test_default_is_leadership(self, member):
        assert member.is_leadership is False

    def test_ordering(self):
        m1 = TeamMember.objects.create(
            name="B Member",
            role="Dev",
            bio="Bio",
            order=2,
        )
        m2 = TeamMember.objects.create(
            name="A Member",
            role="Dev",
            bio="Bio",
            order=1,
        )
        members = list(TeamMember.objects.values_list("name", flat=True))
        assert members[0] == "A Member"

    def test_meta_verbose_names(self):
        assert TeamMember._meta.verbose_name == "Team Member"
        assert TeamMember._meta.verbose_name_plural == "Team Members"


# ============================================================================
# FAQ Tests
# ============================================================================


@pytest.mark.django_db
class TestFAQ:
    """Tests for the FAQ model."""

    @pytest.fixture
    def faq(self):
        return FAQ.objects.create(
            question="What is Aureon?",
            answer="Aureon is a SaaS platform for business automation.",
            category="general",
        )

    def test_str_representation(self, faq):
        assert str(faq) == "What is Aureon?"

    def test_str_truncation_long_question(self):
        long_question = "Q" * 200
        faq = FAQ.objects.create(
            question=long_question,
            answer="Answer.",
        )
        assert str(faq) == long_question[:100]

    def test_default_category(self, faq):
        assert faq.category == "general"

    def test_all_category_choices(self):
        categories = ["general", "pricing", "features", "technical", "security", "support"]
        for i, cat in enumerate(categories):
            faq = FAQ.objects.create(
                question=f"Question {i}?",
                answer=f"Answer {i}.",
                category=cat,
            )
            assert faq.category == cat

    def test_default_order(self, faq):
        assert faq.order == 0

    def test_default_is_active(self, faq):
        assert faq.is_active is True

    def test_default_is_featured(self, faq):
        assert faq.is_featured is False

    def test_ordering(self):
        faq1 = FAQ.objects.create(
            question="Pricing Q?",
            answer="A",
            category="pricing",
            order=1,
        )
        faq2 = FAQ.objects.create(
            question="General Q?",
            answer="A",
            category="general",
            order=0,
        )
        faqs = list(FAQ.objects.values_list("question", flat=True))
        # Ordering: ['category', 'order'] => general comes before pricing
        assert faqs[0] == "General Q?"
        assert faqs[1] == "Pricing Q?"

    def test_meta_verbose_names(self):
        assert FAQ._meta.verbose_name == "FAQ"
        assert FAQ._meta.verbose_name_plural == "FAQs"


# ============================================================================
# Testimonial Tests
# ============================================================================


@pytest.mark.django_db
class TestTestimonial:
    """Tests for the Testimonial model."""

    @pytest.fixture
    def testimonial(self):
        return Testimonial.objects.create(
            client_name="Bob Smith",
            client_role="CTO",
            client_company="Tech Inc",
            content="Great platform!",
            rating=5,
        )

    def test_str_representation(self, testimonial):
        assert str(testimonial) == "Bob Smith - Tech Inc"

    def test_str_without_company(self):
        testimonial = Testimonial.objects.create(
            client_name="Alice",
            client_role="Dev",
            content="Nice!",
        )
        assert str(testimonial) == "Alice - "

    def test_default_rating(self):
        testimonial = Testimonial.objects.create(
            client_name="Test",
            client_role="Role",
            content="Content",
        )
        assert testimonial.rating == 5

    def test_default_order(self, testimonial):
        assert testimonial.order == 0

    def test_default_is_active(self, testimonial):
        assert testimonial.is_active is True

    def test_default_is_featured(self, testimonial):
        assert testimonial.is_featured is False

    def test_company_optional(self):
        testimonial = Testimonial.objects.create(
            client_name="No Company",
            client_role="Role",
            content="Content",
        )
        assert testimonial.client_company == ""

    def test_ordering(self):
        t1 = Testimonial.objects.create(
            client_name="First",
            client_role="Role",
            content="Content",
            order=2,
        )
        t2 = Testimonial.objects.create(
            client_name="Second",
            client_role="Role",
            content="Content",
            order=1,
        )
        testimonials = list(
            Testimonial.objects.values_list("client_name", flat=True)
        )
        assert testimonials[0] == "Second"  # order=1

    def test_meta_verbose_names(self):
        assert Testimonial._meta.verbose_name == "Testimonial"
        assert Testimonial._meta.verbose_name_plural == "Testimonials"


# ============================================================================
# SiteSettings Tests
# ============================================================================


@pytest.mark.django_db
class TestSiteSettings:
    """Tests for the SiteSettings model."""

    def test_str_representation(self):
        settings = SiteSettings.objects.create()
        assert str(settings) == "Site Settings"

    def test_get_settings_creates_singleton(self):
        settings = SiteSettings.get_settings()
        assert settings is not None
        assert settings.pk == 1

    def test_get_settings_returns_existing(self):
        SiteSettings.objects.create(pk=1, company_name="Custom Name")
        settings = SiteSettings.get_settings()
        assert settings.company_name == "Custom Name"

    def test_get_settings_idempotent(self):
        s1 = SiteSettings.get_settings()
        s2 = SiteSettings.get_settings()
        assert s1.pk == s2.pk
        assert SiteSettings.objects.count() == 1

    def test_default_company_name(self):
        settings = SiteSettings.get_settings()
        assert settings.company_name == "Aureon by Rhematek Solutions"

    def test_default_tagline(self):
        settings = SiteSettings.get_settings()
        assert settings.tagline == "Automate Your Business, Amplify Your Growth"

    def test_default_contact_email(self):
        settings = SiteSettings.get_settings()
        assert settings.contact_email == "info@rhematek-solutions.com"

    def test_default_support_email(self):
        settings = SiteSettings.get_settings()
        assert settings.support_email == "support@rhematek-solutions.com"

    def test_default_sales_email(self):
        settings = SiteSettings.get_settings()
        assert settings.sales_email == "sales@rhematek-solutions.com"

    def test_default_maintenance_mode(self):
        settings = SiteSettings.get_settings()
        assert settings.maintenance_mode is False

    def test_default_allow_newsletter(self):
        settings = SiteSettings.get_settings()
        assert settings.allow_newsletter_signup is True

    def test_default_show_blog(self):
        settings = SiteSettings.get_settings()
        assert settings.show_blog is True

    def test_default_show_store(self):
        settings = SiteSettings.get_settings()
        assert settings.show_store is True

    def test_social_media_links_optional(self):
        settings = SiteSettings.get_settings()
        assert settings.facebook_url == ""
        assert settings.twitter_url == ""
        assert settings.linkedin_url == ""
        assert settings.youtube_url == ""
        assert settings.instagram_url == ""
        assert settings.github_url == ""

    def test_analytics_ids_optional(self):
        settings = SiteSettings.get_settings()
        assert settings.google_analytics_id == ""
        assert settings.google_tag_manager_id == ""
        assert settings.facebook_pixel_id == ""

    def test_meta_verbose_names(self):
        assert SiteSettings._meta.verbose_name == "Site Settings"
        assert SiteSettings._meta.verbose_name_plural == "Site Settings"

    def test_updated_at_auto_set(self):
        settings = SiteSettings.get_settings()
        assert settings.updated_at is not None
