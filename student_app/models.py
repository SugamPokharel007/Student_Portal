from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Create your models here.
class Subject(models.Model):
    name = models.CharField(max_length=100)
    year = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} - {self.year}"


class Notice(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    is_general = models.BooleanField(default=True)  # True for general notices, False for subject-specific

    def __str__(self):
        return self.title


# contact form submission 

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}"

#registered user displaying


class RegisteredUser(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class Syllabus(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    file = models.FileField(upload_to='syllabus/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

class QuestionBank(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='question_banks/')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

class Note(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='notes/')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

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