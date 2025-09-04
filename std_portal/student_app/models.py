from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.validators import FileExtensionValidator
from taggit.managers import TaggableManager
from django.db.models import Count, Q
from django.urls import reverse

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

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def increment_view(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])


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

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def increment_view(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])


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

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def increment_view(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])


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

    def __str__(self):
        return self.user.username

    def get_role_display_name(self):
        return dict(self.ROLE_CHOICES)[self.role]

    def can_upload(self):
        """Check if user can upload content"""
        return self.role in ['contributor', 'admin'] and self.is_contributor_approved

    def increment_uploads(self):
        self.total_uploads += 1
        self.save(update_fields=['total_uploads'])

    def increment_downloads(self):
        self.total_downloads += 1
        self.save(update_fields=['total_downloads'])


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

# NOTE: After these changes, run 'python manage.py makemigrations student_app' and 'python manage.py migrate' to apply the new models and fields.