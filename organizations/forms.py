from django import forms
from django.contrib.auth.models import User
from .models import Organization, UserRole, OrganizationInvitation
from .validators import validate_unique_email, validate_unique_username

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'description', 'logo', 'website', 'address', 'phone', 'email', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserRole
        fields = ['user', 'role', 'is_active']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class OrganizationInvitationForm(forms.ModelForm):
    class Meta:
        model = OrganizationInvitation
        fields = ['email', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

class BulkInviteForm(forms.Form):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('staff', 'Staff'),
        ('org_admin', 'Organization Admin'),
    ]
    
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.filter(is_active=True),
        empty_label="Select an organization",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    email_domain = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'eafit.edu.co'
        }),
        help_text="Enter the email domain without @ (e.g., eafit.edu.co)"
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='member'
    )
    
    def clean_email_domain(self):
        domain = self.cleaned_data['email_domain']
        # Remove @ if user included it
        if domain.startswith('@'):
            domain = domain[1:]
        return domain.lower()

class CSVBulkInviteForm(forms.Form):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('staff', 'Staff'),
        ('org_admin', 'Organization Admin'),
    ]
    
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.filter(is_active=True),
        empty_label="Select an organization",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the organization to invite users to"
    )
    
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text="Upload a CSV file with email addresses in the first column"
    )
    
    default_role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='member',
        help_text="Default role for all invited users"
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        if not file.name.endswith('.csv'):
            raise forms.ValidationError('Please upload a CSV file.')
        if file.size > 5 * 1024 * 1024:  # 5MB limit
            raise forms.ValidationError('File size must be less than 5MB.')
        return file

class CreateUserForm(forms.Form):
    """
    Formulario para crear usuarios con validaciones de email y username únicos
    """
    ROLE_CHOICES = [
        ('member', 'Regular Member'),
        ('staff', 'Staff Member'),
    ]
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text="Required. Enter a valid email address."
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Password must be at least 8 characters long."
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='member'
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
