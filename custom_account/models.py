import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail


class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé pour étendre les fonctionnalités par défaut de Django.
    """
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Numéro de profil client (optionnel).",
    )
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username

class CustomerProfileStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Actif"
    IN_OBSERVATION = "IN_OBSERVATION", "En observation"
    SUSPENDED = "SUSPENDED", "Suspendu"
    CLOSED = "CLOSED", "Fermé"

class CustomerProfile(models.Model):
    """
    Profil client lié à un utilisateur personnalisé.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="customer_profile",
        null=True,
        blank=True,
    )
    customer_profile_number = models.CharField(max_length=50, unique=True)

    # Status du profil (actif, suspendu, fermé, etc.)
    status = models.CharField(
        max_length=20,
        choices=CustomerProfileStatus.choices,
        default=CustomerProfileStatus.ACTIVE,
    )

    # True si le profil a été créé manuellement par un admin AVANT le user
    created_by_admin = models.BooleanField(
        default=False,
        help_text="Coché si ce profil a été créé par un admin avant la création de l'utilisateur.",
    )

    company_name = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.customer_profile_number} - {self.company_name or 'Individual'}"


@receiver(post_save, sender=CustomUser)
def create_or_link_customer_profile(sender, instance, created, **kwargs):
    """
    - Si un profile_number est fourni et correspond à un CustomerProfile existant:
        -> on lie ce profil au user
        -> si le profil a été créé par un admin, on envoie un email pour prévenir.
    - Sinon:
        -> on génère un nouveau numéro + on crée un CustomerProfile pour ce user.
    """
    if not created:
        return

    # 1) Si l'utilisateur a fourni un profile_number
    if instance.profile_number:
        try:
            profile = CustomerProfile.objects.get(
                customer_profile_number=instance.profile_number
            )
            # Lier ce profil au user
            profile.user = instance
            profile.save()

            # Si ce profil a été créé par un admin -> envoyer un email de notification
            if profile.created_by_admin:
                _notify_admin_user_attached_to_profile(instance, profile)
            return
        except CustomerProfile.DoesNotExist:
            # Le numéro entré ne correspond à aucun profil -> on continue et on en crée un
            pass

    # 2) Aucun profile_number valide -> on en génère un nouveau
    profile_number = instance.profile_number
    if not profile_number:
        profile_number = str(uuid.uuid4())[:8]
        instance.profile_number = profile_number
        instance.save(update_fields=["profile_number"])

    # Créer le profil associé (profil auto, pas créé par admin)
    CustomerProfile.objects.create(
        user=instance,
        customer_profile_number=profile_number,
        status=CustomerProfileStatus.ACTIVE,
        created_by_admin=False,
    )


def _notify_admin_user_attached_to_profile(user, profile: CustomerProfile):
    """
    Envoie un email à l'admin pour l'informer qu'un user a été rattaché
    à un profil pré-créé par l'admin.
    """
    subject = "Un utilisateur a été rattaché à un profil client"
    message = (
        f"Bonjour,\n\n"
        f"L'utilisateur {user.username} (ID: {user.id}, email: {user.email}) "
        f"a été rattaché au profil client numéro {profile.customer_profile_number}.\n\n"
        f"Company: {profile.company_name or 'N/A'}\n"
        f"Status profil: {profile.status}\n\n"
        f"Cordialement,\n"
        f"Votre système."
    )

    # Adresse(s) destinataire(s) : soit une liste dans settings, soit un fallback
    recipient_list = getattr(
        settings,
        "PROFILE_ADMIN_NOTIFICATION_EMAILS",
        [getattr(settings, "DEFAULT_FROM_EMAIL", "admin@rhematek-solutions.com")],
    )

    send_mail(
        subject,
        message,
        getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
        recipient_list,
        fail_silently=False,
    )
