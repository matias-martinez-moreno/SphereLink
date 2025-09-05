from django.contrib import messages

def clear_all_messages(request):
    """
    Función de utilidad para limpiar todos los mensajes de la sesión
    - Limpia el storage de mensajes
    - Limpia la sesión de mensajes
    - Maneja errores de forma segura
    """
    try:
        # Limpiar storage de mensajes
        storage = messages.get_messages(request)
        storage.used = True
        
        # Limpiar sesión de mensajes
        if hasattr(request, 'session'):
            request.session['_messages'] = []
            
    except Exception:
        # Ignorar cualquier error que pueda ocurrir
        pass
