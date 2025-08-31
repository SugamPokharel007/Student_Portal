from django.urls import path, include
from . import api_views

api_urlpatterns = [
    # Faculty and Subject endpoints
    path('faculties/', api_views.FacultyListAPIView.as_view(), name='api_faculty_list'),
    path('subjects/', api_views.SubjectListAPIView.as_view(), name='api_subject_list'),
    
    # Search endpoints
    path('search/', api_views.search_api, name='api_search'),
    path('trending/', api_views.trending_subjects_api, name='api_trending'),
    
    # Notice endpoints
    path('notices/', api_views.NoticeListAPIView.as_view(), name='api_notice_list'),
    
    # Resource creation endpoints
    path('syllabus/create/', api_views.SyllabusCreateAPIView.as_view(), name='api_syllabus_create'),
    path('notes/create/', api_views.NoteCreateAPIView.as_view(), name='api_note_create'),
    path('questions/create/', api_views.QuestionBankCreateAPIView.as_view(), name='api_questionbank_create'),
    
    # User endpoints
    path('user/stats/', api_views.user_stats_api, name='api_user_stats'),
]