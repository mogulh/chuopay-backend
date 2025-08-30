"""
Signals for the approval system
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import EventApproval, EventDocument, DocumentSignature


@receiver(post_save, sender=EventApproval)
def handle_approval_save(sender, instance, created, **kwargs):
    """Handle actions when an approval is saved"""
    if created:
        # New approval created
        print(f"New approval created: {instance}")
        
        # You could add notification logic here
        # send_approval_notification(instance)
    
    elif instance.status == 'approved':
        # Approval was just approved
        print(f"Approval approved: {instance}")
        
        # Generate document if needed
        if instance.event.requires_approval and instance.event.documents.exists():
            # Update existing documents with approval information
            for document in instance.event.documents.all():
                if document.requires_parent_signature:
                    # Create document signature record
                    DocumentSignature.objects.create(
                        document=document,
                        signer=instance.parent,
                        approval=instance,
                        signature_type='parent',
                        signature_data=instance.signature_data,
                        signature_hash=instance.signature_hash,
                        ip_address=instance.ip_address,
                        user_agent=instance.user_agent
                    )


@receiver(post_save, sender=EventDocument)
def handle_document_save(sender, instance, created, **kwargs):
    """Handle actions when a document is saved"""
    if created:
        # New document created
        print(f"New document created: {instance}")
        
        # You could add notification logic here
        # send_document_notification(instance)
    
    elif instance.admin_signed_by and not instance.admin_signed_at:
        # Document was just signed by admin
        print(f"Document signed by admin: {instance}")
        
        # You could add notification logic here
        # send_document_signed_notification(instance)


@receiver(post_save, sender=DocumentSignature)
def handle_signature_save(sender, instance, created, **kwargs):
    """Handle actions when a document signature is saved"""
    if created:
        # New signature created
        print(f"New signature created: {instance}")
        
        # You could add notification logic here
        # send_signature_notification(instance)
    
    elif instance.is_verified:
        # Signature was just verified
        print(f"Signature verified: {instance}")
        
        # You could add notification logic here
        # send_signature_verified_notification(instance)


@receiver(pre_save, sender=EventApproval)
def handle_approval_pre_save(sender, instance, **kwargs):
    """Handle actions before an approval is saved"""
    if instance.pk:  # Not a new instance
        try:
            old_instance = EventApproval.objects.get(pk=instance.pk)
            
            # Check if status changed to approved
            if old_instance.status != 'approved' and instance.status == 'approved':
                instance.approved_at = timezone.now()
                
        except EventApproval.DoesNotExist:
            pass


@receiver(pre_save, sender=EventDocument)
def handle_document_pre_save(sender, instance, **kwargs):
    """Handle actions before a document is saved"""
    if instance.pk:  # Not a new instance
        try:
            old_instance = EventDocument.objects.get(pk=instance.pk)
            
            # Check if admin signature was added
            if not old_instance.admin_signed_by and instance.admin_signed_by:
                instance.admin_signed_at = timezone.now()
                
        except EventDocument.DoesNotExist:
            pass
