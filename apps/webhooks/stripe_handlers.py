"""
Stripe webhook event handlers.

Processes Stripe webhook events and updates related models.
"""

import logging
from django.db import transaction
from apps.payments.models import Payment
from apps.invoicing.models import Invoice
from django.utils import timezone

logger = logging.getLogger(__name__)


class StripeWebhookHandler:
    """Handler for Stripe webhook events."""

    def __init__(self, event):
        """
        Initialize handler with Stripe event.

        Args:
            event: Stripe event object
        """
        self.event = event
        self.event_type = event['type']
        self.data = event['data']['object']

    def handle(self):
        """
        Route event to appropriate handler method.

        Returns:
            dict: Processing result
        """
        handler_map = {
            'payment_intent.succeeded': self.handle_payment_intent_succeeded,
            'payment_intent.payment_failed': self.handle_payment_intent_failed,
            'payment_intent.processing': self.handle_payment_intent_processing,
            'payment_intent.canceled': self.handle_payment_intent_canceled,
            'charge.succeeded': self.handle_charge_succeeded,
            'charge.failed': self.handle_charge_failed,
            'charge.refunded': self.handle_charge_refunded,
            'invoice.payment_succeeded': self.handle_invoice_payment_succeeded,
            'invoice.payment_failed': self.handle_invoice_payment_failed,
            'customer.subscription.created': self.handle_subscription_created,
            'customer.subscription.updated': self.handle_subscription_updated,
            'customer.subscription.deleted': self.handle_subscription_deleted,
        }

        handler = handler_map.get(self.event_type)

        if handler:
            try:
                result = handler()
                logger.info(f"Successfully handled {self.event_type}: {self.event['id']}")
                return result
            except Exception as e:
                logger.error(f"Error handling {self.event_type}: {str(e)}", exc_info=True)
                raise
        else:
            logger.warning(f"No handler for event type: {self.event_type}")
            return {'status': 'ignored', 'message': f'No handler for {self.event_type}'}

    @transaction.atomic
    def handle_payment_intent_succeeded(self):
        """Handle successful payment intent."""
        payment_intent_id = self.data['id']
        amount = self.data['amount'] / 100  # Convert from cents
        currency = self.data['currency'].upper()

        # Find or create payment record
        payment, created = Payment.objects.get_or_create(
            stripe_payment_intent_id=payment_intent_id,
            defaults={
                'amount': amount,
                'currency': currency,
                'status': Payment.SUCCESS,
                'payment_method': Payment.CARD,  # Default to card
            }
        )

        if not created:
            payment.status = Payment.SUCCESS
            payment.save(update_fields=['status', 'updated_at'])

        # Update related invoice if exists
        if payment.invoice:
            invoice = payment.invoice
            invoice.mark_as_paid()
            logger.info(f"Marked invoice {invoice.invoice_number} as paid")

        return {
            'status': 'processed',
            'payment_id': str(payment.id),
            'amount': amount,
            'invoice_updated': payment.invoice is not None
        }

    @transaction.atomic
    def handle_payment_intent_failed(self):
        """Handle failed payment intent."""
        payment_intent_id = self.data['id']
        error_message = self.data.get('last_payment_error', {}).get('message', 'Payment failed')

        # Update payment record
        payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()

        if payment:
            payment.status = Payment.FAILED
            payment.failure_reason = error_message
            payment.save(update_fields=['status', 'failure_reason', 'updated_at'])

            logger.warning(f"Payment {payment.id} failed: {error_message}")

            return {
                'status': 'processed',
                'payment_id': str(payment.id),
                'error': error_message
            }

        return {'status': 'ignored', 'message': 'Payment record not found'}

    @transaction.atomic
    def handle_payment_intent_processing(self):
        """Handle payment intent in processing state."""
        payment_intent_id = self.data['id']

        payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()

        if payment:
            payment.status = Payment.PROCESSING
            payment.save(update_fields=['status', 'updated_at'])

            return {
                'status': 'processed',
                'payment_id': str(payment.id)
            }

        return {'status': 'ignored', 'message': 'Payment record not found'}

    @transaction.atomic
    def handle_payment_intent_canceled(self):
        """Handle canceled payment intent."""
        payment_intent_id = self.data['id']

        payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()

        if payment:
            payment.status = Payment.CANCELLED
            payment.save(update_fields=['status', 'updated_at'])

            return {
                'status': 'processed',
                'payment_id': str(payment.id)
            }

        return {'status': 'ignored', 'message': 'Payment record not found'}

    @transaction.atomic
    def handle_charge_succeeded(self):
        """Handle successful charge."""
        charge_id = self.data['id']
        payment_intent_id = self.data.get('payment_intent')

        if payment_intent_id:
            payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()

            if payment:
                payment.stripe_charge_id = charge_id
                payment.status = Payment.SUCCESS
                payment.save(update_fields=['stripe_charge_id', 'status', 'updated_at'])

                return {
                    'status': 'processed',
                    'payment_id': str(payment.id)
                }

        return {'status': 'ignored', 'message': 'Payment not found'}

    @transaction.atomic
    def handle_charge_failed(self):
        """Handle failed charge."""
        payment_intent_id = self.data.get('payment_intent')
        error_message = self.data.get('failure_message', 'Charge failed')

        if payment_intent_id:
            payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()

            if payment:
                payment.status = Payment.FAILED
                payment.failure_reason = error_message
                payment.save(update_fields=['status', 'failure_reason', 'updated_at'])

                return {
                    'status': 'processed',
                    'payment_id': str(payment.id)
                }

        return {'status': 'ignored', 'message': 'Payment not found'}

    @transaction.atomic
    def handle_charge_refunded(self):
        """Handle charge refund."""
        charge_id = self.data['id']
        refund_amount = self.data['amount_refunded'] / 100

        payment = Payment.objects.filter(stripe_charge_id=charge_id).first()

        if payment:
            payment.status = Payment.REFUNDED
            payment.refunded_amount = refund_amount
            payment.save(update_fields=['status', 'refunded_amount', 'updated_at'])

            logger.info(f"Payment {payment.id} refunded: ${refund_amount}")

            return {
                'status': 'processed',
                'payment_id': str(payment.id),
                'refund_amount': refund_amount
            }

        return {'status': 'ignored', 'message': 'Payment not found'}

    @transaction.atomic
    def handle_invoice_payment_succeeded(self):
        """Handle Stripe invoice payment succeeded (for subscriptions)."""
        # This handles Stripe's invoice object, not our Invoice model
        invoice_id = self.data['id']
        payment_intent_id = self.data.get('payment_intent')

        logger.info(f"Stripe invoice {invoice_id} paid via payment intent {payment_intent_id}")

        return {
            'status': 'processed',
            'message': 'Stripe invoice payment recorded'
        }

    @transaction.atomic
    def handle_invoice_payment_failed(self):
        """Handle Stripe invoice payment failed."""
        invoice_id = self.data['id']

        logger.warning(f"Stripe invoice {invoice_id} payment failed")

        return {
            'status': 'processed',
            'message': 'Stripe invoice payment failure recorded'
        }

    @transaction.atomic
    def handle_subscription_created(self):
        """Handle new subscription creation."""
        from apps.subscriptions.models import Subscription

        subscription_id = self.data['id']
        customer_id = self.data['customer']
        status = self.data['status']

        logger.info(f"Subscription {subscription_id} created for customer {customer_id} with status {status}")

        # Update local subscription record
        try:
            subscription = Subscription.objects.filter(
                stripe_subscription_id=subscription_id
            ).first()
            if subscription:
                subscription.status = status
                subscription.save(update_fields=['status', 'updated_at'])
                logger.info(f"Updated local subscription {subscription.id} to status {status}")
        except Exception as e:
            logger.warning(f"Could not update local subscription for {subscription_id}: {e}")

        return {
            'status': 'processed',
            'subscription_id': subscription_id,
            'subscription_status': status
        }

    @transaction.atomic
    def handle_subscription_updated(self):
        """Handle subscription update."""
        from apps.subscriptions.models import Subscription

        subscription_id = self.data['id']
        status = self.data['status']
        cancel_at_period_end = self.data.get('cancel_at_period_end', False)

        logger.info(f"Subscription {subscription_id} updated to status {status}")

        try:
            subscription = Subscription.objects.filter(
                stripe_subscription_id=subscription_id
            ).first()
            if subscription:
                subscription.status = status
                subscription.cancel_at_period_end = cancel_at_period_end
                if self.data.get('current_period_end'):
                    from datetime import datetime
                    subscription.current_period_end = datetime.fromtimestamp(
                        self.data['current_period_end'],
                        tz=timezone.utc
                    )
                subscription.save()
                logger.info(f"Updated local subscription {subscription.id}")
        except Exception as e:
            logger.warning(f"Could not update local subscription for {subscription_id}: {e}")

        return {
            'status': 'processed',
            'subscription_id': subscription_id,
            'subscription_status': status,
            'canceling': cancel_at_period_end
        }

    @transaction.atomic
    def handle_subscription_deleted(self):
        """Handle subscription cancellation."""
        from apps.subscriptions.models import Subscription

        subscription_id = self.data['id']

        logger.info(f"Subscription {subscription_id} canceled")

        try:
            subscription = Subscription.objects.filter(
                stripe_subscription_id=subscription_id
            ).first()
            if subscription:
                subscription.status = 'canceled'
                subscription.canceled_at = timezone.now()
                subscription.save(update_fields=['status', 'canceled_at', 'updated_at'])
                logger.info(f"Canceled local subscription {subscription.id}")
        except Exception as e:
            logger.warning(f"Could not cancel local subscription for {subscription_id}: {e}")

        return {
            'status': 'processed',
            'subscription_id': subscription_id,
            'message': 'Subscription canceled'
        }
