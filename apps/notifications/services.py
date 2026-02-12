"""Services for sending notifications via different channels."""

import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from .models import Notification, NotificationTemplate

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""

    @staticmethod
    def send_email(notification):
        """
        Send email notification.

        Args:
            notification: Notification instance

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Create email message
            email = EmailMultiAlternatives(
                subject=notification.subject,
                body=notification.message_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[notification.recipient],
            )

            # Attach HTML version if available
            if notification.message_html:
                email.attach_alternative(notification.message_html, "text/html")

            # Send email
            email.send(fail_silently=False)

            # Mark as sent
            notification.mark_as_sent()
            logger.info(f"Email sent successfully to {notification.recipient}")

            return True

        except Exception as e:
            logger.error(f"Failed to send email to {notification.recipient}: {str(e)}", exc_info=True)
            notification.mark_as_failed(str(e))
            return False


class NotificationService:
    """Main service for creating and sending notifications."""

    @staticmethod
    def send_notification(template_type, recipient_email, context, **kwargs):
        """
        Create and send a notification.

        Args:
            template_type: Type of notification template to use
            recipient_email: Email address of recipient
            context: Dict of template variables
            **kwargs: Additional notification fields

        Returns:
            Notification: Created notification instance
        """
        try:
            # Get template
            template = NotificationTemplate.objects.get(
                template_type=template_type,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Notification template not found: {template_type}")
            return None

        # Render template
        rendered = template.render(context)

        # Create notification - for SMS, store recipient in phone field
        notification_fields = {
            'template': template,
            'channel': template.channel,
            'subject': rendered['subject'],
            'message_text': rendered['body_text'],
            'message_html': rendered['body_html'] or '',
        }
        if template.channel == NotificationTemplate.SMS:
            notification_fields['phone'] = recipient_email
        else:
            notification_fields['email'] = recipient_email
        notification_fields.update(kwargs)
        notification = Notification.objects.create(**notification_fields)

        # Send notification based on channel
        if template.channel == NotificationTemplate.EMAIL:
            EmailService.send_email(notification)
        elif template.channel == NotificationTemplate.SMS:
            try:
                from django.conf import settings as django_settings
                sns_client = None
                try:
                    import boto3
                    sns_client = boto3.client('sns',
                        region_name=getattr(django_settings, 'AWS_SES_REGION_NAME', 'us-east-1'))
                except (ImportError, Exception):
                    pass

                phone_number = notification.phone or (notification.user.phone if notification.user and hasattr(notification.user, 'phone') else None)
                if sns_client and hasattr(django_settings, 'AWS_SNS_ENABLED') and django_settings.AWS_SNS_ENABLED:
                    if not phone_number:
                        logger.error(f"SMS notification {notification.id} has no phone number")
                        notification.mark_as_failed('No phone number available')
                    else:
                        sns_client.publish(
                            PhoneNumber=phone_number,
                            Message=rendered['body_text'],
                        )
                        notification.mark_as_sent()
                        logger.info(f"SMS sent to {phone_number}")
                else:
                    logger.info(f"SMS service not configured, notification stored for {recipient_email}")
                    notification.mark_as_delivered()
            except Exception as e:
                logger.error(f"SMS sending failed for {recipient_email}: {e}")
                notification.mark_as_failed(str(e))
        elif template.channel == NotificationTemplate.IN_APP:
            # In-app notifications are just stored, not sent
            notification.mark_as_delivered()

        return notification

    @staticmethod
    def send_invoice_notification(invoice, template_type):
        """
        Send invoice-related notification.

        Args:
            invoice: Invoice instance
            template_type: Type of notification template

        Returns:
            Notification: Created notification instance
        """
        context = {
            'invoice_number': invoice.invoice_number,
            'client_name': invoice.client.get_full_name(),
            'amount': f"${invoice.total:.2f}",
            'currency': invoice.currency,
            'due_date': invoice.due_date.strftime('%B %d, %Y'),
            'issue_date': invoice.issue_date.strftime('%B %d, %Y'),
            'company_name': settings.SITE_NAME,
        }

        return NotificationService.send_notification(
            template_type=template_type,
            recipient_email=invoice.client.email,
            context=context,
            related_invoice=invoice
        )

    @staticmethod
    def send_payment_receipt(payment):
        """
        Send payment receipt notification.

        Args:
            payment: Payment instance

        Returns:
            Notification: Created notification instance
        """
        invoice = payment.invoice
        context = {
            'payment_id': str(payment.id),
            'invoice_number': invoice.invoice_number if invoice else 'N/A',
            'client_name': invoice.client.get_full_name() if invoice and invoice.client else 'Customer',
            'amount': f"${payment.amount:.2f}",
            'currency': payment.currency,
            'payment_date': payment.payment_date.strftime('%B %d, %Y'),
            'payment_method': payment.get_payment_method_display(),
            'company_name': settings.SITE_NAME,
        }

        recipient = invoice.client.email if invoice and invoice.client else ''

        return NotificationService.send_notification(
            template_type=NotificationTemplate.PAYMENT_RECEIPT,
            recipient_email=recipient,
            context=context,
            related_payment=payment,
            related_invoice=invoice
        )

    @staticmethod
    def send_contract_notification(contract, template_type):
        """
        Send contract-related notification.

        Args:
            contract: Contract instance
            template_type: Type of notification template

        Returns:
            Notification: Created notification instance
        """
        context = {
            'contract_title': contract.title,
            'client_name': contract.client.get_full_name(),
            'contract_value': f"${contract.total_value:.2f}",
            'start_date': contract.start_date.strftime('%B %d, %Y'),
            'end_date': contract.end_date.strftime('%B %d, %Y') if contract.end_date else 'Ongoing',
            'company_name': settings.SITE_NAME,
        }

        return NotificationService.send_notification(
            template_type=template_type,
            recipient_email=contract.client.email,
            context=context,
            related_contract=contract
        )

    @staticmethod
    def send_client_welcome(client):
        """
        Send welcome email to new client.

        Args:
            client: Client instance

        Returns:
            Notification: Created notification instance
        """
        context = {
            'client_name': client.get_full_name(),
            'company_name': settings.SITE_NAME,
        }

        return NotificationService.send_notification(
            template_type=NotificationTemplate.CLIENT_WELCOME,
            recipient_email=client.email,
            context=context
        )
