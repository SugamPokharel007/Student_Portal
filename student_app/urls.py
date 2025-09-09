from django.urls import path, include
from . import views
from . import oauth_views
from . import password_reset_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Basic pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('year/', views.year, name='year'),  # Redirects to home
    path('contact/', views.contact_view, name='contact'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password Reset
    path('password-reset/', password_reset_views.password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', password_reset_views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-done/', password_reset_views.password_reset_done, name='password_reset_done'),
    path('password-reset-success/', password_reset_views.password_reset_success, name='password_reset_success'),
    
    # OAuth Authentication
    path('oauth/google/', oauth_views.google_oauth_initiate, name='google_oauth_initiate'),
    path('oauth/google/callback/', oauth_views.google_oauth_callback, name='google_oauth_callback'),
    path('oauth/facebook/', oauth_views.facebook_oauth_initiate, name='facebook_oauth_initiate'),
    path('oauth/facebook/callback/', oauth_views.facebook_oauth_callback, name='facebook_oauth_callback'),
    
    # User management
    path('select-faculty/', views.select_faculty, name='select_faculty'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Admin dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Academic content
    # Faculty-related URLs
    path('faculty/<str:faculty_slug>/<int:level>/', views.faculty_subjects, name='faculty_subjects'),
    path('faculty/<str:faculty_slug>/', views.faculty_overview, name='faculty_overview'),
    path('subject/<int:subject_id>/', views.subject_detail, name='subject_detail'),
    path('subject/<int:subject_id>/syllabus/', views.subject_syllabus_redirect, name='subject_syllabus'),
    path('subject/<int:subject_id>/notes/', views.subject_notes, name='subject_notes'),
    path('subject/<int:subject_id>/questions/', views.subject_questions_redirect, name='subject_questions'),
    path('subject/<int:subject_id>/chapter/<int:chapter_id>/', views.chapter_detail, name='chapter_detail'),
    path('download/chapter/<int:chapter_id>/', views.download_chapter, name='download_chapter'),
    path('subject/<int:subject_id>/question-bank/<int:question_bank_id>/', views.question_bank_detail, name='question_bank_detail'),
    path('subject/<int:subject_id>/question-bank-solution/<int:solution_id>/', views.question_bank_solution_detail, name='question_bank_solution_detail'),
    path('subject/<int:subject_id>/syllabus/<int:syllabus_id>/', views.syllabus_detail, name='syllabus_detail'),
    
    # Resource management
    path('subject/<int:subject_id>/add-syllabus/', views.add_syllabus, name='add_syllabus'),
    path('subject/<int:subject_id>/add-question-bank/', views.add_question_bank, name='add_question_bank'),
    path('subject/<int:subject_id>/add-question-bank-solution/', views.add_question_bank_solution, name='add_question_bank_solution'),
    path('subject/<int:subject_id>/add-notice/', views.add_subject_notice, name='add_subject_notice'),
    path('contribute/', views.contribute_resource, name='contribute_resource'),
    
    # Search functionality
    path('search/', views.search, name='search'),
    path('advanced-search/', views.advanced_search, name='advanced_search'),
    
    # Recommendations
    path('recommendations/', views.recommendations_dashboard, name='recommendations'),
    path('recommendations/faculty/<str:faculty_slug>/', views.faculty_recommendations, name='faculty_recommendations'),
    
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

    # Article system
    path('articles/', views.articles, name='articles'),
    path('articles/submit/', views.submit_article, name='submit_article'),
    path('articles/my-articles/', views.my_articles, name='my_articles'),
    path('articles/edit/<int:article_id>/', views.edit_article, name='edit_article'),
    path('articles/like/<int:article_id>/', views.like_article, name='like_article'),
    path('articles/comment/<int:article_id>/', views.add_comment, name='add_comment'),
    path('articles/<str:slug>/', views.article_detail, name='article_detail'),

    # Admin management URLs
    path('admin-manage-subjects/', views.admin_manage_subjects, name='admin_manage_subjects'),
    path('admin-manage-faculties/', views.admin_manage_faculties, name='admin_manage_faculties'),
    path('admin-manage-syllabus/', views.admin_manage_syllabus, name='admin_manage_syllabus'),
    path('admin-manage-notes/', views.admin_manage_notes, name='admin_manage_notes'),
    path('admin-manage-question-banks/', views.admin_manage_question_banks, name='admin_manage_question_banks'),
    path('admin-manage-contributor-requests/', views.admin_manage_contributor_requests, name='admin_manage_contributor_requests'),
    path('admin-manage-contacts/', views.admin_manage_contacts, name='admin_manage_contacts'),
    path('admin-manage-chapters/', views.admin_manage_chapters, name='admin_manage_chapters'),
    path('admin-manage-articles/', views.admin_manage_articles, name='admin_manage_articles'),
    
    # Admin approval actions
    path('admin-approve-resource/', views.admin_approve_resource, name='admin_approve_resource'),
    path('admin-reject-resource/', views.admin_reject_resource, name='admin_reject_resource'),
    path('admin-preview-resource/', views.admin_preview_resource, name='admin_preview_resource'),
    
    # Faculty-wise Resource Management URLs
    path('admin-faculty-management/', views.admin_faculty_management, name='admin_faculty_management'),
    path('admin-faculty-levels/<str:faculty_slug>/', views.admin_faculty_levels, name='admin_faculty_levels'),
    path('admin-faculty-subjects/<str:faculty_slug>/<int:level>/', views.admin_faculty_subjects, name='admin_faculty_subjects'),
    path('admin-subject-resources/<int:subject_id>/', views.admin_subject_resources_management, name='admin_subject_resources_management'),
    
    # MCQ URLs
    path('mcq/', views.mcq_faculty_selection, name='mcq_faculty_selection'),
    path('mcq/faculty/<int:faculty_id>/', views.mcq_quiz_selection, name='mcq_quiz_selection'),
    path('mcq/quiz/<int:quiz_id>/', views.mcq_quiz, name='mcq_quiz'),
    path('mcq/result/<int:session_id>/', views.mcq_result, name='mcq_result'),
    path('mcq/retake/<int:session_id>/', views.mcq_retake_quiz, name='mcq_retake_quiz'),
    path('mcq/my-quizzes/', views.mcq_my_quizzes, name='mcq_my_quizzes'),
    
    # MCQ Admin URLs
    path('mcq/admin/', views.mcq_admin_dashboard, name='mcq_admin_dashboard'),
    path('mcq/admin/add-question/', views.mcq_admin_add_question, name='mcq_admin_add_question'),
    path('mcq/admin/add-options/<int:question_id>/', views.mcq_admin_add_options, name='mcq_admin_add_options'),
    path('mcq/admin/questions/', views.mcq_admin_question_list, name='mcq_admin_question_list'),
    path('mcq/admin/toggle-publish/<int:question_id>/', views.mcq_admin_toggle_publish, name='mcq_admin_toggle_publish'),
    path('mcq/admin/delete-question/<int:question_id>/', views.mcq_admin_delete_question, name='mcq_admin_delete_question'),
    path('mcq/admin/delete-option/<int:option_id>/', views.mcq_admin_delete_option, name='mcq_admin_delete_option'),
    path('mcq/admin/get-quizzes/', views.mcq_admin_get_quizzes, name='mcq_admin_get_quizzes'),
    path('mcq/admin/create-quiz/', views.mcq_admin_create_quiz, name='mcq_admin_create_quiz'),
    path('mcq/admin/faculties/', views.mcq_admin_faculty_list, name='mcq_admin_faculty_list'),
    path('mcq/admin/faculty/<int:faculty_id>/quizzes/', views.mcq_admin_quiz_list, name='mcq_admin_quiz_list'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

