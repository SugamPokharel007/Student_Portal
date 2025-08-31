from rest_framework import serializers
from .models import Faculty, Subject, Notice, Syllabus, QuestionBank, Note, UserProfile


class FacultySerializer(serializers.ModelSerializer):
    subject_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Faculty
        fields = ['id', 'name', 'slug', 'description', 'academic_structure', 
                 'total_levels', 'subject_count', 'created_date']
        
    def get_subject_count(self, obj):
        return obj.subjects.filter(is_active=True).count()


class SubjectSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    total_resources = serializers.ReadOnlyField()
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'faculty', 'faculty_name', 'level', 
                 'description', 'total_resources', 'created_at']


class NoticeSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Notice
        fields = ['id', 'title', 'content', 'created_at', 'subject', 
                 'subject_name', 'is_general', 'is_important', 
                 'created_by_username']


class SyllabusSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = Syllabus
        fields = ['id', 'subject', 'subject_name', 'title', 'content', 
                 'file', 'status', 'created_at', 'download_count', 
                 'view_count', 'uploaded_by_username']
        read_only_fields = ['status', 'download_count', 'view_count', 'uploaded_by']


class QuestionBankSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = QuestionBank
        fields = ['id', 'subject', 'subject_name', 'title', 'file', 
                 'description', 'status', 'created_at', 'download_count', 
                 'view_count', 'uploaded_by_username']
        read_only_fields = ['status', 'download_count', 'view_count', 'uploaded_by']


class NoteSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = Note
        fields = ['id', 'subject', 'subject_name', 'title', 'file', 
                 'description', 'status', 'created_at', 'download_count', 
                 'view_count', 'uploaded_by_username']
        read_only_fields = ['status', 'download_count', 'view_count', 'uploaded_by']


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'faculty', 'faculty_name', 
                 'role', 'bio', 'avatar', 'total_uploads', 'total_downloads']