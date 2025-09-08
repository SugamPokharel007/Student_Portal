#!/usr/bin/env python
"""
Test Email Configuration Script
This script tests if the email configuration is working properly.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'std_portal.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

User = get_user_model()

def test_email_config():
    print("=" * 60)
    print("🧪 TESTING EMAIL CONFIGURATION")
    print("=" * 60)
    print()
    
    # Display current configuration
    print("📧 Current Email Configuration:")
    print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"   EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"   EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"   EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
    print(f"   EMAIL_HOST_PASSWORD: {'*' * len(getattr(settings, 'EMAIL_HOST_PASSWORD', '')) if getattr(settings, 'EMAIL_HOST_PASSWORD', '') else 'Not set'}")
    print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print()
    
    # Check if using SMTP or console
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
        print("✅ Using SMTP backend - emails will be sent to real addresses")
        
        # Test email sending
        test_email = input("📧 Enter a test email address to send a test email: ").strip()
        if test_email:
            try:
                send_mail(
                    subject='Test Email from Sikshya Kendra',
                    message='This is a test email to verify email configuration is working properly.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[test_email],
                    fail_silently=False,
                )
                print(f"✅ Test email sent successfully to {test_email}!")
                print("   Check your inbox for the test email.")
            except Exception as e:
                print(f"❌ Failed to send test email: {str(e)}")
                print("   Please check your Gmail credentials and app password.")
    else:
        print("⚠️  Using console backend - emails will be printed to console")
        print("   To enable real email sending, add your Gmail credentials to .env file")
        
        # Test console email
        try:
            send_mail(
                subject='Test Email from Sikshya Kendra (Console)',
                message='This is a test email - check console output.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['test@example.com'],
                fail_silently=False,
            )
            print("✅ Test email sent to console - check the output above")
        except Exception as e:
            print(f"❌ Failed to send test email: {str(e)}")
    
    print()
    print("🔧 To configure Gmail SMTP:")
    print("1. Run: python setup_gmail_password_reset.py")
    print("2. Or manually create .env file with your Gmail credentials")
    print("3. Restart Django server")

def check_env_file():
    """Check if .env file exists and show its contents"""
    print("\n📁 Checking .env file:")
    
    env_path = Path('.env')
    if env_path.exists():
        print("✅ .env file found")
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        print("   Contents:")
        for line in lines:
            if line.strip() and not line.startswith('#'):
                if 'PASSWORD' in line or 'SECRET' in line:
                    key, value = line.split('=', 1)
                    print(f"   {key.strip()}={value.strip()[:3]}...")
                else:
                    print(f"   {line.strip()}")
    else:
        print("❌ .env file not found")
        print("   Create one using: python setup_env.py")

if __name__ == "__main__":
    check_env_file()
    test_email_config()
