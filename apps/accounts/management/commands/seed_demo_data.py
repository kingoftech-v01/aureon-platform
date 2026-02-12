"""
Management command to seed the database with demo data.

Usage:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --clear  # Clear existing data first
    python manage.py seed_demo_data --users 5 --clients 20  # Customize counts
"""

import random
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker

from apps.clients.models import Client, ClientNote
from apps.contracts.models import Contract, ContractMilestone
from apps.invoicing.models import Invoice, InvoiceItem
from apps.payments.models import Payment, PaymentMethod
from apps.analytics.models import RevenueMetric, ClientMetric, ActivityLog
from apps.notifications.models import NotificationTemplate, Notification

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Seeds the database with demo data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Number of users to create (default: 5)',
        )
        parser.add_argument(
            '--clients',
            type=int,
            default=20,
            help='Number of clients to create (default: 20)',
        )
        parser.add_argument(
            '--contracts',
            type=int,
            default=15,
            help='Number of contracts to create (default: 15)',
        )
        parser.add_argument(
            '--invoices',
            type=int,
            default=30,
            help='Number of invoices to create (default: 30)',
        )

    def handle(self, *args, **options):
        """Execute the seeding process."""

        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()
            self.stdout.write(self.style.SUCCESS('✓ Data cleared'))

        self.stdout.write(self.style.SUCCESS('\n===== Starting Data Seeding =====\n'))

        # Seed users
        users = self.seed_users(options['users'])
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(users)} users'))

        # Seed clients
        clients = self.seed_clients(options['clients'], users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(clients)} clients'))

        # Seed contracts
        contracts = self.seed_contracts(options['contracts'], clients)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(contracts)} contracts'))

        # Seed invoices
        invoices = self.seed_invoices(options['invoices'], clients, contracts)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(invoices)} invoices'))

        # Seed payments
        payments = self.seed_payments(invoices)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(payments)} payments'))

        # Seed payment methods
        payment_methods = self.seed_payment_methods(clients)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(payment_methods)} payment methods'))

        # Seed client metrics
        self.seed_client_metrics(clients)
        self.stdout.write(self.style.SUCCESS(f'✓ Calculated client metrics'))

        # Seed revenue metrics
        self.seed_revenue_metrics()
        self.stdout.write(self.style.SUCCESS(f'✓ Calculated revenue metrics'))

        # Seed activity logs
        activity_logs = self.seed_activity_logs(users, clients, invoices)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(activity_logs)} activity logs'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n===== Seeding Complete ====='))
        self.stdout.write(self.style.SUCCESS(f'Total Users: {len(users)}'))
        self.stdout.write(self.style.SUCCESS(f'Total Clients: {len(clients)}'))
        self.stdout.write(self.style.SUCCESS(f'Total Contracts: {len(contracts)}'))
        self.stdout.write(self.style.SUCCESS(f'Total Invoices: {len(invoices)}'))
        self.stdout.write(self.style.SUCCESS(f'Total Payments: {len(payments)}'))
        self.stdout.write(self.style.SUCCESS(f'Total Activity Logs: {len(activity_logs)}\n'))

    def clear_data(self):
        """Clear existing demo data."""
        ActivityLog.objects.all().delete()
        ClientMetric.objects.all().delete()
        RevenueMetric.objects.all().delete()
        Payment.objects.all().delete()
        PaymentMethod.objects.all().delete()
        InvoiceItem.objects.all().delete()
        Invoice.objects.all().delete()
        ContractMilestone.objects.all().delete()
        Contract.objects.all().delete()
        ClientNote.objects.all().delete()
        Client.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def seed_users(self, count):
        """Create demo users."""
        users = []

        # Create admin user
        admin, created = User.objects.get_or_create(
            email='admin@aureon.local',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
        users.append(admin)

        # Create regular users
        for i in range(count - 1):
            email = f'user{i+1}@aureon.local'
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'is_staff': random.choice([True, False]),
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)

        return users

    def seed_clients(self, count, users):
        """Create demo clients."""
        clients = []

        lifecycle_stages = [Client.LEAD, Client.PROSPECT, Client.ACTIVE, Client.INACTIVE]
        client_types = [Client.INDIVIDUAL, Client.COMPANY]

        for i in range(count):
            client_type = random.choice(client_types)

            client_data = {
                'client_type': client_type,
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'email': fake.email(),
                'phone': fake.phone_number()[:20],
                'lifecycle_stage': random.choice(lifecycle_stages),
                'owner': random.choice(users),
                'address': fake.street_address(),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'zip_code': fake.zipcode(),
                'country': 'US',
                'tags': random.sample(['vip', 'enterprise', 'startup', 'agency', 'freelancer'], k=random.randint(1, 3)),
            }

            if client_type == Client.COMPANY:
                client_data['company_name'] = fake.company()

            client = Client.objects.create(**client_data)
            clients.append(client)

            # Add notes to some clients
            if random.random() > 0.5:
                ClientNote.objects.create(
                    client=client,
                    note=fake.paragraph(),
                    created_by=client.owner
                )

        return clients

    def seed_contracts(self, count, clients):
        """Create demo contracts."""
        contracts = []

        contract_types = [Contract.FIXED_PRICE, Contract.HOURLY, Contract.RETAINER, Contract.MILESTONE]
        statuses = [Contract.DRAFT, Contract.PENDING, Contract.ACTIVE, Contract.COMPLETED]

        for i in range(count):
            client = random.choice(clients)
            contract_type = random.choice(contract_types)

            start_date = timezone.now().date() - timedelta(days=random.randint(0, 365))
            end_date = start_date + timedelta(days=random.randint(30, 365))

            contract_data = {
                'client': client,
                'title': f'{fake.catch_phrase()} Project',
                'contract_type': contract_type,
                'status': random.choice(statuses),
                'start_date': start_date,
                'end_date': end_date,
                'description': fake.paragraph(nb_sentences=5),
                'value': Decimal(random.uniform(1000, 50000)),
            }

            if contract_type == Contract.HOURLY:
                contract_data['hourly_rate'] = Decimal(random.uniform(50, 200))

            contract = Contract.objects.create(**contract_data)
            contracts.append(contract)

            # Add milestones for milestone contracts
            if contract_type == Contract.MILESTONE:
                for j in range(random.randint(2, 5)):
                    ContractMilestone.objects.create(
                        contract=contract,
                        title=f'Milestone {j+1}: {fake.bs()}',
                        description=fake.paragraph(),
                        amount=Decimal(contract.value / random.randint(2, 5)),
                        due_date=start_date + timedelta(days=30 * (j+1)),
                        status=random.choice([
                            ContractMilestone.PENDING,
                            ContractMilestone.IN_PROGRESS,
                            ContractMilestone.COMPLETED
                        ])
                    )

        return contracts

    def seed_invoices(self, count, clients, contracts):
        """Create demo invoices."""
        invoices = []

        statuses = [Invoice.DRAFT, Invoice.SENT, Invoice.VIEWED, Invoice.PAID, Invoice.OVERDUE]

        for i in range(count):
            client = random.choice(clients)
            contract = random.choice([c for c in contracts if c.client == client]) if contracts else None

            issue_date = timezone.now().date() - timedelta(days=random.randint(0, 180))
            due_date = issue_date + timedelta(days=random.choice([15, 30, 45, 60]))

            status = random.choice(statuses)

            # Adjust due date for overdue invoices
            if status == Invoice.OVERDUE:
                due_date = timezone.now().date() - timedelta(days=random.randint(1, 60))

            invoice = Invoice.objects.create(
                client=client,
                contract=contract,
                invoice_number=f'INV-{2024}-{str(i+1).zfill(5)}',
                status=status,
                issue_date=issue_date,
                due_date=due_date,
                tax_rate=Decimal('0.00'),  # No tax for demo
                discount=Decimal('0.00'),
                notes=fake.paragraph() if random.random() > 0.7 else '',
            )

            # Add line items
            for j in range(random.randint(1, 5)):
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=fake.bs().title(),
                    quantity=random.randint(1, 10),
                    unit_price=Decimal(random.uniform(50, 500)),
                )

            # Recalculate totals
            invoice.calculate_totals()
            invoice.save()

            invoices.append(invoice)

        return invoices

    def seed_payments(self, invoices):
        """Create demo payments for paid invoices."""
        payments = []

        for invoice in invoices:
            if invoice.status in [Invoice.PAID]:
                payment = Payment.objects.create(
                    invoice=invoice,
                    client=invoice.client,
                    amount=invoice.total,
                    payment_method=random.choice([
                        Payment.CARD,
                        Payment.BANK_TRANSFER,
                        Payment.CHECK
                    ]),
                    status=Payment.SUCCEEDED,
                    payment_date=invoice.issue_date + timedelta(days=random.randint(1, 30)),
                    stripe_payment_intent_id=f'pi_demo_{fake.uuid4()[:12]}',
                    stripe_charge_id=f'ch_demo_{fake.uuid4()[:12]}',
                )
                payments.append(payment)

        return payments

    def seed_payment_methods(self, clients):
        """Create saved payment methods for clients."""
        payment_methods = []

        for client in random.sample(list(clients), k=min(10, len(clients))):
            payment_method = PaymentMethod.objects.create(
                client=client,
                type=PaymentMethod.CARD,
                last4='4242',
                brand='Visa',
                exp_month=random.randint(1, 12),
                exp_year=random.randint(2025, 2030),
                is_default=True,
                stripe_payment_method_id=f'pm_demo_{fake.uuid4()[:12]}',
            )
            payment_methods.append(payment_method)

        return payment_methods

    def seed_client_metrics(self, clients):
        """Calculate and store client metrics."""
        from apps.analytics.services import ClientMetricsCalculator

        for client in clients:
            ClientMetricsCalculator.calculate_client_metrics(client)

    def seed_revenue_metrics(self):
        """Calculate and store revenue metrics for past 12 months."""
        from apps.analytics.services import RevenueMetricsCalculator

        for i in range(12):
            date = timezone.now() - timedelta(days=30 * i)
            RevenueMetricsCalculator.calculate_month_metrics(date.year, date.month)

    def seed_activity_logs(self, users, clients, invoices):
        """Create activity logs."""
        activity_logs = []

        activity_types = [
            ActivityLog.INVOICE_CREATED,
            ActivityLog.INVOICE_SENT,
            ActivityLog.INVOICE_PAID,
            ActivityLog.PAYMENT_RECEIVED,
            ActivityLog.CONTRACT_CREATED,
            ActivityLog.CLIENT_CREATED,
        ]

        for i in range(50):
            activity_type = random.choice(activity_types)
            user = random.choice(users)

            log_data = {
                'activity_type': activity_type,
                'user': user,
                'description': self.get_activity_description(activity_type),
                'created_at': timezone.now() - timedelta(days=random.randint(0, 90)),
            }

            if activity_type in [ActivityLog.INVOICE_CREATED, ActivityLog.INVOICE_SENT, ActivityLog.INVOICE_PAID]:
                invoice = random.choice(invoices)
                log_data['related_object_type'] = 'Invoice'
                log_data['related_object_id'] = str(invoice.id)

            activity_log = ActivityLog.objects.create(**log_data)
            activity_logs.append(activity_log)

        return activity_logs

    def get_activity_description(self, activity_type):
        """Get description for activity type."""
        descriptions = {
            ActivityLog.INVOICE_CREATED: 'Created new invoice',
            ActivityLog.INVOICE_SENT: 'Sent invoice to client',
            ActivityLog.INVOICE_PAID: 'Invoice marked as paid',
            ActivityLog.PAYMENT_RECEIVED: 'Payment received',
            ActivityLog.CONTRACT_CREATED: 'Created new contract',
            ActivityLog.CLIENT_CREATED: 'Added new client',
        }
        return descriptions.get(activity_type, 'Activity performed')
