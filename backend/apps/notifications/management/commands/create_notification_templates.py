"""
Management command to create default notification templates.

Usage:
    python manage.py create_notification_templates
"""

from django.core.management.base import BaseCommand
from apps.notifications.models import NotificationTemplate


class Command(BaseCommand):
    help = 'Creates default notification templates for the platform'

    def handle(self, *args, **options):
        """Create all default notification templates."""

        templates_created = 0
        templates_updated = 0

        # Define all default templates
        templates = [
            {
                'template_type': NotificationTemplate.INVOICE_CREATED,
                'name': 'Invoice Created',
                'channel': NotificationTemplate.EMAIL,
                'subject': 'Invoice {{invoice_number}} Created',
                'body_text': '''Hello {{client_name}},

A new invoice has been created for your account.

Invoice Number: {{invoice_number}}
Amount: {{amount}} {{currency}}
Issue Date: {{issue_date}}
Due Date: {{due_date}}

Please log in to your account to view the invoice details.

Thank you,
{{company_name}}''',
                'body_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #1E40AF;">Invoice Created</h2>
    <p>Hello {{client_name}},</p>
    <p>A new invoice has been created for your account.</p>
    <div style="background: #F3F4F6; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p><strong>Invoice Number:</strong> {{invoice_number}}</p>
        <p><strong>Amount:</strong> {{amount}} {{currency}}</p>
        <p><strong>Issue Date:</strong> {{issue_date}}</p>
        <p><strong>Due Date:</strong> {{due_date}}</p>
    </div>
    <p>Please log in to your account to view the invoice details.</p>
    <p>Thank you,<br>{{company_name}}</p>
</body>
</html>''',
                'send_to_client': True,
                'send_to_owner': False,
                'available_variables': ['invoice_number', 'client_name', 'amount', 'currency', 'due_date', 'issue_date', 'company_name'],
            },
            {
                'template_type': NotificationTemplate.INVOICE_SENT,
                'name': 'Invoice Sent to Client',
                'channel': NotificationTemplate.EMAIL,
                'subject': 'Invoice {{invoice_number}} from {{company_name}}',
                'body_text': '''Hello {{client_name}},

Please find your invoice attached.

Invoice Number: {{invoice_number}}
Amount Due: {{amount}} {{currency}}
Due Date: {{due_date}}

You can view and pay this invoice by logging into your account.

Thank you for your business!

Best regards,
{{company_name}}''',
                'body_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #1E40AF;">Invoice from {{company_name}}</h2>
    <p>Hello {{client_name}},</p>
    <p>Please find your invoice below.</p>
    <div style="background: #F3F4F6; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p><strong>Invoice Number:</strong> {{invoice_number}}</p>
        <p><strong>Amount Due:</strong> <span style="color: #10B981; font-size: 20px;">{{amount}} {{currency}}</span></p>
        <p><strong>Due Date:</strong> {{due_date}}</p>
    </div>
    <p>You can view and pay this invoice by logging into your account.</p>
    <p>Thank you for your business!</p>
    <p>Best regards,<br>{{company_name}}</p>
</body>
</html>''',
                'send_to_client': True,
                'send_to_owner': False,
                'available_variables': ['invoice_number', 'client_name', 'amount', 'currency', 'due_date', 'company_name'],
            },
            {
                'template_type': NotificationTemplate.INVOICE_PAID,
                'name': 'Invoice Paid Confirmation',
                'channel': NotificationTemplate.EMAIL,
                'subject': 'Payment Received - Invoice {{invoice_number}}',
                'body_text': '''Hello {{client_name}},

Thank you! We have received your payment.

Invoice Number: {{invoice_number}}
Amount Paid: {{amount}} {{currency}}
Payment Date: {{issue_date}}

A receipt has been sent to your email.

Thank you for your business!

Best regards,
{{company_name}}''',
                'body_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #10B981;">✓ Payment Received</h2>
    <p>Hello {{client_name}},</p>
    <p>Thank you! We have received your payment.</p>
    <div style="background: #ECFDF5; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #10B981;">
        <p><strong>Invoice Number:</strong> {{invoice_number}}</p>
        <p><strong>Amount Paid:</strong> {{amount}} {{currency}}</p>
        <p><strong>Payment Date:</strong> {{issue_date}}</p>
    </div>
    <p>A receipt has been sent to your email.</p>
    <p>Thank you for your business!</p>
    <p>Best regards,<br>{{company_name}}</p>
</body>
</html>''',
                'send_to_client': True,
                'send_to_owner': False,
                'available_variables': ['invoice_number', 'client_name', 'amount', 'currency', 'issue_date', 'company_name'],
            },
            {
                'template_type': NotificationTemplate.INVOICE_OVERDUE,
                'name': 'Invoice Overdue Reminder',
                'channel': NotificationTemplate.EMAIL,
                'subject': 'Overdue Invoice Reminder - {{invoice_number}}',
                'body_text': '''Hello {{client_name}},

This is a friendly reminder that invoice {{invoice_number}} is now overdue.

Invoice Number: {{invoice_number}}
Amount Due: {{amount}} {{currency}}
Original Due Date: {{due_date}}

Please arrange payment at your earliest convenience.

If you have any questions, please don't hesitate to contact us.

Best regards,
{{company_name}}''',
                'body_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #EF4444;">Overdue Invoice Reminder</h2>
    <p>Hello {{client_name}},</p>
    <p>This is a friendly reminder that the following invoice is now overdue.</p>
    <div style="background: #FEF2F2; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #EF4444;">
        <p><strong>Invoice Number:</strong> {{invoice_number}}</p>
        <p><strong>Amount Due:</strong> {{amount}} {{currency}}</p>
        <p><strong>Original Due Date:</strong> {{due_date}}</p>
    </div>
    <p>Please arrange payment at your earliest convenience.</p>
    <p>If you have any questions, please don't hesitate to contact us.</p>
    <p>Best regards,<br>{{company_name}}</p>
</body>
</html>''',
                'send_to_client': True,
                'send_to_owner': False,
                'available_variables': ['invoice_number', 'client_name', 'amount', 'currency', 'due_date', 'company_name'],
            },
            {
                'template_type': NotificationTemplate.PAYMENT_RECEIPT,
                'name': 'Payment Receipt',
                'channel': NotificationTemplate.EMAIL,
                'subject': 'Payment Receipt - {{payment_id}}',
                'body_text': '''Hello {{client_name}},

Thank you for your payment! Here is your receipt.

Payment ID: {{payment_id}}
Invoice Number: {{invoice_number}}
Amount: {{amount}} {{currency}}
Payment Date: {{payment_date}}
Payment Method: {{payment_method}}

Thank you for your business!

Best regards,
{{company_name}}''',
                'body_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #10B981;">Payment Receipt</h2>
    <p>Hello {{client_name}},</p>
    <p>Thank you for your payment! Here is your receipt.</p>
    <div style="background: #ECFDF5; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #059669;">Payment Details</h3>
        <p><strong>Payment ID:</strong> {{payment_id}}</p>
        <p><strong>Invoice Number:</strong> {{invoice_number}}</p>
        <p><strong>Amount:</strong> <span style="font-size: 24px; color: #059669;">{{amount}} {{currency}}</span></p>
        <p><strong>Payment Date:</strong> {{payment_date}}</p>
        <p><strong>Payment Method:</strong> {{payment_method}}</p>
    </div>
    <p>Thank you for your business!</p>
    <p>Best regards,<br>{{company_name}}</p>
</body>
</html>''',
                'send_to_client': True,
                'send_to_owner': False,
                'available_variables': ['payment_id', 'invoice_number', 'client_name', 'amount', 'currency', 'payment_date', 'payment_method', 'company_name'],
            },
            {
                'template_type': NotificationTemplate.REMINDER_PAYMENT_DUE,
                'name': 'Payment Due Reminder',
                'channel': NotificationTemplate.EMAIL,
                'subject': 'Payment Due in 3 Days - {{invoice_number}}',
                'body_text': '''Hello {{client_name}},

This is a friendly reminder that payment for invoice {{invoice_number}} is due in 3 days.

Invoice Number: {{invoice_number}}
Amount Due: {{amount}} {{currency}}
Due Date: {{due_date}}

Please ensure payment is made before the due date.

Thank you!

Best regards,
{{company_name}}''',
                'body_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #F59E0B;">Payment Reminder</h2>
    <p>Hello {{client_name}},</p>
    <p>This is a friendly reminder that payment for the following invoice is due in 3 days.</p>
    <div style="background: #FFFBEB; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #F59E0B;">
        <p><strong>Invoice Number:</strong> {{invoice_number}}</p>
        <p><strong>Amount Due:</strong> {{amount}} {{currency}}</p>
        <p><strong>Due Date:</strong> {{due_date}}</p>
    </div>
    <p>Please ensure payment is made before the due date.</p>
    <p>Thank you!</p>
    <p>Best regards,<br>{{company_name}}</p>
</body>
</html>''',
                'send_to_client': True,
                'send_to_owner': False,
                'available_variables': ['invoice_number', 'client_name', 'amount', 'currency', 'due_date', 'company_name'],
            },
            {
                'template_type': NotificationTemplate.CONTRACT_SIGNED,
                'name': 'Contract Signed Confirmation',
                'channel': NotificationTemplate.EMAIL,
                'subject': 'Contract Signed - {{contract_title}}',
                'body_text': '''Hello {{client_name}},

Your contract has been successfully signed!

Contract: {{contract_title}}
Value: {{contract_value}}
Start Date: {{start_date}}

A copy of the signed contract has been sent to your email.

Thank you for your business!

Best regards,
{{company_name}}''',
                'body_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #10B981;">✓ Contract Signed</h2>
    <p>Hello {{client_name}},</p>
    <p>Your contract has been successfully signed!</p>
    <div style="background: #ECFDF5; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p><strong>Contract:</strong> {{contract_title}}</p>
        <p><strong>Value:</strong> {{contract_value}}</p>
        <p><strong>Start Date:</strong> {{start_date}}</p>
    </div>
    <p>A copy of the signed contract has been sent to your email.</p>
    <p>Thank you for your business!</p>
    <p>Best regards,<br>{{company_name}}</p>
</body>
</html>''',
                'send_to_client': True,
                'send_to_owner': False,
                'available_variables': ['contract_title', 'client_name', 'contract_value', 'start_date', 'company_name'],
            },
            {
                'template_type': NotificationTemplate.CLIENT_WELCOME,
                'name': 'Welcome New Client',
                'channel': NotificationTemplate.EMAIL,
                'subject': 'Welcome to {{company_name}}!',
                'body_text': '''Hello {{client_name}},

Welcome to {{company_name}}! We're excited to work with you.

We've created your account and you can now access your client portal to:
- View invoices and contracts
- Make payments
- Download receipts
- Track project progress

If you have any questions, please don't hesitate to reach out.

Best regards,
{{company_name}}''',
                'body_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #1E40AF;">Welcome to {{company_name}}!</h2>
    <p>Hello {{client_name}},</p>
    <p>Welcome! We're excited to work with you.</p>
    <div style="background: #EEF2FF; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #1E40AF;">Your Client Portal</h3>
        <p>You can now access your client portal to:</p>
        <ul style="list-style: none; padding-left: 0;">
            <li>✓ View invoices and contracts</li>
            <li>✓ Make payments</li>
            <li>✓ Download receipts</li>
            <li>✓ Track project progress</li>
        </ul>
    </div>
    <p>If you have any questions, please don't hesitate to reach out.</p>
    <p>Best regards,<br>{{company_name}}</p>
</body>
</html>''',
                'send_to_client': True,
                'send_to_owner': False,
                'available_variables': ['client_name', 'company_name'],
            },
            {
                'template_type': NotificationTemplate.PAYMENT_RECEIVED,
                'name': 'Payment Received Notification',
                'channel': NotificationTemplate.EMAIL,
                'subject': 'Payment Received - {{amount}} {{currency}}',
                'body_text': '''Hello,

We have received a payment for invoice {{invoice_number}}.

Payment Details:
Amount: {{amount}} {{currency}}
Payment Method: {{payment_method}}
Payment Date: {{payment_date}}
Transaction ID: {{transaction_id}}

The invoice has been marked as paid.

Thank you!

Best regards,
{{company_name}}''',
                'body_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #10B981;">✓ Payment Received</h2>
    <p>Hello,</p>
    <p>We have received a payment for invoice <strong>{{invoice_number}}</strong>.</p>
    <div style="background: #ECFDF5; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #10B981;">
        <h3 style="margin-top: 0; color: #059669;">Payment Details</h3>
        <p><strong>Amount:</strong> <span style="font-size: 24px; color: #059669;">{{amount}} {{currency}}</span></p>
        <p><strong>Payment Method:</strong> {{payment_method}}</p>
        <p><strong>Payment Date:</strong> {{payment_date}}</p>
        <p><strong>Transaction ID:</strong> {{transaction_id}}</p>
    </div>
    <p>The invoice has been marked as paid.</p>
    <p>Thank you!</p>
    <p>Best regards,<br>{{company_name}}</p>
</body>
</html>''',
                'send_to_client': False,
                'send_to_owner': True,
                'available_variables': ['invoice_number', 'amount', 'currency', 'payment_method', 'payment_date', 'transaction_id', 'company_name'],
            },
            {
                'template_type': NotificationTemplate.PAYMENT_FAILED,
                'name': 'Payment Failed Notification',
                'channel': NotificationTemplate.EMAIL,
                'subject': 'Payment Failed - Invoice {{invoice_number}}',
                'body_text': '''Hello {{client_name}},

We were unable to process your payment for invoice {{invoice_number}}.

Invoice Details:
Invoice Number: {{invoice_number}}
Amount: {{amount}} {{currency}}
Due Date: {{due_date}}

Failure Reason: {{failure_reason}}

Please update your payment method or contact us to resolve this issue.

You can view and pay this invoice by logging into your account.

If you have any questions, please don't hesitate to contact us.

Best regards,
{{company_name}}''',
                'body_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #EF4444;">⚠ Payment Failed</h2>
    <p>Hello {{client_name}},</p>
    <p>We were unable to process your payment for invoice <strong>{{invoice_number}}</strong>.</p>
    <div style="background: #FEF2F2; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #EF4444;">
        <h3 style="margin-top: 0; color: #DC2626;">Invoice Details</h3>
        <p><strong>Invoice Number:</strong> {{invoice_number}}</p>
        <p><strong>Amount:</strong> {{amount}} {{currency}}</p>
        <p><strong>Due Date:</strong> {{due_date}}</p>
        <p style="margin-top: 15px; padding: 10px; background: #FEE2E2; border-radius: 3px;">
            <strong>Failure Reason:</strong> {{failure_reason}}
        </p>
    </div>
    <p><strong>Please update your payment method or contact us to resolve this issue.</strong></p>
    <p>You can view and pay this invoice by logging into your account.</p>
    <p>If you have any questions, please don't hesitate to contact us.</p>
    <p>Best regards,<br>{{company_name}}</p>
</body>
</html>''',
                'send_to_client': True,
                'send_to_owner': False,
                'available_variables': ['client_name', 'invoice_number', 'amount', 'currency', 'due_date', 'failure_reason', 'company_name'],
            },
            {
                'template_type': NotificationTemplate.CONTRACT_EXPIRING,
                'name': 'Contract Expiring Soon',
                'channel': NotificationTemplate.EMAIL,
                'subject': 'Contract Expiring Soon - {{contract_title}}',
                'body_text': '''Hello {{client_name}},

This is a reminder that your contract is expiring soon.

Contract Details:
Contract: {{contract_title}}
Expiration Date: {{expiration_date}}
Days Remaining: {{days_remaining}}

If you would like to renew this contract, please contact us.

We value your business and look forward to continuing our partnership.

Best regards,
{{company_name}}''',
                'body_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #F59E0B;">⏰ Contract Expiring Soon</h2>
    <p>Hello {{client_name}},</p>
    <p>This is a reminder that your contract is expiring soon.</p>
    <div style="background: #FFFBEB; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #F59E0B;">
        <h3 style="margin-top: 0; color: #D97706;">Contract Details</h3>
        <p><strong>Contract:</strong> {{contract_title}}</p>
        <p><strong>Expiration Date:</strong> {{expiration_date}}</p>
        <p><strong>Days Remaining:</strong> <span style="font-size: 20px; color: #D97706;">{{days_remaining}}</span></p>
    </div>
    <p><strong>If you would like to renew this contract, please contact us.</strong></p>
    <p>We value your business and look forward to continuing our partnership.</p>
    <p>Best regards,<br>{{company_name}}</p>
</body>
</html>''',
                'send_to_client': True,
                'send_to_owner': False,
                'available_variables': ['client_name', 'contract_title', 'expiration_date', 'days_remaining', 'company_name'],
            },
        ]

        # Create or update templates
        for template_data in templates:
            template, created = NotificationTemplate.objects.update_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )

            if created:
                templates_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created template: {template.name}')
                )
            else:
                templates_updated += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated template: {template.name}')
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully created {templates_created} new templates'
            )
        )
        if templates_updated > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'↻ Updated {templates_updated} existing templates'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n📧 Total templates: {templates_created + templates_updated}'
            )
        )
