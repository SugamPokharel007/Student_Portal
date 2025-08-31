#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'std_portal.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser():
    """Create a superuser with default credentials"""
    username = 'admin'
    email = 'admin@sikshyakendra.com'
    password = 'admin123'
    
    if User.objects.filter(username=username).exists():
        print(f"Superuser '{username}' already exists!")
        return
    
    try:
        user = User.objects.create_superuser(username, email, password)
        print(f"Superuser created successfully!")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print("\nYou can now login to the admin panel at: http://127.0.0.1:8000/admin/")
    except Exception as e:
        print(f"Error creating superuser: {e}")

if __name__ == '__main__':
    create_superuser() 