from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'photo'] 
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Cuéntanos sobre ti, tus intereses y qué buscas en los eventos...'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            # Verificar tamaño del archivo (máximo 5MB)
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("El tamaño de la imagen debe ser menor a 5MB.")
            
            # Verificar extensión del archivo
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            file_extension = photo.name.lower()
            if not any(file_extension.endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError("Por favor sube un archivo de imagen válido (JPG, PNG o GIF).")
        
        return photo
