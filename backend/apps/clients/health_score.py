"""
Client Health Score Calculator
Scores clients from 0-100 based on payment history, engagement, and revenue.
"""
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone


class ClientHealthCalculator:
    """Calculates a health score for a client based on multiple factors."""

    WEIGHTS = {
        'payment_reliability': 0.30,   # 30% - Do they pay on time?
        'revenue_value': 0.25,         # 25% - How much do they spend?
        'engagement': 0.20,            # 20% - How active are they?
        'contract_health': 0.15,       # 15% - Active contracts?
        'recency': 0.10,              # 10% - Recent activity?
    }

    def __init__(self, client):
        self.client = client
        self.now = timezone.now()

    def calculate(self):
        """Calculate overall health score (0-100)."""
        scores = {
            'payment_reliability': self._payment_reliability_score(),
            'revenue_value': self._revenue_value_score(),
            'engagement': self._engagement_score(),
            'contract_health': self._contract_health_score(),
            'recency': self._recency_score(),
        }

        total = sum(score * self.WEIGHTS[key] for key, score in scores.items())

        return {
            'overall_score': round(total, 1),
            'grade': self._get_grade(total),
            'breakdown': {k: round(v, 1) for k, v in scores.items()},
            'recommendations': self._get_recommendations(scores),
        }

    def _payment_reliability_score(self):
        """Score based on payment success rate and timeliness."""
        from apps.payments.models import Payment

        payments = Payment.objects.filter(invoice__client=self.client)
        total = payments.count()
        if total == 0:
            return 50  # Neutral score for new clients

        succeeded = payments.filter(status='succeeded').count()
        failed = payments.filter(status='failed').count()

        success_rate = succeeded / total * 100 if total > 0 else 0

        # Check for overdue invoices
        from apps.invoicing.models import Invoice
        overdue = Invoice.objects.filter(client=self.client, status='overdue').count()

        score = success_rate
        score -= overdue * 10  # Penalize per overdue invoice

        return max(0, min(100, score))

    def _revenue_value_score(self):
        """Score based on total revenue relative to average."""
        from apps.payments.models import Payment

        client_revenue = Payment.objects.filter(
            invoice__client=self.client, status='succeeded'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        avg_revenue = Payment.objects.filter(
            status='succeeded'
        ).values('invoice__client').annotate(
            total=Sum('amount')
        ).aggregate(avg=Avg('total'))['avg'] or Decimal('1')

        if avg_revenue > 0:
            ratio = float(client_revenue / avg_revenue)
            score = min(100, ratio * 50)  # 2x average = 100
        else:
            score = 50

        return max(0, score)

    def _engagement_score(self):
        """Score based on number of interactions and contracts."""
        from apps.contracts.models import Contract
        from apps.invoicing.models import Invoice

        # Count recent interactions
        three_months_ago = self.now - timedelta(days=90)

        recent_invoices = Invoice.objects.filter(
            client=self.client, created_at__gte=three_months_ago
        ).count()
        recent_contracts = Contract.objects.filter(
            client=self.client, created_at__gte=three_months_ago
        ).count()

        # More interactions = higher score
        interaction_score = min(100, (recent_invoices * 15) + (recent_contracts * 25))

        return interaction_score

    def _contract_health_score(self):
        """Score based on active contracts and their status."""
        from apps.contracts.models import Contract

        contracts = Contract.objects.filter(client=self.client)
        total = contracts.count()
        if total == 0:
            return 30  # Low score if no contracts

        active = contracts.filter(status='active').count()
        completed = contracts.filter(status='completed').count()
        cancelled = contracts.filter(status='cancelled').count()

        score = 50  # Base
        score += active * 15  # Reward active contracts
        score += completed * 5  # Small boost for completed
        score -= cancelled * 10  # Penalize cancellations

        return max(0, min(100, score))

    def _recency_score(self):
        """Score based on how recently the client was active."""
        from apps.payments.models import Payment
        from apps.invoicing.models import Invoice

        last_payment = Payment.objects.filter(
            invoice__client=self.client, status='succeeded'
        ).order_by('-created_at').values_list('created_at', flat=True).first()

        last_invoice = Invoice.objects.filter(
            client=self.client
        ).order_by('-created_at').values_list('created_at', flat=True).first()

        last_activity = max(filter(None, [last_payment, last_invoice]), default=None)

        if not last_activity:
            return 20  # Low score if no activity

        days_since = (self.now - last_activity).days

        if days_since <= 7:
            return 100
        elif days_since <= 30:
            return 80
        elif days_since <= 90:
            return 60
        elif days_since <= 180:
            return 40
        else:
            return 20

    @staticmethod
    def _get_grade(score):
        if score >= 90: return 'A+'
        elif score >= 80: return 'A'
        elif score >= 70: return 'B'
        elif score >= 60: return 'C'
        elif score >= 50: return 'D'
        else: return 'F'

    @staticmethod
    def _get_recommendations(scores):
        recs = []
        if scores['payment_reliability'] < 60:
            recs.append('Set up automated payment reminders for this client.')
        if scores['engagement'] < 40:
            recs.append('Schedule a check-in call to re-engage this client.')
        if scores['contract_health'] < 40:
            recs.append('Propose a new contract to strengthen the relationship.')
        if scores['recency'] < 40:
            recs.append('This client has been inactive. Send a follow-up email.')
        if scores['revenue_value'] < 30:
            recs.append('Consider upselling additional services to this client.')
        return recs
