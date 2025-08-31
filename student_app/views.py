from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.db.models.functions import Coalesce
from datetime import timedelta
import json
import re
from collections import Counter
import math

from .models import (
    Subject, Notice, Syllabus, QuestionBank, Note, Subscription, 
    Faculty, UserProfile, ContactMessage, ContributorRequest,
    DownloadLog, ViewLog
)
from .forms import (
    ContributeResourceForm, ContributorRequestForm, EnhancedContactForm,
    UserRegistrationForm, UserProfileForm, AdminResponseForm,
    ResourceFilterForm, AdvancedSearchForm
)


def home(request):
    latest_notices = Notice.objects.filter(is_general=True, is_important=True).order_by('-created_at')[:3]
    
    week_ago = timezone.now() - timedelta(days=7)
    trending_subjects = Subject.objects.annotate(
        recent_activity=Count('syllabi', filter=Q(syllabi__created_at__gte=week_ago)) +
                        Count('notes', filter=Q(notes__created_at__gte=week_ago)) +
                        Count('question_banks', filter=Q(question_banks__created_at__gte=week_ago))
    ).filter(recent_activity__gt=0).order_by('-recent_activity')[:6]
    
    recent_resources = []
    recent_syllabi = Syllabus.objects.filter(status='approved').order_by('-created_at')[:3]
    recent_notes = Note.objects.filter(status='approved').order_by('-created_at')[:3]
    recent_questions = QuestionBank.objects.filter(status='approved').order_by('-created_at')[:3]
    
    recent_resources.extend(recent_syllabi)
    recent_resources.extend(recent_notes)
    recent_resources.extend(recent_questions)
    recent_resources.sort(key=lambda x: x.created_at, reverse=True)
    recent_resources = recent_resources[:6]
    
    if not latest_notices.exists():
        Notice.objects.create(
            title="Welcome to Sikshya Kendra",
            content="Welcome to our Student Portal! This is a test notice to demonstrate the notice system. You can add more notices through the admin panel.",
            is_general=True,
            is_important=True
        )
        latest_notices = Notice.objects.filter(is_general=True, is_important=True).order_by('-created_at')[:3]
    
    context = {
        'latest_notices': latest_notices,
        'trending_subjects': trending_subjects,
        'recent_resources': recent_resources,
    }
    return render(request, 'home.html', context)

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        else:
            return redirect('dashboard')
    
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            else:
                user_profile, _ = UserProfile.objects.get_or_create(user=user)
                if not user_profile.faculty:
                    return redirect('select_faculty')
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password!")
            return redirect('login')
    return render(request, 'login.html')

def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if not user_profile.faculty:
        return redirect('select_faculty')
    
    # Get user's recent activity
    recent_uploads = []
    if user_profile.can_upload():
        recent_uploads.extend(list(Note.objects.filter(uploaded_by=request.user).order_by('-created_at')[:3]))
        recent_uploads.extend(list(Syllabus.objects.filter(uploaded_by=request.user).order_by('-created_at')[:3]))
        recent_uploads.extend(list(QuestionBank.objects.filter(uploaded_by=request.user).order_by('-created_at')[:3]))
        recent_uploads.sort(key=lambda x: x.created_at, reverse=True)
        recent_uploads = recent_uploads[:5]
    
    # Get user's recent downloads
    recent_downloads = DownloadLog.objects.filter(user=request.user).order_by('-downloaded_at')[:5]
    
    # Get subscription info
    try:
        subscription = Subscription.objects.get(user=request.user, is_active=True)
    except Subscription.DoesNotExist:
        subscription = None
    
    context = {
        'user_profile': user_profile,
        'recent_uploads': recent_uploads,
        'recent_downloads': recent_downloads,
        'subscription': subscription,
    }
    return render(request, 'dashboard.html', context)

@login_required
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Get recent downloads
    recent_downloads = DownloadLog.objects.filter(user=request.user).order_by('-downloaded_at')[:5]
    
    # Get all faculties for the faculty explorer
    faculties = Faculty.objects.filter(is_active=True)
    
    context = {
        'user_profile': user_profile,
        'recent_downloads': recent_downloads,
        'faculties': faculties,
    }
    
    return render(request, 'profile.html', context)

@login_required
def select_faculty(request):
    faculties = Faculty.objects.filter(is_active=True)
    
    if request.method == 'POST':
        faculty_id = request.POST.get('faculty')
        faculty = Faculty.objects.filter(id=faculty_id).first()
        if faculty:
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            user_profile.faculty = faculty
            user_profile.save()
            messages.success(request, f'Faculty selected: {faculty.name}')
            
            # Check if this is for subject view
            year = request.POST.get('year')
            if year:
                # Redirect to faculty overview instead of old subjects URL
                return redirect('faculty_overview', faculty_slug=faculty.slug)
            else:
                return redirect('dashboard')
        messages.error(request, 'Select a valid faculty.')
    
    return render(request, 'faculty_selection.html', {'faculties': faculties})

def faculty_overview(request, faculty_slug):
    """Show overview of a faculty with all levels"""
    try:
        faculty = Faculty.objects.get(slug=faculty_slug, is_active=True)
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty not found.')
        return redirect('home')
    
    # Get all subjects for this faculty
    all_subjects = Subject.objects.filter(
        faculty=faculty, 
        is_active=True,
        faculty__isnull=False
    ).order_by('level', 'name')
    
    # Group subjects by level
    subjects_by_level = {}
    for subject in all_subjects:
        level = subject.level if subject.level else 0  # Use 0 for subjects without level
        if level not in subjects_by_level:
            subjects_by_level[level] = []
        subjects_by_level[level].append(subject)
    
    context = {
        'faculty': faculty,
        'subjects_by_level': subjects_by_level,
        'levels': range(1, faculty.total_levels + 1),
        'all_subjects': all_subjects,  # Add all subjects for debugging
    }
    
    return render(request, 'faculty_overview.html', context)


