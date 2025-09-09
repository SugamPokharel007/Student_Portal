from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta
from django.conf import settings
from django.core.validators import FileExtensionValidator
from taggit.managers import TaggableManager
from django.db.models import Count, Q
from django.urls import reverse
from django.core.exceptions import ValidationError

# Create your models here.
class Faculty(models.Model):
    ACADEMIC_STRUCTURE_CHOICES = [
        ('semester', 'Semester System'),
        ('year', 'Year System'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=50, unique=True, null=True, blank=True, help_text="URL-friendly name (e.g., 'bsccsit', 'bba', 'bbs')")
    description = models.TextField(blank=True)
    academic_structure = models.CharField(max_length=10, choices=ACADEMIC_STRUCTURE_CHOICES, default='semester')
    total_levels = models.PositiveIntegerField(default=8, help_text="Number of semesters (8) or years (4)")
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Faculties"

    def get_level_display_name(self, level_number):
        """Get display name for level (semester/year)"""
        if self.academic_structure == 'semester':
            return f"{level_number}{self._get_ordinal_suffix(level_number)} Semester"
        else:
            return f"{level_number}{self._get_ordinal_suffix(level_number)} Year"
    
    def _get_ordinal_suffix(self, number):
        """Get ordinal suffix for numbers"""
        if 10 <= number % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')
        return suffix


class Subject(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='subjects', null=True, blank=True)
    level = models.PositiveIntegerField(null=True, blank=True, help_text="Semester number (1-8) or Year number (1-4)")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    tags = TaggableManager(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        if self.faculty:
            level_name = self.faculty.get_level_display_name(self.level) if self.level else "No Level"
            return f"{self.name} - {self.faculty.name} ({level_name})"
        else:
            level_name = f"Level {self.level}" if self.level else "No Level"
            return f"{self.name} - No Faculty ({level_name})"

    def get_absolute_url(self):
        return reverse('subject_detail', kwargs={'subject_id': self.id})

    @property
    def total_resources(self):
        """Get total number of approved resources for this subject"""
        return (
            self.syllabi.filter(status='approved').count() +
            self.question_banks.filter(status='approved').count() +
            self.notes.filter(status='approved').count()
        )

    class Meta:
        # unique_together = ['name', 'faculty', 'level']  # Temporarily commented out
        ordering = ['faculty', 'level', 'name']


class Notice(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    is_general = models.BooleanField(default=True)  # True for general notices, False for subject-specific
    is_important = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


# contact form submission 
class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200, default="General Inquiry")
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    admin_response = models.TextField(blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

    class Meta:
        ordering = ['-submitted_at']


#registered user displaying
class RegisteredUser(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class ContributorRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    reason = models.TextField()
    experience = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Contributor request from {self.user.username}"

    class Meta:
        ordering = ['-submitted_at']


class Syllabus(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='syllabi')
    title = models.CharField(max_length=200)
    content = models.TextField()
    file = models.FileField(
        upload_to='syllabus/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt'])]
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='syllabi')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager(blank=True)
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True, help_text="Last time this resource was viewed")

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def increment_view(self):
        self.view_count += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed'])


class QuestionBank(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='question_banks')
    title = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='question_banks/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt'])]
    )
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='question_banks')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager(blank=True)
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True, help_text="Last time this resource was viewed")

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def increment_view(self):
        self.view_count += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed'])


class QuestionBankSolution(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='question_bank_solutions')
    title = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='question_bank_solutions/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt'])]
    )
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='question_bank_solutions')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager(blank=True)
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True, help_text="Last time this resource was viewed")

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def increment_view(self):
        self.view_count += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed'])

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Question Bank Solution'
        verbose_name_plural = 'Question Bank Solutions'


class Note(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='notes/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx'])]
    )
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='notes')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager(blank=True)
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True, help_text="Last time this resource was viewed")

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def increment_view(self):
        self.view_count += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed'])


class Chapter(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    chapter_number = models.PositiveIntegerField(help_text="Chapter number (1, 2, 3, etc.)")
    file = models.FileField(
        upload_to='chapters/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx'])]
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='chapters')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager(blank=True)
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True, help_text='Last time this resource was viewed')
    student_count = models.PositiveIntegerField(default=0, help_text="Number of students who accessed this chapter")
    question_count = models.PositiveIntegerField(default=0, help_text="Number of questions available for this chapter")

    def __str__(self):
        return f"{self.subject.name} - Chapter {self.chapter_number}: {self.title}"

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def increment_view(self):
        self.view_count += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed'])

    def increment_student(self):
        self.student_count += 1
        self.save(update_fields=['student_count'])

    class Meta:
        ordering = ['chapter_number']
        unique_together = ['subject', 'chapter_number']


