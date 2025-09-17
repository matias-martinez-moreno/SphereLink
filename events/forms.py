from django import forms
from django.utils import timezone
from .models import Event

class EventForm(forms.ModelForm):
    """
    Formulario para crear y editar eventos
    - Incluye todos los campos necesarios para un evento
    - El campo is_official solo se muestra para usuarios staff
    - Usa widgets personalizados con clases CSS de Bootstrap
    """
    class Meta:
        model = Event
        # Excluimos los campos que no deben ser llenados por el usuario
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'max_capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Enter maximum number of participants'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Inicialización personalizada del formulario
        - Recibe el usuario actual para determinar permisos
        - Oculta el campo is_official para usuarios no-staff
        - Mantiene la funcionalidad estándar del formulario
        """
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Solo mostrar campo is_official para staff y super_admin
        # Esto controla qué usuarios pueden marcar eventos como oficiales
        if not user or not self._is_staff_user(user):
            self.fields.pop('is_official', None)
    def clean_date(self):
        """
        Validación para la fecha del evento
        - No puede ser una fecha en el pasado
        """
        date = self.cleaned_data.get('date')
        if date and date < timezone.now():
            raise forms.ValidationError("The event date cannot be in the past.")
        return date

    
    def clean_max_capacity(self):
        """
        Validación personalizada para la capacidad máxima
        - Debe ser un número positivo
        - Mínimo 1 participante
        """
        max_capacity = self.cleaned_data.get('max_capacity')
        
        if max_capacity is not None:
            if max_capacity < 1:
                raise forms.ValidationError("Maximum capacity must be at least 1 participant.")
            
            # Si es una edición, verificar que no sea menor que los registros actuales
            if self.instance and self.instance.pk:
                current_registrations = self.instance.current_registrations
                if max_capacity < current_registrations:
                    raise forms.ValidationError(
                        f"Cannot reduce capacity below current registrations ({current_registrations} participants)."
                    )
        
        return max_capacity
    
    def _is_staff_user(self, user):
        """
        Verifica si el usuario tiene rol de staff o superior
        - Retorna True si es superuser de Django
        - Retorna True si tiene rol staff, org_admin o super_admin en alguna organización
        - Retorna False si no está autenticado o no tiene permisos
        """
        if not user.is_authenticated:
            return False
        
        # Verificar si es superuser de Django (acceso completo al sistema)
        if user.is_superuser:
            return True
        
        # Verificar roles en organizaciones (sistema de permisos personalizado)
        # Solo usuarios con roles administrativos pueden marcar eventos como oficiales
        from organizations.models import UserRole
        staff_roles = UserRole.objects.filter(
            user=user,
            is_active=True,
            role__in=['staff', 'org_admin', 'super_admin']
        )
        return staff_roles.exists()
