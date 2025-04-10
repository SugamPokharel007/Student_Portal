from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Subject, Notice, Syllabus, QuestionBank, Note, Subscription
from django.utils import timezone

# Create your views here.
def home(request):
    # Get the latest general notices
    latest_notices = Notice.objects.filter(is_general=True).order_by('-created_at')[:3]
    
    # If no notices exist, create a test notice
    if not latest_notices.exists():
        Notice.objects.create(
            title="Welcome to Student Portal",
            content="Welcome to our Student Portal! This is a test notice to demonstrate the notice system. You can add more notices through the admin panel.",
            is_general=True
        )
        latest_notices = Notice.objects.filter(is_general=True).order_by('-created_at')[:3]
    
    return render(request, 'home.html', {'latest_notices': latest_notices})

def login(request):
    return render(request, 'login.html')

def about(request):
    return render(request, 'about.html')

def year(request):
    return render(request, 'year.html')

def contact(request):
    return render(request, 'contact.html')
 
def register(request):
    return render(request, 'register.html')

def subjects(request, year):
    subjects_list = Subject.objects.filter(year=year)
    return render(request, 'subjects.html', {
        'year': year,
        'subjects': subjects_list
    })

def subject_detail(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    notices = Notice.objects.filter(subject=subject, is_general=False)
    syllabus = Syllabus.objects.filter(subject=subject).first()
    question_banks = QuestionBank.objects.filter(subject=subject)
    notes = Note.objects.filter(subject=subject)
    
    return render(request, 'subject_detail.html', {
        'subject': subject,
        'notices': notices,
        'syllabus': syllabus,
        'question_banks': question_banks,
        'notes': notes
    })

def notice_list(request):
    general_notices = Notice.objects.filter(is_general=True).order_by('-created_at')
    return render(request, 'notices.html', {'notices': general_notices})

@login_required
def add_syllabus(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        file = request.FILES.get('file')
        
        Syllabus.objects.create(
            subject=subject,
            title=title,
            content=content,
            file=file
        )
        messages.success(request, 'Syllabus added successfully!')
        return redirect('subject_detail', subject_id=subject_id)
    
    return render(request, 'add_syllabus.html', {'subject': subject})

@login_required
def add_question_bank(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        
        QuestionBank.objects.create(
            subject=subject,
            title=title,
            description=description,
            file=file
        )
        messages.success(request, 'Question bank added successfully!')
        return redirect('subject_detail', subject_id=subject_id)
    
    return render(request, 'add_question_bank.html', {'subject': subject})

@login_required
def add_subject_notice(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        Notice.objects.create(
            subject=subject,
            title=title,
            content=content,
            is_general=False
        )
        messages.success(request, 'Notice added successfully!')
        return redirect('subject_detail', subject_id=subject_id)
    
    return render(request, 'add_subject_notice.html', {'subject': subject})

# for contact form submission
from .models import ContactMessage
from django.contrib import messages



def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        if name and email and message:
            # Save to database
            ContactMessage.objects.create(name=name, email=email, message=message)

            # Success message
            messages.success(request, "Your message has been sent successfully!")
        else:
            # Error message
            messages.error(request, "Please fill in all fields before submitting.")

        return redirect("contact")  # Redirect to clear form and display message

    return render(request, "contact.html")


#register the user 
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages

def register_view(request):
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email'] 
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered!")
            return redirect('register')

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        messages.success(request, "Registration successful! You can now log in.")
        return redirect('login')

    return render(request, 'register.html')
  


  #login logic 

from django.contrib.auth import login, authenticate

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('home')  #special features accesss
        else:
            messages.error(request, "Invalid username or password!")
            return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

def subject_syllabus(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    syllabus = Syllabus.objects.filter(subject=subject).first()
    
    context = {
        'subject': subject,
        'syllabus': syllabus,
    }
    return render(request, 'subject_syllabus.html', context)

def subscription_view(request):
    """View for the subscription page with pricing packages"""
    if not request.user.is_authenticated:
        messages.info(request, 'Please log in to view subscription options.')
        return redirect('login')
    return render(request, 'subscription.html')

@login_required
def subscribe(request, subscription_type):
    """View for the subscription form"""
    if subscription_type not in ['monthly', 'semi_yearly', 'yearly']:
        messages.error(request, 'Invalid subscription type')
        return redirect('subscription')
    
    # Check if user already has an active subscription
    try:
        existing_subscription = Subscription.objects.get(user=request.user, is_active=True)
        if existing_subscription:
            messages.info(request, 'You already have an active subscription')
            return redirect('home')
    except Subscription.DoesNotExist:
        pass
    
    if request.method == 'POST':
        try:
            # Create a new subscription
            subscription = Subscription.objects.create(
                user=request.user,
                subscription_type=subscription_type,
                start_date=timezone.now(),
                is_active=True
            )
            
            # Redirect to success page
            return redirect('subscription_success')
        except Exception as e:
            messages.error(request, f'Error creating subscription: {str(e)}')
            return redirect('subscription')
    
    return render(request, 'subscribe.html', {'subscription_type': subscription_type})

@login_required
def subscription_success(request):
    """View for the subscription success page"""
    try:
        subscription = Subscription.objects.get(user=request.user, is_active=True)
        return render(request, 'subscription_success.html', {'subscription': subscription})
    except Subscription.DoesNotExist:
        messages.error(request, 'No active subscription found')
        return redirect('subscription')

# Decorator to check if user has an active subscription
def subscription_required(view_func):
    def wrapper(request, *args, **kwargs):
        try:
            subscription = Subscription.objects.get(user=request.user, is_active=True)
            if timezone.now() > subscription.end_date:
                subscription.is_active = False
                subscription.save()
                messages.error(request, 'Your subscription has expired. Please renew to access premium content.')
                return redirect('subscription')
            return view_func(request, *args, **kwargs)
        except Subscription.DoesNotExist:
            messages.error(request, 'You need an active subscription to access this content.')
            return redirect('subscription')
        except Exception as e:
            messages.error(request, f'Error checking subscription: {str(e)}')
            return redirect('home')
    return wrapper

# Update the subject_questions view to require only login
@login_required
def subject_questions(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    question_banks = QuestionBank.objects.filter(subject=subject)
    
    context = {
        'subject': subject,
        'question_banks': question_banks,
    }
    return render(request, 'subject_questions.html', context)

# Update the subject_notes view to require only login
@login_required
def subject_notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    notes = Note.objects.filter(subject=subject).order_by('-created_at')
    
    context = {
        'subject': subject,
        'notes': notes,
    }
    return render(request, 'subject_notes.html', context)
