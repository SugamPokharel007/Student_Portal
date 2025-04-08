from django.contrib import admin
from django.contrib.auth.models import User
from .models import Subject, Notice, Syllabus, QuestionBank, ContactMessage, Note

# Register your models here.
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'created_at')
    search_fields = ('name', 'year')
    list_filter = ('year',)

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'is_general', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('is_general', 'subject', 'created_at')

@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ('subject', 'title', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('subject', 'created_at')

@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('subject', 'title', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    list_filter = ('subject', 'created_at')

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('subject', 'title', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    list_filter = ('subject', 'created_at')

# For contact page submission
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'submitted_at')
    search_fields = ('name', 'email', 'message')
    list_filter = ('submitted_at',)

# Customizing the User model admin
class UserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'username', 'email', 'date_joined')
    search_fields = ('username', 'email')

# Unregister the default User model registration first to avoid duplicate registration
admin.site.unregister(User)

# Register the customized UserAdmin for the User model
admin.site.register(User, UserAdmin)
