from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
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
    Subject, Notice, Syllabus, QuestionBank, QuestionBankSolution, Note, Chapter, Viva, TextBook, Practical, Subscription, 
    Faculty, UserProfile, ContactMessage, ContributorRequest,
    DownloadLog, ViewLog, MCQQuestion, MCQOption, MCQUserAnswer, MCQQuizSession, MCQQuiz
)
from .forms import (
    ContributeResourceForm, ContributorRequestForm, EnhancedContactForm,
    UserRegistrationForm, UserProfileForm, AdminResponseForm,
    ResourceFilterForm, AdvancedSearchForm, MCQQuestionForm, MCQOptionForm,
    MCQQuizForm, FacultySelectionForm, SubjectSelectionForm
)

def invalidate_user_recommendations_cache(user_id):
    """Invalidate user recommendations cache when user activity changes"""
    cache_key = f"user_recommendations_{user_id}"
    cache.delete(cache_key)


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
    
    # Get recommendations for authenticated users (excluding admins)
    recommendations = None
    if request.user.is_authenticated and not request.user.is_superuser:
        from .recommend_utils import get_user_recommendations, get_user_faculty
        
        # Create a cache key that includes user ID and recent activity timestamp
        # This ensures recommendations update when user activity changes
        user_activity_key = f"user_recommendations_{request.user.id}"
        
        # Check if we have cached recommendations
        recommendations = cache.get(user_activity_key)
        
        if not recommendations:
            # Generate fresh recommendations
            recommendations = get_user_recommendations(request.user, limit=6)
            # Cache for 10 minutes - short enough to feel dynamic, long enough to be efficient
            cache.set(user_activity_key, recommendations, 600)
        else:
            # For better user experience, we can also generate fresh recommendations
            # in the background and update cache asynchronously
            recommendations = get_user_recommendations(request.user, limit=6)
            cache.set(user_activity_key, recommendations, 600)
    
    context = {
        'latest_notices': latest_notices,
        'trending_subjects': trending_subjects,
        'recent_resources': recent_resources,
        'recommendations': recommendations,
    }
    return render(request, 'general/home.html', context)

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
    return render(request, 'auth/login.html')

