from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Faculty, Subject, Notice, ContactMessage, RegisteredUser, 
    Syllabus, QuestionBank, Note, Subscription, UserProfile,
    ContributorRequest, DownloadLog, ViewLog
)

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'subject_count', 'user_count', 'is_active', 'created_date']
    list_filter = ['is_active', 'created_date']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['name']

    def subject_count(self, obj):
        return obj.subjects.count()
    subject_count.short_description = 'Subjects'

    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Users'


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'faculty', 'level', 'is_active', 'total_resources']
    list_filter = ['faculty', 'level', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'faculty__name']
    ordering = ['faculty', 'level', 'name']
    autocomplete_fields = ['faculty']
    readonly_fields = ['total_resources', 'created_at']


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'is_general', 'is_important', 'created_by', 'created_at']
    list_filter = ['is_general', 'is_important', 'created_at', 'subject__faculty']
    search_fields = ['title', 'content']
    list_editable = ['is_important']
    ordering = ['-created_at']
    autocomplete_fields = ['subject', 'created_by']
    date_hierarchy = 'created_at'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status', 'submitted_at', 'responded_at']
    list_filter = ['status', 'submitted_at', 'responded_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'subject', 'message', 'submitted_at']
    ordering = ['-submitted_at']
    date_hierarchy = 'submitted_at'
    actions = ['mark_in_progress', 'mark_resolved', 'mark_closed']

    def mark_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
    mark_in_progress.short_description = "Mark selected messages as 'In Progress'"

    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved')
    mark_resolved.short_description = "Mark selected messages as 'Resolved'"

    def mark_closed(self, request, queryset):
        queryset.update(status='closed')
    mark_closed.short_description = "Mark selected messages as 'Closed'"


@admin.register(ContributorRequest)
class ContributorRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'faculty', 'status', 'submitted_at', 'reviewed_at', 'reviewed_by']
    list_filter = ['status', 'faculty', 'submitted_at', 'reviewed_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'reason']
    readonly_fields = ['user', 'faculty', 'reason', 'experience', 'submitted_at']
    ordering = ['-submitted_at']
    date_hierarchy = 'submitted_at'
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        for req in queryset.filter(status='pending'):
            req.status = 'approved'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
    approve_requests.short_description = "Approve selected requests"

    def reject_requests(self, request, queryset):
        for req in queryset.filter(status='pending'):
            req.status = 'rejected'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
    reject_requests.short_description = "Reject selected requests"


class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'uploaded_by', 'status', 'download_count', 'view_count', 'created_at']
    list_filter = ['status', 'created_at', 'subject__faculty', 'subject__year']
    search_fields = ['title', 'description', 'subject__name']
    list_editable = ['status']
    ordering = ['-created_at']
    autocomplete_fields = ['subject', 'uploaded_by']
    readonly_fields = ['download_count', 'view_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    actions = ['approve_resources', 'reject_resources']

    def approve_resources(self, request, queryset):
        queryset.update(status='approved')
    approve_resources.short_description = "Approve selected resources"

    def reject_resources(self, request, queryset):
        queryset.update(status='rejected')
    reject_resources.short_description = "Reject selected resources"


@admin.register(Syllabus)
class SyllabusAdmin(ResourceAdmin):
    list_display = ['title', 'subject', 'subject__faculty', 'subject__level', 'status', 'uploaded_by', 'created_at']
    list_filter = ['status', 'subject__faculty', 'subject__level', 'created_at']
    search_fields = ['title', 'content', 'subject__name', 'subject__faculty__name']
    ordering = ['-created_at']
    autocomplete_fields = ['subject', 'uploaded_by']
    readonly_fields = ['download_count', 'view_count', 'created_at', 'updated_at']


@admin.register(QuestionBank)
class QuestionBankAdmin(ResourceAdmin):
    list_display = ['title', 'subject', 'subject__faculty', 'subject__level', 'status', 'uploaded_by', 'created_at']
    list_filter = ['status', 'subject__faculty', 'subject__level', 'created_at']
    search_fields = ['title', 'description', 'subject__name', 'subject__faculty__name']
    ordering = ['-created_at']
    autocomplete_fields = ['subject', 'uploaded_by']
    readonly_fields = ['download_count', 'view_count', 'created_at', 'updated_at']


@admin.register(Note)
class NoteAdmin(ResourceAdmin):
    list_display = ['title', 'subject', 'subject__faculty', 'subject__level', 'status', 'uploaded_by', 'created_at']
    list_filter = ['status', 'subject__faculty', 'subject__level', 'created_at']
    search_fields = ['title', 'description', 'subject__name', 'subject__faculty__name']
    ordering = ['-created_at']
    autocomplete_fields = ['subject', 'uploaded_by']
    readonly_fields = ['download_count', 'view_count', 'created_at', 'updated_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_type', 'start_date', 'end_date', 'is_active', 'days_remaining']
    list_filter = ['subscription_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['days_remaining', 'is_expiring_soon']
    ordering = ['-start_date']
    date_hierarchy = 'start_date'

    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = 'Days Remaining'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'faculty', 'is_contributor_approved', 'total_uploads', 'total_downloads']
    list_filter = ['role', 'faculty', 'is_contributor_approved']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    list_editable = ['role', 'is_contributor_approved']
    autocomplete_fields = ['user', 'faculty']
    readonly_fields = ['total_uploads', 'total_downloads']


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'content_id', 'downloaded_at', 'ip_address']
    list_filter = ['content_type', 'downloaded_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'content_type', 'content_id', 'downloaded_at', 'ip_address']
    ordering = ['-downloaded_at']
    date_hierarchy = 'downloaded_at'


@admin.register(ViewLog)
class ViewLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'content_id', 'viewed_at', 'ip_address']
    list_filter = ['content_type', 'viewed_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'content_type', 'content_id', 'viewed_at', 'ip_address']
    ordering = ['-viewed_at']
    date_hierarchy = 'viewed_at'


# Custom admin site configuration
admin.site.site_header = "Sikshya Kendra Admin"
admin.site.site_title = "Sikshya Kendra Admin Portal"
admin.site.index_title = "Welcome to Sikshya Kendra Administration"

# Register the old RegisteredUser model if needed
@admin.register(RegisteredUser)
class RegisteredUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['-date_joined']
    readonly_fields = ['date_joined']


# Custom admin actions for analytics
class AnalyticsAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def changelist_view(self, request, extra_context=None):
        # Add analytics data to the changelist view
        extra_context = extra_context or {}
        
        # Get trending subjects (based on downloads in last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        trending_subjects = Subject.objects.annotate(
            recent_downloads=Count(
                'syllabi__download_count',
                filter=Q(syllabi__created_at__gte=week_ago)
            ) + Count(
                'notes__download_count',
                filter=Q(notes__created_at__gte=week_ago)
            ) + Count(
                'question_banks__download_count',
                filter=Q(question_banks__created_at__gte=week_ago)
            )
        ).order_by('-recent_downloads')[:5]
        
        extra_context['trending_subjects'] = trending_subjects
        extra_context['total_users'] = UserProfile.objects.count()
        extra_context['total_resources'] = (
            Syllabus.objects.filter(status='approved').count() +
            Note.objects.filter(status='approved').count() +
            QuestionBank.objects.filter(status='approved').count()
        )
        extra_context['pending_approvals'] = (
            Syllabus.objects.filter(status='pending').count() +
            Note.objects.filter(status='pending').count() +
            QuestionBank.objects.filter(status='pending').count()
        )
        
        return super().changelist_view(request, extra_context)