def faculty_subjects(request, faculty_slug, level):
    """Show subjects for a specific faculty and level (semester/year)"""
    try:
        faculty = Faculty.objects.get(slug=faculty_slug, is_active=True)
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty not found.')
        return redirect('home')
    
    # Validate level
    if level < 1 or level > faculty.total_levels:
        messages.error(request, f'Invalid level. {faculty.name} has {faculty.total_levels} levels.')
        return redirect('faculty_overview', faculty_slug=faculty_slug)
    
    # Get subjects for this faculty and level
    subjects = Subject.objects.filter(
        faculty=faculty, 
        level=level, 
        is_active=True,
        faculty__isnull=False
    ).order_by('name')
    
    # Get all faculties for navigation
    faculties = Faculty.objects.filter(is_active=True)
    
    context = {
        'faculty': faculty,
        'level': level,
        'subjects': subjects,
        'faculties': faculties,
        'level_name': faculty.get_level_display_name(level),
        'levels': range(1, faculty.total_levels + 1),
    }
    
    return render(request, 'faculty_subjects.html', context)

def subject_detail(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id, is_active=True, faculty__isnull=False)
    
    # Increment view count if user is authenticated
    if request.user.is_authenticated:
        ViewLog.objects.create(
            user=request.user,
            content_type='subject',
            content_id=subject_id,
            ip_address=request.META.get('REMOTE_ADDR')
        )
    
    notices = Notice.objects.filter(subject=subject, is_general=False)
    syllabus = Syllabus.objects.filter(subject=subject, status='approved').first()
    question_banks = QuestionBank.objects.filter(subject=subject, status='approved')
    notes = Note.objects.filter(subject=subject, status='approved')
    
    return render(request, 'subject_detail.html', {
        'subject': subject,
        'notices': notices,
        'syllabus': syllabus,
        'question_banks': question_banks,
        'notes': notes
    })

@login_required
def subject_syllabus(request, subject_id):
    faculty_id = request.GET.get('faculty')
    if request.user.is_superuser and faculty_id:
        subject = get_object_or_404(Subject.objects.select_related('faculty'), id=subject_id, faculty_id=faculty_id)
    else:
        subject = get_object_or_404(Subject.objects.select_related('faculty'), id=subject_id)
    
    if request.user.is_superuser:
        syllabi = Syllabus.objects.filter(subject=subject, status='approved').select_related('subject', 'uploaded_by')
    else:
        user_profile = UserProfile.objects.select_related('faculty').get(user=request.user)
        syllabi = Syllabus.objects.filter(subject=subject, status='approved', subject__faculty=user_profile.faculty).select_related('subject', 'uploaded_by')
    
    return render(request, 'subject_syllabus.html', {'subject': subject, 'syllabi': syllabi})

@login_required
def subject_questions(request, subject_id):
    faculty_id = request.GET.get('faculty')
    if request.user.is_superuser and faculty_id:
        subject = get_object_or_404(Subject.objects.select_related('faculty'), id=subject_id, faculty_id=faculty_id)
    else:
        subject = get_object_or_404(Subject.objects.select_related('faculty'), id=subject_id)
    
    if request.user.is_superuser:
        questions = QuestionBank.objects.filter(subject=subject, status='approved').select_related('subject', 'uploaded_by')
    else:
        user_profile = UserProfile.objects.select_related('faculty').get(user=request.user)
        questions = QuestionBank.objects.filter(subject=subject, status='approved', subject__faculty=user_profile.faculty).select_related('subject', 'uploaded_by')
    
    return render(request, 'subject_questions.html', {'subject': subject, 'questions': questions})

@login_required
def subject_notes(request, subject_id):
    faculty_id = request.GET.get('faculty')
    if request.user.is_superuser and faculty_id:
        subject = get_object_or_404(Subject.objects.select_related('faculty'), id=subject_id, faculty_id=faculty_id)
    else:
        subject = get_object_or_404(Subject.objects.select_related('faculty'), id=subject_id)
    
    if request.user.is_superuser:
        notes = Note.objects.filter(subject=subject, status='approved').select_related('subject', 'uploaded_by')
    else:
        user_profile = UserProfile.objects.select_related('faculty').get(user=request.user)
        notes = Note.objects.filter(subject=subject, status='approved', subject__faculty=user_profile.faculty).select_related('subject', 'uploaded_by')
    
    return render(request, 'subject_notes.html', {'subject': subject, 'notes': notes})

