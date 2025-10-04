from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    """
    Formulario para editar solo la foto del perfil del usuario
    - Solo incluye campo para foto de perfil
    - Usa widgets personalizados con Bootstrap
    """
    class Meta:
        model = Profile
        fields = ['photo']
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_photo(self):
        """
        Validación personalizada para la foto del perfil
        - Verifica el tamaño del archivo (máximo 5MB)
        - Verifica el tipo de archivo (solo imágenes)
        """
        photo = self.cleaned_data.get('photo')
        
        if photo:
            # Verificar tamaño del archivo (5MB máximo)
            if photo.size > 5 * 1024 * 1024:  # 5MB en bytes
                raise forms.ValidationError("Image size must be less than 5MB.")
            
            # Verificar tipo de archivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if hasattr(photo, 'content_type') and photo.content_type not in allowed_types:
                raise forms.ValidationError("Please upload a valid image file (JPG, PNG or GIF).")
        
        return photo

class PhotoForm(forms.ModelForm):
    """
    Formulario simple solo para cambiar la foto del perfil
    """
    class Meta:
        model = Profile
        fields = ['photo']
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_photo(self):
        """
        Validación personalizada para la foto del perfil
        - Verifica el tamaño del archivo (máximo 5MB)
        - Verifica el tipo de archivo (solo imágenes)
        """
        photo = self.cleaned_data.get('photo')
        
        if photo:
            # Verificar tamaño del archivo (5MB máximo)
            if photo.size > 5 * 1024 * 1024:  # 5MB en bytes
                raise forms.ValidationError("Image size must be less than 5MB.")
            
            # Verificar tipo de archivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if hasattr(photo, 'content_type') and photo.content_type not in allowed_types:
                raise forms.ValidationError("Please upload a valid image file (JPG, PNG or GIF).")
        
        return photo