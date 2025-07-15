from django.views.generic.base import TemplateView  # Import TemplateView here
from django.conf import settings  # Import settings
from django.views.static import serve
from django.urls import path, re_path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from login import views

urlpatterns = [
    path('local_files/', views.local_files_view, name='local_files'),
    path('view_file_data/<str:username>/<str:filename>/', views.view_file_data, name='view_file_data'),
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
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    path('view-local-ppg/<str:filename>/', views.view_local_ppg, name='view_local_ppg'),
    path('view-local-gsr/<str:filename>/', views.view_local_gsr, name='view_local_gsr'),
    path('convert_local_csv_to_hl7/<str:filename>/', views.convert_local_csv_to_hl7, name='convert_local_csv_to_hl7'),
    path('download_hl7_pdf/<str:filename>/', views.download_hl7_pdf, name='download_hl7_pdf'),
    
    # Home/Landing Page for Actigraphy
    path('homme/<str:filename>/', views.homme, name='homme'),  # For normal users
    path('homme/<str:username>/<str:filename>/', views.homme, name='homme_superuser'),  # For superusers

    
    # Weekly overview (clickable)
    path('weekly/<str:username>/<str:filename>/', views.actigraphy_weekly, name='weekly'),
    
    # # Day view API endpoint (for AJAX)
    # path('api/day/<str:filename>/<int:day_id>/', views.actigraphy_day_view, name='day_api'),
    
    # # Day view standalone page
    # path('day/<str:filename>/<int:day_id>/', views.actigraphy_day_page, name='day_page'),
    # Regular user routes
    path('actigraphy/<str:filename>/day/<int:day_id>/', views.actigraphy_day_page, name='day_page'),
    path('actigraphy/api/<str:filename>/day/<int:day_id>/', views.actigraphy_day_view, name='day_api'),

    # Admin routes with username
    path('actigraphy/<str:username>/<str:filename>/day/<int:day_id>/', views.actigraphy_day_page, name='day_page'),
    path('actigraphy/api/<str:username>/<str:filename>/day/<int:day_id>/', views.actigraphy_day_view, name='day_api'),
    # Summary statistics
    path('stats/<str:filename>/', views.actigraphy_stats, name='stats'),
   
    path('compact/<str:filename>/', views.compact, name='compact'),


]
