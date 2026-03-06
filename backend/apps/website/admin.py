from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    BlogPost, BlogCategory, BlogTag, Product,
    ContactSubmission, NewsletterSubscriber, SiteSettings,
    CaseStudyCategory, CaseStudy, Service, TeamMember, FAQ, Testimonial
)


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    def post_count(self, obj):
        count = obj.posts.filter(status='published').count()
        return format_html('<strong>{}</strong>', count)
    post_count.short_description = 'Published Posts'


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    def post_count(self, obj):
        count = obj.posts.filter(status='published').count()
        return format_html('<strong>{}</strong>', count)
    post_count.short_description = 'Published Posts'


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'category', 'status',
        'featured_badge', 'views_count', 'published_at', 'created_at'
    ]
    list_filter = ['status', 'featured', 'category', 'created_at', 'published_at']
    search_fields = ['title', 'excerpt', 'content', 'meta_keywords']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    readonly_fields = ['views_count', 'reading_time', 'created_at', 'updated_at']
    date_hierarchy = 'published_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'category', 'tags')
        }),
        ('Content', {
            'fields': ('excerpt', 'content', 'featured_image', 'featured_image_alt')
        }),
        ('SEO Optimization', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'canonical_url'),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('status', 'published_at', 'featured')
        }),
        ('Engagement Metrics', {
            'fields': ('views_count', 'reading_time'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def featured_badge(self, obj):
        if obj.featured:
            return format_html('<span style="color: gold;">★ Featured</span>')
        return '-'
    featured_badge.short_description = 'Featured'

    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    actions = ['publish_posts', 'unpublish_posts', 'feature_posts', 'unfeature_posts']

    def publish_posts(self, request, queryset):
        updated = queryset.filter(status='draft').update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f'{updated} post(s) published successfully.')
    publish_posts.short_description = 'Publish selected posts'

    def unpublish_posts(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} post(s) unpublished.')
    unpublish_posts.short_description = 'Unpublish selected posts'

    def feature_posts(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} post(s) featured.')
    feature_posts.short_description = 'Feature selected posts'

    def unfeature_posts(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} post(s) unfeatured.')
    unfeature_posts.short_description = 'Unfeature selected posts'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'product_type', 'price', 'discount_badge',
        'stripe_status', 'is_active', 'is_featured', 'in_stock', 'created_at'
    ]
    list_filter = ['product_type', 'is_active', 'is_featured', 'in_stock', 'created_at']
    search_fields = ['name', 'description', 'sku', 'meta_keywords']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['sku', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'product_type', 'sku')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_price_id', 'stripe_product_id'),
            'classes': ('collapse',)
        }),
        ('Images', {
            'fields': ('featured_image', 'image_1', 'image_2', 'image_3')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'in_stock')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def discount_badge(self, obj):
        if obj.has_discount:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px;">{}% OFF</span>',
                obj.discount_percentage
            )
        return '-'
    discount_badge.short_description = 'Discount'

    def stripe_status(self, obj):
        if obj.stripe_price_id and obj.stripe_product_id:
            return format_html('<span style="color: green;">✓ Linked</span>')
        elif obj.stripe_product_id:
            return format_html('<span style="color: orange;">⚠ Partial</span>')
        return format_html('<span style="color: red;">✗ Not Linked</span>')
    stripe_status.short_description = 'Stripe'

    actions = ['activate_products', 'deactivate_products', 'feature_products']

    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} product(s) activated.')
    activate_products.short_description = 'Activate selected products'

    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} product(s) deactivated.')
    deactivate_products.short_description = 'Deactivate selected products'

    def feature_products(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} product(s) featured.')
    feature_products.short_description = 'Feature selected products'


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'email', 'inquiry_type', 'status_badge',
        'assigned_to', 'created_at'
    ]
    list_filter = ['status', 'inquiry_type', 'created_at']
    search_fields = ['name', 'email', 'company', 'subject', 'message']
    readonly_fields = [
        'name', 'email', 'phone', 'company', 'inquiry_type',
        'subject', 'message', 'ip_address', 'user_agent',
        'referrer', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'company')
        }),
        ('Inquiry Details', {
            'fields': ('inquiry_type', 'subject', 'message')
        }),
        ('Management', {
            'fields': ('status', 'assigned_to', 'notes', 'responded_at')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'referrer'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'new': '#dc3545',
            'in_progress': '#ffc107',
            'resolved': '#28a745',
            'spam': '#6c757d',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    actions = ['mark_as_in_progress', 'mark_as_resolved', 'mark_as_spam']

    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} submission(s) marked as in progress.')
    mark_as_in_progress.short_description = 'Mark as In Progress'

    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='resolved', responded_at=timezone.now())
        self.message_user(request, f'{updated} submission(s) marked as resolved.')
    mark_as_resolved.short_description = 'Mark as Resolved'

    def mark_as_spam(self, request, queryset):
        updated = queryset.update(status='spam')
        self.message_user(request, f'{updated} submission(s) marked as spam.')
    mark_as_spam.short_description = 'Mark as Spam'


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'name', 'status_badge', 'confirmed_badge',
        'source', 'subscribed_at'
    ]
    list_filter = ['status', 'confirmed_at', 'subscribed_at']
    search_fields = ['email', 'name']
    readonly_fields = [
        'email', 'confirmation_token', 'confirmed_at',
        'ip_address', 'subscribed_at', 'unsubscribed_at', 'updated_at'
    ]
    date_hierarchy = 'subscribed_at'

    fieldsets = (
        ('Subscriber Information', {
            'fields': ('email', 'name', 'status')
        }),
        ('Preferences', {
            'fields': ('interests',)
        }),
        ('Metadata', {
            'fields': ('source', 'ip_address', 'confirmation_token'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('subscribed_at', 'confirmed_at', 'unsubscribed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'active': '#28a745',
            'unsubscribed': '#6c757d',
            'bounced': '#dc3545',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def confirmed_badge(self, obj):
        if obj.is_confirmed:
            return format_html('<span style="color: green;">✓ Confirmed</span>')
        return format_html('<span style="color: orange;">⚠ Pending</span>')
    confirmed_badge.short_description = 'Confirmation'

    actions = ['confirm_subscriptions', 'unsubscribe_selected']

    def confirm_subscriptions(self, request, queryset):
        for subscriber in queryset:
            subscriber.confirm_subscription()
        self.message_user(request, f'{queryset.count()} subscriber(s) confirmed.')
    confirm_subscriptions.short_description = 'Confirm selected subscriptions'

    def unsubscribe_selected(self, request, queryset):
        for subscriber in queryset:
            subscriber.unsubscribe()
        self.message_user(request, f'{queryset.count()} subscriber(s) unsubscribed.')
    unsubscribe_selected.short_description = 'Unsubscribe selected'


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Only allow one instance
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False

    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'tagline', 'description')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'support_email', 'sales_email', 'phone', 'address')
        }),
        ('Social Media Links', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'youtube_url', 'instagram_url', 'github_url')
        }),
        ('SEO Defaults', {
            'fields': ('default_meta_title', 'default_meta_description', 'default_meta_keywords')
        }),
        ('Analytics', {
            'fields': ('google_analytics_id', 'google_tag_manager_id', 'facebook_pixel_id'),
            'classes': ('collapse',)
        }),
        ('Features', {
            'fields': ('maintenance_mode', 'allow_newsletter_signup', 'show_blog', 'show_store')
        }),
    )


