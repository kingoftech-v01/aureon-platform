"""
Tests for analytics Celery tasks.

Tests cover daily analytics generation, weekly reports, and revenue metric calculation.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.utils import timezone

from apps.analytics.tasks import (
    generate_daily_analytics,
    generate_weekly_reports,
    calculate_revenue_metrics,
)


@pytest.mark.django_db
class TestGenerateDailyAnalytics:
    """Tests for generate_daily_analytics task."""

    @patch('apps.analytics.tasks.ClientMetricsCalculator')
    @patch('apps.analytics.tasks.RevenueMetricsCalculator')
    @patch('apps.analytics.tasks.Client')
    def test_generates_daily_analytics_successfully(
        self, mock_client_model, mock_revenue_calc, mock_client_calc
    ):
        """Test that daily analytics generates revenue and client metrics."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('50000.00')
        mock_revenue_calc.calculate_month_metrics.return_value = mock_metric

        mock_client_qs = MagicMock()
        mock_client_qs.__iter__ = MagicMock(return_value=iter([]))
        mock_client_model.objects.filter.return_value = mock_client_qs

        result = generate_daily_analytics()

        assert result['status'] == 'success'
        assert result['revenue'] == '50000.00'
        mock_revenue_calc.calculate_month_metrics.assert_called_once()

    @patch('apps.analytics.tasks.ClientMetricsCalculator')
    @patch('apps.analytics.tasks.RevenueMetricsCalculator')
    @patch('apps.analytics.tasks.Client')
    def test_updates_active_client_metrics(
        self, mock_client_model, mock_revenue_calc, mock_client_calc
    ):
        """Test that metrics are calculated for each active client."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('10000.00')
        mock_revenue_calc.calculate_month_metrics.return_value = mock_metric

        mock_client_1 = MagicMock()
        mock_client_1.id = 1
        mock_client_2 = MagicMock()
        mock_client_2.id = 2
        mock_client_qs = MagicMock()
        mock_client_qs.__iter__ = MagicMock(return_value=iter([mock_client_1, mock_client_2]))
        mock_client_model.objects.filter.return_value = mock_client_qs

        result = generate_daily_analytics()

        assert result['clients_updated'] == 2
        assert mock_client_calc.calculate_client_metrics.call_count == 2

    @patch('apps.analytics.tasks.ClientMetricsCalculator')
    @patch('apps.analytics.tasks.RevenueMetricsCalculator')
    @patch('apps.analytics.tasks.Client')
    def test_handles_client_metric_failure_gracefully(
        self, mock_client_model, mock_revenue_calc, mock_client_calc
    ):
        """Test that a failure in one client's metrics does not stop the rest."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('5000.00')
        mock_revenue_calc.calculate_month_metrics.return_value = mock_metric

        mock_client_1 = MagicMock()
        mock_client_1.id = 1
        mock_client_2 = MagicMock()
        mock_client_2.id = 2
        mock_client_qs = MagicMock()
        mock_client_qs.__iter__ = MagicMock(return_value=iter([mock_client_1, mock_client_2]))
        mock_client_model.objects.filter.return_value = mock_client_qs

        # First client fails, second succeeds
        mock_client_calc.calculate_client_metrics.side_effect = [
            Exception("Calculation failed"),
            MagicMock(),
        ]

        result = generate_daily_analytics()

        assert result['status'] == 'success'
        assert result['clients_updated'] == 1

    @patch('apps.analytics.tasks.ClientMetricsCalculator')
    @patch('apps.analytics.tasks.RevenueMetricsCalculator')
    @patch('apps.analytics.tasks.Client')
    def test_returns_correct_date(
        self, mock_client_model, mock_revenue_calc, mock_client_calc
    ):
        """Test that the result includes today's date."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('0.00')
        mock_revenue_calc.calculate_month_metrics.return_value = mock_metric

        mock_client_qs = MagicMock()
        mock_client_qs.__iter__ = MagicMock(return_value=iter([]))
        mock_client_model.objects.filter.return_value = mock_client_qs

        result = generate_daily_analytics()

        assert result['date'] == date.today().isoformat()


@pytest.mark.django_db
class TestGenerateWeeklyReports:
    """Tests for generate_weekly_reports task."""

    @patch('apps.analytics.tasks.DashboardDataService')
    @patch('apps.analytics.tasks.RevenueMetricsCalculator')
    def test_generates_weekly_report_successfully(
        self, mock_revenue_calc, mock_dashboard_svc
    ):
        """Test that weekly reports calculate metrics for 4 weeks."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('25000.00')
        mock_revenue_calc.calculate_month_metrics.return_value = mock_metric

        mock_dashboard_svc.get_dashboard_summary.return_value = {
            'active_clients': 15,
        }

        result = generate_weekly_reports()

        assert result['status'] == 'success'
        assert result['active_clients'] == 15
        # Should calculate metrics for up to 4 weeks
        assert mock_revenue_calc.calculate_month_metrics.call_count <= 4

    @patch('apps.analytics.tasks.DashboardDataService')
    @patch('apps.analytics.tasks.RevenueMetricsCalculator')
    def test_calculates_total_revenue_from_all_weeks(
        self, mock_revenue_calc, mock_dashboard_svc
    ):
        """Test that total revenue sums all months' revenue."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('10000.00')
        mock_revenue_calc.calculate_month_metrics.return_value = mock_metric

        mock_dashboard_svc.get_dashboard_summary.return_value = {
            'active_clients': 5,
        }

        result = generate_weekly_reports()

        assert result['status'] == 'success'
        # total_revenue should be sum of all metrics
        assert Decimal(result['total_revenue']) > Decimal('0.00')

    @patch('apps.analytics.tasks.DashboardDataService')
    @patch('apps.analytics.tasks.RevenueMetricsCalculator')
    def test_includes_week_number(
        self, mock_revenue_calc, mock_dashboard_svc
    ):
        """Test that the result includes the current ISO week number."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('0.00')
        mock_revenue_calc.calculate_month_metrics.return_value = mock_metric

        mock_dashboard_svc.get_dashboard_summary.return_value = {
            'active_clients': 0,
        }

        result = generate_weekly_reports()

        assert 'week' in result
        assert isinstance(result['week'], int)