def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # UserProfile is automatically created by signal handler in models.py
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})

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
    return render(request, 'general/dashboard.html', context)

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
    
    return render(request, 'general/profile.html', context)

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
    
    return render(request, 'faculty/faculty_selection.html', {'faculties': faculties})

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
    
    return render(request, 'faculty/faculty_overview.html', context)


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
    
    return render(request, 'faculty/faculty_subjects.html', context)

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
        # Invalidate user recommendations cache to ensure dynamic updates
        invalidate_user_recommendations_cache(request.user.id)
    
    notices = Notice.objects.filter(subject=subject, is_general=False)
    syllabus = Syllabus.objects.filter(subject=subject, status='approved').first()
    question_banks = QuestionBank.objects.filter(subject=subject, status='approved')
    question_bank_solutions = QuestionBankSolution.objects.filter(subject=subject, status='approved')
    notes = Note.objects.filter(subject=subject, status='approved')
    chapters = Chapter.objects.filter(subject=subject, status='approved').order_by('chapter_number')
    
    return render(request, 'subject/subject_detail.html', {
        'subject': subject,
        'notices': notices,
        'syllabus': syllabus,
        'question_banks': question_banks,
        'question_bank_solutions': question_bank_solutions,
        'notes': notes,
        'chapters': chapters
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
    
    return render(request, 'subject/subject_syllabus.html', {'subject': subject, 'syllabi': syllabi})

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
    
    return render(request, 'subject/subject_questions.html', {'subject': subject, 'questions': questions})

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
    
    return render(request, 'subject/subject_notes.html', {'subject': subject, 'notes': notes})

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
                return render(request, 'general/contribute_resource.html', {'form': form})
            
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
    
    return render(request, 'general/contribute_resource.html', {'form': form})

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
    
    return render(request, 'general/contributor_request.html', {'form': form})

def contact_view(request):
    if request.method == "POST":
        form = EnhancedContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect("contact")
    else:
        form = EnhancedContactForm()
    
    return render(request, 'general/contact.html', {'form': form})

def notice_list(request):
    general_notices = Notice.objects.filter(is_general=True).order_by('-created_at')
    return render(request, 'general/notices.html', {'notices': general_notices})

def notice_detail(request, notice_id):
    """Display individual notice details"""
    try:
        notice = Notice.objects.get(id=notice_id)
        return render(request, 'general/notice_detail.html', {'notice': notice})
    except Notice.DoesNotExist:
        messages.error(request, 'Notice not found.')
        return redirect('notice_list')

def about(request):
    return render(request, 'general/about.html')

def year(request):
    return redirect('home')

def contact(request):
    return redirect('contact_view')

def register(request):
    return render(request, 'auth/register.html')

def login_page(request):
    return render(request, 'auth/login.html')


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
    
    subjects = Subject.objects.filter(is_active=True).select_related('faculty')
    syllabi = Syllabus.objects.filter(status='approved').select_related('subject', 'subject__faculty')
    questionbanks = QuestionBank.objects.filter(status='approved').select_related('subject', 'subject__faculty')
    chapters = Chapter.objects.filter(status='approved').select_related('subject', 'subject__faculty')
    vivas = Viva.objects.filter(status='approved').select_related('subject', 'subject__faculty')
    textbooks = TextBook.objects.filter(status='approved').select_related('subject', 'subject__faculty')
    practicals = Practical.objects.filter(status='approved').select_related('subject', 'subject__faculty')
    
    if query:
        subjects = subjects.filter(Q(name__icontains=query) | Q(description__icontains=query))
        syllabi = syllabi.filter(Q(title__icontains=query) | Q(content__icontains=query))
        questionbanks = questionbanks.filter(Q(title__icontains=query) | Q(description__icontains=query))
        chapters = chapters.filter(Q(title__icontains=query) | Q(description__icontains=query))
        vivas = vivas.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(question__icontains=query) | Q(answer__icontains=query))
        textbooks = textbooks.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(author__icontains=query) | Q(publisher__icontains=query))
        practicals = practicals.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(objective__icontains=query) | Q(procedure__icontains=query))
    
    if faculty_id:
        subjects = subjects.filter(faculty_id=faculty_id)
        syllabi = syllabi.filter(subject__faculty_id=faculty_id)
        questionbanks = questionbanks.filter(subject__faculty_id=faculty_id)
        chapters = chapters.filter(subject__faculty_id=faculty_id)
        vivas = vivas.filter(subject__faculty_id=faculty_id)
        textbooks = textbooks.filter(subject__faculty_id=faculty_id)
        practicals = practicals.filter(subject__faculty_id=faculty_id)
    
    if subject_id:
        subjects = subjects.filter(id=subject_id)
        syllabi = syllabi.filter(subject_id=subject_id)
        questionbanks = questionbanks.filter(subject_id=subject_id)
        chapters = chapters.filter(subject_id=subject_id)
        vivas = vivas.filter(subject_id=subject_id)
        textbooks = textbooks.filter(subject_id=subject_id)
        practicals = practicals.filter(subject_id=subject_id)
    
    if level:
        subjects = subjects.filter(level=level)
        syllabi = syllabi.filter(subject__level=level)
        questionbanks = questionbanks.filter(subject__level=level)
        chapters = chapters.filter(subject__level=level)
        vivas = vivas.filter(subject__level=level)
        textbooks = textbooks.filter(subject__level=level)
        practicals = practicals.filter(subject__level=level)
    
    results = []
    if not resource_type or resource_type == 'subject':
        results += list(subjects)
    if not resource_type or resource_type == 'syllabus':
        results += list(syllabi)
    if not resource_type or resource_type == 'questionbank':
        results += list(questionbanks)
    if not resource_type or resource_type == 'chapter':
        results += list(chapters)
    if not resource_type or resource_type == 'viva':
        results += list(vivas)
    if not resource_type or resource_type == 'textbook':
        results += list(textbooks)
    if not resource_type or resource_type == 'practical':
        results += list(practicals)
    
    results = sorted(results, key=lambda x: getattr(x, 'name', getattr(x, 'title', '')).lower())
    paginator = Paginator(results, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    faculties = Faculty.objects.filter(is_active=True)
    subjects = Subject.objects.filter(is_active=True)
    
    # Group results by type for template
    search_results = {
        'subjects': [item for item in results if item.__class__.__name__ == 'Subject'],
        'syllabi': [item for item in results if item.__class__.__name__ == 'Syllabus'],
        'question_banks': [item for item in results if item.__class__.__name__ == 'QuestionBank'],
        'chapters': [item for item in results if item.__class__.__name__ == 'Chapter'],
        'vivas': [item for item in results if item.__class__.__name__ == 'Viva'],
        'textbooks': [item for item in results if item.__class__.__name__ == 'TextBook'],
        'practicals': [item for item in results if item.__class__.__name__ == 'Practical']
    }
    
    # Calculate search statistics
    search_stats = {
        'total_results': len(results),
        'subjects_count': len(search_results['subjects']),
        'syllabi_count': len(search_results['syllabi']),
        'question_banks_count': len(search_results['question_banks']),
        'chapters_count': len(search_results['chapters']),
        'vivas_count': len(search_results['vivas']),
        'textbooks_count': len(search_results['textbooks']),
        'practicals_count': len(search_results['practicals'])
    }
    
    return render(request, 'general/search.html', {
        'page_obj': page_obj,
        'faculties': faculties,
        'subjects': subjects,
        'query': query,
        'faculty_id': faculty_id,
        'subject_id': subject_id,
        'resource_type': resource_type,
        'level': level,
        'search_results': search_results,
        'search_stats': search_stats
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
        elif content_type == 'chapter':
            resource = get_object_or_404(Chapter, id=content_id, status='approved')
        elif content_type == 'textbook':
            resource = get_object_or_404(TextBook, id=content_id, status='approved')
        elif content_type == 'practical':
            resource = get_object_or_404(Practical, id=content_id, status='approved')
        else:
            return HttpResponse('Invalid content type', status=400)
        
        # Log download
        DownloadLog.objects.create(
            user=request.user,
            content_type=content_type,
            content_id=content_id,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        # Invalidate user recommendations cache to ensure dynamic updates
        invalidate_user_recommendations_cache(request.user.id)
        
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
                messages.error(request, f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}")
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
            messages.error(request, f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}")
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
def add_question_bank_solution(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Check if user has permission to add question bank solution
    user_profile = UserProfile.objects.get(user=request.user)
    if not user_profile.can_upload() and not request.user.is_superuser:
        messages.error(request, 'You need contributor access to add question bank solutions.')
        return redirect('subject_detail', subject_id=subject_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        
        # Validate required fields
        if not title:
            messages.error(request, 'Title is required.')
            return render(request, 'add_question_bank_solution.html', {'subject': subject})
        
        if not file:
            messages.error(request, 'File is required for question bank solutions.')
            return render(request, 'add_question_bank_solution.html', {'subject': subject})
        
        # Validate file
        # Check file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            messages.error(request, 'File size must be under 10MB.')
            return render(request, 'add_question_bank_solution.html', {'subject': subject})
        
        # Check file extension
        allowed_extensions = ['pdf', 'doc', 'docx', 'txt']
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            messages.error(request, f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}")
            return render(request, 'add_question_bank_solution.html', {'subject': subject})
        
        try:
            QuestionBankSolution.objects.create(
                subject=subject,
                title=title,
                description=description or '',
                file=file,
                uploaded_by=request.user,
                status='pending' if not request.user.is_superuser else 'approved'
            )
            messages.success(request, 'Question bank solution added successfully!')
            return redirect('subject_detail', subject_id=subject_id)
        except Exception as e:
            messages.error(request, f'Error adding question bank solution: {str(e)}')
            return render(request, 'add_question_bank_solution.html', {'subject': subject})
    
    return render(request, 'add_question_bank_solution.html', {'subject': subject})

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
    faculties = Faculty.objects.filter(is_active=True).order_by('name')
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
def admin_approve_resource(request):
    """Admin function to approve pending resources"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        resource_type = request.POST.get('resource_type')
        resource_id = request.POST.get('resource_id')
        
        try:
            if resource_type == 'syllabus':
                resource = get_object_or_404(Syllabus, id=resource_id)
            elif resource_type == 'note':
                resource = get_object_or_404(Note, id=resource_id)
            elif resource_type == 'question_bank':
                resource = get_object_or_404(QuestionBank, id=resource_id)
            elif resource_type == 'chapter':
                resource = get_object_or_404(Chapter, id=resource_id)
            else:
                messages.error(request, 'Invalid resource type.')
                return redirect('admin_dashboard')
            
            resource.status = 'approved'
            resource.save()
            messages.success(request, f'{resource_type.title()} approved successfully!')
            
        except Exception as e:
            messages.error(request, f'Error approving resource: {str(e)}')
    
    return redirect('admin_dashboard')

@login_required
def admin_reject_resource(request):
    """Admin function to reject pending resources"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        resource_type = request.POST.get('resource_type')
        resource_id = request.POST.get('resource_id')
        rejection_reason = request.POST.get('rejection_reason', 'Rejected by admin')
        
        try:
            if resource_type == 'syllabus':
                resource = get_object_or_404(Syllabus, id=resource_id)
            elif resource_type == 'note':
                resource = get_object_or_404(Note, id=resource_id)
            elif resource_type == 'question_bank':
                resource = get_object_or_404(QuestionBank, id=resource_id)
            elif resource_type == 'chapter':
                resource = get_object_or_404(Chapter, id=resource_id)
            else:
                messages.error(request, 'Invalid resource type.')
                return redirect('admin_dashboard')
            
            resource.status = 'rejected'
            resource.rejection_reason = rejection_reason
            resource.save()
            messages.success(request, f'{resource_type.title()} rejected successfully!')
            
        except Exception as e:
            messages.error(request, f'Error rejecting resource: {str(e)}')
    
    return redirect('admin_dashboard')

@login_required
def admin_preview_resource(request):
    """Admin function to preview resources"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    resource_type = request.GET.get('type')
    resource_id = request.GET.get('id')
    
    try:
        if resource_type == 'syllabus':
            resource = get_object_or_404(Syllabus, id=resource_id)
        elif resource_type == 'note':
            resource = get_object_or_404(Note, id=resource_id)
        elif resource_type == 'question_bank':
            resource = get_object_or_404(QuestionBank, id=resource_id)
        elif resource_type == 'chapter':
            resource = get_object_or_404(Chapter, id=resource_id)
        else:
            messages.error(request, 'Invalid resource type.')
            return redirect('admin_dashboard')
        
        context = {
            'resource': resource,
            'resource_type': resource_type,
        }
        
        return render(request, 'admin/resource_preview.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading resource: {str(e)}')
        return redirect('admin_dashboard')

@login_required
def syllabus_detail(request, subject_id, syllabus_id):
    """Display syllabus detail"""
    subject = get_object_or_404(Subject, id=subject_id)
    syllabus = get_object_or_404(Syllabus, id=syllabus_id, subject=subject)
    
    # Check if user has access to this subject (basic check)
    if not request.user.is_authenticated:
        messages.error(request, 'You need to be logged in to access syllabus.')
        return redirect('login')
    
    # Log view
    ViewLog.objects.create(
        user=request.user,
        content_type='syllabus',
        content_id=syllabus.id,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    # Invalidate user recommendations cache to ensure dynamic updates
    invalidate_user_recommendations_cache(request.user.id)
    
    # Get related syllabi
    related_syllabi = Syllabus.objects.filter(
        subject=subject,
        status='approved'
    ).exclude(id=syllabus_id)[:5]
    
    context = {
        'subject': subject,
        'syllabus': syllabus,
        'related_syllabi': related_syllabi,
    }
    
    return render(request, 'subject/syllabus_detail.html', context)

@login_required
def question_bank_detail(request, subject_id, question_bank_id):
    """Display question bank detail"""
    subject = get_object_or_404(Subject, id=subject_id)
    question_bank = get_object_or_404(QuestionBank, id=question_bank_id, subject=subject)
    
    # Check if user has access to this subject (basic check)
    if not request.user.is_authenticated:
        messages.error(request, 'You need to be logged in to access question banks.')
        return redirect('login')
    
    # Log view
    ViewLog.objects.create(
        user=request.user,
        content_type='questionbank',
        content_id=question_bank.id,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    # Invalidate user recommendations cache to ensure dynamic updates
    invalidate_user_recommendations_cache(request.user.id)
    
    # Get related question banks
    related_question_banks = QuestionBank.objects.filter(
        subject=subject,
        status='approved'
    ).exclude(id=question_bank_id)[:5]
    
    context = {
        'subject': subject,
        'question_bank': question_bank,
        'related_question_banks': related_question_banks,
    }
    
    return render(request, 'subject/question_bank_detail.html', context)

@login_required
def question_bank_solution_detail(request, subject_id, solution_id):
    """Display question bank solution detail"""
    subject = get_object_or_404(Subject, id=subject_id)
    solution = get_object_or_404(QuestionBankSolution, id=solution_id, subject=subject)
    
    # Check if user has access to this subject (basic check)
    if not request.user.is_authenticated:
        messages.error(request, 'You need to be logged in to access question bank solutions.')
        return redirect('login')
    
    # Log view
    ViewLog.objects.create(
        user=request.user,
        content_type='questionbanksolution',
        content_id=solution.id,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    # Invalidate user recommendations cache to ensure dynamic updates
    invalidate_user_recommendations_cache(request.user.id)
    
    # Get related question bank solutions
    related_solutions = QuestionBankSolution.objects.filter(
        subject=subject,
        status='approved'
    ).exclude(id=solution_id)[:5]
    
    context = {
        'subject': subject,
        'solution': solution,
        'related_solutions': related_solutions,
    }
    
    return render(request, 'subject/question_bank_solution_detail.html', context)

@login_required
def edit_profile(request):
    """Edit user profile"""
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'role': 'student',
            'bio': '',
        }
    )
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            profile = form.save()
            return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = UserProfileForm(instance=user_profile)
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            form_html = render_to_string('general/profile_edit_form.html', {
                'form': form,
                'user_profile': user_profile,
                'user': request.user
            })
            return JsonResponse({'form_html': form_html})
        else:
            return render(request, 'general/profile_edit_form.html', {
                'form': form,
                'user_profile': user_profile,
                'user': request.user
            })

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
    total_chapters = Chapter.objects.count()
    total_resources = total_syllabi + total_notes + total_question_banks + total_chapters
    
    # Approval statistics
    pending_syllabi = Syllabus.objects.filter(status='pending').count()
    pending_notes = Note.objects.filter(status='pending').count()
    pending_question_banks = QuestionBank.objects.filter(status='pending').count()
    pending_chapters = Chapter.objects.filter(status='pending').count()
    total_pending = pending_syllabi + pending_notes + pending_question_banks + pending_chapters
    
    approved_syllabi = Syllabus.objects.filter(status='approved').count()
    approved_notes = Note.objects.filter(status='approved').count()
    approved_question_banks = QuestionBank.objects.filter(status='approved').count()
    approved_chapters = Chapter.objects.filter(status='approved').count()
    total_approved = approved_syllabi + approved_notes + approved_question_banks + approved_chapters
    
    # Get faculties for faculty management section
    faculties = Faculty.objects.filter(is_active=True).annotate(
        subject_count=Count('subjects', filter=Q(subjects__is_active=True)),
        resource_count=Count('subjects__syllabi', filter=Q(subjects__syllabi__status='approved')) +
                     Count('subjects__notes', filter=Q(subjects__notes__status='approved')) +
                     Count('subjects__question_banks', filter=Q(subjects__question_banks__status='approved')) +
                     Count('subjects__chapters', filter=Q(subjects__chapters__status='approved'))
    ).order_by('name')
    
    # Faculty-wise statistics with level breakdown
    faculty_stats = []
    for faculty in Faculty.objects.filter(is_active=True):
        faculty_subjects = Subject.objects.filter(faculty=faculty).count()
        faculty_syllabi = Syllabus.objects.filter(subject__faculty=faculty).count()
        faculty_notes = Note.objects.filter(subject__faculty=faculty).count()
        faculty_questions = QuestionBank.objects.filter(subject__faculty=faculty).count()
        faculty_chapters = Chapter.objects.filter(subject__faculty=faculty).count()
        
        # Get level-wise breakdown for this faculty
        level_breakdown = []
        for level in range(1, faculty.total_levels + 1):
            level_subjects = Subject.objects.filter(faculty=faculty, level=level)
            level_syllabi = Syllabus.objects.filter(subject__faculty=faculty, subject__level=level).count()
            level_questions = QuestionBank.objects.filter(subject__faculty=faculty, subject__level=level).count()
            level_chapters = Chapter.objects.filter(subject__faculty=faculty, subject__level=level).count()
            level_textbooks = TextBook.objects.filter(subject__faculty=faculty, subject__level=level).count()
            level_practicals = Practical.objects.filter(subject__faculty=faculty, subject__level=level).count()
            level_vivas = Viva.objects.filter(subject__faculty=faculty, subject__level=level).count()
            
            level_breakdown.append({
                'level': level,
                'level_name': faculty.get_level_display_name(level),
                'subjects': level_subjects.count(),
                'syllabi': level_syllabi,
                'questions': level_questions,
                'chapters': level_chapters,
                'textbooks': level_textbooks,
                'practicals': level_practicals,
                'vivas': level_vivas,
                'total_resources': level_syllabi + level_questions + level_chapters + level_textbooks + level_practicals + level_vivas,
                'subject_list': list(level_subjects.values('id', 'name', 'level'))
            })
        
        faculty_stats.append({
            'faculty': faculty,
            'subjects': faculty_subjects,
            'syllabi': faculty_syllabi,
            'notes': faculty_notes,
            'questions': faculty_questions,
            'chapters': faculty_chapters,
            'total_resources': faculty_syllabi + faculty_notes + faculty_questions + faculty_chapters,
            'level_breakdown': level_breakdown
        })
    
    # Recent activity
    recent_uploads = []
    recent_uploads.extend(list(Syllabus.objects.all().order_by('-created_at')[:5]))
    recent_uploads.extend(list(Note.objects.all().order_by('-created_at')[:5]))
    recent_uploads.extend(list(QuestionBank.objects.all().order_by('-created_at')[:5]))
    recent_uploads.extend(list(Chapter.objects.all().order_by('-created_at')[:5]))
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
    pending_approvals.extend(list(Chapter.objects.filter(status='pending').order_by('-created_at')[:5]))
    pending_approvals.sort(key=lambda x: x.created_at, reverse=True)
    pending_approvals = pending_approvals[:10]
    
    # Contributor requests
    contributor_requests = ContributorRequest.objects.filter(status='pending').order_by('-submitted_at')[:10]
    contributor_requests_count = ContributorRequest.objects.filter(status='pending').count()
    
    # Contact messages
    recent_contacts = ContactMessage.objects.filter(status='pending').order_by('-submitted_at')[:10]
    
    # MCQ Statistics
    total_mcq_questions = MCQQuestion.objects.count()
    published_mcq_questions = MCQQuestion.objects.filter(published=True).count()
    total_mcq_quizzes = MCQQuizSession.objects.count()
    
    # Recent MCQ Questions
    recent_mcq_questions = MCQQuestion.objects.select_related('quiz', 'created_by', 'quiz__faculty').order_by('-created_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_subjects': total_subjects,
        'total_faculties': total_faculties,
        'total_resources': total_resources,
        'total_pending': total_pending,
        'total_approved': total_approved,
        'contributor_requests_count': contributor_requests_count,
        'faculty_stats': faculty_stats,
        'faculties': faculties,
        'recent_uploads': recent_uploads,
        'pending_approvals': pending_approvals,
        'contributor_requests': contributor_requests,
        'recent_contacts': recent_contacts,
        'total_mcq_questions': total_mcq_questions,
        'published_mcq_questions': published_mcq_questions,
        'total_mcq_quizzes': total_mcq_quizzes,
        'recent_mcq_questions': recent_mcq_questions,
        'resource_breakdown': {
            'syllabi': {'total': total_syllabi, 'pending': pending_syllabi, 'approved': approved_syllabi},
            'notes': {'total': total_notes, 'pending': pending_notes, 'approved': approved_notes},
            'question_banks': {'total': total_question_banks, 'pending': pending_question_banks, 'approved': approved_question_banks},
            'chapters': {'total': total_chapters, 'pending': pending_chapters, 'approved': approved_chapters},
        }
    }
    
    return render(request, 'admin/admin_dashboard.html', context)

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
    return render(request, 'admin/admin_manage_subjects.html', context)


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
    return render(request, 'admin/admin_manage_syllabus.html', context)


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
    return render(request, 'admin/admin_manage_notes.html', context)


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
    return render(request, 'admin/admin_manage_question_banks.html', context)

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
    return render(request, 'admin/admin_manage_faculties.html', context)

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
    return render(request, 'admin/admin_manage_contributor_requests.html', context)


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
    return render(request, 'admin/admin_manage_contacts.html', context)


def chapter_detail(request, subject_id, chapter_id):
    """Chapter detail view with PDF viewer and sidebar navigation"""
    subject = get_object_or_404(Subject, id=subject_id)
    chapter = get_object_or_404(Chapter, id=chapter_id, subject=subject, status='approved')
    chapters = Chapter.objects.filter(subject=subject, status='approved').order_by('chapter_number')
    
    # Increment view count
    chapter.increment_view()
    
    context = {
        'subject': subject,
        'chapter': chapter,
        'chapters': chapters,
    }
    return render(request, 'subject/chapter_detail.html', context)


def download_chapter(request, chapter_id):
    """Download chapter file"""
    chapter = get_object_or_404(Chapter, id=chapter_id, status='approved')
    
    # Check if file exists
    if not chapter.file or not chapter.file.storage.exists(chapter.file.name):
        messages.error(request, 'File not found. Please contact administrator.')
        return redirect('admin_dashboard')
    
    # Increment download count
    chapter.increment_download()
    
    # Log download
    if request.user.is_authenticated:
        DownloadLog.objects.create(
            user=request.user,
            content_type='chapter',
            content_id=chapter.id,
            ip_address=request.META.get('REMOTE_ADDR')
        )
    
    response = FileResponse(chapter.file, as_attachment=True, filename=f"{chapter.title}.pdf")
    return response


@login_required
def admin_manage_chapters(request):
    """Admin view to manage chapters"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    # Get filter parameters
    faculty_filter = request.GET.get('faculty', '')
    subject_filter = request.GET.get('subject', '')
    status_filter = request.GET.get('status', '')
    
    # Get all chapters with related data
    chapters = Chapter.objects.select_related('subject', 'subject__faculty', 'uploaded_by').all()
    
    # Apply filters
    if faculty_filter:
        chapters = chapters.filter(subject__faculty__slug=faculty_filter)
    if subject_filter:
        chapters = chapters.filter(subject_id=subject_filter)
    if status_filter:
        chapters = chapters.filter(status=status_filter)
    
    chapters = chapters.order_by('-created_at')
    subjects = Subject.objects.select_related('faculty').all().order_by('faculty__name', 'name')
    faculties = Faculty.objects.all().order_by('name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve_chapter':
            chapter_id = request.POST.get('chapter_id')
            try:
                chapter = Chapter.objects.get(id=chapter_id)
                chapter.status = 'approved'
                chapter.save()
                messages.success(request, f'Chapter "{chapter.title}" approved successfully.')
            except Chapter.DoesNotExist:
                messages.error(request, 'Chapter not found.')
        
        elif action == 'reject_chapter':
            chapter_id = request.POST.get('chapter_id')
            try:
                chapter = Chapter.objects.get(id=chapter_id)
                chapter.status = 'rejected'
                chapter.save()
                messages.success(request, f'Chapter "{chapter.title}" rejected.')
            except Chapter.DoesNotExist:
                messages.error(request, 'Chapter not found.')
        
        elif action == 'delete_chapter':
            chapter_id = request.POST.get('chapter_id')
            try:
                chapter = Chapter.objects.get(id=chapter_id)
                chapter.delete()
                messages.success(request, 'Chapter deleted successfully.')
            except Chapter.DoesNotExist:
                messages.error(request, 'Chapter not found.')
        
        return redirect('admin_manage_chapters')
    
    context = {
        'chapters': chapters,
        'subjects': subjects,
        'faculties': faculties,
        'current_faculty': faculty_filter,
        'current_subject': subject_filter,
        'current_status': status_filter,
    }
    return render(request, 'admin/admin_manage_chapters.html', context)

def admin_manage_questions(request):
    """Admin view to manage question banks"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    questions = QuestionBank.objects.all().order_by('-created_at')
    subjects = Subject.objects.all().order_by('faculty', 'level', 'name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve_question':
            question_id = request.POST.get('question_id')
            try:
                question = QuestionBank.objects.get(id=question_id)
                question.status = 'approved'
                question.save()
                messages.success(request, f'Question Bank "{question.title}" approved successfully.')
            except QuestionBank.DoesNotExist:
                messages.error(request, 'Question Bank not found.')
        
        elif action == 'reject_question':
            question_id = request.POST.get('question_id')
            try:
                question = QuestionBank.objects.get(id=question_id)
                question.status = 'rejected'
                question.save()
                messages.success(request, f'Question Bank "{question.title}" rejected.')
            except QuestionBank.DoesNotExist:
                messages.error(request, 'Question Bank not found.')
        
        elif action == 'delete_question':
            question_id = request.POST.get('question_id')
            try:
                question = QuestionBank.objects.get(id=question_id)
                question.delete()
                messages.success(request, 'Question Bank deleted successfully.')
            except QuestionBank.DoesNotExist:
                messages.error(request, 'Question Bank not found.')
        
        return redirect('admin_manage_questions')
    
    context = {
        'questions': questions,
        'subjects': subjects,
    }
    return render(request, 'admin/admin_manage_questions.html', context)

def admin_semester_management(request, faculty_slug, level):
    """Admin view to manage subjects in a specific semester/year"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    try:
        faculty = Faculty.objects.get(slug=faculty_slug)
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty not found.')
        return redirect('admin_dashboard')
    
    subjects = Subject.objects.filter(faculty=faculty, level=level).order_by('name')
    
    # Calculate resource counts for this level
    total_syllabi = Syllabus.objects.filter(subject__faculty=faculty, subject__level=level).count()
    total_notes = Note.objects.filter(subject__faculty=faculty, subject__level=level).count()
    total_questions = QuestionBank.objects.filter(subject__faculty=faculty, subject__level=level).count()
    total_chapters = Chapter.objects.filter(subject__faculty=faculty, subject__level=level).count()
    
    level_name = faculty.get_level_display_name(level)
    
    context = {
        'faculty': faculty,
        'level': level,
        'level_name': level_name,
        'subjects': subjects,
        'total_syllabi': total_syllabi,
        'total_notes': total_notes,
        'total_questions': total_questions,
        'total_chapters': total_chapters,
    }
    return render(request, 'admin/semester_management.html', context)

def admin_subject_resources(request, subject_id):
    """Admin view to manage resources for a specific subject"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    try:
        subject = Subject.objects.get(id=subject_id)
    except Subject.DoesNotExist:
        messages.error(request, 'Subject not found.')
        return redirect('admin_dashboard')
    
    # Get all resources for this subject
    chapters = Chapter.objects.filter(subject=subject).order_by('-created_at')
    syllabi = Syllabus.objects.filter(subject=subject).order_by('-created_at')
    notes = Note.objects.filter(subject=subject).order_by('-created_at')
    questions = QuestionBank.objects.filter(subject=subject).order_by('-created_at')
    
    # Check file existence for chapters
    for chapter in chapters:
        if chapter.file:
            import os
            chapter.file_exists = os.path.exists(chapter.file.path)
        else:
            chapter.file_exists = False
    
    context = {
        'subject': subject,
        'chapters': chapters,
        'syllabi': syllabi,
        'notes': notes,
        'questions': questions,
    }
    return render(request, 'admin/subject_resources.html', context)

def admin_add_subject(request):
    """Admin view to add a new subject"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        faculty_id = request.POST.get('faculty_id')
        level = request.POST.get('level')
        
        if name and faculty_id and level:
            try:
                faculty = Faculty.objects.get(id=faculty_id)
                subject = Subject.objects.create(
                    name=name,
                    description=description,
                    faculty=faculty,
                    level=int(level)
                )
                messages.success(request, f'Subject "{name}" added successfully.')
                return redirect('admin_semester_management', faculty.slug, level)
            except Faculty.DoesNotExist:
                messages.error(request, 'Faculty not found.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return redirect('admin_dashboard')

def admin_add_chapter(request):
    """Admin view to add a new chapter"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        subject_id = request.POST.get('subject_id')
        chapter_number = request.POST.get('chapter_number')
        file = request.FILES.get('file')
        
        if title and subject_id and file and chapter_number:
            try:
                subject = Subject.objects.get(id=subject_id)
                chapter = Chapter.objects.create(
                    title=title,
                    description=description,
                    subject=subject,
                    chapter_number=int(chapter_number),
                    file=file,
                    uploaded_by=request.user,
                    status='approved'  # Auto-approve admin uploads
                )
                messages.success(request, f'Chapter "{title}" added successfully.')
                return redirect('admin_subject_resources', subject_id)
            except Subject.DoesNotExist:
                messages.error(request, 'Subject not found.')
            except ValueError:
                messages.error(request, 'Invalid chapter number.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return redirect('admin_dashboard')

def admin_add_syllabus(request):
    """Admin view to add a new syllabus"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        subject_id = request.POST.get('subject_id')
        file = request.FILES.get('file')
        
        if title and subject_id and file:
            try:
                subject = Subject.objects.get(id=subject_id)
                syllabus = Syllabus.objects.create(
                    title=title,
                    description=description,
                    subject=subject,
                    file=file,
                    uploaded_by=request.user,
                    status='approved'  # Auto-approve admin uploads
                )
                messages.success(request, f'Syllabus "{title}" added successfully.')
                return redirect('admin_subject_resources', subject_id)
            except Subject.DoesNotExist:
                messages.error(request, 'Subject not found.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return redirect('admin_dashboard')

def admin_add_note(request):
    """Admin view to add a new note"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        subject_id = request.POST.get('subject_id')
        file = request.FILES.get('file')
        
        if title and subject_id and file:
            try:
                subject = Subject.objects.get(id=subject_id)
                note = Note.objects.create(
                    title=title,
                    description=description,
                    subject=subject,
                    file=file,
                    uploaded_by=request.user,
                    status='approved'  # Auto-approve admin uploads
                )
                messages.success(request, f'Note "{title}" added successfully.')
                return redirect('admin_subject_resources', subject_id)
            except Subject.DoesNotExist:
                messages.error(request, 'Subject not found.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return redirect('admin_dashboard')

def admin_add_question(request):
    """Admin view to add a new question bank"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        subject_id = request.POST.get('subject_id')
        file = request.FILES.get('file')
        
        if title and subject_id and file:
            try:
                subject = Subject.objects.get(id=subject_id)
                question = QuestionBank.objects.create(
                    title=title,
                    description=description,
                    subject=subject,
                    file=file,
                    uploaded_by=request.user,
                    status='approved'  # Auto-approve admin uploads
                )
                messages.success(request, f'Question Bank "{title}" added successfully.')
                return redirect('admin_subject_resources', subject_id)
            except Subject.DoesNotExist:
                messages.error(request, 'Subject not found.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return redirect('admin_dashboard')

def admin_delete_chapter(request):
    """Admin view to delete a chapter"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        chapter_id = request.POST.get('chapter_id')
        if chapter_id:
            try:
                chapter = Chapter.objects.get(id=chapter_id)
                subject_id = chapter.subject.id
                chapter.delete()
                messages.success(request, 'Chapter deleted successfully.')
                return redirect('admin_subject_resources', subject_id)
            except Chapter.DoesNotExist:
                messages.error(request, 'Chapter not found.')
        else:
            messages.error(request, 'Chapter ID not provided.')
    
    return redirect('admin_dashboard')

def admin_delete_syllabus(request):
    """Admin view to delete a syllabus"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        syllabus_id = request.POST.get('syllabus_id')
        if syllabus_id:
            try:
                syllabus = Syllabus.objects.get(id=syllabus_id)
                subject_id = syllabus.subject.id
                syllabus.delete()
                messages.success(request, 'Syllabus deleted successfully.')
                return redirect('admin_subject_resources', subject_id)
            except Syllabus.DoesNotExist:
                messages.error(request, 'Syllabus not found.')
        else:
            messages.error(request, 'Syllabus ID not provided.')
    
    return redirect('admin_dashboard')

def admin_delete_note(request):
    """Admin view to delete a note"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        note_id = request.POST.get('note_id')
        if note_id:
            try:
                note = Note.objects.get(id=note_id)
                subject_id = note.subject.id
                note.delete()
                messages.success(request, 'Note deleted successfully.')
                return redirect('admin_subject_resources', subject_id)
            except Note.DoesNotExist:
                messages.error(request, 'Note not found.')
        else:
            messages.error(request, 'Note ID not provided.')
    
    return redirect('admin_dashboard')

def admin_delete_question(request):
    """Admin view to delete a question bank"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        if question_id:
            try:
                question = QuestionBank.objects.get(id=question_id)
                subject_id = question.subject.id
                question.delete()
                messages.success(request, 'Question Bank deleted successfully.')
                return redirect('admin_subject_resources', subject_id)
            except QuestionBank.DoesNotExist:
                messages.error(request, 'Question Bank not found.')
        else:
            messages.error(request, 'Question Bank ID not provided.')
    
    return redirect('admin_dashboard')


# Article Views - Temporarily disabled
def articles(request):
    """Display all published articles"""
    return render(request, 'articles/article_list.html', {'articles': []})


def article_detail(request, slug):
    """Display individual article"""
    return render(request, 'articles/article_detail.html', {'article': None})


@login_required
def submit_article(request):
    """Submit new article"""
    return render(request, 'articles/submit_article.html', {'categories': []})


@login_required
def edit_article(request, article_id):
    """Edit existing article"""
    return render(request, 'articles/edit_article.html', {'article': None, 'categories': []})


@login_required
def my_articles(request):
    """Display user's articles"""
    return render(request, 'articles/my_articles.html', {'articles': [], 'current_status': None})


@login_required
@require_POST
def like_article(request, article_id):
    """Like/unlike article"""
    return JsonResponse({'liked': False, 'like_count': 0})


@login_required
@require_POST
def add_comment(request, article_id):
    """Add comment to article"""
    return JsonResponse({'success': False})


@login_required
def admin_manage_articles(request):
    """Admin view to manage articles"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    return render(request, 'articles/admin_manage_articles.html', {'articles': [], 'current_status': None})


# Faculty-wise Resource Management System
@login_required
def admin_faculty_management(request):
    """Main faculty management dashboard"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    # Get all faculties with their statistics
    faculties = Faculty.objects.filter(is_active=True).annotate(
        subject_count=Count('subjects', filter=Q(subjects__is_active=True)),
        resource_count=Count('subjects__syllabi', filter=Q(subjects__syllabi__status='approved')) +
                     Count('subjects__question_banks', filter=Q(subjects__question_banks__status='approved')) +
                     Count('subjects__chapters', filter=Q(subjects__chapters__status='approved')) +
                     Count('subjects__textbooks', filter=Q(subjects__textbooks__status='approved')) +
                     Count('subjects__practicals', filter=Q(subjects__practicals__status='approved')) +
                     Count('subjects__vivas', filter=Q(subjects__vivas__status='approved'))
    ).order_by('name')
    
    context = {
        'faculties': faculties,
    }
    return render(request, 'admin/faculty_management.html', context)


@login_required
def admin_faculty_levels(request, faculty_slug):
    """Show semester/year levels for a specific faculty"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    try:
        faculty = Faculty.objects.get(slug=faculty_slug, is_active=True)
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty not found.')
        return redirect('admin_faculty_management')
    
    # Get level-wise statistics
    levels_data = []
    for level in range(1, faculty.total_levels + 1):
        level_subjects = Subject.objects.filter(faculty=faculty, level=level, is_active=True)
        level_syllabi = Syllabus.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        level_questions = QuestionBank.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        level_chapters = Chapter.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        level_textbooks = TextBook.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        level_practicals = Practical.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        level_vivas = Viva.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        
        levels_data.append({
            'level': level,
            'level_name': faculty.get_level_display_name(level),
            'subjects': level_subjects.count(),
            'syllabi': level_syllabi,
            'questions': level_questions,
            'chapters': level_chapters,
            'textbooks': level_textbooks,
            'practicals': level_practicals,
            'vivas': level_vivas,
            'total_resources': level_syllabi + level_questions + level_chapters + level_textbooks + level_practicals + level_vivas,
            'subject_list': list(level_subjects.values('id', 'name', 'level'))
        })
    
    context = {
        'faculty': faculty,
        'levels_data': levels_data,
    }
    return render(request, 'admin/faculty_levels.html', context)


@login_required
def admin_faculty_subjects(request, faculty_slug, level):
    """Manage subjects for a specific faculty and level"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    try:
        faculty = Faculty.objects.get(slug=faculty_slug, is_active=True)
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty not found.')
        return redirect('admin_faculty_management')
    
    # Get subjects for this faculty and level
    subjects = Subject.objects.filter(faculty=faculty, level=level, is_active=True).order_by('name')
    
    # Handle POST requests for subject management
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_subject':
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            if name:
                try:
                    Subject.objects.create(
                        name=name,
                        description=description,
                        faculty=faculty,
                        level=level,
                        is_active=True
                    )
                    messages.success(request, f'Subject "{name}" added successfully.')
                except Exception as e:
                    messages.error(request, f'Error adding subject: {str(e)}')
            else:
                messages.error(request, 'Subject name is required.')
        
        elif action == 'edit_subject':
            subject_id = request.POST.get('subject_id')
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            try:
                subject = Subject.objects.get(id=subject_id, faculty=faculty, level=level)
                subject.name = name
                subject.description = description
                subject.save()
                messages.success(request, f'Subject "{name}" updated successfully.')
            except Subject.DoesNotExist:
                messages.error(request, 'Subject not found.')
            except Exception as e:
                messages.error(request, f'Error updating subject: {str(e)}')
        
        elif action == 'delete_subject':
            subject_id = request.POST.get('subject_id')
            
            try:
                subject = Subject.objects.get(id=subject_id, faculty=faculty, level=level)
                subject_name = subject.name
                subject.delete()
                messages.success(request, f'Subject "{subject_name}" deleted successfully.')
            except Subject.DoesNotExist:
                messages.error(request, 'Subject not found.')
            except Exception as e:
                messages.error(request, f'Error deleting subject: {str(e)}')
        
        return redirect('admin_faculty_subjects', faculty_slug=faculty_slug, level=level)
    
    context = {
        'faculty': faculty,
        'level': level,
        'level_name': faculty.get_level_display_name(level),
        'subjects': subjects,
    }
    return render(request, 'admin/faculty_subjects.html', context)


@login_required
def admin_subject_resources_management(request, subject_id):
    """Manage all resources for a specific subject"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    try:
        subject = Subject.objects.get(id=subject_id, is_active=True)
    except Subject.DoesNotExist:
        messages.error(request, 'Subject not found.')
        return redirect('admin_faculty_management')
    
    # Get all resources for this subject
    chapters = Chapter.objects.filter(subject=subject).order_by('chapter_number')
    syllabi = Syllabus.objects.filter(subject=subject).order_by('-created_at')
    questions = QuestionBank.objects.filter(subject=subject).order_by('-created_at')
    textbooks = TextBook.objects.filter(subject=subject).order_by('-created_at')
    practicals = Practical.objects.filter(subject=subject).order_by('-created_at')
    vivas = Viva.objects.filter(subject=subject).order_by('-created_at')
    
    # Handle POST requests for resource management
    if request.method == 'POST':
        action = request.POST.get('action')
        resource_type = request.POST.get('resource_type')
        
        if action == 'add_resource':
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            file = request.FILES.get('file')
            
            if title:
                try:
                    if resource_type == 'chapter':
                        chapter_number = request.POST.get('chapter_number')
                        if not chapter_number:
                            messages.error(request, 'Chapter number is required.')
                            return redirect('admin_subject_resources_management', subject_id=subject_id)
                        
                        Chapter.objects.create(
                            title=title,
                            description=description,
                            subject=subject,
                            chapter_number=int(chapter_number),
                            file=file,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Chapter "{title}" added successfully.')
                    
                    elif resource_type == 'syllabus':
                        Syllabus.objects.create(
                            title=title,
                            content=description,
                            subject=subject,
                            file=file,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Syllabus "{title}" added successfully.')
                    
                    elif resource_type == 'question':
                        QuestionBank.objects.create(
                            title=title,
                            description=description,
                            subject=subject,
                            file=file,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Question Bank "{title}" added successfully.')
                    
                    elif resource_type == 'textbook':
                        TextBook.objects.create(
                            title=title,
                            author=request.POST.get('author', ''),
                            publisher=request.POST.get('publisher', ''),
                            isbn=request.POST.get('isbn', ''),
                            description=description,
                            subject=subject,
                            file=file,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Textbook "{title}" added successfully.')
                    
                    elif resource_type == 'practical':
                        Practical.objects.create(
                            title=title,
                            description=description,
                            objective=request.POST.get('objective', ''),
                            materials_required=request.POST.get('materials_required', ''),
                            procedure=request.POST.get('procedure', ''),
                            expected_result=request.POST.get('expected_result', ''),
                            difficulty_level=request.POST.get('difficulty_level', 'medium'),
                            subject=subject,
                            file=file,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Practical "{title}" added successfully.')
                    
                    elif resource_type == 'viva':
                        Viva.objects.create(
                            title=title,
                            description=description,
                            question=request.POST.get('question', ''),
                            answer=request.POST.get('answer', ''),
                            difficulty_level=request.POST.get('difficulty_level', 'medium'),
                            subject=subject,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Viva "{title}" added successfully.')
                    
                except Exception as e:
                    messages.error(request, f'Error adding resource: {str(e)}')
            else:
                messages.error(request, 'Title is required.')
        
        elif action == 'delete_resource':
            resource_id = request.POST.get('resource_id')
            
            try:
                if resource_type == 'chapter':
                    resource = Chapter.objects.get(id=resource_id, subject=subject)
                elif resource_type == 'syllabus':
                    resource = Syllabus.objects.get(id=resource_id, subject=subject)
                elif resource_type == 'question':
                    resource = QuestionBank.objects.get(id=resource_id, subject=subject)
                elif resource_type == 'textbook':
                    resource = TextBook.objects.get(id=resource_id, subject=subject)
                elif resource_type == 'practical':
                    resource = Practical.objects.get(id=resource_id, subject=subject)
                elif resource_type == 'viva':
                    resource = Viva.objects.get(id=resource_id, subject=subject)
                else:
                    messages.error(request, 'Invalid resource type.')
                    return redirect('admin_subject_resources_management', subject_id=subject_id)
                
                resource_name = resource.title
                resource.delete()
                messages.success(request, f'{resource_type.title()} "{resource_name}" deleted successfully.')
                
            except Exception as e:
                messages.error(request, f'Error deleting resource: {str(e)}')
        
        return redirect('admin_subject_resources_management', subject_id=subject_id)
    
    # Get level name
    level_name = subject.faculty.get_level_display_name(subject.level) if subject.level else "No Level"
    
    context = {
        'subject': subject,
        'level_name': level_name,
        'chapters': chapters,
        'syllabi': syllabi,
        'questions': questions,
        'textbooks': textbooks,
        'practicals': practicals,
        'vivas': vivas,
    }
    return render(request, 'admin/subject_resources_management.html', context)


# Faculty-wise Resource Management System
@login_required
def admin_faculty_management(request):
    """Main faculty management dashboard"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    # Get all faculties with their statistics
    faculties = Faculty.objects.filter(is_active=True).annotate(
        subject_count=Count('subjects', filter=Q(subjects__is_active=True)),
        resource_count=Count('subjects__syllabi', filter=Q(subjects__syllabi__status='approved')) +
                     Count('subjects__question_banks', filter=Q(subjects__question_banks__status='approved')) +
                     Count('subjects__chapters', filter=Q(subjects__chapters__status='approved')) +
                     Count('subjects__textbooks', filter=Q(subjects__textbooks__status='approved')) +
                     Count('subjects__practicals', filter=Q(subjects__practicals__status='approved')) +
                     Count('subjects__vivas', filter=Q(subjects__vivas__status='approved'))
    ).order_by('name')
    
    context = {
        'faculties': faculties,
    }
    return render(request, 'admin/faculty_management.html', context)


@login_required
def admin_faculty_levels(request, faculty_slug):
    """Show semester/year levels for a specific faculty"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    try:
        faculty = Faculty.objects.get(slug=faculty_slug, is_active=True)
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty not found.')
        return redirect('admin_faculty_management')
    
    # Get level-wise statistics
    levels_data = []
    for level in range(1, faculty.total_levels + 1):
        level_subjects = Subject.objects.filter(faculty=faculty, level=level, is_active=True)
        level_syllabi = Syllabus.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        level_questions = QuestionBank.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        level_chapters = Chapter.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        level_textbooks = TextBook.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        level_practicals = Practical.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        level_vivas = Viva.objects.filter(subject__faculty=faculty, subject__level=level, status='approved').count()
        
        levels_data.append({
            'level': level,
            'level_name': faculty.get_level_display_name(level),
            'subjects': level_subjects.count(),
            'syllabi': level_syllabi,
            'questions': level_questions,
            'chapters': level_chapters,
            'textbooks': level_textbooks,
            'practicals': level_practicals,
            'vivas': level_vivas,
            'total_resources': level_syllabi + level_questions + level_chapters + level_textbooks + level_practicals + level_vivas,
            'subject_list': list(level_subjects.values('id', 'name', 'level'))
        })
    
    context = {
        'faculty': faculty,
        'levels_data': levels_data,
    }
    return render(request, 'admin/faculty_levels.html', context)


@login_required
def admin_faculty_subjects(request, faculty_slug, level):
    """Manage subjects for a specific faculty and level"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    try:
        faculty = Faculty.objects.get(slug=faculty_slug, is_active=True)
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty not found.')
        return redirect('admin_faculty_management')
    
    # Validate level
    if level < 1 or level > faculty.total_levels:
        messages.error(request, f'Invalid level. {faculty.name} has {faculty.total_levels} levels.')
        return redirect('admin_faculty_levels', faculty_slug=faculty_slug)
    
    subjects = Subject.objects.filter(faculty=faculty, level=level, is_active=True).order_by('name')
    
    # Handle POST requests for subject management
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_subject':
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            if name:
                try:
                    Subject.objects.create(
                        name=name,
                        description=description,
                        faculty=faculty,
                        level=level,
                        is_active=True
                    )
                    messages.success(request, f'Subject "{name}" added successfully.')
                except Exception as e:
                    messages.error(request, f'Error adding subject: {str(e)}')
            else:
                messages.error(request, 'Subject name is required.')
        
        elif action == 'edit_subject':
            subject_id = request.POST.get('subject_id')
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            try:
                subject = Subject.objects.get(id=subject_id, faculty=faculty, level=level)
                subject.name = name
                subject.description = description
                subject.save()
                messages.success(request, f'Subject "{name}" updated successfully.')
            except Subject.DoesNotExist:
                messages.error(request, 'Subject not found.')
        
        elif action == 'delete_subject':
            subject_id = request.POST.get('subject_id')
            try:
                subject = Subject.objects.get(id=subject_id, faculty=faculty, level=level)
                subject_name = subject.name
                subject.delete()
                messages.success(request, f'Subject "{subject_name}" deleted successfully.')
            except Subject.DoesNotExist:
                messages.error(request, 'Subject not found.')
        
        return redirect('admin_faculty_subjects', faculty_slug=faculty_slug, level=level)
    
    level_name = faculty.get_level_display_name(level)
    
    context = {
        'faculty': faculty,
        'level': level,
        'level_name': level_name,
        'subjects': subjects,
    }
    return render(request, 'admin/faculty_subjects.html', context)


@login_required
def admin_subject_resources_management(request, subject_id):
    """Manage all resources for a specific subject"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    try:
        subject = Subject.objects.get(id=subject_id, is_active=True)
    except Subject.DoesNotExist:
        messages.error(request, 'Subject not found.')
        return redirect('admin_faculty_management')
    
    # Get all resources for this subject
    chapters = Chapter.objects.filter(subject=subject).order_by('chapter_number')
    syllabi = Syllabus.objects.filter(subject=subject).order_by('-created_at')
    questions = QuestionBank.objects.filter(subject=subject).order_by('-created_at')
    textbooks = TextBook.objects.filter(subject=subject).order_by('-created_at')
    practicals = Practical.objects.filter(subject=subject).order_by('-created_at')
    vivas = Viva.objects.filter(subject=subject).order_by('-created_at')
    
    # Handle POST requests for resource management
    if request.method == 'POST':
        action = request.POST.get('action')
        resource_type = request.POST.get('resource_type')
        
        if action == 'add_resource':
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            file = request.FILES.get('file')
            
            if title:
                try:
                    if resource_type == 'chapter':
                        chapter_number = request.POST.get('chapter_number')
                        if not chapter_number:
                            messages.error(request, 'Chapter number is required.')
                            return redirect('admin_subject_resources_management', subject_id=subject_id)
                        
                        Chapter.objects.create(
                            title=title,
                            description=description,
                            subject=subject,
                            chapter_number=int(chapter_number),
                            file=file,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Chapter "{title}" added successfully.')
                    
                    elif resource_type == 'syllabus':
                        Syllabus.objects.create(
                            title=title,
                            content=description,
                            subject=subject,
                            file=file,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Syllabus "{title}" added successfully.')
                    
                    elif resource_type == 'question':
                        QuestionBank.objects.create(
                            title=title,
                            description=description,
                            subject=subject,
                            file=file,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Question Bank "{title}" added successfully.')
                    
                    elif resource_type == 'textbook':
                        TextBook.objects.create(
                            title=title,
                            author=request.POST.get('author', ''),
                            publisher=request.POST.get('publisher', ''),
                            isbn=request.POST.get('isbn', ''),
                            description=description,
                            subject=subject,
                            file=file,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Textbook "{title}" added successfully.')
                    
                    elif resource_type == 'practical':
                        Practical.objects.create(
                            title=title,
                            description=description,
                            objective=request.POST.get('objective', ''),
                            materials_required=request.POST.get('materials_required', ''),
                            procedure=request.POST.get('procedure', ''),
                            expected_result=request.POST.get('expected_result', ''),
                            difficulty_level=request.POST.get('difficulty_level', 'medium'),
                            subject=subject,
                            file=file,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Practical "{title}" added successfully.')
                    
                    elif resource_type == 'viva':
                        Viva.objects.create(
                            title=title,
                            description=description,
                            question=request.POST.get('question', ''),
                            answer=request.POST.get('answer', ''),
                            difficulty_level=request.POST.get('difficulty_level', 'medium'),
                            subject=subject,
                            uploaded_by=request.user,
                            status='approved'
                        )
                        messages.success(request, f'Viva "{title}" added successfully.')
                    
                except Exception as e:
                    messages.error(request, f'Error adding resource: {str(e)}')
            else:
                messages.error(request, 'Title is required.')
        
        elif action == 'delete_resource':
            resource_id = request.POST.get('resource_id')
            
            try:
                if resource_type == 'chapter':
                    resource = Chapter.objects.get(id=resource_id, subject=subject)
                elif resource_type == 'syllabus':
                    resource = Syllabus.objects.get(id=resource_id, subject=subject)
                elif resource_type == 'question':
                    resource = QuestionBank.objects.get(id=resource_id, subject=subject)
                elif resource_type == 'textbook':
                    resource = TextBook.objects.get(id=resource_id, subject=subject)
                elif resource_type == 'practical':
                    resource = Practical.objects.get(id=resource_id, subject=subject)
                elif resource_type == 'viva':
                    resource = Viva.objects.get(id=resource_id, subject=subject)
                else:
                    messages.error(request, 'Invalid resource type.')
                    return redirect('admin_subject_resources_management', subject_id=subject_id)
                
                resource_name = resource.title
                resource.delete()
                messages.success(request, f'{resource_type.title()} "{resource_name}" deleted successfully.')
                
            except Exception as e:
                messages.error(request, f'Error deleting resource: {str(e)}')
        
        return redirect('admin_subject_resources_management', subject_id=subject_id)
    
    # Get level name
    level_name = subject.faculty.get_level_display_name(subject.level) if subject.level else "No Level"
    
    context = {
        'subject': subject,
        'level_name': level_name,
        'chapters': chapters,
        'syllabi': syllabi,
        'questions': questions,
        'textbooks': textbooks,
        'practicals': practicals,
        'vivas': vivas,
    }
    return render(request, 'admin/subject_resources_management.html', context)
@login_required
def recommendations_dashboard(request):
    """
    Display personalized recommendations for the logged-in user.
    Shows trending resources, similar resources, and personalized recommendations.
    Provides fallback recommendations when user's faculty has no content.
    """
    user = request.user
    
    # Get user's faculty
    from .recommend_utils import get_user_recommendations, get_user_faculty, get_global_trending_resources
    
    user_faculty = get_user_faculty(user)
    
    # Get recommendations
    recommendations = get_user_recommendations(user, limit=5)
    
    # Debug information (can be removed in production)
    debug_info = {
        'user_faculty': user_faculty.name if user_faculty else 'None',
        'trending_count': len(recommendations['trending']),
        'similar_count': len(recommendations['similar']),
        'personalized_count': len(recommendations['personalized']),
    }
    
    # Prepare context
    context = {
        'page_title': 'Recommendations',
        'user_faculty': user_faculty,
        'trending_resources': recommendations['trending'],
        'similar_resources': recommendations['similar'],
        'personalized_resources': recommendations['personalized'],
        'has_recommendations': any(recommendations.values()),
        'debug_info': debug_info,  # Remove this in production
    }
    
    return render(request, 'general/recommendations.html', context)


@login_required
def faculty_recommendations(request, faculty_slug):
    """
    Display recommendations for a specific faculty.
    Useful for testing and faculty-specific recommendation pages.
    """
    from .recommend_utils import get_recommendations_for_faculty_slug
    
    try:
        faculty = Faculty.objects.get(slug=faculty_slug, is_active=True)
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty not found.')
        return redirect('recommendations')
    
    # Get recommendations for this faculty
    recommendations = get_recommendations_for_faculty_slug(faculty_slug, limit=5)
    
    context = {
        'page_title': f'Recommendations - {faculty.name}',
        'faculty': faculty,
        'trending_resources': recommendations['trending'],
        'similar_resources': recommendations['similar'],
        'personalized_resources': recommendations['personalized'],
        'has_recommendations': any(recommendations.values()),
    }
    
    return render(request, 'general/recommendations.html', context)


def subject_syllabus_redirect(request, subject_id):
    """Redirect old syllabus URL to specific syllabus ID"""
    try:
        # Get the first approved syllabus for this subject
        syllabus = Syllabus.objects.filter(subject_id=subject_id, status='approved').first()
        if syllabus:
            return redirect('syllabus_detail', subject_id=subject_id, syllabus_id=syllabus.id)
        else:
            # If no syllabus found, redirect to subject detail
            return redirect('subject_detail', subject_id=subject_id)
    except Exception:
        return redirect('subject_detail', subject_id=subject_id)


def subject_questions_redirect(request, subject_id):
    """Redirect old questions URL to specific question bank ID"""
    try:
        # Get the first approved question bank for this subject
        question_bank = QuestionBank.objects.filter(subject_id=subject_id, status='approved').first()
        if question_bank:
            return redirect('question_bank_detail', subject_id=subject_id, question_bank_id=question_bank.id)
        else:
            # If no question bank found, redirect to subject detail
            return redirect('subject_detail', subject_id=subject_id)
    except Exception:
        return redirect('subject_detail', subject_id=subject_id)


# MCQ Views
def mcq_faculty_selection(request):
    """MCQ Faculty Selection Page"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to access MCQ quizzes.')
        return redirect('login')
    
    faculties = Faculty.objects.filter(is_active=True).annotate(
        quiz_count=Count('mcq_quizzes', filter=Q(mcq_quizzes__is_active=True)),
        question_count=Count('mcq_quizzes__questions', filter=Q(mcq_quizzes__is_active=True))
    ).order_by('name')
    
    context = {
        'faculties': faculties,
        'title': 'Select Faculty - MCQ Quiz'
    }
    return render(request, 'mcq/user_faculty_selection.html', context)


def mcq_quiz_selection(request, faculty_id):
    """MCQ Quiz Selection Page"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to access MCQ quizzes.')
        return redirect('login')
    
    faculty = get_object_or_404(Faculty, id=faculty_id, is_active=True)
    quizzes = MCQQuiz.objects.filter(faculty=faculty, is_active=True).order_by('quiz_number')
    
    if not quizzes.exists():
        messages.warning(request, f'No quizzes available for {faculty.name}.')
        return redirect('mcq_faculty_selection')
    
    context = {
        'quizzes': quizzes,
        'faculty': faculty,
        'title': f'Select Quiz - {faculty.name}'
    }
    return render(request, 'mcq/quiz_selection.html', context)


@login_required
def mcq_quiz(request, quiz_id):
    """MCQ Quiz Page"""
    quiz = get_object_or_404(MCQQuiz, id=quiz_id, is_active=True)
    questions = MCQQuestion.objects.filter(
        quiz=quiz, 
        published=True
    ).prefetch_related('options')
    
    if not questions.exists():
        messages.warning(request, f'No published MCQ questions available for {quiz.display_name}.')
        return redirect('mcq_faculty_selection')
    
    # Check if user has already taken this quiz
    existing_session = MCQQuizSession.objects.filter(
        user=request.user, 
        quiz=quiz,
        completed_at__isnull=False
    ).first()
    
    if existing_session:
        messages.info(request, 'You have already completed this quiz.')
        return redirect('mcq_result', session_id=existing_session.id)
    
    # Check if this is a retake request (session_id in URL)
    session_id = request.GET.get('session_id')
    if session_id:
        try:
            retake_session = MCQQuizSession.objects.get(
                id=session_id, 
                user=request.user,
                quiz=quiz,
                completed_at__isnull=True  # Only allow retake of reset sessions
            )
            # Use the existing session for retake
            quiz_session = retake_session
        except MCQQuizSession.DoesNotExist:
            # Create new session if retake session not found
            quiz_session = None
    else:
        quiz_session = None
    
    form = MCQQuizForm(questions)
    
    if request.method == 'POST':
        form = MCQQuizForm(questions, request.POST)
        if form.is_valid():
            # Create quiz session if not already exists (for retake)
            if not quiz_session:
                quiz_session = MCQQuizSession.objects.create(
                    user=request.user,
                    quiz=quiz
                )
                quiz_session.questions.set(questions)
            
            # Save answers
            form.save_answers(request.user, questions)
            
            # Calculate score
            quiz_session.calculate_score()
            
            messages.success(request, 'Quiz submitted successfully!')
            return redirect('mcq_result', session_id=quiz_session.id)
    
    context = {
        'form': form,
        'quiz': quiz,
        'questions': questions,
        'title': f'MCQ Quiz - {quiz.display_name}'
    }
    return render(request, 'mcq/quiz.html', context)


@login_required
def mcq_result(request, session_id):
    """MCQ Result Page"""
    session = get_object_or_404(MCQQuizSession, id=session_id, user=request.user)
    
    # Get user answers for this session
    user_answers = MCQUserAnswer.objects.filter(
        user=request.user,
        question__in=session.questions.all()
    ).select_related('question', 'selected_option')
    
    # Create a dictionary for easy lookup
    answers_dict = {answer.question.id: answer for answer in user_answers}
    
    # Get all questions with their correct options
    questions_with_answers = []
    for question in session.questions.all():
        correct_option = question.options.filter(is_correct=True).first()
        user_answer = answers_dict.get(question.id)
        
        questions_with_answers.append({
            'question': question,
            'correct_option': correct_option,
            'user_answer': user_answer,
            'is_correct': user_answer.is_correct if user_answer else False
        })
    
    context = {
        'session': session,
        'questions_with_answers': questions_with_answers,
        'title': f'Quiz Result - {session.quiz.display_name}'
    }
    return render(request, 'mcq/result.html', context)


@login_required
def mcq_my_quizzes(request):
    """User's Quiz History"""
    sessions = MCQQuizSession.objects.filter(
        user=request.user,
        completed_at__isnull=False
    ).order_by('-completed_at')
    
    context = {
        'sessions': sessions,
        'title': 'My Quiz History'
    }
    return render(request, 'mcq/my_quizzes.html', context)


# Admin Views for MCQ
@login_required
def mcq_admin_dashboard(request):
    """Admin MCQ Dashboard"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    # Get statistics
    total_questions = MCQQuestion.objects.count()
    published_questions = MCQQuestion.objects.filter(published=True).count()
    total_quizzes = MCQQuizSession.objects.count()
    total_faculties = Faculty.objects.filter(is_active=True).count()
    
    # Get recent questions
    recent_questions = MCQQuestion.objects.select_related('quiz', 'created_by').order_by('-created_at')[:10]
    
    context = {
        'total_questions': total_questions,
        'published_questions': published_questions,
        'total_quizzes': total_quizzes,
        'total_faculties': total_faculties,
        'recent_questions': recent_questions,
        'title': 'MCQ Admin Dashboard'
    }
    return render(request, 'mcq/admin/dashboard.html', context)


@login_required
def mcq_admin_add_question(request):
    """Admin Add Question Page"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    if request.method == 'POST':
        form = MCQQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.created_by = request.user
            question.save()
            messages.success(request, 'Question created successfully! Now add options.')
            return redirect('mcq_admin_add_options', question_id=question.id)
    else:
        form = MCQQuestionForm()
    
    context = {
        'form': form,
        'title': 'Add MCQ Question'
    }
    return render(request, 'mcq/admin/add_question.html', context)


@login_required
def mcq_admin_add_options(request, question_id):
    """Admin Add Options Page"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    question = get_object_or_404(MCQQuestion, id=question_id, created_by=request.user)
    options = question.options.all()
    
    if request.method == 'POST':
        form = MCQOptionForm(request.POST, question=question)
        if form.is_valid():
            option = form.save(commit=False)
            option.question = question
            option.save()
            messages.success(request, 'Option added successfully!')
            return redirect('mcq_admin_add_options', question_id=question.id)
    else:
        form = MCQOptionForm(question=question)
    
    context = {
        'form': form,
        'question': question,
        'options': options,
        'title': f'Add Options - {question.question_text[:50]}...'
    }
    return render(request, 'mcq/admin/add_options.html', context)


@login_required
def mcq_admin_question_list(request):
    """Admin Question List"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    questions = MCQQuestion.objects.select_related('quiz', 'created_by').order_by('-created_at')
    
    # Filter by faculty if provided
    faculty_id = request.GET.get('faculty')
    if faculty_id:
        questions = questions.filter(quiz__faculty_id=faculty_id)
    
    # Filter by quiz if provided
    quiz_id = request.GET.get('quiz')
    if quiz_id:
        questions = questions.filter(quiz_id=quiz_id)
    
    # Filter by published status
    published = request.GET.get('published')
    if published == 'true':
        questions = questions.filter(published=True)
    elif published == 'false':
        questions = questions.filter(published=False)
    
    paginator = Paginator(questions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    faculties = Faculty.objects.filter(is_active=True)
    quizzes = MCQQuiz.objects.filter(is_active=True) if not faculty_id else MCQQuiz.objects.filter(faculty_id=faculty_id, is_active=True)
    
    context = {
        'page_obj': page_obj,
        'faculties': faculties,
        'quizzes': quizzes,
        'selected_faculty': faculty_id,
        'selected_quiz': quiz_id,
        'selected_published': published,
        'title': 'MCQ Questions Management'
    }
    return render(request, 'mcq/admin/question_list.html', context)


@login_required
def mcq_admin_toggle_publish(request, question_id):
    """Toggle question published status"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    question = get_object_or_404(MCQQuestion, id=question_id, created_by=request.user)
    
    if question.published:
        question.published = False
        messages.success(request, 'Question unpublished successfully!')
    else:
        # Check if question has valid options before publishing
        if question.options.count() < 2:
            messages.error(request, 'Question must have at least 2 options to be published.')
        elif question.options.filter(is_correct=True).count() != 1:
            messages.error(request, 'Question must have exactly one correct option to be published.')
        else:
            question.published = True
            messages.success(request, 'Question published successfully!')
    
    question.save()
    return redirect('mcq_admin_question_list')


@login_required
def mcq_admin_delete_question(request, question_id):
    """Delete question"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    question = get_object_or_404(MCQQuestion, id=question_id, created_by=request.user)
    question.delete()
    messages.success(request, 'Question deleted successfully!')
    return redirect('mcq_admin_question_list')


def mcq_admin_get_quizzes(request):
    """AJAX endpoint to get quizzes for a faculty"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    faculty_id = request.GET.get('faculty_id')
    
    if not faculty_id:
        return JsonResponse({'quizzes': [], 'error': 'Faculty ID is required'})
    
    try:
        # Validate faculty_id is a number
        faculty_id = int(faculty_id)
        
        # Check if faculty exists and is active
        faculty = Faculty.objects.filter(id=faculty_id, is_active=True).first()
        if not faculty:
            return JsonResponse({
                'quizzes': [], 
                'error': 'Faculty not found or inactive'
            })
        
        # Get quizzes for this faculty
        quizzes = MCQQuiz.objects.filter(
            faculty_id=faculty_id, 
            is_active=True
        ).order_by('quiz_number').values('id', 'quiz_number', 'title')
        
        quizzes_list = list(quizzes)
        
        return JsonResponse({
            'quizzes': quizzes_list,
            'faculty_name': faculty.name,
            'count': len(quizzes_list)
        })
        
    except ValueError:
        return JsonResponse({
            'quizzes': [], 
            'error': 'Invalid faculty ID format'
        })
    except Exception as e:
        print(f"Error in mcq_admin_get_quizzes: {e}")  # Debug logging
        return JsonResponse({
            'quizzes': [], 
            'error': 'Internal server error'
        })


@login_required
def mcq_admin_delete_option(request, option_id):
    """Delete option"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    option = get_object_or_404(MCQOption, id=option_id, question__created_by=request.user)
    question_id = option.question.id
    option.delete()
    messages.success(request, 'Option deleted successfully!')
    return redirect('mcq_admin_add_options', question_id=question_id)


@login_required
def mcq_retake_quiz(request, session_id):
    """Retake a completed quiz"""
    session = get_object_or_404(MCQQuizSession, id=session_id, user=request.user)
    
    # Check if session is completed
    if not session.completed_at:
        messages.error(request, 'This quiz is not completed yet.')
        return redirect('mcq_quiz', quiz_id=session.quiz.id)
    
    # Delete existing user answers for this session
    MCQUserAnswer.objects.filter(
        user=request.user,
        question__in=session.questions.all()
    ).delete()
    
    # Reset session
    session.completed_at = None
    session.correct_answers = 0
    session.score_percentage = 0.0
    session.save()
    
    messages.success(request, 'Quiz reset successfully! You can now retake the quiz.')
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    return HttpResponseRedirect(reverse('mcq_quiz', args=[session.quiz.id]) + f'?session_id={session_id}')

@login_required
def mcq_admin_create_quiz(request):
    """AJAX endpoint to create a new quiz"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Admin privileges required'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        faculty_id = data.get('faculty_id')
        title = data.get('title', '').strip()
        
        if not faculty_id:
            return JsonResponse({'error': 'Faculty ID is required'}, status=400)
        
        faculty = Faculty.objects.filter(id=faculty_id, is_active=True).first()
        if not faculty:
            return JsonResponse({'error': 'Faculty not found or inactive'}, status=404)
        
        # Get the next quiz number for this faculty
        last_quiz = MCQQuiz.objects.filter(faculty=faculty).order_by('-quiz_number').first()
        next_quiz_number = (last_quiz.quiz_number + 1) if last_quiz else 1
        
        # Create new quiz
        quiz = MCQQuiz.objects.create(
            faculty=faculty,
            quiz_number=next_quiz_number,
            title=title,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'quiz': {
                'id': quiz.id,
                'quiz_number': quiz.quiz_number,
                'title': quiz.title,
                'display_name': quiz.display_name
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Error in mcq_admin_create_quiz: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def mcq_admin_faculty_list(request):
    """MCQ Faculty List Page for Admin"""
    if not request.user.is_staff:
        messages.error(request, 'Admin privileges required.')
        return redirect('dashboard')
    
    faculties = Faculty.objects.filter(is_active=True).annotate(
        quiz_count=Count('mcq_quizzes', filter=Q(mcq_quizzes__is_active=True)),
        question_count=Count('mcq_quizzes__questions', filter=Q(mcq_quizzes__is_active=True))
    ).order_by('name')
    
    context = {
        'faculties': faculties,
        'title': 'MCQ Faculty Management'
    }
    return render(request, 'mcq/admin/faculty_list.html', context)

@login_required
def mcq_admin_quiz_list(request, faculty_id):
    """MCQ Quiz List Page for Admin"""
    if not request.user.is_staff:
        messages.error(request, 'Admin privileges required.')
        return redirect('dashboard')
    
    faculty = get_object_or_404(Faculty, id=faculty_id, is_active=True)
    quizzes = MCQQuiz.objects.filter(faculty=faculty, is_active=True).annotate(
        question_count=Count('questions'),
        published_count=Count('questions', filter=Q(questions__published=True))
    ).order_by('quiz_number')
    
    context = {
        'faculty': faculty,
        'quizzes': quizzes,
        'title': f'Quiz Management - {faculty.name}'
    }
    return render(request, 'mcq/admin/quiz_list.html', context)
