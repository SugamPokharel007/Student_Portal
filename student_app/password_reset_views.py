"""
Password Reset Views for Student Portal
"""

from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@csrf_protect
@never_cache
def password_reset_request(request):
    """
    Display password reset request form and handle form submission
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'auth/password_reset_request.html')
        
        try:
            # Find user by email
            user = User.objects.get(email=email)
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Get current site and construct proper URL
            current_site = get_current_site(request)
            
            # Use site configuration from settings for consistent URLs
            if hasattr(settings, 'SITE_DOMAIN'):
                domain = settings.SITE_DOMAIN
                site_name = getattr(settings, 'SITE_NAME', 'Sikshya Kendra')
            else:
                domain = current_site.domain
                site_name = current_site.name
                
                # Fallback for development if site domain is example.com
                if settings.DEBUG and domain == 'example.com':
                    domain = '127.0.0.1:8000'
                    site_name = 'Sikshya Kendra (Development)'
            
            # Determine protocol
            protocol = 'https' if not settings.DEBUG else 'http'
            
            # Create reset URL
            reset_url = f"{protocol}://{domain}/password-reset-confirm/{uid}/{token}/"
            
            # Prepare email context
            context = {
                'user': user,
                'domain': domain,
                'uid': uid,
                'token': token,
                'reset_url': reset_url,
                'site_name': site_name,
            }
            
            # Render email templates
            subject = f'Password Reset Request - {site_name}'
            message = render_to_string('auth/password_reset_email.txt', context)
            html_message = render_to_string('auth/password_reset_email.html', context)
            
            # Send email
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                logger.info(f"Password reset email sent to {email}")
                return redirect('password_reset_done')
                
            except Exception as e:
                logger.error(f"Failed to send password reset email to {email}: {str(e)}")
                # In development, show more detailed error
                if settings.DEBUG:
                    messages.error(
                        request, 
                        f'Email sending failed: {str(e)}. '
                        'Check console for email content (using console backend in DEBUG mode).'
                    )
                else:
                    messages.error(
                        request, 
                        'There was an error sending the password reset email. '
                        'Please try again later or contact support.'
                    )
                return render(request, 'auth/password_reset_request.html')
                
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return redirect('password_reset_done')
        
        return render(request, 'auth/password_reset_request.html')
    
    return render(request, 'auth/password_reset_request.html')


@csrf_protect
@never_cache
def password_reset_confirm(request, uidb64, token):
    """
    Display password reset form and handle form submission
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if not password1 or not password2:
                messages.error(request, 'Please fill in all fields.')
                return render(request, 'auth/password_reset_confirm.html', {'validlink': True})
            
            if password1 != password2:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'auth/password_reset_confirm.html', {'validlink': True})
            
            if len(password1) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'auth/password_reset_confirm.html', {'validlink': True})
            
            # Set new password
            user.set_password(password1)
            user.save()
            
            logger.info(f"Password reset successful for user: {user.email}")
            return redirect('password_reset_success')
        
        return render(request, 'auth/password_reset_confirm.html', {'validlink': True})
    else:
        messages.error(request, 'This password reset link is invalid or has expired.')
        return render(request, 'auth/password_reset_confirm.html', {'validlink': False})


@csrf_protect
@never_cache
def password_reset_done(request):
    """
    Display password reset confirmation message after email sent
    """
    return render(request, 'auth/password_reset_done.html')


@csrf_protect
@never_cache
def password_reset_success(request):
    """
    Display password reset success message after password changed
    """
    return render(request, 'auth/password_reset_success.html')