class Viva(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='vivas')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    question = models.TextField(help_text="Viva question or topic")
    answer = models.TextField(help_text="Expected answer or explanation")
    difficulty_level = models.CharField(
        max_length=20, 
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], 
        default='medium'
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='vivas')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager(blank=True)
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True, help_text='Last time this resource was viewed')

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    def increment_view(self):
        self.view_count += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed'])

    class Meta:
        ordering = ['-created_at']


class TextBook(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='textbooks')
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to='textbooks/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'epub', 'mobi'])]
    )
    isbn = models.CharField(max_length=20, blank=True, help_text="ISBN number if available")
    edition = models.CharField(max_length=50, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='textbooks')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager(blank=True)
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True, help_text='Last time this resource was viewed')

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def increment_view(self):
        self.view_count += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed'])

    class Meta:
        ordering = ['-created_at']


class Practical(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='practicals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    objective = models.TextField(help_text="Objective of the practical")
    materials_required = models.TextField(blank=True, help_text="Materials or software required")
    procedure = models.TextField(help_text="Step-by-step procedure")
    expected_result = models.TextField(blank=True, help_text="Expected result or output")
    file = models.FileField(
        upload_to='practicals/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'zip', 'rar'])],
        blank=True,
        null=True
    )
    difficulty_level = models.CharField(
        max_length=20, 
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], 
        default='medium'
    )
    estimated_time = models.PositiveIntegerField(blank=True, null=True, help_text="Estimated time in minutes")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='practicals')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager(blank=True)
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True, help_text='Last time this resource was viewed')

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def increment_view(self):
        self.view_count += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed'])

    class Meta:
        ordering = ['-created_at']


class Subscription(models.Model):
    SUBSCRIPTION_TYPES = (
        ('monthly', 'Monthly'),
        ('semi_yearly', 'Semi-Yearly'),
        ('yearly', 'Yearly'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.subscription_type}"
    
    def save(self, *args, **kwargs):
        # Calculate end date based on subscription type
        if self.subscription_type == 'monthly':
            self.end_date = self.start_date + timedelta(days=30)
        elif self.subscription_type == 'semi_yearly':
            self.end_date = self.start_date + timedelta(days=180)
        elif self.subscription_type == 'yearly':
            self.end_date = self.start_date + timedelta(days=365)
        
        # Check if subscription is still active
        if timezone.now() > self.end_date:
            self.is_active = False
        
        super().save(*args, **kwargs)

    @property
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if self.is_active and self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0

    @property
    def is_expiring_soon(self):
        """Check if subscription expires within 7 days"""
        return self.days_remaining <= 7 and self.days_remaining > 0


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('contributor', 'Contributor'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_contributor_approved = models.BooleanField(default=False)
    contributor_since = models.DateTimeField(null=True, blank=True)
    total_uploads = models.PositiveIntegerField(default=0)
    total_downloads = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    def get_role_display_name(self):
        return dict(self.ROLE_CHOICES)[self.role]

    def can_upload(self):
        """Check if user can upload content"""
        return self.role in ['contributor', 'admin'] and self.is_contributor_approved

    def increment_uploads(self):
        self.total_uploads += 1
        self.save(update_fields=['total_uploads', 'updated_at'])

    def increment_downloads(self):
        self.total_downloads += 1
        self.save(update_fields=['total_downloads', 'updated_at'])


class DownloadLog(models.Model):
    """Track user downloads for analytics"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=20)  # 'syllabus', 'note', 'questionbank'
    content_id = models.PositiveIntegerField()
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-downloaded_at']


class ViewLog(models.Model):
    """Track user views for analytics"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    content_type = models.CharField(max_length=20)  # 'syllabus', 'note', 'questionbank'
    content_id = models.PositiveIntegerField()
    viewed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-viewed_at']


# Signal handlers for automatic actions
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

@receiver(post_save, sender=ContributorRequest)
def handle_contributor_approval(sender, instance, **kwargs):
    """Handle contributor request approval"""
    if instance.status == 'approved' and not instance.user.userprofile.is_contributor_approved:
        profile = instance.user.userprofile
        profile.role = 'contributor'
        profile.is_contributor_approved = True
        profile.contributor_since = timezone.now()
        profile.save()

# Article Models
class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('technology', 'Technology'),
        ('general', 'General'),
        ('tutorial', 'Tutorial'),
        ('news', 'News'),
        ('opinion', 'Opinion'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=500, blank=True, help_text="Short description of the article")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
    featured_image = models.ImageField(upload_to='articles/images/', null=True, blank=True)
    tags = TaggableManager(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_articles')
    admin_notes = models.TextField(blank=True, help_text="Admin notes for approval/rejection")
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'slug': self.slug})
    
    def is_published(self):
        return self.status == 'approved' and self.published_at is not None
    
    def can_edit(self, user):
        return user == self.author or user.is_superuser
    
    def can_delete(self, user):
        return user == self.author or user.is_superuser


class ArticleComment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Article Comment'
        verbose_name_plural = 'Article Comments'
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.article.title}"
    
    def is_reply(self):
        return self.parent is not None


