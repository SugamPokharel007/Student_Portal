from django.db import models

# Create your models here.
class Subject(models.Model):
    YEAR_CHOICES = [
        ('first', 'First Year'),
        ('second', 'Second Year'),
        ('third', 'Third Year'),
        ('fourth', 'Fourth Year'),
    ]
    
    name = models.CharField(max_length=200)  # Name of the subject
    year = models.CharField(choices=YEAR_CHOICES, max_length=10)  # Year for the subject
    image = models.ImageField(upload_to='subjects/', blank=True, null=True)  # Subject image


    
    def __str__(self):
        return self.name


class Notice(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# contact form submission 

class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

#registered user displaying


class RegisteredUser(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username