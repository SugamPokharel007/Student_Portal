from django.urls import path,include
from . import views
from django.conf import settings  # Import settings
from django.conf.urls.static import static  # Import static
from .views import (
    notice_list, contact_view, register_view, login_view, logout_view,
    subject_detail, add_syllabus, add_question_bank, add_subject_notice
)

urlpatterns = [
    path('',views.home,name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('about/',views.about, name='about'),
    path('year/',views.year, name='year'),
    path('subjects/<str:year>/', views.subjects, name='subjects'),
    path('subject/<int:subject_id>/', views.subject_detail, name='subject_detail'),
    path('subject/<int:subject_id>/add-syllabus/', views.add_syllabus, name='add_syllabus'),
    path('subject/<int:subject_id>/add-question-bank/', views.add_question_bank, name='add_question_bank'),
    path('subject/<int:subject_id>/add-notice/', views.add_subject_notice, name='add_subject_notice'),
    path('subject/<int:subject_id>/syllabus/', views.subject_syllabus, name='subject_syllabus'),
    path('subject/<int:subject_id>/questions/', views.subject_questions, name='subject_questions'),
    path('subject/<int:subject_id>/notes/', views.subject_notes, name='subject_notes'),
    path('notices/', views.notice_list, name='notice_list'),
    path('contact/', views.contact_view, name='contact'),
    # Subscription URLs
    path('subscription/', views.subscription_view, name='subscription'),
    path('subscribe/<str:subscription_type>/', views.subscribe, name='subscribe'),
    path('subscription/success/', views.subscription_success, name='subscription_success'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

