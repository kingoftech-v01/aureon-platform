"""
Revenue Forecasting
Simple linear regression-based revenue forecasting.
"""
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class RevenueForecastView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        months_ahead = int(request.query_params.get('months', 6))
        months_ahead = min(months_ahead, 12)  # Cap at 12

        from apps.payments.models import Payment
        from apps.invoicing.models import Invoice
        from apps.contracts.models import Contract

        # Get historical monthly revenue (last 12 months)
        today = timezone.now().date()
        history = []
        for i in range(12, 0, -1):
            month_start = date(today.year, today.month, 1) - timedelta(days=i * 30)
            month_end = month_start + timedelta(days=30)
            revenue = Payment.objects.filter(
                status='succeeded',
                payment_date__gte=month_start,
                payment_date__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            history.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': float(revenue),
            })

        # Simple linear regression for forecasting
        revenues = [h['revenue'] for h in history]
        n = len(revenues)
        if n > 0 and sum(revenues) > 0:
            x_mean = (n - 1) / 2
            y_mean = sum(revenues) / n

            numerator = sum((i - x_mean) * (revenues[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))

            slope = numerator / denominator if denominator != 0 else 0
            intercept = y_mean - slope * x_mean

            forecast = []
            for i in range(months_ahead):
                projected = max(0, intercept + slope * (n + i))
                month_date = date(today.year, today.month, 1) + timedelta(days=(i + 1) * 30)
                forecast.append({
                    'month': month_date.strftime('%Y-%m'),
                    'projected_revenue': round(projected, 2),
                    'confidence': max(0.5, 1 - (i * 0.05)),  # Decreasing confidence
                })
        else:
            forecast = []

        # Recurring revenue from active contracts
        recurring_monthly = Contract.objects.filter(
            status='active',
            contract_type='retainer'
        ).aggregate(total=Sum('value'))['total'] or Decimal('0')

        # Pending invoices
        pending_amount = Invoice.objects.filter(
            status__in=['sent', 'overdue']
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')

        return Response({
            'history': history,
            'forecast': forecast,
            'recurring_monthly_revenue': float(recurring_monthly),
            'pending_receivables': float(pending_amount),
            'trend': 'up' if slope > 0 else 'down' if slope < 0 else 'flat' if n > 0 and sum(revenues) > 0 else 'insufficient_data',
            'average_monthly_revenue': round(y_mean, 2) if n > 0 and sum(revenues) > 0 else 0,
        })
