from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
from django.core.validators import EmailValidator
import uuid

User = get_user_model()


class BlogCategory(models.Model):
    """Blog post categories for organization"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Blog Category'
        verbose_name_plural = 'Blog Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('website:blog_category', kwargs={'slug': self.slug})


class BlogTag(models.Model):
    """Blog post tags for flexible categorization"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Blog Tag'
        verbose_name_plural = 'Blog Tags'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('website:blog_tag', kwargs={'slug': self.slug})


class BlogPost(models.Model):
    """Blog posts with SEO optimization and rich content"""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blog_posts')
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    tags = models.ManyToManyField(BlogTag, blank=True, related_name='posts')

    # Content
    excerpt = models.TextField(max_length=300, help_text='Brief summary for listings and SEO')
    content = RichTextUploadingField()
    featured_image = models.ImageField(upload_to='blog/featured/', blank=True, null=True)
    featured_image_alt = models.CharField(max_length=200, blank=True, help_text='Alt text for SEO')

    # SEO Fields
    meta_title = models.CharField(max_length=70, blank=True, help_text='SEO title (leave blank to use post title)')
    meta_description = models.CharField(max_length=160, blank=True, help_text='SEO meta description')
    meta_keywords = models.CharField(max_length=255, blank=True, help_text='Comma-separated keywords')
    canonical_url = models.URLField(blank=True, help_text='Canonical URL if content is republished')

    # Status and Publishing
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    featured = models.BooleanField(default=False, help_text='Show in featured posts section')

    # Engagement
    views_count = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=5, help_text='Estimated reading time in minutes')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto-set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        # Calculate reading time based on content word count
        if self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, round(word_count / 200))  # Average 200 words per minute

        # Use title as meta_title if not set
        if not self.meta_title:
            self.meta_title = self.title[:70]

        # Use excerpt as meta_description if not set
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('website:blog_detail', kwargs={'slug': self.slug})

    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    @property
    def is_published(self):
        return self.status == 'published' and self.published_at and self.published_at <= timezone.now()


class Product(models.Model):
    """Products for the store (e.g., templates, add-ons, services)"""

    PRODUCT_TYPE_CHOICES = [
        ('digital', 'Digital Product'),
        ('subscription', 'Subscription'),
        ('service', 'Service'),
        ('physical', 'Physical Product'),
    ]

    # Basic Information
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='digital')
    sku = models.CharField(max_length=100, unique=True, blank=True)

    # Description
    short_description = models.TextField(max_length=300)
    description = RichTextUploadingField()

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                          help_text='Original price for showing discounts')

    # Stripe Integration
    stripe_price_id = models.CharField(max_length=255, blank=True, help_text='Stripe Price ID')
    stripe_product_id = models.CharField(max_length=255, blank=True, help_text='Stripe Product ID')

    # Images
    featured_image = models.ImageField(upload_to='products/featured/', blank=True, null=True)
    image_1 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='products/', blank=True, null=True)

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = f"PROD-{uuid.uuid4().hex[:8].upper()}"
        if not self.meta_title:
            self.meta_title = self.name[:70]
        if not self.meta_description and self.short_description:
            self.meta_description = self.short_description[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('website:product_detail', kwargs={'slug': self.slug})

    @property
    def discount_percentage(self):
        """Calculate discount percentage if compare_at_price is set"""
        if self.compare_at_price and self.compare_at_price > self.price:
            return round(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0

    @property
    def has_discount(self):
        """Check if product has a discount"""
        return self.discount_percentage > 0


class ContactSubmission(models.Model):
    """Contact form submissions from the website"""

    INQUIRY_TYPE_CHOICES = [
        ('general', 'General Inquiry'),
        ('sales', 'Sales'),
        ('support', 'Support'),
        ('partnership', 'Partnership'),
        ('media', 'Media'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('spam', 'Spam'),
    ]

    # Contact Information
    name = models.CharField(max_length=200)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=200, blank=True)

    # Inquiry Details
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES, default='general')
    subject = models.CharField(max_length=200)
    message = models.TextField()

    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True, max_length=500)

    # Follow-up
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_contacts')
    notes = models.TextField(blank=True, help_text='Internal notes')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} - {self.subject}"

    @property
    def is_new(self):
        return self.status == 'new'