@login_required
def contribute_resource(request):
    user_profile = UserProfile.objects.select_related('faculty').get(user=request.user)
    
    if not user_profile.can_upload():
        messages.error(request, 'You need contributor access to upload resources.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ContributeResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource_type = form.cleaned_data['resource_type']
            faculty = form.cleaned_data['faculty']
            subject = form.cleaned_data['subject']
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            file = form.cleaned_data['file']
            tags = form.cleaned_data['tags']
            
            # Verify subject belongs to selected faculty
            if subject.faculty != faculty:
                messages.error(request, 'Selected subject does not belong to the selected faculty.')
                return render(request, 'contribute_resource.html', {'form': form})
            
            if resource_type == 'note':
                resource = Note.objects.create(
                    subject=subject, 
                    title=title, 
                    description=description, 
                    file=file, 
                    uploaded_by=request.user, 
                    status='pending'
                )
            elif resource_type == 'syllabus':
                resource = Syllabus.objects.create(
                    subject=subject, 
                    title=title, 
                    content=description, 
                    file=file, 
                    uploaded_by=request.user, 
                    status='pending'
                )
            elif resource_type == 'questionbank':
                resource = QuestionBank.objects.create(
                    subject=subject, 
                    title=title, 
                    description=description, 
                    file=file, 
                    uploaded_by=request.user, 
                    status='pending'
                )
            
            # Add tags if provided
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                resource.tags.add(*tag_list)
            
            user_profile.increment_uploads()
            messages.success(request, 'Resource submitted for admin approval.')
            return redirect('dashboard')
    else:
        # Set initial faculty if user has one assigned
        initial_data = {}
        if user_profile.faculty:
            initial_data['faculty'] = user_profile.faculty
        form = ContributeResourceForm(initial=initial_data)
    
    return render(request, 'contribute_resource.html', {'form': form})

@login_required
def contributor_request(request):
    # Check if user already has a pending request
    existing_request = ContributorRequest.objects.filter(user=request.user, status='pending').first()
    if existing_request:
        messages.info(request, 'You already have a pending contributor request.')
        return redirect('dashboard')
    
    # Check if user is already a contributor
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.is_contributor_approved:
        messages.info(request, 'You are already an approved contributor.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ContributorRequestForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            messages.success(request, 'Contributor request submitted successfully!')
            return redirect('dashboard')
    else:
        form = ContributorRequestForm()
    
    return render(request, 'contributor_request.html', {'form': form})

def contact_view(request):
    if request.method == "POST":
        form = EnhancedContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect("contact")
    else:
        form = EnhancedContactForm()
    
    return render(request, 'contact.html', {'form': form})

def notice_list(request):
    general_notices = Notice.objects.filter(is_general=True).order_by('-created_at')
    return render(request, 'notices.html', {'notices': general_notices})

def notice_detail(request, notice_id):
    """Display individual notice details"""
    try:
        notice = Notice.objects.get(id=notice_id)
        return render(request, 'notice_detail.html', {'notice': notice})
    except Notice.DoesNotExist:
        messages.error(request, 'Notice not found.')
        return redirect('notice_list')

def about(request):
    return render(request, 'about.html')

def year(request):
    return render(request, 'year.html')

def contact(request):
    return render(request, 'contact.html')

def register(request):
    return render(request, 'register.html')

def login_page(request):
    return render(request, 'login.html')


def calculate_tf_idf(query, documents):
    """Simple TF-IDF implementation for search ranking"""
    query_terms = re.findall(r'\b\w+\b', query.lower())
    query_tf = Counter(query_terms)
    
    results = []
    for doc in documents:
        # Get document text (title + description)
        doc_text = f"{doc.title} {getattr(doc, 'description', '')} {getattr(doc, 'content', '')}"
        doc_terms = re.findall(r'\b\w+\b', doc_text.lower())
        doc_tf = Counter(doc_terms)
        
        # Calculate TF-IDF score
        score = 0
        for term in query_terms:
            if term in doc_tf:
                # Simple TF-IDF: tf * idf
                tf = doc_tf[term] / len(doc_terms) if doc_terms else 0
                # Count documents containing this term
                doc_count = sum(1 for d in documents if term in f"{d.title} {getattr(d, 'description', '')} {getattr(d, 'content', '')}".lower())
                idf = math.log(len(documents) / doc_count) if doc_count > 0 else 0
                score += tf * idf
        
        if score > 0:
            results.append((doc, score))
    
    # Sort by score
    results.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, score in results]

@login_required
def advanced_search(request):
    form = AdvancedSearchForm(request.GET)
    results = []
    
    # Handle faculty filtering from URL parameters (for navbar links)
    faculty_id = request.GET.get('faculty')
    resource_type = request.GET.get('resource_type')
    
    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        faculty = form.cleaned_data.get('faculty')
        subject = form.cleaned_data.get('subject')
        resource_types = form.cleaned_data.get('resource_type', [])
        levels = form.cleaned_data.get('level', [])
        sort_by = form.cleaned_data.get('sort_by', 'relevance')
        
        # Override faculty if provided in URL
        if faculty_id:
            try:
                faculty = Faculty.objects.get(id=faculty_id)
            except Faculty.DoesNotExist:
                faculty = None
        
        # Override resource types if provided in URL
        if resource_type:
            resource_types = [resource_type]
        
        # Get all approved resources
        notes = Note.objects.filter(status='approved').select_related('subject', 'subject__faculty')
        syllabi = Syllabus.objects.filter(status='approved').select_related('subject', 'subject__faculty')
        questionbanks = QuestionBank.objects.filter(status='approved').select_related('subject', 'subject__faculty')
        
        # Apply filters
        if faculty:
            notes = notes.filter(subject__faculty=faculty)
            syllabi = syllabi.filter(subject__faculty=faculty)
            questionbanks = questionbanks.filter(subject__faculty=faculty)
        
        if subject:
            notes = notes.filter(subject=subject)
            syllabi = syllabi.filter(subject=subject)
            questionbanks = questionbanks.filter(subject=subject)
        
        if levels:
            notes = notes.filter(subject__level__in=levels)
            syllabi = syllabi.filter(subject__level__in=levels)
            questionbanks = questionbanks.filter(subject__level__in=levels)
        
        # Apply text search
        if query:
            notes = notes.filter(Q(title__icontains=query) | Q(description__icontains=query))
            syllabi = syllabi.filter(Q(title__icontains=query) | Q(content__icontains=query))
            questionbanks = questionbanks.filter(Q(title__icontains=query) | Q(description__icontains=query))
        
        # Combine results
        all_results = []
        if not resource_types or 'note' in resource_types:
            all_results.extend(list(notes))
        if not resource_types or 'syllabus' in resource_types:
            all_results.extend(list(syllabi))
        if not resource_types or 'questionbank' in resource_types:
            all_results.extend(list(questionbanks))
        
        # Apply TF-IDF ranking if query provided
        if query and all_results:
            results = calculate_tf_idf(query, all_results)
        else:
            results = all_results
        
        # Apply sorting
        if sort_by == 'newest':
            results.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by == 'oldest':
            results.sort(key=lambda x: x.created_at)
        elif sort_by == 'downloads':
            results.sort(key=lambda x: x.download_count, reverse=True)
        elif sort_by == 'views':
            results.sort(key=lambda x: x.view_count, reverse=True)
    
    # Pagination
    paginator = Paginator(results, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'results_count': len(results),
    }
    return render(request, 'advanced_search.html', context)

@login_required
def search(request):
    query = request.GET.get('q', '')
    faculty_id = request.GET.get('faculty')
    subject_id = request.GET.get('subject')
    resource_type = request.GET.get('type')
    level = request.GET.get('level')
    
    notes = Note.objects.filter(status='approved').select_related('subject', 'subject__faculty')
    syllabi = Syllabus.objects.filter(status='approved').select_related('subject', 'subject__faculty')
    questionbanks = QuestionBank.objects.filter(status='approved').select_related('subject', 'subject__faculty')
    
    if query:
        notes = notes.filter(Q(title__icontains=query) | Q(description__icontains=query))
        syllabi = syllabi.filter(Q(title__icontains=query) | Q(content__icontains=query))
        questionbanks = questionbanks.filter(Q(title__icontains=query) | Q(description__icontains=query))
    
    if faculty_id:
        notes = notes.filter(subject__faculty_id=faculty_id)
        syllabi = syllabi.filter(subject__faculty_id=faculty_id)
        questionbanks = questionbanks.filter(subject__faculty_id=faculty_id)
    
    if subject_id:
        notes = notes.filter(subject_id=subject_id)
        syllabi = syllabi.filter(subject_id=subject_id)
        questionbanks = questionbanks.filter(subject_id=subject_id)
    
    if level:
        notes = notes.filter(subject__level=level)
        syllabi = syllabi.filter(subject__level=level)
        questionbanks = questionbanks.filter(subject__level=level)
    
    results = []
    if not resource_type or resource_type == 'note':
        results += list(notes)
    if not resource_type or resource_type == 'syllabus':
        results += list(syllabi)
    if not resource_type or resource_type == 'questionbank':
        results += list(questionbanks)
    
    results = sorted(results, key=lambda x: x.title.lower())
    paginator = Paginator(results, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    faculties = Faculty.objects.filter(is_active=True)
    subjects = Subject.objects.filter(is_active=True)
    
    return render(request, 'search.html', {
        'page_obj': page_obj,
        'faculties': faculties,
        'subjects': subjects,
        'query': query,
        'faculty_id': faculty_id,
        'subject_id': subject_id,
        'resource_type': resource_type,
        'level': level
    })


@login_required
def download_resource(request, content_type, content_id):
    """Track resource downloads and increment counters"""
    try:
        if content_type == 'syllabus':
            resource = get_object_or_404(Syllabus, id=content_id, status='approved')
        elif content_type == 'note':
            resource = get_object_or_404(Note, id=content_id, status='approved')
        elif content_type == 'questionbank':
            resource = get_object_or_404(QuestionBank, id=content_id, status='approved')
        else:
            return HttpResponse('Invalid content type', status=400)
        
        # Log download
        DownloadLog.objects.create(
            user=request.user,
            content_type=content_type,
            content_id=content_id,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Increment download count
        resource.increment_download()
        
        # Increment user's download count
        user_profile = UserProfile.objects.get(user=request.user)
        user_profile.increment_downloads()
        
        # Return file for download
        try:
            return FileResponse(
                resource.file.open('rb'),
                as_attachment=True,
                filename=resource.file.name.split('/')[-1]
            )
        except FileNotFoundError:
            messages.error(request, 'File not found on server.')
            return redirect('dashboard')
        
    except Exception as e:
        messages.error(request, f'Error downloading file: {str(e)}')
        return redirect('dashboard')


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


@login_required
def add_syllabus(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Check if user has permission to add syllabus
    user_profile = UserProfile.objects.get(user=request.user)
    if not user_profile.can_upload() and not request.user.is_superuser:
        messages.error(request, 'You need contributor access to add syllabus.')
        return redirect('subject_detail', subject_id=subject_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        file = request.FILES.get('file')
        
        # Validate required fields
        if not title:
            messages.error(request, 'Title is required.')
            return render(request, 'add_syllabus.html', {'subject': subject})
        
        if not content:
            messages.error(request, 'Content is required.')
            return render(request, 'add_syllabus.html', {'subject': subject})
        
        # Validate file if provided
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                messages.error(request, 'File size must be under 10MB.')
                return render(request, 'add_syllabus.html', {'subject': subject})
            
            # Check file extension
            allowed_extensions = ['pdf', 'doc', 'docx', 'txt']
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                messages.error(request, f'Invalid file type. Allowed types: {', '.join(allowed_extensions)}')
                return render(request, 'add_syllabus.html', {'subject': subject})
        
        try:
            Syllabus.objects.create(
                subject=subject,
                title=title,
                content=content,
                file=file,
                uploaded_by=request.user,
                status='pending' if not request.user.is_superuser else 'approved'
            )
            messages.success(request, 'Syllabus added successfully!')
            return redirect('subject_detail', subject_id=subject_id)
        except Exception as e:
            messages.error(request, f'Error adding syllabus: {str(e)}')
            return render(request, 'add_syllabus.html', {'subject': subject})
    
    return render(request, 'add_syllabus.html', {'subject': subject})

@login_required
def add_question_bank(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Check if user has permission to add question bank
    user_profile = UserProfile.objects.get(user=request.user)
    if not user_profile.can_upload() and not request.user.is_superuser:
        messages.error(request, 'You need contributor access to add question banks.')
        return redirect('subject_detail', subject_id=subject_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        
        # Validate required fields
        if not title:
            messages.error(request, 'Title is required.')
            return render(request, 'add_question_bank.html', {'subject': subject})
        
        if not file:
            messages.error(request, 'File is required for question banks.')
            return render(request, 'add_question_bank.html', {'subject': subject})
        
        # Validate file
        # Check file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            messages.error(request, 'File size must be under 10MB.')
            return render(request, 'add_question_bank.html', {'subject': subject})
        
        # Check file extension
        allowed_extensions = ['pdf', 'doc', 'docx', 'txt']
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            messages.error(request, f'Invalid file type. Allowed types: {', '.join(allowed_extensions)}')
            return render(request, 'add_question_bank.html', {'subject': subject})
        
        try:
            QuestionBank.objects.create(
                subject=subject,
                title=title,
                description=description or '',
                file=file,
                uploaded_by=request.user,
                status='pending' if not request.user.is_superuser else 'approved'
            )
            messages.success(request, 'Question bank added successfully!')
            return redirect('subject_detail', subject_id=subject_id)
        except Exception as e:
            messages.error(request, f'Error adding question bank: {str(e)}')
            return render(request, 'add_question_bank.html', {'subject': subject})
    
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

# API views for AJAX requests
@login_required
@require_POST
def toggle_dark_mode(request):
    """Toggle dark mode for the user"""
    if request.method == 'POST':
        # Check if request is AJAX (modern way)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            dark_mode = request.POST.get('dark_mode') == 'true'
            # Store preference in session
            request.session['dark_mode'] = dark_mode
            return JsonResponse({'status': 'success', 'dark_mode': dark_mode})
    return JsonResponse({'status': 'error'}, status=400)

def syllabus_redirect(request):
    """Redirect to search with syllabus filter"""
    return redirect('advanced_search' + '?resource_type=syllabus')

def notes_redirect(request):
    """Redirect to search with notes filter"""
    return redirect('advanced_search' + '?resource_type=notes')

def question_bank_redirect(request):
    """Redirect to search with question bank filter"""
    return redirect('advanced_search' + '?resource_type=questionbank')

@login_required
def get_trending_subjects(request):
    """Get trending subjects for AJAX requests"""
    week_ago = timezone.now() - timedelta(days=7)
    trending_subjects = Subject.objects.annotate(
        recent_activity=Count('syllabi', filter=Q(syllabi__created_at__gte=week_ago)) +
                        Count('notes', filter=Q(notes__created_at__gte=week_ago)) +
                        Count('question_banks', filter=Q(question_banks__created_at__gte=week_ago))
    ).filter(recent_activity__gt=0).order_by('-recent_activity')[:5]
    
    data = []
    for subject in trending_subjects:
        data.append({
            'id': subject.id,
            'name': subject.name,
            'level': subject.level,
            'faculty': subject.faculty.name if subject.faculty else '',
            'activity': subject.recent_activity,
        })
    
    return JsonResponse({'subjects': data})

def base_context(request):
    """Context processor for base template"""
    faculties = Faculty.objects.filter(is_active=True)
    dark_mode = request.session.get('dark_mode', True)  # Default to dark mode
    
    # Get trending subjects for sidebar
    week_ago = timezone.now() - timedelta(days=7)
    trending_subjects = cache.get('trending_subjects')
    if not trending_subjects:
        trending_subjects = Subject.objects.annotate(
            recent_activity=Count('syllabi', filter=Q(syllabi__created_at__gte=week_ago)) +
                            Count('notes', filter=Q(notes__created_at__gte=week_ago)) +
                            Count('question_banks', filter=Q(question_banks__created_at__gte=week_ago))
        ).filter(recent_activity__gt=0).order_by('-recent_activity')[:5]
        cache.set('trending_subjects', trending_subjects, 300)  # Cache for 5 minutes
    
    return {
        'faculties': faculties,
        'dark_mode': dark_mode,
        'trending_subjects': trending_subjects,
    }

def get_subjects_for_faculty(request, faculty_id):
    """API endpoint to get subjects for a specific faculty"""
    try:
        faculty = Faculty.objects.get(id=faculty_id, is_active=True)
        subjects = Subject.objects.filter(faculty=faculty, is_active=True, faculty__isnull=False).order_by('level', 'name')
        
        subjects_data = []
        for subject in subjects:
            subjects_data.append({
                'id': subject.id,
                'name': subject.name,
                'level': subject.level,
                'level_name': faculty.get_level_display_name(subject.level)
            })
        
        return JsonResponse({
            'success': True,
            'faculty': faculty.name,
            'subjects': subjects_data
        })
    except Faculty.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Faculty not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def admin_dashboard(request):
    """Custom admin dashboard for superusers"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    # Get comprehensive statistics
    total_users = User.objects.count()
    total_subjects = Subject.objects.count()
    total_faculties = Faculty.objects.filter(is_active=True).count()
    
    # Resource statistics
    total_syllabi = Syllabus.objects.count()
    total_notes = Note.objects.count()
    total_question_banks = QuestionBank.objects.count()
    total_resources = total_syllabi + total_notes + total_question_banks
    
    # Approval statistics
    pending_syllabi = Syllabus.objects.filter(status='pending').count()
    pending_notes = Note.objects.filter(status='pending').count()
    pending_question_banks = QuestionBank.objects.filter(status='pending').count()
    total_pending = pending_syllabi + pending_notes + pending_question_banks
    
    approved_syllabi = Syllabus.objects.filter(status='approved').count()
    approved_notes = Note.objects.filter(status='approved').count()
    approved_question_banks = QuestionBank.objects.filter(status='approved').count()
    total_approved = approved_syllabi + approved_notes + approved_question_banks
    
    # Faculty-wise statistics
    faculty_stats = []
    for faculty in Faculty.objects.filter(is_active=True):
        faculty_subjects = Subject.objects.filter(faculty=faculty).count()
        faculty_syllabi = Syllabus.objects.filter(subject__faculty=faculty).count()
        faculty_notes = Note.objects.filter(subject__faculty=faculty).count()
        faculty_questions = QuestionBank.objects.filter(subject__faculty=faculty).count()
        
        faculty_stats.append({
            'faculty': faculty,
            'subjects': faculty_subjects,
            'syllabi': faculty_syllabi,
            'notes': faculty_notes,
            'questions': faculty_questions,
            'total_resources': faculty_syllabi + faculty_notes + faculty_questions
        })
    
    # Recent activity
    recent_uploads = []
    recent_uploads.extend(list(Syllabus.objects.all().order_by('-created_at')[:5]))
    recent_uploads.extend(list(Note.objects.all().order_by('-created_at')[:5]))
    recent_uploads.extend(list(QuestionBank.objects.all().order_by('-created_at')[:5]))
    recent_uploads.sort(key=lambda x: x.created_at, reverse=True)
    recent_uploads = recent_uploads[:10]
    
    # Debug: Print recent uploads for debugging
    print(f"DEBUG: Total recent uploads: {len(recent_uploads)}")
    for i, upload in enumerate(recent_uploads):
        print(f"DEBUG: {i+1}. {upload.__class__.__name__} - {upload.title} - {upload.created_at}")
    
    # Pending approvals
    pending_approvals = []
    pending_approvals.extend(list(Syllabus.objects.filter(status='pending').order_by('-created_at')[:5]))
    pending_approvals.extend(list(Note.objects.filter(status='pending').order_by('-created_at')[:5]))
    pending_approvals.extend(list(QuestionBank.objects.filter(status='pending').order_by('-created_at')[:5]))
    pending_approvals.sort(key=lambda x: x.created_at, reverse=True)
    pending_approvals = pending_approvals[:10]
    
    # Contributor requests
    contributor_requests = ContributorRequest.objects.filter(status='pending').order_by('-submitted_at')[:10]
    contributor_requests_count = ContributorRequest.objects.filter(status='pending').count()
    
    # Contact messages
    recent_contacts = ContactMessage.objects.filter(status='pending').order_by('-submitted_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_subjects': total_subjects,
        'total_faculties': total_faculties,
        'total_resources': total_resources,
        'total_pending': total_pending,
        'total_approved': total_approved,
        'contributor_requests_count': contributor_requests_count,
        'faculty_stats': faculty_stats,
        'recent_uploads': recent_uploads,
        'pending_approvals': pending_approvals,
        'contributor_requests': contributor_requests,
        'recent_contacts': recent_contacts,
        'resource_breakdown': {
            'syllabi': {'total': total_syllabi, 'pending': pending_syllabi, 'approved': approved_syllabi},
            'notes': {'total': total_notes, 'pending': pending_notes, 'approved': approved_notes},
            'question_banks': {'total': total_question_banks, 'pending': pending_question_banks, 'approved': approved_question_banks},
        }
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
def admin_manage_subjects(request):
    """Admin view to manage subjects"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    faculties = Faculty.objects.filter(is_active=True)
    subjects = Subject.objects.all().order_by('faculty__name', 'level', 'name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_subject':
            name = request.POST.get('name')
            faculty_id = request.POST.get('faculty')
            level = request.POST.get('level')
            
            if name and faculty_id and level:
                try:
                    faculty = Faculty.objects.get(id=faculty_id)
                    Subject.objects.create(
                        name=name,
                        faculty=faculty,
                        level=level,
                        is_active=True
                    )
                    messages.success(request, f'Subject "{name}" added successfully.')
                except Faculty.DoesNotExist:
                    messages.error(request, 'Invalid faculty selected.')
            else:
                messages.error(request, 'All fields are required.')
        
        elif action == 'edit_subject':
            subject_id = request.POST.get('subject_id')
            name = request.POST.get('name')
            faculty_id = request.POST.get('faculty')
            level = request.POST.get('level')
            is_active = request.POST.get('is_active') == 'on'
            
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.name = name
                subject.faculty_id = faculty_id
                subject.level = level
                subject.is_active = is_active
                subject.save()
                messages.success(request, f'Subject "{name}" updated successfully.')
            except Subject.DoesNotExist:
                messages.error(request, 'Subject not found.')
        
        elif action == 'delete_subject':
            subject_id = request.POST.get('subject_id')
            try:
                subject = Subject.objects.get(id=subject_id)
                subject_name = subject.name
                subject.delete()
                messages.success(request, f'Subject "{subject_name}" deleted successfully.')
            except Subject.DoesNotExist:
                messages.error(request, 'Subject not found.')
        
        return redirect('admin_manage_subjects')
    
    context = {
        'faculties': faculties,
        'subjects': subjects,
    }
    return render(request, 'admin_manage_subjects.html', context)


@login_required
def admin_manage_syllabus(request):
    """Admin view to manage syllabus"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    syllabi = Syllabus.objects.all().order_by('-created_at')
    subjects = Subject.objects.filter(is_active=True).order_by('faculty__name', 'level', 'name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_syllabus':
            title = request.POST.get('title')
            subject_id = request.POST.get('subject')
            content = request.POST.get('content', '')
            file = request.FILES.get('file')
            
            if title and subject_id:
                try:
                    subject = Subject.objects.get(id=subject_id)
                    syllabus = Syllabus.objects.create(
                        title=title,
                        subject=subject,
                        content=content,
                        file=file,
                        uploaded_by=request.user,
                        status='approved'  # Auto-approve admin uploads
                    )
                    messages.success(request, f'Syllabus "{title}" added successfully.')
                except Subject.DoesNotExist:
                    messages.error(request, 'Selected subject not found.')
                except Exception as e:
                    messages.error(request, f'Error adding syllabus: {str(e)}')
            else:
                messages.error(request, 'Title and subject are required.')
        
        elif action == 'delete_syllabus':
            syllabus_id = request.POST.get('syllabus_id')
            try:
                syllabus = Syllabus.objects.get(id=syllabus_id)
                syllabus_name = syllabus.title
                syllabus.delete()
                messages.success(request, f'Syllabus "{syllabus_name}" deleted successfully.')
            except Syllabus.DoesNotExist:
                messages.error(request, 'Syllabus not found.')
        
        elif action == 'approve_syllabus':
            syllabus_id = request.POST.get('syllabus_id')
            try:
                syllabus = Syllabus.objects.get(id=syllabus_id)
                syllabus.status = 'approved'
                syllabus.save()
                messages.success(request, f'Syllabus "{syllabus.title}" approved successfully.')
            except Syllabus.DoesNotExist:
                messages.error(request, 'Syllabus not found.')
        
        elif action == 'reject_syllabus':
            syllabus_id = request.POST.get('syllabus_id')
            try:
                syllabus = Syllabus.objects.get(id=syllabus_id)
                syllabus.status = 'rejected'
                syllabus.save()
                messages.success(request, f'Syllabus "{syllabus.title}" rejected successfully.')
            except Syllabus.DoesNotExist:
                messages.error(request, 'Syllabus not found.')
        
        return redirect('admin_manage_syllabus')
    
    context = {
        'syllabi': syllabi,
        'subjects': subjects,
    }
    return render(request, 'admin_manage_syllabus.html', context)


@login_required
def admin_manage_notes(request):
    """Admin view to manage notes"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    notes = Note.objects.all().order_by('-created_at')
    subjects = Subject.objects.filter(is_active=True).order_by('faculty__name', 'level', 'name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_note':
            title = request.POST.get('title')
            subject_id = request.POST.get('subject')
            description = request.POST.get('description', '')
            file = request.FILES.get('file')
            
            if title and subject_id and file:
                try:
                    subject = Subject.objects.get(id=subject_id)
                    note = Note.objects.create(
                        title=title,
                        subject=subject,
                        description=description,
                        file=file,
                        uploaded_by=request.user,
                        status='approved'  # Auto-approve admin uploads
                    )
                    messages.success(request, f'Note "{title}" added successfully.')
                except Subject.DoesNotExist:
                    messages.error(request, 'Selected subject not found.')
                except Exception as e:
                    messages.error(request, f'Error adding note: {str(e)}')
            else:
                messages.error(request, 'Title, subject, and file are required.')
        
        elif action == 'delete_note':
            note_id = request.POST.get('note_id')
            try:
                note = Note.objects.get(id=note_id)
                note_name = note.title
                note.delete()
                messages.success(request, f'Note "{note_name}" deleted successfully.')
            except Note.DoesNotExist:
                messages.error(request, 'Note not found.')
        
        elif action == 'approve_note':
            note_id = request.POST.get('note_id')
            try:
                note = Note.objects.get(id=note_id)
                note.status = 'approved'
                note.save()
                messages.success(request, f'Note "{note.title}" approved successfully.')
            except Note.DoesNotExist:
                messages.error(request, 'Note not found.')
        
        elif action == 'reject_note':
            note_id = request.POST.get('note_id')
            try:
                note = Note.objects.get(id=note_id)
                note.status = 'rejected'
                note.save()
                messages.success(request, f'Note "{note.title}" rejected successfully.')
            except Note.DoesNotExist:
                messages.error(request, 'Note not found.')
        
        return redirect('admin_manage_notes')
    
    context = {
        'notes': notes,
        'subjects': subjects,
    }
    return render(request, 'admin_manage_notes.html', context)


@login_required
def admin_manage_question_banks(request):
    """Admin view to manage question banks"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    question_banks = QuestionBank.objects.all().order_by('-created_at')
    subjects = Subject.objects.filter(is_active=True).order_by('faculty__name', 'level', 'name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_question_bank':
            title = request.POST.get('title')
            subject_id = request.POST.get('subject')
            description = request.POST.get('description', '')
            file = request.FILES.get('file')
            
            if title and subject_id and file:
                try:
                    subject = Subject.objects.get(id=subject_id)
                    question_bank = QuestionBank.objects.create(
                        title=title,
                        subject=subject,
                        description=description,
                        file=file,
                        uploaded_by=request.user,
                        status='approved'  # Auto-approve admin uploads
                    )
                    messages.success(request, f'Question Bank "{title}" added successfully.')
                except Subject.DoesNotExist:
                    messages.error(request, 'Selected subject not found.')
                except Exception as e:
                    messages.error(request, f'Error adding question bank: {str(e)}')
            else:
                messages.error(request, 'Title, subject, and file are required.')
        
        elif action == 'delete_question_bank':
            qb_id = request.POST.get('question_bank_id')
            try:
                qb = QuestionBank.objects.get(id=qb_id)
                qb_name = qb.title
                qb.delete()
                messages.success(request, f'Question Bank "{qb_name}" deleted successfully.')
            except QuestionBank.DoesNotExist:
                messages.error(request, 'Question Bank not found.')
        
        elif action == 'approve_question_bank':
            qb_id = request.POST.get('question_bank_id')
            try:
                qb = QuestionBank.objects.get(id=qb_id)
                qb.status = 'approved'
                qb.save()
                messages.success(request, f'Question Bank "{qb.title}" approved successfully.')
            except QuestionBank.DoesNotExist:
                messages.error(request, 'Question Bank not found.')
        
        elif action == 'reject_question_bank':
            qb_id = request.POST.get('question_bank_id')
            try:
                qb = QuestionBank.objects.get(id=qb_id)
                qb.status = 'rejected'
                qb.save()
                messages.success(request, f'Question Bank "{qb.title}" rejected successfully.')
            except QuestionBank.DoesNotExist:
                messages.error(request, 'Question Bank not found.')
        
        return redirect('admin_manage_question_banks')
    
    context = {
        'question_banks': question_banks,
        'subjects': subjects,
    }
    return render(request, 'admin_manage_question_banks.html', context)

@login_required
def admin_manage_faculties(request):
    """Admin view to manage faculties"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    faculties = Faculty.objects.all().order_by('name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_faculty':
            name = request.POST.get('name')
            slug = request.POST.get('slug')
            description = request.POST.get('description')
            academic_structure = request.POST.get('academic_structure')
            total_levels = request.POST.get('total_levels')
            
            if name and slug and academic_structure and total_levels:
                try:
                    Faculty.objects.create(
                        name=name,
                        slug=slug,
                        description=description,
                        academic_structure=academic_structure,
                        total_levels=total_levels,
                        is_active=True
                    )
                    messages.success(request, f'Faculty "{name}" added successfully.')
                except Exception as e:
                    messages.error(request, f'Error adding faculty: {str(e)}')
            else:
                messages.error(request, 'Name, slug, academic structure, and total levels are required.')
        
        elif action == 'edit_faculty':
            faculty_id = request.POST.get('faculty_id')
            name = request.POST.get('name')
            slug = request.POST.get('slug')
            description = request.POST.get('description')
            academic_structure = request.POST.get('academic_structure')
            total_levels = request.POST.get('total_levels')
            is_active = request.POST.get('is_active') == 'on'
            
            try:
                faculty = Faculty.objects.get(id=faculty_id)
                faculty.name = name
                faculty.slug = slug
                faculty.description = description
                faculty.academic_structure = academic_structure
                faculty.total_levels = total_levels
                faculty.is_active = is_active
                faculty.save()
                messages.success(request, f'Faculty "{name}" updated successfully.')
            except Faculty.DoesNotExist:
                messages.error(request, 'Faculty not found.')
        
        elif action == 'delete_faculty':
            faculty_id = request.POST.get('faculty_id')
            try:
                faculty = Faculty.objects.get(id=faculty_id)
                faculty_name = faculty.name
                faculty.delete()
                messages.success(request, f'Faculty "{faculty_name}" deleted successfully.')
            except Faculty.DoesNotExist:
                messages.error(request, 'Faculty not found.')
        
        return redirect('admin_manage_faculties')
    
    context = {
        'faculties': faculties,
    }
    return render(request, 'admin_manage_faculties.html', context)

@login_required
def admin_manage_contributor_requests(request):
    """Admin view to manage contributor requests"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    requests = ContributorRequest.objects.all().order_by('-submitted_at')
    faculties = Faculty.objects.filter(is_active=True)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve_request':
            request_id = request.POST.get('request_id')
            try:
                contributor_request = ContributorRequest.objects.get(id=request_id)
                contributor_request.status = 'approved'
                contributor_request.reviewed_by = request.user
                contributor_request.reviewed_at = timezone.now()
                contributor_request.save()
                
                # Update user profile
                user_profile = UserProfile.objects.get(user=contributor_request.user)
                user_profile.is_contributor_approved = True
                user_profile.contributor_since = timezone.now()
                user_profile.save()
                
                messages.success(request, f'Contributor request for {contributor_request.user.username} approved successfully.')
            except ContributorRequest.DoesNotExist:
                messages.error(request, 'Contributor request not found.')
        
        elif action == 'reject_request':
            request_id = request.POST.get('request_id')
            admin_notes = request.POST.get('admin_notes', '')
            try:
                contributor_request = ContributorRequest.objects.get(id=request_id)
                contributor_request.status = 'rejected'
                contributor_request.reviewed_by = request.user
                contributor_request.reviewed_at = timezone.now()
                contributor_request.admin_notes = admin_notes
                contributor_request.save()
                messages.success(request, f'Contributor request for {contributor_request.user.username} rejected.')
            except ContributorRequest.DoesNotExist:
                messages.error(request, 'Contributor request not found.')
        
        elif action == 'delete_request':
            request_id = request.POST.get('request_id')
            try:
                contributor_request = ContributorRequest.objects.get(id=request_id)
                contributor_request.delete()
                messages.success(request, 'Contributor request deleted successfully.')
            except ContributorRequest.DoesNotExist:
                messages.error(request, 'Contributor request not found.')
        
        return redirect('admin_manage_contributor_requests')
    
    context = {
        'requests': requests,
        'faculties': faculties,
    }
    return render(request, 'admin_manage_contributor_requests.html', context)


@login_required
def admin_manage_contacts(request):
    """Admin view to manage contact messages"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    contacts = ContactMessage.objects.all().order_by('-submitted_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'respond_to_contact':
            contact_id = request.POST.get('contact_id')
            admin_response = request.POST.get('admin_response', '')
            status = request.POST.get('status', 'in_progress')
            
            try:
                contact = ContactMessage.objects.get(id=contact_id)
                contact.admin_response = admin_response
                contact.status = status
                contact.responded_by = request.user
                contact.responded_at = timezone.now()
                contact.save()
                messages.success(request, 'Response sent successfully.')
            except ContactMessage.DoesNotExist:
                messages.error(request, 'Contact message not found.')
        
        elif action == 'delete_contact':
            contact_id = request.POST.get('contact_id')
            try:
                contact = ContactMessage.objects.get(id=contact_id)
                contact.delete()
                messages.success(request, 'Contact message deleted successfully.')
            except ContactMessage.DoesNotExist:
                messages.error(request, 'Contact message not found.')
        
        return redirect('admin_manage_contacts')
    
    context = {
        'contacts': contacts,
    }
    return render(request, 'admin_manage_contacts.html', context)
