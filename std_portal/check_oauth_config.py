#!/usr/bin/env python
"""
Script to check if OAuth configuration is properly set up
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'std_portal.settings')
django.setup()

from django.conf import settings

def check_oauth_config():
    """Check OAuth configuration"""
    print("\n" + "="*50)
    print("OAuth Configuration Check")
    print("="*50 + "\n")
    
    # Check Google OAuth
    print("Google OAuth Configuration:")
    print("-" * 30)
    
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_ID != '':
        print(f"✅ GOOGLE_CLIENT_ID is set: {settings.GOOGLE_CLIENT_ID[:20]}...")
    else:
        print("❌ GOOGLE_CLIENT_ID is not set")
        print("   Please add GOOGLE_CLIENT_ID to your .env file")
    
    if settings.GOOGLE_CLIENT_SECRET and settings.GOOGLE_CLIENT_SECRET != '':
        print(f"✅ GOOGLE_CLIENT_SECRET is set: {'*' * 10}")
    else:
        print("❌ GOOGLE_CLIENT_SECRET is not set")
        print("   Please add GOOGLE_CLIENT_SECRET to your .env file")
    
    # Check Facebook OAuth
    print("\nFacebook OAuth Configuration (Optional):")
    print("-" * 30)
    
    if settings.FACEBOOK_APP_ID and settings.FACEBOOK_APP_ID != '':
        print(f"✅ FACEBOOK_APP_ID is set: {settings.FACEBOOK_APP_ID}")
    else:
        print("⚠️  FACEBOOK_APP_ID is not set (optional)")
    
    if settings.FACEBOOK_APP_SECRET and settings.FACEBOOK_APP_SECRET != '':
        print(f"✅ FACEBOOK_APP_SECRET is set: {'*' * 10}")
    else:
        print("⚠️  FACEBOOK_APP_SECRET is not set (optional)")
    
    # Check if .env file exists
    print("\nEnvironment File Check:")
    print("-" * 30)
    
    env_file_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file_path):
        print(f"✅ .env file exists at: {env_file_path}")
    else:
        print(f"❌ .env file not found at: {env_file_path}")
        print("   Please create a .env file based on env_example.txt")
    
    # Check Django settings
    print("\nDjango Settings:")
    print("-" * 30)
    print(f"DEBUG: {settings.DEBUG}")
    print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"SITE_ID: {settings.SITE_ID}")
    
    # OAuth URLs
    print("\nOAuth Redirect URLs (for your reference):")
    print("-" * 30)
    print("Google OAuth Redirect URI:")
    print("  - Local: http://localhost:8000/oauth/google/callback/")
    print("  - Production: https://yourdomain.com/oauth/google/callback/")
    print("\nFacebook OAuth Redirect URI:")
    print("  - Local: http://localhost:8000/oauth/facebook/callback/")
    print("  - Production: https://yourdomain.com/oauth/facebook/callback/")
    
    print("\n" + "="*50)
    print("Configuration check complete!")
    print("="*50 + "\n")
    
    # Summary
    google_configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    facebook_configured = bool(settings.FACEBOOK_APP_ID and settings.FACEBOOK_APP_SECRET)
    
    if google_configured:
        print("✅ Google OAuth is properly configured")
    else:
        print("❌ Google OAuth is not configured. See OAUTH_SETUP.md for instructions")
    
    if facebook_configured:
        print("✅ Facebook OAuth is properly configured")
    else:
        print("⚠️  Facebook OAuth is not configured (optional)")
    
    print("\nFor detailed setup instructions, see OAUTH_SETUP.md")
    
    return google_configured

if __name__ == '__main__':
    try:
        configured = check_oauth_config()
        sys.exit(0 if configured else 1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)