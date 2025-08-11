from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar'] 
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
