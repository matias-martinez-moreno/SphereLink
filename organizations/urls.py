from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    path('', views.organization_list, name='organization_list'),
    path('create/', views.create_organization, name='create_organization'),
    path('<int:org_id>/edit/', views.edit_organization, name='edit_organization'),
    path('<int:org_id>/', views.organization_detail, name='organization_detail'),
    path('<int:org_id>/manage-users/', views.manage_user_roles, name='manage_user_roles'),
    path('user-role/<int:role_id>/delete/', views.delete_user_role, name='delete_user_role'),
    path('<int:org_id>/invite/', views.invite_user, name='invite_user'),
    path('bulk-invite/', views.bulk_invite, name='bulk_invite'),
    path('user-management/', views.user_management, name='user_management'),
    path('invitation/<str:token>/accept/', views.accept_invitation, name='accept_invitation'),
]
