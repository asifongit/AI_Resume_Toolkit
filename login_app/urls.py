# login_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('welcome/', views.welcome_view, name='welcome'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-page/', views.admin_page_view, name='admin_page'),
    path('manage-users/', views.manage_users_view, name='manage_users'),
    path('add-user/', views.add_user_view, name='add_user'),
    path('edit-user/<int:user_id>/', views.edit_user_view, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('resume-enhancer/', views.resume_enhancer_view, name='resume_enhancer'),
    path('section/', views.section_enhancer_view, name='section'),
    # New URL for the ATS functionality
    path('ats-scanner/', views.ats_scanner_view, name='ats_scanner'),
]
