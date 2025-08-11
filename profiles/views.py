from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileForm


def my_profile(request):
    profile = request.user.profile
    return render(request, 'profiles/my_profile.html', {'profile': profile})


def edit_profile(request):
    # No hay usuario, así que creamos un formulario vacío (o con datos por defecto)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            # Aquí podrías guardar en algún lugar (pero no tienes usuario)
            # Por ejemplo, podrías guardar en sesión, o simplemente mostrar un mensaje
            return redirect('my_profile')
    else:
        form = ProfileForm()  # formulario vacío

    return render(request, 'profiles/edit_profile.html', {'form': form})

# def edit_profile(request):
#     profile = request.user.profile  
#     if request.method == "POST":
#         form = ProfileForm(request.POST, request.FILES, instance=profile)
#         if form.is_valid():
#             form.save()
#             return redirect('my_profile')
#     else:
#         form = ProfileForm(instance=profile)
#     return render(request, 'profiles/edit_profile.html', {'form': form})
