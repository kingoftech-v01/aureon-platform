"""
AI-Powered Analytics Insights
Generates intelligent insights from financial data patterns.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone


class InsightsEngine:
    """Generates AI-powered financial insights from business data."""

    def __init__(self, user=None):
        self.user = user
        self.now = timezone.now()
        self.month_ago = self.now - timedelta(days=30)
        self.two_months_ago = self.now - timedelta(days=60)

    def generate_all_insights(self):
        """Generate all categories of insights."""
        insights = []
        insights.extend(self._revenue_insights())
        insights.extend(self._invoice_insights())
        insights.extend(self._client_insights())
        insights.extend(self._contract_insights())
        insights.extend(self._payment_insights())
        # Sort by priority (high first)
        insights.sort(key=lambda x: {'urgent': 0, 'warning': 1, 'positive': 2, 'info': 3}.get(x['severity'], 4))
        return insights[:10]  # Top 10 insights

    def _revenue_insights(self):
        from apps.payments.models import Payment
        insights = []

        current_revenue = Payment.objects.filter(
            status='succeeded', created_at__gte=self.month_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        previous_revenue = Payment.objects.filter(
            status='succeeded', created_at__gte=self.two_months_ago, created_at__lt=self.month_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        if previous_revenue > 0:
            growth_rate = ((current_revenue - previous_revenue) / previous_revenue * 100)
            if growth_rate > 10:
                insights.append({
                    'type': 'revenue_growth',
                    'severity': 'positive',
                    'title': 'Revenue Growing Strong',
                    'description': f'Revenue increased {growth_rate:.1f}% this month (${current_revenue:,.2f} vs ${previous_revenue:,.2f} last month).',
                    'metric': float(growth_rate),
                    'action': 'Keep up the momentum! Consider scaling your outreach.',
                })
            elif growth_rate < -10:
                insights.append({
                    'type': 'revenue_decline',
                    'severity': 'warning',
                    'title': 'Revenue Decline Detected',
                    'description': f'Revenue decreased {abs(growth_rate):.1f}% this month. Review your pipeline.',
                    'metric': float(growth_rate),
                    'action': 'Follow up on pending invoices and reconnect with dormant clients.',
                })
        elif current_revenue > 0:
            insights.append({
                'type': 'first_revenue',
                'severity': 'positive',
                'title': 'First Revenue Recorded!',
                'description': f'You earned ${current_revenue:,.2f} this month. Great start!',
                'metric': float(current_revenue),
                'action': 'Create more invoices to build consistent revenue.',
            })

        return insights

    def _invoice_insights(self):
        from apps.invoicing.models import Invoice
        insights = []

        overdue = Invoice.objects.filter(status='overdue')
        overdue_count = overdue.count()
        overdue_total = overdue.aggregate(total=Sum('total'))['total'] or Decimal('0')

        if overdue_count > 0:
            insights.append({
                'type': 'overdue_invoices',
                'severity': 'urgent' if overdue_count >= 5 else 'warning',
                'title': f'{overdue_count} Overdue Invoice{"s" if overdue_count > 1 else ""}',
                'description': f'${overdue_total:,.2f} in overdue payments need attention.',
                'metric': overdue_count,
                'action': 'Send payment reminders to overdue clients immediately.',
            })

        # Average days to payment
        paid = Invoice.objects.filter(status='paid', paid_at__isnull=False, sent_at__isnull=False)
        if paid.exists():
            avg_days = paid.annotate(
                days_to_pay=F('paid_at') - F('sent_at')
            ).aggregate(avg=Avg('days_to_pay'))['avg']
            if avg_days and avg_days.days > 30:
                insights.append({
                    'type': 'slow_payments',
                    'severity': 'warning',
                    'title': 'Slow Payment Collection',
                    'description': f'Average payment takes {avg_days.days} days. Consider incentives for early payment.',
                    'metric': avg_days.days,
                    'action': 'Offer early payment discounts or switch to upfront billing.',
                })

        # Draft invoices not sent
        drafts = Invoice.objects.filter(status='draft').count()
        if drafts >= 3:
            insights.append({
                'type': 'draft_invoices',
                'severity': 'info',
                'title': f'{drafts} Draft Invoices Pending',
                'description': 'You have unsent invoices. Review and send them to improve cash flow.',
                'metric': drafts,
                'action': 'Review and send your draft invoices.',
            })

        return insights

    def _client_insights(self):
        from apps.clients.models import Client
        insights = []

        total = Client.objects.filter(is_active=True).count()
        active = Client.objects.filter(lifecycle_stage='active').count()

        if total > 0:
            retention_rate = (active / total * 100)
            if retention_rate >= 80:
                insights.append({
                    'type': 'client_retention',
                    'severity': 'positive',
                    'title': 'Excellent Client Retention',
                    'description': f'{retention_rate:.0f}% of your clients are active. Strong engagement!',
                    'metric': float(retention_rate),
                    'action': 'Leverage referrals from satisfied clients.',
                })
            elif retention_rate < 50:
                insights.append({
                    'type': 'client_churn',
                    'severity': 'warning',
                    'title': 'High Client Churn Risk',
                    'description': f'Only {retention_rate:.0f}% of clients are active. Re-engage dormant clients.',
                    'metric': float(retention_rate),
                    'action': 'Schedule check-ins with inactive clients.',
                })

        new_this_month = Client.objects.filter(created_at__gte=self.month_ago).count()
        if new_this_month > 0:
            insights.append({
                'type': 'new_clients',
                'severity': 'positive',
                'title': f'{new_this_month} New Client{"s" if new_this_month > 1 else ""} This Month',
                'description': f'Your client base is growing with {new_this_month} new additions.',
                'metric': new_this_month,
                'action': 'Send welcome emails and schedule onboarding calls.',
            })

        return insights

    def _contract_insights(self):
        from apps.contracts.models import Contract
        insights = []

        expiring_soon = Contract.objects.filter(
            status='active',
            end_date__lte=self.now + timedelta(days=30),
            end_date__gte=self.now
        ).count()

        if expiring_soon > 0:
            insights.append({
                'type': 'expiring_contracts',
                'severity': 'warning',
                'title': f'{expiring_soon} Contract{"s" if expiring_soon > 1 else ""} Expiring Soon',
                'description': f'{expiring_soon} contract(s) expire within 30 days. Start renewal discussions.',
                'metric': expiring_soon,
                'action': 'Contact clients for contract renewals.',
            })

        pending = Contract.objects.filter(status='pending').count()
        if pending > 0:
            insights.append({
                'type': 'pending_signatures',
                'severity': 'info',
                'title': f'{pending} Contract{"s" if pending > 1 else ""} Awaiting Signature',
                'description': 'Follow up to get pending contracts signed.',
                'metric': pending,
                'action': 'Send signature reminders to clients.',
            })

        return insights

    def _payment_insights(self):
        from apps.payments.models import Payment
        insights = []

        failed = Payment.objects.filter(
            status='failed', created_at__gte=self.month_ago
        ).count()

        if failed > 0:
            insights.append({
                'type': 'failed_payments',
                'severity': 'urgent' if failed >= 3 else 'warning',
                'title': f'{failed} Failed Payment{"s" if failed > 1 else ""} This Month',
                'description': 'Failed payments need immediate attention.',
                'metric': failed,
                'action': 'Update payment methods and retry failed charges.',
            })

        return insights
