from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Faculty, Subject, Notice, ContactMessage, RegisteredUser, 
    Syllabus, QuestionBank, QuestionBankSolution, Note, Chapter, Viva, TextBook, Practical, Subscription, UserProfile,
    ContributorRequest, DownloadLog, ViewLog, Article, ArticleComment, ArticleLike,
    MCQQuiz, MCQQuestion, MCQOption, MCQUserAnswer, MCQQuizSession
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


@admin.register(QuestionBankSolution)
class QuestionBankSolutionAdmin(ResourceAdmin):
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


@admin.register(Chapter)
class ChapterAdmin(ResourceAdmin):
    list_display = ['title', 'subject', 'subject__faculty', 'subject__level', 'chapter_number', 'status', 'uploaded_by', 'student_count', 'question_count', 'created_at']
    list_filter = ['status', 'subject__faculty', 'subject__level', 'chapter_number', 'created_at']
    search_fields = ['title', 'description', 'subject__name', 'subject__faculty__name']
    ordering = ['subject', 'chapter_number']
    autocomplete_fields = ['subject', 'uploaded_by']
    readonly_fields = ['download_count', 'view_count', 'student_count', 'question_count', 'created_at', 'updated_at']
    list_editable = ['chapter_number', 'status']
    
    fieldsets = (
        ('Chapter Information', {
            'fields': ('subject', 'title', 'description', 'chapter_number')
        }),
        ('File Upload', {
            'fields': ('file',)
        }),
        ('Status & Statistics', {
            'fields': ('status', 'uploaded_by', 'student_count', 'question_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Download/View Stats', {
            'fields': ('download_count', 'view_count'),
            'classes': ('collapse',)
        }),
    )


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


@admin.register(Viva)
class VivaAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'difficulty_level', 'status', 'uploaded_by', 'view_count', 'created_at']
    list_filter = ['status', 'difficulty_level', 'subject__faculty', 'created_at']
    search_fields = ['title', 'description', 'question', 'answer', 'subject__name']
    list_editable = ['status', 'difficulty_level']
    ordering = ['-created_at']
    autocomplete_fields = ['subject', 'uploaded_by']
    readonly_fields = ['view_count', 'last_viewed', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subject', 'description', 'status')
        }),
        ('Viva Content', {
            'fields': ('question', 'answer', 'difficulty_level')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'tags', 'view_count', 'last_viewed'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(TextBook)
class TextBookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'subject', 'publisher', 'status', 'uploaded_by', 'download_count', 'view_count', 'created_at']
    list_filter = ['status', 'subject__faculty', 'created_at']
    search_fields = ['title', 'author', 'description', 'isbn', 'publisher', 'subject__name']
    list_editable = ['status']
    ordering = ['-created_at']
    autocomplete_fields = ['subject', 'uploaded_by']
    readonly_fields = ['download_count', 'view_count', 'last_viewed', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subject', 'description', 'status')
        }),
        ('Book Details', {
            'fields': ('author', 'isbn', 'edition', 'publisher')
        }),
        ('File', {
            'fields': ('file',)
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'tags', 'download_count', 'view_count', 'last_viewed'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Practical)
class PracticalAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'difficulty_level', 'estimated_time', 'status', 'uploaded_by', 'download_count', 'view_count', 'created_at']
    list_filter = ['status', 'difficulty_level', 'subject__faculty', 'created_at']
    search_fields = ['title', 'description', 'objective', 'materials_required', 'subject__name']
    list_editable = ['status', 'difficulty_level']
    ordering = ['-created_at']
    autocomplete_fields = ['subject', 'uploaded_by']
    readonly_fields = ['download_count', 'view_count', 'last_viewed', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subject', 'description', 'status')
        }),
        ('Practical Details', {
            'fields': ('objective', 'materials_required', 'difficulty_level', 'estimated_time')
        }),
        ('Content', {
            'fields': ('procedure', 'expected_result')
        }),
        ('File', {
            'fields': ('file',)
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'tags', 'download_count', 'view_count', 'last_viewed'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


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
            QuestionBank.objects.filter(status='approved').count() +
            Chapter.objects.filter(status='approved').count()
        )
        extra_context['pending_approvals'] = (
            Syllabus.objects.filter(status='pending').count() +
            Note.objects.filter(status='pending').count() +
            QuestionBank.objects.filter(status='pending').count() +
            Chapter.objects.filter(status='pending').count()
        )
        
        return super().changelist_view(request, extra_context)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'view_count', 'like_count', 'comment_count', 'created_at', 'published_at']
    list_filter = ['status', 'category', 'created_at', 'published_at', 'author']
    search_fields = ['title', 'content', 'excerpt', 'author__username', 'author__first_name', 'author__last_name']
    list_editable = ['status']
    ordering = ['-created_at']
    autocomplete_fields = ['author', 'reviewed_by']
    readonly_fields = ['view_count', 'like_count', 'comment_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    actions = ['approve_articles', 'reject_articles', 'unpublish_articles']
    
    fieldsets = (
        ('Article Information', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'category', 'featured_image', 'tags')
        }),
        ('Author & Status', {
            'fields': ('author', 'status', 'submitted_at', 'published_at')
        }),
        ('Review Information', {
            'fields': ('reviewed_at', 'reviewed_by', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Engagement Metrics', {
            'fields': ('view_count', 'like_count', 'comment_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def approve_articles(self, request, queryset):
        for article in queryset.filter(status='pending'):
            article.status = 'approved'
            article.published_at = timezone.now()
            article.reviewed_at = timezone.now()
            article.reviewed_by = request.user
            article.save()
    approve_articles.short_description = "Approve selected articles"
    
    def reject_articles(self, request, queryset):
        for article in queryset.filter(status='pending'):
            article.status = 'rejected'
            article.reviewed_at = timezone.now()
            article.reviewed_by = request.user
            article.save()
    reject_articles.short_description = "Reject selected articles"
    
    def unpublish_articles(self, request, queryset):
        for article in queryset.filter(status='approved'):
            article.published_at = None
            article.save()
    unpublish_articles.short_description = "Unpublish selected articles"


@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ['article', 'author', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at', 'article__status']
    search_fields = ['content', 'author__username', 'article__title']
    list_editable = ['is_approved']
    ordering = ['-created_at']
    autocomplete_fields = ['article', 'author', 'parent']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    actions = ['approve_comments', 'disapprove_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_comments.short_description = "Disapprove selected comments"


@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'created_at']
    list_filter = ['created_at', 'article__status']
    search_fields = ['article__title', 'user__username']
    ordering = ['-created_at']
    autocomplete_fields = ['article', 'user']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


# MCQ Admin Classes
class MCQOptionInline(admin.TabularInline):
    model = MCQOption
    extra = 1
    fields = ['option_text', 'is_correct']
    ordering = ['id']


@admin.register(MCQQuestion)
class MCQQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'quiz', 'faculty', 'created_by', 'published', 'options_count', 'created_at']
    list_filter = ['published', 'created_at', 'quiz__faculty', 'created_by']
    search_fields = ['question_text', 'quiz__title', 'created_by__username']
    ordering = ['-created_at']
    inlines = [MCQOptionInline]
    autocomplete_fields = ['quiz', 'created_by']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Question Details', {
            'fields': ('quiz', 'question_text', 'published')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_text_short(self, obj):
        return obj.question_text[:80] + '...' if len(obj.question_text) > 80 else obj.question_text
    question_text_short.short_description = 'Question'
    
    def faculty(self, obj):
        return obj.quiz.faculty.name
    faculty.short_description = 'Faculty'
    
    def options_count(self, obj):
        return obj.options.count()
    options_count.short_description = 'Options'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MCQOption)
class MCQOptionAdmin(admin.ModelAdmin):
    list_display = ['option_text_short', 'question', 'is_correct', 'created_at']
    list_filter = ['is_correct', 'created_at', 'question__quiz__faculty']
    search_fields = ['option_text', 'question__question_text']
    ordering = ['question', 'id']
    autocomplete_fields = ['question']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def option_text_short(self, obj):
        return obj.option_text[:50] + '...' if len(obj.option_text) > 50 else obj.option_text
    option_text_short.short_description = 'Option Text'


@admin.register(MCQUserAnswer)
class MCQUserAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'question_short', 'selected_option_short', 'is_correct', 'submitted_at']
    list_filter = ['is_correct', 'submitted_at', 'question__quiz__faculty']
    search_fields = ['user__username', 'question__question_text', 'selected_option__option_text']
    ordering = ['-submitted_at']
    autocomplete_fields = ['user', 'question', 'selected_option']
    readonly_fields = ['submitted_at']
    date_hierarchy = 'submitted_at'
    
    def question_short(self, obj):
        return obj.question.question_text[:50] + '...' if len(obj.question.question_text) > 50 else obj.question.question_text
    question_short.short_description = 'Question'
    
    def selected_option_short(self, obj):
        return obj.selected_option.option_text[:30] + '...' if len(obj.selected_option.option_text) > 30 else obj.selected_option.option_text
    selected_option_short.short_description = 'Selected Option'


@admin.register(MCQQuizSession)
class MCQQuizSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score_percentage', 'correct_answers', 'total_questions', 'completed_at']
    list_filter = ['completed_at', 'quiz__faculty', 'score_percentage']
    search_fields = ['user__username', 'quiz__title']
    ordering = ['-completed_at']
    autocomplete_fields = ['user', 'quiz']
    readonly_fields = ['started_at', 'completed_at', 'score_percentage']
    date_hierarchy = 'completed_at'
    
    fieldsets = (
        ('Session Details', {
            'fields': ('user', 'quiz', 'questions')
        }),
        ('Results', {
            'fields': ('total_questions', 'correct_answers', 'score_percentage', 'started_at', 'completed_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(completed_at__isnull=False)


@admin.register(MCQQuiz)
class MCQQuizAdmin(admin.ModelAdmin):
    list_display = ['faculty', 'quiz_number', 'title', 'question_count', 'is_active', 'created_by', 'created_at']
    list_filter = ['faculty', 'is_active', 'created_at']
    search_fields = ['title', 'faculty__name']
    list_editable = ['is_active']
    ordering = ['faculty', 'quiz_number']
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('faculty', 'created_by')
