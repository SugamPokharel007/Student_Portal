#!/usr/bin/env python
"""
Script to help set up the .env file for OAuth configuration
"""
import os
import sys

def setup_env():
    """Help user set up .env file"""
    print("\n" + "="*50)
    print("OAuth Environment Setup Helper")
    print("="*50 + "\n")
    
    env_file_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_file_path):
        response = input(".env file already exists. Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    print("\nLet's set up your OAuth credentials.")
    print("Leave blank to skip (you can add them later).\n")
    
    # Google OAuth
    print("Google OAuth Setup:")
    print("-" * 30)
    print("To get Google credentials:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create OAuth 2.0 Client ID")
    print("3. Add redirect URI: http://localhost:8000/oauth/google/callback/\n")
    
    google_client_id = input("Enter your Google Client ID (or press Enter to skip): ").strip()
    google_client_secret = input("Enter your Google Client Secret (or press Enter to skip): ").strip()
    
    # Facebook OAuth (optional)
    print("\nFacebook OAuth Setup (Optional):")
    print("-" * 30)
    use_facebook = input("Do you want to set up Facebook OAuth? (y/N): ")
    
    facebook_app_id = ""
    facebook_app_secret = ""
    
    if use_facebook.lower() == 'y':
        print("\nTo get Facebook credentials:")
        print("1. Go to https://developers.facebook.com/")
        print("2. Create a new app")
        print("3. Add redirect URI: http://localhost:8000/oauth/facebook/callback/\n")
        
        facebook_app_id = input("Enter your Facebook App ID: ").strip()
        facebook_app_secret = input("Enter your Facebook App Secret: ").strip()
    
    # Create .env file
    env_content = f"""# Django Settings
SECRET_KEY=django-insecure-3r+4139faw00sr0r=j4sm(mwz&4dfn#e%kqim*%1zm_a_t#1kp
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google OAuth Credentials
GOOGLE_CLIENT_ID={google_client_id}
GOOGLE_CLIENT_SECRET={google_client_secret}

# Facebook OAuth Credentials (Optional)
FACEBOOK_APP_ID={facebook_app_id}
FACEBOOK_APP_SECRET={facebook_app_secret}

# Database Settings (for production)
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=your_database_name
# DB_USER=your_database_user
# DB_PASSWORD=your_database_password
# DB_HOST=localhost
# DB_PORT=5432

# Email Settings (for password reset and notifications)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-specific-password
"""
    
    try:
        with open(env_file_path, 'w') as f:
            f.write(env_content)
        
        print("\n" + "="*50)
        print("✅ .env file created successfully!")
        print("="*50 + "\n")
        
        if google_client_id and google_client_secret:
            print("✅ Google OAuth credentials saved")
        else:
            print("⚠️  Google OAuth credentials not set")
            print("   You can add them later by editing the .env file")
        
        if facebook_app_id and facebook_app_secret:
            print("✅ Facebook OAuth credentials saved")
        else:
            print("ℹ️  Facebook OAuth not configured (optional)")
        
        print("\nNOTE: Never commit the .env file to version control!")
        print("Make sure .env is in your .gitignore file.")
        
        print("\nTo test your configuration, run:")
        print("  python check_oauth_config.py")
        
    except Exception as e:
        print(f"\n❌ Error creating .env file: {str(e)}")
        return

if __name__ == '__main__':
    setup_env()