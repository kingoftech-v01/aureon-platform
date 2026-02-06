from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from custom_account.models import CustomerProfile

def invoice_number_generator():
    """
    Génère un numéro de facture unique.
    Format: FYYYY-MMDD-HHMM-SS-NNNN (ex: F2025-MM-0001)
    """
    from datetime import datetime

    current_year = datetime.now().year
    current_month = datetime.now().month
    current_day = datetime.now().day
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    current_second = datetime.now().second

    last_invoice = Invoice.objects.filter(number__startswith=f"F{current_year}").order_by('number').last()
    if not last_invoice:
        new_number = f"F{current_year}-{current_month:02d}{current_day:02d}-{current_hour:02d}{current_minute:02d}-{current_second:02d}-0001"
    else:
        last_number = int(last_invoice.number.split('-')[5])
        new_number = f"F{current_year}-{last_number + 1:04d}"
    return new_number

# Create your models here.
class ContractType(models.TextChoices):
    SYSTEM_INSTALLMENT = "SYSTEM_INSTALLMENT", "Systeme en tranches"
    SUBSCRIPTION = "SUBSCRIPTION", "Abonnement"


class Contract(models.Model):
    """
    Contrat entre ton agence et le client.
    - Peut représenter soit un système à payer sur 48 mois, soit un abonnement mensuel, etc.
    """
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name="contracts",
    )
    contract_type = models.CharField(
        max_length=30,
        choices=ContractType.choices,
    )
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)  # ex.: 48 mois
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    # paid amount
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # date de signature du contrat
    signed_date = models.DateField(null=True, blank=True)
    # date de résiliation du contrat
    termination_date = models.DateField(null=True, blank=True)
    # Montant minimum à garder en cas de résiliation (ex: 15% pour les systèmes)
    early_termination_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.15"),
        help_text="Pourcentage retenu en cas de résiliation anticipée",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_signed = models.BooleanField(default=False)

    contract_file = models.FileField(upload_to="contracts/", null=True, blank=True)
    cahier_des_charges_file = models.FileField(upload_to="cahiers_des_charges/", null=True, blank=True)
    notion_link = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.get_contract_type_display()} - {self.customer}"
    
    def calculate_early_termination_fee(self) -> Decimal:
        """
        Calcule les frais de résiliation anticipée basés sur le taux défini.
        """
        return self.total_amount * self.early_termination_rate
    
    def remaining_balance(self) -> Decimal:
        """
        Calcule le solde restant dû sur le contrat.
        """
        return self.total_amount - self.paid_amount
    
    def is_terminated(self) -> bool:
        """
        Vérifie si le contrat est résilié.
        """
        return self.termination_date is not None
    
    def mark_as_signed(self):
        """
        Marque le contrat comme signé.
        """
        self.is_signed = True
        self.signed_date = timezone.now().date()
        self.save()
    
    def terminate_contract(self, termination_date: timezone.datetime.date):
        """
        Résilie le contrat à la date spécifiée.
        """
        self.termination_date = termination_date
        self.is_active = False
        self.save()

class PaymentSchedule(models.Model):
    """
    Calendrier des paiements pour un contrat donné.
    - Pour un système en tranches, cela pourrait être 48 paiements mensuels.
    - Pour un abonnement, cela pourrait être des paiements mensuels récurrents.
    """
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="payment_schedules",
    )
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Payment of {self.amount_due} due on {self.due_date} for {self.contract}"
    
class InvoiceStatus(models.TextChoices):
    DRAFT = "DRAFT", "Brouillon"
    OPEN = "OPEN", "Ouverte"
    PAID = "PAID", "Payée"
    CANCELLED = "CANCELLED", "Annulée"


class Invoice(models.Model):
    """
    Facture liée à un contrat (et donc à un client).
    """
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    number = models.CharField(max_length=50, unique=True)  # ex: F2025-0001
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.number
    
    def save(self, *args, **kwargs):
        # Calculer subtotal, tax_amount, total avant de sauvegarder
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.tax_amount = self.subtotal * Decimal("0.20")  # Exemple: 20% de TVA
        self.total = self.subtotal + self.tax_amount
        # Calculer balance_due en soustrayant les paiements effectués
        paid_amount = sum(payment.amount for payment in self.payments.all())
        self.balance_due = self.total - paid_amount
        super().save(*args, **kwargs)


class InvoiceItem(models.Model):
    """
    Ligne de facture (service, tranche, abonnement mensuel, etc.).
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.description} ({self.invoice.number})"

class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Cash"
    CARD = "CARD", "Carte"
    BANK_TRANSFER = "BANK_TRANSFER", "Virement"
    STRIPE = "STRIPE", "Stripe"
    SAMSUNG_PAY = "SAMSUNG_PAY", "Samsung Pay"
    APPLE_PAY = "APPLE_PAY", "Apple Pay"
    CRYPTO = "CRYPTO", "Crypto-monnaie"

class Payment(models.Model):
    """
    Enregistrement d'un paiement appliqué à une facture.
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.amount} sur {self.invoice.number}"


class Refund(models.Model):
    """
    Enregistrement d'un remboursement effectué à un client.
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Remboursement de {self.amount} pour {self.payment.invoice.number}"
    
class InstallmentStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    PAID = "PAID", "Payée"
    OVERDUE = "OVERDUE", "En retard"

class InstallmentType(models.TextChoices):
    FIXED = "FIXED", "Fixe"
    PERCENTAGE = "PERCENTAGE", "Pourcentage"

class InstallmentPlan(models.TextChoices):
    EQUAL = "EQUAL", "Égal"
    CUSTOM = "CUSTOM", "Personnalisé"

class Installment(models.Model):
    """
    Tranche d'un paiement de système.
    Exemple: 50% / 50% avec dates définies, ou 40% / 30% / 30%.
    """
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="installments",
    )
    label = models.CharField(max_length=50, blank=True)  # ex: "1ère tranche 50%"
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=InstallmentStatus.choices,
        default=InstallmentStatus.PENDING,
    )
    # Optionnel: lien vers la facture qui contient cette tranche
    invoice = models.ForeignKey(
        Invoice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="installment_links",
    )

    def __str__(self):
        return f"{self.label} - {self.amount}"

class SubscriptionStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Actif"
    SUSPENDED = "SUSPENDED", "Suspendu"
    CANCELLED = "CANCELLED", "Annulé"


class Subscription(models.Model):
    """
    Abonnement lié à un contrat de type SUBSCRIPTION.
    L'abonnement ne peut être suspendu que si balance = 0.
    """
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    start_date = models.DateField(default=timezone.now)
    next_billing_date = models.DateField()
    billing_cycle_days = models.PositiveIntegerField(default=30)  # 30 = mensuel
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )

    def __str__(self):
        return f"Abonnement {self.contract.customer}"

    def can_suspend(self) -> bool:
        """
        Règle : peut suspendre seulement si le contrat n'a pas de balance.
        -> logique à implémenter via les factures liées.
        """
        # Ex.: vérifier que toutes les factures du contrat sont à balance_due=0
        return not self.contract.invoices.filter(balance_due__gt=0).exists()

class SubscriptionPaymentHistory(models.Model):
    """
    Historique des paiements d'un abonnement.
    """
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="payment_history",
    )
    payment_date = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="subscription_payments",
    )

    def __str__(self):
        return f"Paiement de {self.amount} pour {self.subscription}"