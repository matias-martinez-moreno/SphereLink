from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

def validate_unique_email(email):
    """
    Valida que el email sea único en el sistema
    """
    if User.objects.filter(email=email).exists():
        raise ValidationError(f"Email '{email}' is already in use. Please choose a different email.")
    return email

def validate_unique_username(username):
    """
    Valida que el username sea único en el sistema
    """
    if User.objects.filter(username=username).exists():
        raise ValidationError(f"Username '{username}' is already in use. Please choose a different username.")
    return username
