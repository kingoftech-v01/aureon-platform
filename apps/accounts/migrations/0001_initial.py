# Generated for Aureon SaaS Platform
# Updated to match current User model

from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('username', models.CharField(blank=True, help_text='Optional. 150 characters or fewer.', max_length=150, null=True, unique=True, verbose_name='Username')),
                ('email', models.EmailField(help_text='Primary email address for authentication', max_length=254, unique=True, verbose_name='Email Address')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('role', models.CharField(choices=[('admin', 'Admin - Full Access'), ('manager', 'Manager - Manage Contracts & Invoices'), ('contributor', 'Contributor - Limited Access'), ('client', 'Client - Portal Access Only')], default='contributor', help_text='User role within the organization', max_length=20, verbose_name='Role')),
                ('full_name', models.CharField(blank=True, help_text='User full name', max_length=255, verbose_name='Full Name')),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(blank=True, help_text='Contact phone number', max_length=128, null=True, region=None, verbose_name='Phone Number')),
                ('job_title', models.CharField(blank=True, help_text='User job title or position', max_length=100, verbose_name='Job Title')),
                ('avatar', models.ImageField(blank=True, help_text='Profile picture', null=True, upload_to='avatars/', verbose_name='Avatar')),
                ('timezone', models.CharField(default='UTC', help_text='User preferred timezone', max_length=50, verbose_name='Timezone')),
                ('language', models.CharField(default='en', help_text='Preferred language code', max_length=10, verbose_name='Language')),
                ('email_notifications', models.BooleanField(default=True, help_text='Receive email notifications', verbose_name='Email Notifications')),
                ('sms_notifications', models.BooleanField(default=False, help_text='Receive SMS notifications', verbose_name='SMS Notifications')),
                ('two_factor_enabled', models.BooleanField(default=False, help_text='Enable 2FA for enhanced security', verbose_name='Two-Factor Authentication')),
                ('two_factor_secret', models.CharField(blank=True, help_text='TOTP secret key for 2FA', max_length=32, verbose_name='2FA Secret Key')),
                ('two_factor_backup_codes', models.JSONField(blank=True, default=list, help_text='Backup codes for 2FA recovery', verbose_name='2FA Backup Codes')),
                ('last_login_ip', models.GenericIPAddressField(blank=True, help_text='IP address of last login', null=True, verbose_name='Last Login IP')),
                ('is_verified', models.BooleanField(default=False, help_text='Whether email has been verified', verbose_name='Email Verified')),
                ('verified_at', models.DateTimeField(blank=True, help_text='When email was verified', null=True, verbose_name='Verified At')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional user metadata in JSON format', verbose_name='Metadata')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Staff Status')),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='Date Joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'ordering': ['-date_joined'],
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='accounts_us_email_06fc52_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_active'], name='accounts_us_is_acti_4ee882_idx'),
        ),
    ]
