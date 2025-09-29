from django import forms
from .models import ContactMessage

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