class NewsletterSubscriber(models.Model):
    """Newsletter subscription management"""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('unsubscribed', 'Unsubscribed'),
        ('bounced', 'Bounced'),
    ]

    email = models.EmailField(unique=True, validators=[EmailValidator()])
    name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Preferences
    interests = models.JSONField(default=dict, blank=True, help_text='User interests and preferences')

    # Metadata
    source = models.CharField(max_length=100, blank=True, help_text='Where did they subscribe from?')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    confirmation_token = models.CharField(max_length=64, blank=True, unique=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Generate confirmation token if new
        if not self.confirmation_token:
            self.confirmation_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def confirm_subscription(self):
        """Confirm the newsletter subscription"""
        self.confirmed_at = timezone.now()
        self.status = 'active'
        self.save(update_fields=['confirmed_at', 'status'])

    def unsubscribe(self):
        """Unsubscribe from newsletter"""
        self.status = 'unsubscribed'
        self.unsubscribed_at = timezone.now()
        self.save(update_fields=['status', 'unsubscribed_at'])

    @property
    def is_confirmed(self):
        return self.confirmed_at is not None

    @property
    def is_active(self):
        return self.status == 'active' and self.is_confirmed


class CaseStudyCategory(models.Model):
    """Categories for case studies"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='FontAwesome icon class')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Case Study Category'
        verbose_name_plural = 'Case Study Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('website:case_study_category', kwargs={'slug': self.slug})


class CaseStudy(models.Model):
    """Case studies showcasing client success stories"""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    client_name = models.CharField(max_length=200)
    client_logo = models.ImageField(upload_to='case_studies/logos/', blank=True, null=True)
    category = models.ForeignKey(CaseStudyCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='case_studies')

    # Content
    excerpt = models.TextField(max_length=300, help_text='Brief summary for listings')
    challenge = RichTextUploadingField(help_text='The challenge the client faced')
    solution = RichTextUploadingField(help_text='How Aureon solved the problem')
    results = RichTextUploadingField(help_text='The results achieved')
    testimonial = models.TextField(blank=True, help_text='Client testimonial quote')
    testimonial_author = models.CharField(max_length=200, blank=True)
    testimonial_role = models.CharField(max_length=200, blank=True)

    # Metrics/Results
    metric_1_value = models.CharField(max_length=50, blank=True, help_text='e.g., 50%')
    metric_1_label = models.CharField(max_length=100, blank=True, help_text='e.g., Time Saved')
    metric_2_value = models.CharField(max_length=50, blank=True)
    metric_2_label = models.CharField(max_length=100, blank=True)
    metric_3_value = models.CharField(max_length=50, blank=True)
    metric_3_label = models.CharField(max_length=100, blank=True)

    # Images
    featured_image = models.ImageField(upload_to='case_studies/featured/', blank=True, null=True)
    featured_image_alt = models.CharField(max_length=200, blank=True)
    gallery_image_1 = models.ImageField(upload_to='case_studies/gallery/', blank=True, null=True)
    gallery_image_2 = models.ImageField(upload_to='case_studies/gallery/', blank=True, null=True)
    gallery_image_3 = models.ImageField(upload_to='case_studies/gallery/', blank=True, null=True)

    # SEO Fields
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    # Status and Publishing
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    featured = models.BooleanField(default=False, help_text='Show in featured section')

    # Engagement
    views_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Case Study'
        verbose_name_plural = 'Case Studies'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.title} - {self.client_name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        if not self.meta_title:
            self.meta_title = self.title[:70]
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('website:case_study_detail', kwargs={'slug': self.slug})

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    @property
    def is_published(self):
        return self.status == 'published' and self.published_at and self.published_at <= timezone.now()


class Service(models.Model):
    """Services offered by Aureon"""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='FontAwesome icon class e.g., fa-chart-line')
    short_description = models.TextField(max_length=300)
    description = RichTextUploadingField()
    featured_image = models.ImageField(upload_to='services/', blank=True, null=True)

    # Features (bullet points)
    feature_1 = models.CharField(max_length=200, blank=True)
    feature_2 = models.CharField(max_length=200, blank=True)
    feature_3 = models.CharField(max_length=200, blank=True)
    feature_4 = models.CharField(max_length=200, blank=True)
    feature_5 = models.CharField(max_length=200, blank=True)

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    # Display
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.meta_title:
            self.meta_title = self.name[:70]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('website:service_detail', kwargs={'slug': self.slug})

    @property
    def features_list(self):
        """Return list of non-empty features"""
        features = [self.feature_1, self.feature_2, self.feature_3, self.feature_4, self.feature_5]
        return [f for f in features if f]


class TeamMember(models.Model):
    """Team members for the about/team page"""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    role = models.CharField(max_length=200)
    bio = models.TextField()
    photo = models.ImageField(upload_to='team/', blank=True, null=True)

    # Social Links
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)

    # Display
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_leadership = models.BooleanField(default=False, help_text='Show in leadership section')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.role}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class FAQ(models.Model):
    """Frequently Asked Questions"""

    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('pricing', 'Pricing & Billing'),
        ('features', 'Features'),
        ('technical', 'Technical'),
        ('security', 'Security & Privacy'),
        ('support', 'Support'),
    ]

    question = models.CharField(max_length=500)
    answer = RichTextUploadingField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text='Show on homepage FAQ section')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['category', 'order']

    def __str__(self):
        return self.question[:100]


class Testimonial(models.Model):
    """Client testimonials"""

    client_name = models.CharField(max_length=200)
    client_role = models.CharField(max_length=200)
    client_company = models.CharField(max_length=200, blank=True)
    client_photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    content = models.TextField()
    rating = models.PositiveIntegerField(default=5, help_text='Rating out of 5')

    # Display
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.client_name} - {self.client_company}"


class SiteSettings(models.Model):
    """Global site settings for the marketing website"""

    # Company Information
    company_name = models.CharField(max_length=200, default='Aureon by Rhematek Solutions')
    tagline = models.CharField(max_length=200, default='Automate Your Business, Amplify Your Growth')
    description = models.TextField(blank=True)

    # Contact Information
    contact_email = models.EmailField(default='info@rhematek-solutions.com')
    support_email = models.EmailField(default='support@rhematek-solutions.com')
    sales_email = models.EmailField(default='sales@rhematek-solutions.com')
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)

    # Social Media Links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)

    # SEO Defaults
    default_meta_title = models.CharField(max_length=70, blank=True)
    default_meta_description = models.CharField(max_length=160, blank=True)
    default_meta_keywords = models.CharField(max_length=255, blank=True)

    # Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True, help_text='GA4 Measurement ID')
    google_tag_manager_id = models.CharField(max_length=50, blank=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True)

    # Features
    maintenance_mode = models.BooleanField(default=False)
    allow_newsletter_signup = models.BooleanField(default=True)
    show_blog = models.BooleanField(default=True)
    show_store = models.BooleanField(default=True)

    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    @classmethod
    def get_settings(cls):
        """Get or create site settings singleton"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
