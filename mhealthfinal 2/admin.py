from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ExcelFile
from django.http import HttpResponseForbidden

class ExcelFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'uploaded_at')
    fields = ['name', 'file']

    # Override save_model to restrict uploads to superusers
    def save_model(self, request, obj, form, change):
        if request.user.is_superuser:
            super().save_model(request, obj, form, change)
        else:
            return HttpResponseForbidden("You are not allowed to upload files.")

    # Disable delete permission for non-superusers (optional)
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

admin.site.register(ExcelFile, ExcelFileAdmin)
# from .models import ParticipantConsent
# admin.site.register(ParticipantConsent)


from django.contrib import admin
from .models import ContactMessage
from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email')

from django.contrib import admin
from .models import GoogleSheet

class GoogleSheetAdmin(admin.ModelAdmin):
    list_display = ('user', 'sheet_url', 'created_at')  # Customize the columns you want to show in the admin list view

# Register the model along with the custom admin class
admin.site.register(GoogleSheet, GoogleSheetAdmin)


from django.contrib import admin
from .models import UserProfile

# Register the UserProfile model
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'form_submitted')  # Display these fields in the admin list view
    list_filter = ('form_submitted',)  # Add a filter for the 'form_submitted' field
    search_fields = ('user__username',)  # Add a search bar to find by username
