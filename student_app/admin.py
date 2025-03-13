from django.contrib import admin
from django.contrib.auth.models import User
from .models import Subject, Notice, ContactMessage

# Register your models here.
admin.site.register(Subject)
admin.site.register(Notice)

# For contact page submission
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'submitted_at')
    search_fields = ('name', 'email')

# Customizing the User model admin
class UserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'username', 'email', 'date_joined')
    search_fields = ('username', 'email')

# Unregister the default User model registration first to avoid duplicate registration
admin.site.unregister(User)

# Register the customized UserAdmin for the User model
admin.site.register(User, UserAdmin)