class ArticleLike(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['article', 'user']
        verbose_name = 'Article Like'
        verbose_name_plural = 'Article Likes'
    
    def __str__(self):
        return f"{self.user.username} likes {self.article.title}"


# MCQ Models
class MCQQuiz(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='mcq_quizzes')
    quiz_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200, default="")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_mcq_quizzes')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'MCQ Quiz'
        verbose_name_plural = 'MCQ Quizzes'
        unique_together = ['faculty', 'quiz_number']
        ordering = ['faculty', 'quiz_number']
    
    def __str__(self):
        return f"{self.faculty.name} - Quiz {self.quiz_number}: {self.title}"
    
    @property
    def display_name(self):
        return f"Quiz {self.quiz_number}: {self.title}" if self.title else f"Quiz {self.quiz_number}"


class MCQQuestion(models.Model):
    quiz = models.ForeignKey(MCQQuiz, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    question_text = models.TextField(help_text="Enter the question text")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_mcq_questions')
    published = models.BooleanField(default=False, help_text="Only published questions are visible to students")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'MCQ Question'
        verbose_name_plural = 'MCQ Questions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.quiz.display_name} - {self.question_text[:50]}..."
    
    @property
    def is_valid(self):
        """Check if question has valid options for publishing"""
        if not self.pk:
            return False  # Can't validate if not saved yet
        
        options_count = self.options.count()
        correct_options_count = self.options.filter(is_correct=True).count()
        return options_count >= 2 and correct_options_count == 1
    
    def clean(self):
        super().clean()
        if self.published and self.pk:
            # Only validate if question is already saved (has primary key)
            # Check if question has at least 2 options
            if self.options.count() < 2:
                raise ValidationError("A published question must have at least 2 options.")
            
            # Check if exactly one option is marked as correct
            correct_options = self.options.filter(is_correct=True).count()
            if correct_options != 1:
                raise ValidationError("A published question must have exactly one correct option.")


class MCQOption(models.Model):
    question = models.ForeignKey(MCQQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500, help_text="Enter the option text")
    is_correct = models.BooleanField(default=False, help_text="Mark this option as correct")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'MCQ Option'
        verbose_name_plural = 'MCQ Options'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.question.question_text[:30]}... - {self.option_text[:30]}..."
    
    def clean(self):
        super().clean()
        if self.is_correct and self.question_id:
            # Check if there's already a correct option for this question
            existing_correct = MCQOption.objects.filter(
                question_id=self.question_id, 
                is_correct=True
            ).exclude(id=self.id)
            if existing_correct.exists():
                raise ValidationError("Only one option can be marked as correct per question.")


class MCQUserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mcq_answers')
    question = models.ForeignKey(MCQQuestion, on_delete=models.CASCADE, related_name='user_answers')
    selected_option = models.ForeignKey(MCQOption, on_delete=models.CASCADE, related_name='user_selections', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'MCQ User Answer'
        verbose_name_plural = 'MCQ User Answers'
        unique_together = ['user', 'question']  # One answer per user per question
        ordering = ['-submitted_at']
    
    def __str__(self):
        option_text = self.selected_option.option_text[:30] if self.selected_option else "No Answer"
        return f"{self.user.username} - {self.question.question_text[:30]}... - {option_text}..."
    
    def save(self, *args, **kwargs):
        # Automatically set is_correct based on selected option
        if self.selected_option:
            self.is_correct = self.selected_option.is_correct
        else:
            self.is_correct = False  # Unanswered questions are marked as incorrect
        super().save(*args, **kwargs)


class MCQQuizSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mcq_sessions')
    quiz = models.ForeignKey(MCQQuiz, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    questions = models.ManyToManyField(MCQQuestion, related_name='quiz_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    score_percentage = models.FloatField(default=0.0)
    
    class Meta:
        verbose_name = 'MCQ Quiz Session'
        verbose_name_plural = 'MCQ Quiz Sessions'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.display_name} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"
    
    def calculate_score(self):
        """Calculate and update the quiz score"""
        total_questions = self.questions.count()
        if total_questions == 0:
            return
        
        correct_answers = MCQUserAnswer.objects.filter(
            user=self.user,
            question__in=self.questions.all(),
            is_correct=True
        ).count()
        
        self.total_questions = total_questions
        self.correct_answers = correct_answers
        self.score_percentage = (correct_answers / total_questions) * 100
        self.completed_at = timezone.now()
        self.save()


# NOTE: After these changes, run 'python manage.py makemigrations student_app' and 'python manage.py migrate' to apply the new models and fields.