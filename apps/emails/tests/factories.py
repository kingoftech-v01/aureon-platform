"""
Factories for emails app tests.
"""

import factory
import uuid
from django.utils import timezone
from apps.accounts.models import User
from apps.emails.models import EmailAccount, EmailMessage, EmailAttachment, EmailTemplate


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f'user{n}@test.com')
    username = factory.Sequence(lambda n: f'user{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    role = User.ADMIN
    is_staff = True
    is_active = True
    is_verified = True


class EmailAccountFactory(factory.django.DjangoModelFactory):
    """Factory for EmailAccount model."""

    class Meta:
        model = EmailAccount

    user = factory.SubFactory(UserFactory)
    email_address = factory.Sequence(lambda n: f'account{n}@test.com')
    display_name = factory.Faker('name')
    provider = EmailAccount.SMTP
    config = factory.LazyFunction(lambda: {'host': 'smtp.test.com', 'port': 587})
    is_active = True
    is_default = False


class EmailMessageFactory(factory.django.DjangoModelFactory):
    """Factory for EmailMessage model."""

    class Meta:
        model = EmailMessage

    account = factory.SubFactory(EmailAccountFactory)
    direction = EmailMessage.OUTBOUND
    from_email = factory.LazyAttribute(lambda o: o.account.email_address)
    to_emails = factory.LazyFunction(lambda: ['recipient@test.com'])
    cc_emails = factory.LazyFunction(list)
    bcc_emails = factory.LazyFunction(list)
    subject = factory.Sequence(lambda n: f'Test Email Subject {n}')
    body_text = factory.Faker('paragraph')
    body_html = factory.LazyAttribute(lambda o: f'<p>{o.body_text}</p>')
    status = EmailMessage.DRAFT
    is_read = False
    message_id = factory.Sequence(lambda n: f'msg-{n}@test.com')


class EmailAttachmentFactory(factory.django.DjangoModelFactory):
    """Factory for EmailAttachment model."""

    class Meta:
        model = EmailAttachment

    email = factory.SubFactory(EmailMessageFactory)
    file = factory.django.FileField(filename='test_file.pdf', data=b'test file content')
    file_name = factory.Sequence(lambda n: f'attachment_{n}.pdf')
    file_type = 'application/pdf'


class EmailTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for EmailTemplate model."""

    class Meta:
        model = EmailTemplate

    name = factory.Sequence(lambda n: f'Template {n}')
    subject = 'Hello $client_name'
    body_text = 'Dear $client_name, this is about $project_name.'
    body_html = '<p>Dear $client_name, this is about $project_name.</p>'
    category = EmailTemplate.GENERAL
    available_variables = factory.LazyFunction(lambda: ['client_name', 'project_name'])
    is_active = True
    owner = factory.SubFactory(UserFactory)
