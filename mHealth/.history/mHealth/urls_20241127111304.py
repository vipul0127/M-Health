"""
URL configuration for mHealth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.views.generic.base import TemplateView  # Import TemplateView here

from login.views import (
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView
)
from django.contrib import admin
from django.urls import path
from login import views
# urls.py
from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path
from login import views
from login.views import send_otp
from django.urls import path

from django.views.static import serve
from django.urls import path, re_path

urlpatterns = [
    #path('file/<int:file_id>/ppg/', views.view_ppg, name='view_ppg'),
    path('sheet/<int:id>/', views.SheetPage, name='sheet'),
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    path('send-otp/', views.send_otp, name='send_otp'),  # Define URL for sending OTP
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.LoginPage, name='login'),  # Changed URL to avoid conflict
   path('file/<int:file_id>/', views.file_detail, name='file_detail'),
    path('home/', views.home_view, name='home'),  # Renamed to avoid conflict
    path('sheet/', views.SheetPage, name='sheet'),
    path('logout/', views.LogoutPage, name='logout'),
    path('download-csv/', views.download_csv_data, name='download_csv_data'),
    path('generate_hl7/', views.generate_hl7, name='generate_hl7'),
    path('download_hl7/', views.download_hl7, name='download_hl7'),
    
    path('upload-success/', views.upload_success, name='upload_success'),

    path('display_csv/<int:file_id>/', views.display_csv, name='display_csv'),


    path('view_hl7/<int:file_id>/', views.view_hl7, name='view_hl7'),
    path('generate_ppg_graph/<int:file_id>/', views.generate_ppg_graph, name='ppg_graph'),
    path('profile/', views.ProfilePage, name='profile'),
  
    path('about/', views.AboutPage, name='about'),
    path('', views.welcome_view, name='welcome'), 
    
    path('welcome_about/', views.welcome_about, name='about'),  
    path('welcome_contact/', views.welcome_contact_view, name='contact'),  
    path('view_files/', views.view_files, name='view_files'),


    path('authorize/', views.authorize, name='authorize'),
    path('view-sheet/<int:file_id>/', views.get_google_sheet_data, name='get_google_sheet_data'),
    path('file_detail/<int:id>/', views.file_detail, name='file_detail'),


    path('access_excel/', views.access_excel, name='access_excel'),

    path('contact/', views.contact_view, name='contact'),
    path('contact/success/', views.contact_success_view, name='contact_success'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('upload/', views.upload_google_sheet, name='upload_google_sheet'),


    path('form_submit/', views.form_submit, name='form_submit'),



    url(r'^media/(?P<path>.*)$', serve, {'document_root':settings.MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
]

