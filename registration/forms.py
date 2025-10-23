from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from .models import ContactMessage
from organizations.validators import validate_unique_email, validate_unique_username

class ContactForm(forms.ModelForm):
    """
    Form for users to contact administrators about login or account issues
    """
    class Meta:
        model = ContactMessage
        fields = ['email', 'message']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe your issue or what help you need...',
                'rows': 4,
                'required': True
            })
        }
        labels = {
            'email': 'Your Email Address',
            'message': 'Message'
        }
        help_texts = {
            'email': 'We will use this to contact you back',
            'message': 'Please describe your login issue or account problem'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes and validation
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'required': True
            })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
        return email
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if message:
            message = message.strip()
            if len(message) < 5:
                raise forms.ValidationError("Please provide more details about your issue (at least 5 characters).")
        return message

class UserRegistrationForm(forms.Form):
    """
    Formulario de registro de usuarios con validaciones de email y username únicos
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        }),
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        help_text="Required. Enter a valid email address."
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        }),
        help_text="Password must be at least 8 characters long."
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        }),
        help_text="Enter the same password as before, for verification."
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data['username']
        validate_unique_username(username)
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        validate_unique_email(email)
        return email
    
    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

class CustomPasswordResetForm(PasswordResetForm):
    """
    Formulario personalizado para reset de contraseña que verifica si el email existe
    """
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        label='Email Address'
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
            # Verificar si el email existe en el sistema
            if not User.objects.filter(email=email, is_active=True).exists():
                raise forms.ValidationError(
                    "This email address is not registered in our system. "
                    "Please check your email address or contact an administrator for assistance."
                )
        return email
