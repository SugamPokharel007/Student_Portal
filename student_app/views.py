from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Subject, Notice, Syllabus, QuestionBank, Note

# Create your views here.
def home(request):
    return render(request, 'home.html')

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

def subject_questions(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    question_banks = QuestionBank.objects.filter(subject=subject)
    
    context = {
        'subject': subject,
        'question_banks': question_banks,
    }
    return render(request, 'subject_questions.html', context)

def subject_notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    notes = Note.objects.filter(subject=subject).order_by('-created_at')
    
    context = {
        'subject': subject,
        'notes': notes,
    }
    return render(request, 'subject_notes.html', context)
