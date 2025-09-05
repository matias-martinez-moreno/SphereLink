from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Organization, UserRole, OrganizationInvitation

@receiver(post_save, sender=Organization)
def organization_post_save(sender, instance, created, **kwargs):
    """Señal que se ejecuta después de guardar una organización"""
    if created:
        # Lógica adicional cuando se crea una nueva organización
        pass

@receiver(post_save, sender=UserRole)
def user_role_post_save(sender, instance, created, **kwargs):
    """Señal que se ejecuta después de guardar un rol de usuario"""
    if created:
        # Lógica adicional cuando se asigna un nuevo rol
        pass

@receiver(post_delete, sender=UserRole)
def user_role_post_delete(sender, instance, **kwargs):
    """Señal que se ejecuta después de eliminar un rol de usuario"""
    # Lógica adicional cuando se elimina un rol
    pass

@receiver(post_save, sender=OrganizationInvitation)
def invitation_post_save(sender, instance, created, **kwargs):
    """Señal que se ejecuta después de guardar una invitación"""
    if created:
        # Aquí se podría implementar el envío de email
        pass
