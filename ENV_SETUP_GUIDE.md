# 🔧 Environment Variables Setup Guide

## Quick Setup

### Automated Setup (Recommended)
```bash
python setup_env.py
```

### Manual Setup
1. Create `.env` file in project root (same folder as `manage.py`)
2. Add your Gmail credentials:
```env
EMAIL_HOST_USER=yourgmail@gmail.com
EMAIL_HOST_PASSWORD=your_app_password_here
DEFAULT_FROM_EMAIL=yourgmail@gmail.com
```
3. Restart Django server

## Gmail App Password Setup
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Go to "App passwords" section
4. Generate a new app password for "Mail"
5. Use the 16-character password in your `.env` file

## Testing
```bash
python test_email_config.py
```

## Security
- `.env` file is ignored by Git (not committed)
- App passwords used instead of regular passwords
- Automatic loading by Django
