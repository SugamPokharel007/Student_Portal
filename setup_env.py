#!/usr/bin/env python
"""
Environment Setup Script for Student Portal
This script helps you create a .env file with Gmail credentials for password reset.
"""

import os
from pathlib import Path

def main():
    print("=" * 60)
    print("🔧 STUDENT PORTAL - ENVIRONMENT SETUP")
    print("=" * 60)
    print()
    
    # Check if .env already exists
    env_path = Path('.env')
    if env_path.exists():
        print("⚠️  .env file already exists!")
        overwrite = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ Setup cancelled. Existing .env file preserved.")
            return
    
    print("📧 Gmail Configuration for Password Reset")
    print("   This will enable real email sending for password reset feature")
    print()
    
    # Get Gmail credentials
    email = input("Enter your Gmail address: ").strip()
    if not email or '@gmail.com' not in email:
        print("❌ Please enter a valid Gmail address")
        return
    
    print()
    print("🔑 Gmail App Password Setup:")
    print("1. Go to https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification if not already enabled")
    print("3. Go to 'App passwords' section")
    print("4. Generate a new app password for 'Mail'")
    print("5. Copy the 16-character password (e.g., abcd efgh ijkl mnop)")
    print()
    
    app_password = input("Enter your 16-character app password: ").strip().replace(' ', '')
    if len(app_password) != 16:
        print("❌ App password must be 16 characters long")
        return
    
    # Create .env content
    env_content = f"""# =============================================================================
# ENVIRONMENT VARIABLES FOR STUDENT PORTAL
# =============================================================================
# 
# This file contains sensitive information - DO NOT commit to version control!
# The .env file should be in the project root (same folder as manage.py)
# =============================================================================

# Django Settings
SECRET_KEY=django-insecure-3r+4139faw00sr0r=j4sm(mwz&4dfn#e%kqim*%1zm_a_t#1kp
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# =============================================================================
# EMAIL CONFIGURATION FOR PASSWORD RESET
# =============================================================================
# 
# Gmail SMTP Settings for sending password reset emails
# Get your app password from: https://myaccount.google.com/security
# 
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER={email}
EMAIL_HOST_PASSWORD={app_password}
DEFAULT_FROM_EMAIL={email}

# =============================================================================
# OAUTH CREDENTIALS (Optional)
# =============================================================================
# 
# Social login credentials (if using Google/Facebook login)
# 
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
"""
    
    # Write .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print()
        print("✅ .env file created successfully!")
        print()
        print("📋 Next Steps:")
        print("1. Restart your Django server: python manage.py runserver")
        print("2. Test the configuration: python test_email_config.py")
        print("3. Test password reset on the website")
        print()
        print("🔒 Security Notes:")
        print("- The .env file contains sensitive information")
        print("- It's already added to .gitignore (won't be committed)")
        print("- Keep this file secure and never share it")
        print()
        print("🎉 Password reset feature is now ready to use!")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    main()