# ============================================================
# CASE STUDY ADMIN
# ============================================================

@admin.register(CaseStudyCategory)
class CaseStudyCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'case_study_count', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    def case_study_count(self, obj):
        count = obj.case_studies.filter(status='published').count()
        return format_html('<strong>{}</strong>', count)
    case_study_count.short_description = 'Published Studies'


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'client_name', 'category', 'status',
        'featured_badge', 'published_at', 'created_at'
    ]
    list_filter = ['status', 'featured', 'category', 'created_at', 'published_at']
    search_fields = ['title', 'client_name', 'excerpt', 'challenge', 'solution', 'results']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'published_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'client_name', 'client_logo', 'category')
        }),
        ('Summary', {
            'fields': ('excerpt',)
        }),
        ('Case Study Content', {
            'fields': ('challenge', 'solution', 'results', 'testimonial', 'testimonial_author', 'testimonial_role')
        }),
        ('Metrics & Results', {
            'fields': (
                ('metric_1_value', 'metric_1_label'),
                ('metric_2_value', 'metric_2_label'),
                ('metric_3_value', 'metric_3_label'),
            )
        }),
        ('Images', {
            'fields': ('featured_image', 'featured_image_alt', 'gallery_image_1', 'gallery_image_2', 'gallery_image_3')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('status', 'published_at', 'featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def featured_badge(self, obj):
        if obj.featured:
            return format_html('<span style="color: gold;">★ Featured</span>')
        return '-'
    featured_badge.short_description = 'Featured'

    actions = ['publish_case_studies', 'unpublish_case_studies', 'feature_case_studies']

    def publish_case_studies(self, request, queryset):
        updated = queryset.filter(status='draft').update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f'{updated} case study(ies) published successfully.')
    publish_case_studies.short_description = 'Publish selected case studies'

    def unpublish_case_studies(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} case study(ies) unpublished.')
    unpublish_case_studies.short_description = 'Unpublish selected case studies'

    def feature_case_studies(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} case study(ies) featured.')
    feature_case_studies.short_description = 'Feature selected case studies'


# ============================================================
# SERVICE ADMIN
# ============================================================

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'is_featured', 'order', 'created_at']
    list_filter = ['is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'short_description', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['order', 'is_active', 'is_featured']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'icon', 'featured_image')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Features', {
            'fields': ('feature_1', 'feature_2', 'feature_3', 'feature_4', 'feature_5')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('order', 'is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================
# TEAM MEMBER ADMIN
# ============================================================

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'is_leadership', 'is_active', 'order']
    list_filter = ['is_active', 'is_leadership']
    search_fields = ['name', 'role', 'bio']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active', 'is_leadership']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'role', 'photo')
        }),
        ('Biography', {
            'fields': ('bio',)
        }),
        ('Social Links', {
            'fields': ('linkedin_url', 'twitter_url', 'github_url', 'email')
        }),
        ('Status', {
            'fields': ('order', 'is_active', 'is_leadership')
        }),
    )


# ============================================================
# FAQ ADMIN
# ============================================================

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'is_featured', 'is_active', 'order']
    list_filter = ['category', 'is_active', 'is_featured']
    search_fields = ['question', 'answer']
    list_editable = ['order', 'is_active', 'is_featured', 'category']

    fieldsets = (
        ('Question & Answer', {
            'fields': ('question', 'answer')
        }),
        ('Organization', {
            'fields': ('category', 'order', 'is_active', 'is_featured')
        }),
    )


# ============================================================
# TESTIMONIAL ADMIN
# ============================================================

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'client_company', 'rating', 'is_featured', 'is_active', 'order']
    list_filter = ['rating', 'is_active', 'is_featured']
    search_fields = ['client_name', 'client_company', 'content']
    list_editable = ['order', 'is_active', 'is_featured']

    fieldsets = (
        ('Client Information', {
            'fields': ('client_name', 'client_role', 'client_company', 'client_photo')
        }),
        ('Testimonial', {
            'fields': ('content', 'rating')
        }),
        ('Status', {
            'fields': ('order', 'is_active', 'is_featured')
        }),
    )
