"""
Signals for the contracts app.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Contract, ContractMilestone


@receiver(post_save, sender=ContractMilestone)
def update_contract_on_milestone_change(sender, instance, created, **kwargs):
    """
    Update contract completion percentage when milestone is saved.
    """
    if not created:  # Only on updates, not creation
        instance.contract.update_completion_percentage()


@receiver(post_delete, sender=ContractMilestone)
def update_contract_on_milestone_delete(sender, instance, **kwargs):
    """
    Update contract completion percentage when milestone is deleted.
    """
    instance.contract.update_completion_percentage()