@pytest.mark.django_db
class TestCalculateRevenueMetrics:
    """Tests for calculate_revenue_metrics task."""

    @patch('apps.analytics.tasks.RevenueMetricsCalculator')
    def test_calculates_current_month(self, mock_calc):
        """Test that current month revenue metrics are calculated."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('30000.00')
        mock_calc.calculate_month_metrics.return_value = mock_metric

        result = calculate_revenue_metrics()

        assert result['status'] == 'success'
        assert result['revenue'] == '30000.00'
        mock_calc.calculate_month_metrics.assert_called()

    @patch('apps.analytics.tasks.RevenueMetricsCalculator')
    def test_recalculates_previous_month_in_first_week(self, mock_calc):
        """Test that the previous month is also recalculated in the first week."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('20000.00')
        mock_calc.calculate_month_metrics.return_value = mock_metric

        # Simulate being in the first week of the month
        with patch('apps.analytics.tasks.timezone') as mock_tz:
            now = timezone.now().replace(day=3)
            mock_tz.now.return_value = now
            mock_tz.timedelta = timedelta

            result = calculate_revenue_metrics()

            assert result['status'] == 'success'
            # Should be called twice: current month + previous month
            assert mock_calc.calculate_month_metrics.call_count == 2

    @patch('apps.analytics.tasks.RevenueMetricsCalculator')
    def test_does_not_recalculate_previous_month_after_first_week(self, mock_calc):
        """Test that previous month is not recalculated after the first week."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('15000.00')
        mock_calc.calculate_month_metrics.return_value = mock_metric

        with patch('apps.analytics.tasks.timezone') as mock_tz:
            now = timezone.now().replace(day=15)
            mock_tz.now.return_value = now
            mock_tz.timedelta = timedelta

            result = calculate_revenue_metrics()

            assert result['status'] == 'success'
            # Only called once for current month
            assert mock_calc.calculate_month_metrics.call_count == 1

    @patch('apps.analytics.tasks.RevenueMetricsCalculator')
    def test_handles_january_previous_month(self, mock_calc):
        """Test that previous month calculation in January uses December of prior year."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('10000.00')
        mock_calc.calculate_month_metrics.return_value = mock_metric

        with patch('apps.analytics.tasks.timezone') as mock_tz:
            # January 3rd
            import datetime
            now = datetime.datetime(2025, 1, 3, tzinfo=datetime.timezone.utc)
            mock_tz.now.return_value = now
            mock_tz.timedelta = timedelta

            result = calculate_revenue_metrics()

            assert result['status'] == 'success'
            # Should calculate Jan 2025 and Dec 2024
            calls = mock_calc.calculate_month_metrics.call_args_list
            assert len(calls) == 2
            # First call: current month (Jan 2025)
            assert calls[0][0] == (2025, 1)
            # Second call: previous month (Dec 2024)
            assert calls[1][0] == (2024, 12)
