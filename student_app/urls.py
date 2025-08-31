from django.urls import path, include
from . import views
from . import oauth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Basic pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('year/', views.year, name='year'),
    path('contact/', views.contact_view, name='contact'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # OAuth Authentication
    path('oauth/google/', oauth_views.google_oauth_initiate, name='google_oauth_initiate'),
    path('oauth/google/callback/', oauth_views.google_oauth_callback, name='google_oauth_callback'),
    path('oauth/facebook/', oauth_views.facebook_oauth_initiate, name='facebook_oauth_initiate'),
    path('oauth/facebook/callback/', oauth_views.facebook_oauth_callback, name='facebook_oauth_callback'),
    
    # User management
    path('select-faculty/', views.select_faculty, name='select_faculty'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Admin dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Academic content
    # Subject-related URLs
    path('subjects/<str:faculty_slug>/<int:level>/', views.faculty_subjects, name='faculty_subjects'),
    path('subjects/<str:faculty_slug>/', views.faculty_overview, name='faculty_overview'),
    path('subject/<int:subject_id>/', views.subject_detail, name='subject_detail'),
    path('subject/<int:subject_id>/syllabus/', views.subject_syllabus, name='subject_syllabus'),
    path('subject/<int:subject_id>/notes/', views.subject_notes, name='subject_notes'),
    path('subject/<int:subject_id>/questions/', views.subject_questions, name='subject_questions'),
    
    # Resource management
    path('subject/<int:subject_id>/add-syllabus/', views.add_syllabus, name='add_syllabus'),
    path('subject/<int:subject_id>/add-question-bank/', views.add_question_bank, name='add_question_bank'),
    path('subject/<int:subject_id>/add-notice/', views.add_subject_notice, name='add_subject_notice'),
    path('contribute/', views.contribute_resource, name='contribute_resource'),
    
    # Search functionality
    path('search/', views.search, name='search'),
    path('advanced-search/', views.advanced_search, name='advanced_search'),
    
    # Notices
    path('notices/', views.notice_list, name='notices'),
    path('notices/<int:notice_id>/', views.notice_detail, name='notice_detail'),
    
    # Subscription system
    path('subscription/', views.subscription_view, name='subscription'),
    path('subscribe/<str:subscription_type>/', views.subscribe, name='subscribe'),
    path('subscription/success/', views.subscription_success, name='subscription_success'),
    
    # Contributor system
    path('contributor-request/', views.contributor_request, name='contributor_request'),
    
    # Download tracking
    path('download/<str:content_type>/<int:content_id>/', views.download_resource, name='download_resource'),
    
    # API endpoints
    path('api/toggle-dark-mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
    path('api/trending-subjects/', views.get_trending_subjects, name='get_trending_subjects'),
    path('api/subjects/<int:faculty_id>/', views.get_subjects_for_faculty, name='get_subjects_for_faculty'),
    
    # Additional resource URLs (redirect to search with filters)
    path('syllabus/', views.syllabus_redirect, name='syllabus'),
    path('notes/', views.notes_redirect, name='notes'),
    path('question-bank/', views.question_bank_redirect, name='question_bank'),

    # Admin management URLs
    path('admin-manage-subjects/', views.admin_manage_subjects, name='admin_manage_subjects'),
    path('admin-manage-faculties/', views.admin_manage_faculties, name='admin_manage_faculties'),
    path('admin-manage-syllabus/', views.admin_manage_syllabus, name='admin_manage_syllabus'),
    path('admin-manage-notes/', views.admin_manage_notes, name='admin_manage_notes'),
    path('admin-manage-question-banks/', views.admin_manage_question_banks, name='admin_manage_question_banks'),
    path('admin-manage-contributor-requests/', views.admin_manage_contributor_requests, name='admin_manage_contributor_requests'),
    path('admin-manage-contacts/', views.admin_manage_contacts, name='admin_manage_contacts'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

