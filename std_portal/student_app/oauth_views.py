import requests
from django.shortcuts import redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from urllib.parse import urlencode
import json
import re

def google_oauth_callback(request):
    """Handle Google OAuth callback"""
    # Check for error parameters from Google
    error = request.GET.get('error')
    if error:
        error_description = request.GET.get('error_description', 'Unknown error')
        messages.error(request, f'Google authentication failed: {error_description}')
        return redirect('login')
    
    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Authentication failed. No authorization code received.')
        return redirect('login')
    
    # Check if Google OAuth is configured
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.error(request, 'Google OAuth is not configured. Please contact administrator.')
        return redirect('login')
    
    try:
        # Exchange code for access token
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': request.build_absolute_uri('/oauth/google/callback/')
        }
        
        token_response = requests.post(token_url, data=token_data, timeout=10)
        if token_response.status_code != 200:
            error_data = token_response.json() if token_response.content else {}
            error_message = error_data.get('error_description', error_data.get('error', 'Failed to get access token'))
            messages.error(request, f'Google authentication failed: {error_message}')
            return redirect('login')
        
        token_info = token_response.json()
        
        # Verify we got an access token
        if 'access_token' not in token_info:
            messages.error(request, 'Failed to get access token from Google.')
            return redirect('login')
        
        # Get user info from Google
        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f"Bearer {token_info['access_token']}"}
        user_response = requests.get(user_info_url, headers=headers, timeout=10)
        
        if user_response.status_code != 200:
            messages.error(request, 'Failed to get user information from Google.')
            return redirect('login')
        
        user_info = user_response.json()
        
        # Create or get user
        email = user_info.get('email')
        if not email:
            messages.error(request, 'Email not provided by Google.')
            return redirect('login')
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user
            username = email.split('@')[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', '')
            )
            user.set_unusable_password()
            user.save()
        
        # Log in user with proper backend
        from django.contrib.auth import login
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
        
        # Redirect based on user type
        if user.is_superuser:
            return redirect('admin_dashboard')
        else:
            from .models import UserProfile
            user_profile, _ = UserProfile.objects.get_or_create(user=user)
            if not user_profile.faculty:
                return redirect('select_faculty')
            return redirect('dashboard')
            
    except requests.exceptions.Timeout:
        messages.error(request, 'Connection to Google timed out. Please try again.')
        return redirect('login')
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Network error during authentication: {str(e)}')
        return redirect('login')
    except json.JSONDecodeError:
        messages.error(request, 'Invalid response from Google. Please try again.')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('login')

def facebook_oauth_callback(request):
    """Handle Facebook OAuth callback"""
    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Authentication failed. Please try again.')
        return redirect('login')
    
    try:
        # Exchange code for access token
        token_url = 'https://graph.facebook.com/v13.0/oauth/access_token'
        token_data = {
            'client_id': settings.FACEBOOK_APP_ID,
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'code': code,
            'redirect_uri': request.build_absolute_uri('/oauth/facebook/callback/')
        }
        
        token_response = requests.get(token_url, params=token_data)
        token_response.raise_for_status()
        token_info = token_response.json()
        
        # Get user info from Facebook
        user_info_url = 'https://graph.facebook.com/v13.0/me'
        params = {
            'fields': 'id,name,email,first_name,last_name',
            'access_token': token_info['access_token']
        }
        user_response = requests.get(user_info_url, params=params)
        user_response.raise_for_status()
        user_info = user_response.json()
        
        # Create or get user
        email = user_info.get('email')
        if not email:
            messages.error(request, 'Email not provided by Facebook.')
            return redirect('login')
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user
            username = email.split('@')[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=user_info.get('first_name', ''),
                last_name=user_info.get('last_name', '')
            )
            user.set_unusable_password()
            user.save()
        
        # Log in user with proper backend
        from django.contrib.auth import login
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
        
        # Redirect based on user type
        if user.is_superuser:
            return redirect('admin_dashboard')
        else:
            from .models import UserProfile
            user_profile, _ = UserProfile.objects.get_or_create(user=user)
            if not user_profile.faculty:
                return redirect('select_faculty')
            return redirect('dashboard')
            
    except requests.RequestException as e:
        messages.error(request, 'Failed to authenticate with Facebook. Please try again.')
        return redirect('login')
    except Exception as e:
        messages.error(request, 'An error occurred during authentication.')
        return redirect('login')

def google_oauth_initiate(request):
    """Initiate Google OAuth flow"""
    # Check if Google OAuth is configured
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.error(request, 'Google OAuth is not configured. Please contact administrator.')
        return redirect('login')
    
    google_auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': request.build_absolute_uri('/oauth/google/callback/'),
        'scope': 'email profile',
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = f"{google_auth_url}?{urlencode(params)}"
    return redirect(auth_url)

def facebook_oauth_initiate(request):
    """Initiate Facebook OAuth flow"""
    # Check if Facebook OAuth is configured
    if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
        messages.error(request, 'Facebook OAuth is not configured. Please contact administrator.')
        return redirect('login')
    
    facebook_auth_url = 'https://www.facebook.com/v13.0/dialog/oauth'
    params = {
        'client_id': settings.FACEBOOK_APP_ID,
        'redirect_uri': request.build_absolute_uri('/oauth/facebook/callback/'),
        'scope': 'email,public_profile',
        'response_type': 'code'
    }
    
    auth_url = f"{facebook_auth_url}?{urlencode(params)}"
    return redirect(auth_url) 