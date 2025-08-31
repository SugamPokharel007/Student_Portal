from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from drf_spectacular.utils import extend_schema

from .models import Subject, Notice, Syllabus, QuestionBank, Note, Faculty
from .serializers import (
    SubjectSerializer, NoticeSerializer, SyllabusSerializer,
    QuestionBankSerializer, NoteSerializer, FacultySerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@method_decorator(ratelimit(key='ip', rate='100/h', method='GET'), name='get')
class FacultyListAPIView(generics.ListAPIView):
    queryset = Faculty.objects.filter(is_active=True)
    serializer_class = FacultySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination


@method_decorator(ratelimit(key='ip', rate='100/h', method='GET'), name='get')
class SubjectListAPIView(generics.ListAPIView):
    serializer_class = SubjectSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Subject.objects.filter(is_active=True).select_related('faculty')
        faculty_id = self.request.query_params.get('faculty_id')
        level = self.request.query_params.get('level')
        
        if faculty_id:
            queryset = queryset.filter(faculty_id=faculty_id)
        if level:
            queryset = queryset.filter(level=level)
            
        return queryset


@extend_schema(
    description="Search across subjects, notes, syllabi, and question banks",
    parameters=[
        {
            'name': 'q',
            'description': 'Search query',
            'required': True,
            'type': 'string'
        },
        {
            'name': 'type',
            'description': 'Resource type filter',
            'required': False,
            'type': 'string',
            'enum': ['subject', 'note', 'syllabus', 'questionbank']
        }
    ]
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='50/h', method='GET')
def search_api(request):
    query = request.GET.get('q', '').strip()
    resource_type = request.GET.get('type', 'all')
    
    if not query:
        return Response({'error': 'Query parameter is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    results = []
    
    if resource_type in ['all', 'subject']:
        subjects = Subject.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        ).select_related('faculty')[:10]
        
        for subject in subjects:
            results.append({
                'type': 'subject',
                'id': subject.id,
                'title': subject.name,
                'description': subject.description,
                'faculty': subject.faculty.name if subject.faculty else None,
                'url': f'/subject/{subject.id}/'
            })
    
    if resource_type in ['all', 'note']:
        notes = Note.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            status='approved'
        ).select_related('subject__faculty')[:10]
        
        for note in notes:
            results.append({
                'type': 'note',
                'id': note.id,
                'title': note.title,
                'description': note.description,
                'subject': note.subject.name,
                'faculty': note.subject.faculty.name if note.subject.faculty else None,
                'url': f'/subject/{note.subject.id}/notes/'
            })
    
    return Response({
        'query': query,
        'results': results,
        'count': len(results)
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='100/h', method='GET')
def trending_subjects_api(request):
    """Get trending subjects based on recent activity"""
    from datetime import timedelta
    from django.utils import timezone
    
    week_ago = timezone.now() - timedelta(days=7)
    
    trending = Subject.objects.annotate(
        recent_activity=Count('syllabi', filter=Q(syllabi__created_at__gte=week_ago)) +
                        Count('notes', filter=Q(notes__created_at__gte=week_ago)) +
                        Count('question_banks', filter=Q(question_banks__created_at__gte=week_ago))
    ).filter(recent_activity__gt=0, is_active=True).order_by('-recent_activity')[:10]
    
    serializer = SubjectSerializer(trending, many=True)
    return Response(serializer.data)


class NoticeListAPIView(generics.ListAPIView):
    serializer_class = NoticeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Notice.objects.all().select_related('subject__faculty')
        is_general = self.request.query_params.get('is_general')
        is_important = self.request.query_params.get('is_important')
        
        if is_general:
            queryset = queryset.filter(is_general=True)
        if is_important:
            queryset = queryset.filter(is_important=True)
            
        return queryset.order_by('-created_at')


@method_decorator(ratelimit(key='user', rate='10/h', method='POST'), name='post')
class ResourceCreateAPIView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class SyllabusCreateAPIView(ResourceCreateAPIView):
    serializer_class = SyllabusSerializer


class NoteCreateAPIView(ResourceCreateAPIView):
    serializer_class = NoteSerializer


class QuestionBankCreateAPIView(ResourceCreateAPIView):
    serializer_class = QuestionBankSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats_api(request):
    """Get user statistics"""
    user = request.user
    
    stats = {
        'uploads': {
            'notes': Note.objects.filter(uploaded_by=user).count(),
            'syllabi': Syllabus.objects.filter(uploaded_by=user).count(),
            'question_banks': QuestionBank.objects.filter(uploaded_by=user).count(),
        },
        'downloads': getattr(user, 'download_logs', []).count(),
        'profile': {
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined,
        }
    }
    
    return Response(stats)