from django import forms
from django.core.validators import EmailValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML
from crispy_forms.bootstrap import FormActions
from .models import ContactSubmission, NewsletterSubscriber


class ContactForm(forms.ModelForm):
    """Contact form for the contact page"""

    class Meta:
        model = ContactSubmission
        fields = ['name', 'email', 'phone', 'company', 'inquiry_type', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name *',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address *',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number',
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company Name',
            }),
            'inquiry_type': forms.Select(attrs={
                'class': 'form-control nice-select',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject *',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write Your Message *',
                'rows': 6,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'contact-form'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('phone', css_class='form-group col-md-6 mb-3'),
                Column('company', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('inquiry_type', css_class='form-group col-md-6 mb-3'),
                Column('subject', css_class='form-group col-md-6 mb-3'),
            ),
            Field('message', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Send Message', css_class='btn btn-primary px-4 py-2')
            )
        )

        # Make fields required
        self.fields['name'].required = True
        self.fields['email'].required = True
        self.fields['subject'].required = True
        self.fields['message'].required = True

    def clean_email(self):
        """Validate and clean email"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # Additional spam check
            spam_domains = ['tempmail.com', 'throwaway.email', '10minutemail.com']
            domain = email.split('@')[-1]
            if domain in spam_domains:
                raise forms.ValidationError('Please use a valid email address.')
        return email

    def clean_message(self):
        """Validate message content"""
        message = self.cleaned_data.get('message')
        if message:
            # Check minimum length
            if len(message) < 10:
                raise forms.ValidationError('Please provide a more detailed message (at least 10 characters).')
            # Basic spam detection
            spam_keywords = ['viagra', 'cialis', 'casino', 'lottery', 'winner']
            if any(keyword in message.lower() for keyword in spam_keywords):
                raise forms.ValidationError('Your message contains inappropriate content.')
        return message


class NewsletterForm(forms.ModelForm):
    """Newsletter subscription form"""

    class Meta:
        model = NewsletterSubscriber
        fields = ['email', 'name']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'required': True,
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name (optional)',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'newsletter-form d-flex'
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Field('email', css_class='flex-grow-1'),
            Submit('subscribe', 'Subscribe', css_class='btn btn-primary ms-2')
        )

    def clean_email(self):
        """Validate and clean email"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # Check if already subscribed
            if NewsletterSubscriber.objects.filter(email=email, status='active').exists():
                raise forms.ValidationError('This email is already subscribed to our newsletter.')
        return email


class SalesInquiryForm(forms.Form):
    """Sales inquiry form for pricing page or sales contact"""

    COMPANY_SIZE_CHOICES = [
        ('', 'Select Company Size'),
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('500+', '500+ employees'),
    ]

    BUDGET_CHOICES = [
        ('', 'Select Budget Range'),
        ('under-1k', 'Under $1,000/month'),
        ('1k-5k', '$1,000 - $5,000/month'),
        ('5k-10k', '$5,000 - $10,000/month'),
        ('10k-25k', '$10,000 - $25,000/month'),
        ('25k+', '$25,000+/month'),
    ]

    # Contact Information
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name *',
        })
    )

    email = forms.EmailField(
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Work Email *',
        })
    )

    phone = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number',
        })
    )

    # Company Information
    company = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Company Name *',
        })
    )

    company_size = forms.ChoiceField(
        choices=COMPANY_SIZE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control nice-select',
        })
    )

    industry = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Industry',
        })
    )

    # Inquiry Details
    interested_plan = forms.ChoiceField(
        choices=[
            ('', 'Select Plan'),
            ('starter', 'Starter Plan'),
            ('pro', 'Pro Plan'),
            ('business', 'Business Plan'),
            ('enterprise', 'Enterprise Plan'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control nice-select',
        })
    )

    budget_range = forms.ChoiceField(
        choices=BUDGET_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control nice-select',
        })
    )

    timeline = forms.ChoiceField(
        choices=[
            ('', 'Implementation Timeline'),
            ('immediate', 'Immediate (within 1 month)'),
            ('1-3months', '1-3 months'),
            ('3-6months', '3-6 months'),
            ('6months+', '6+ months'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control nice-select',
        })
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Tell us about your needs and goals *',
            'rows': 5,
        })
    )

    # Privacy consent
    accept_privacy = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='I agree to the Privacy Policy and Terms of Service'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'sales-inquiry-form'
        self.helper.layout = Layout(
            HTML('<h4 class="mb-4">Contact Information</h4>'),
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('phone', css_class='form-group col-md-6 mb-3'),
                Column('company', css_class='form-group col-md-6 mb-3'),
            ),
            HTML('<h4 class="mb-4 mt-4">Company Details</h4>'),
            Row(
                Column('company_size', css_class='form-group col-md-6 mb-3'),
                Column('industry', css_class='form-group col-md-6 mb-3'),
            ),
            HTML('<h4 class="mb-4 mt-4">Project Information</h4>'),
            Row(
                Column('interested_plan', css_class='form-group col-md-4 mb-3'),
                Column('budget_range', css_class='form-group col-md-4 mb-3'),
                Column('timeline', css_class='form-group col-md-4 mb-3'),
            ),
            Field('message', css_class='form-group mb-3'),
            Field('accept_privacy', css_class='form-check mb-3'),
            FormActions(
                Submit('submit', 'Request Demo', css_class='btn btn-primary btn-lg px-5 py-3')
            )
        )

    def clean_email(self):
        """Validate business email"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # Encourage business emails
            free_email_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
            domain = email.split('@')[-1]
            if domain in free_email_domains:
                # Don't raise error, but could add a warning in the future
                pass
        return email

    def save(self):
        """Save as ContactSubmission"""
        data = self.cleaned_data
        return ContactSubmission.objects.create(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', ''),
            company=data.get('company', ''),
            inquiry_type='sales',
            subject=f"Sales Inquiry - {data.get('interested_plan', 'General')}",
            message=f"""
Company Size: {data.get('company_size', 'Not specified')}
Industry: {data.get('industry', 'Not specified')}
Interested Plan: {data.get('interested_plan', 'Not specified')}
Budget Range: {data.get('budget_range', 'Not specified')}
Timeline: {data.get('timeline', 'Not specified')}

Message:
{data['message']}
            """.strip()
        )


class QuickContactForm(forms.Form):
    """Quick contact form for sidebar/footer"""

    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Your Name',
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Email Address',
        })
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Your Message',
            'rows': 3,
        })
    )

    def save(self):
        """Save as ContactSubmission"""
        data = self.cleaned_data
        return ContactSubmission.objects.create(
            name=data['name'],
            email=data['email'],
            inquiry_type='general',
            subject='Quick Contact Form',
            message=data['message']
        )
