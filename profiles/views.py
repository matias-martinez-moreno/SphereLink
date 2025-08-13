from django.shortcuts import render, redirect
from .forms import ProfileForm
from .models import Profile


def my_profile(request):
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            # Si el perfil no existe, lo creamos
            profile = Profile.objects.create(user=request.user)
    else:
        # Si no está autenticado, crear un perfil temporal o mostrar mensaje
        profile = None
    
    return render(request, 'profiles/my_profile.html', {'profile': profile})


def edit_profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('my_profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'profiles/edit_profile.html', {'form': form})
