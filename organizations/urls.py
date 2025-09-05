from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    path('', views.organization_list, name='organization_list'),
    path('create/', views.create_organization, name='create_organization'),
    path('edit/<int:org_id>/', views.edit_organization, name='edit_organization'),
    path('delete/<int:org_id>/', views.delete_organization, name='delete_organization'),
    path('detail/<int:org_id>/', views.organization_detail, name='organization_detail'),
    path('manage_user_roles/<int:org_id>/', views.manage_user_roles, name='manage_user_roles'),
    path('create_user/<int:org_id>/', views.create_user_for_organization, name='create_user'),
    path('invite_user/<int:org_id>/', views.invite_user, name='invite_user'),
    path('accept_invitation/<str:token>/', views.accept_invitation, name='accept_invitation'),
    path('user_management/', views.user_management, name='user_management'),
    path('bulk_invite/', views.bulk_invite_confirm_view, name='bulk_invite'),  # Esta sí tiene _view
    path('profile/', views.superadmin_profile, name='superadmin_profile'),
]
