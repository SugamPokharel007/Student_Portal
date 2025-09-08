"""
Recommendation System Utilities for Student Portal

This module provides recommendation algorithms for study materials based on:
- Faculty-based filtering
- Popularity-based ranking (views/downloads)
- Content similarity using TF-IDF + Cosine Similarity
- User's viewing/download history
"""

from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import math

from .models import (
    Syllabus, Note, QuestionBank, Chapter, Viva, TextBook, Practical, Subject, Faculty, 
    ViewLog, DownloadLog, UserProfile
)
from .search_utils import get_tfidf_similarity


def get_trending_resources(faculty, limit=5):
    """
    Get trending resources for a specific faculty based on popularity metrics.
    If faculty has no content, returns trending resources from all faculties.
    
    Args:
        faculty: Faculty instance
        limit: Maximum number of resources to return
        
    Returns:
        List of tuples (resource, explanation) sorted by popularity
    """
    if not faculty:
        return []
    
    # Get all approved resources for the faculty
    resources = []
    
    # Get syllabi
    syllabi = Syllabus.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).select_related('subject').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get notes
    notes = Note.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).select_related('subject').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get question banks
    question_banks = QuestionBank.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).select_related('subject').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get chapters
    chapters = Chapter.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).select_related('subject').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get vivas
    vivas = Viva.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).select_related('subject').annotate(
        popularity_score=F('view_count') * 1.5  # Vivas don't have downloads, only views
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get textbooks
    textbooks = TextBook.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).select_related('subject').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get practicals
    practicals = Practical.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).select_related('subject').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Combine and sort all resources
    all_resources = list(syllabi) + list(notes) + list(question_banks) + list(chapters) + list(vivas) + list(textbooks) + list(practicals)
    all_resources.sort(key=lambda x: x.popularity_score, reverse=True)
    
    # If no resources in this faculty, try to get some global trending as fallback
    if not all_resources:
        return get_global_trending_resources(limit)
    
    # Add explanations for each resource
    result = []
    for resource in all_resources[:limit]:
        # Add resource type information
        if isinstance(resource, Syllabus):
            resource_type = 'syllabus'
        elif isinstance(resource, Note):
            resource_type = 'note'
        elif isinstance(resource, QuestionBank):
            resource_type = 'questionbank'
        elif isinstance(resource, Chapter):
            resource_type = 'chapter'
        elif isinstance(resource, Viva):
            resource_type = 'viva'
        elif isinstance(resource, TextBook):
            resource_type = 'textbook'
        elif isinstance(resource, Practical):
            resource_type = 'practical'
        else:
            resource_type = 'unknown'
        resource.resource_type = resource_type
        
        # Create appropriate explanation based on resource type
        if hasattr(resource, 'download_count'):
            explanation = f"Trending in {faculty.name} - {resource.view_count} views, {resource.download_count} downloads"
        else:
            explanation = f"Trending in {faculty.name} - {resource.view_count} views"
        result.append((resource, explanation))
    
    return result


def get_global_trending_resources(limit=5):
    """
    Get trending resources from all faculties when user's faculty has no content.
    
    Args:
        limit: Maximum number of resources to return
        
    Returns:
        List of tuples (resource, explanation) sorted by popularity
    """
    # Get syllabi from all faculties
    syllabi = Syllabus.objects.filter(
        status='approved'
    ).select_related('subject', 'subject__faculty').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get notes from all faculties
    notes = Note.objects.filter(
        status='approved'
    ).select_related('subject', 'subject__faculty').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get question banks from all faculties
    question_banks = QuestionBank.objects.filter(
        status='approved'
    ).select_related('subject', 'subject__faculty').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get chapters from all faculties
    chapters = Chapter.objects.filter(
        status='approved'
    ).select_related('subject', 'subject__faculty').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get vivas from all faculties
    vivas = Viva.objects.filter(
        status='approved'
    ).select_related('subject', 'subject__faculty').annotate(
        popularity_score=F('view_count') * 1.5
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get textbooks from all faculties
    textbooks = TextBook.objects.filter(
        status='approved'
    ).select_related('subject', 'subject__faculty').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Get practicals from all faculties
    practicals = Practical.objects.filter(
        status='approved'
    ).select_related('subject', 'subject__faculty').annotate(
        popularity_score=F('view_count') + F('download_count') * 2
    ).order_by('-popularity_score', '-last_viewed')[:limit]
    
    # Combine and sort all resources
    all_resources = list(syllabi) + list(notes) + list(question_banks) + list(chapters) + list(vivas) + list(textbooks) + list(practicals)
    all_resources.sort(key=lambda x: x.popularity_score, reverse=True)
    
    # Add explanations for each resource
    result = []
    for resource in all_resources[:limit]:
        # Add resource type information
        if isinstance(resource, Syllabus):
            resource_type = 'syllabus'
        elif isinstance(resource, Note):
            resource_type = 'note'
        elif isinstance(resource, QuestionBank):
            resource_type = 'questionbank'
        elif isinstance(resource, Chapter):
            resource_type = 'chapter'
        elif isinstance(resource, Viva):
            resource_type = 'viva'
        elif isinstance(resource, TextBook):
            resource_type = 'textbook'
        elif isinstance(resource, Practical):
            resource_type = 'practical'
        else:
            resource_type = 'unknown'
        resource.resource_type = resource_type
        
        faculty_name = resource.subject.faculty.name if resource.subject and resource.subject.faculty else "Unknown Faculty"
        if hasattr(resource, 'download_count'):
            explanation = f"Popular across all faculties - {faculty_name} - {resource.view_count} views, {resource.download_count} downloads"
        else:
            explanation = f"Popular across all faculties - {faculty_name} - {resource.view_count} views"
        result.append((resource, explanation))
    
    return result


def get_similar_resources(resource, limit=5):
    """
    Get resources similar to the given resource using TF-IDF + Cosine Similarity.
    
    Args:
        resource: Resource instance (Syllabus, Note, or QuestionBank)
        limit: Maximum number of similar resources to return
        
    Returns:
        List of tuples (resource, explanation) sorted by similarity
    """
    if not resource:
        return []
    
    # Get the resource's faculty for filtering
    faculty = resource.subject.faculty if resource.subject else None
    if not faculty:
        return []
    
    # Get all approved resources from the same faculty
    all_resources = []
    
    # Get syllabi
    syllabi = Syllabus.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).exclude(id=resource.id).select_related('subject')
    
    # Get notes
    notes = Note.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).exclude(id=resource.id).select_related('subject')
    
    # Get question banks
    question_banks = QuestionBank.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).exclude(id=resource.id).select_related('subject')
    
    # Get chapters
    chapters = Chapter.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).exclude(id=resource.id).select_related('subject')
    
    # Get vivas
    vivas = Viva.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).exclude(id=resource.id).select_related('subject')
    
    # Get textbooks
    textbooks = TextBook.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).exclude(id=resource.id).select_related('subject')
    
    # Get practicals
    practicals = Practical.objects.filter(
        subject__faculty=faculty,
        status='approved'
    ).exclude(id=resource.id).select_related('subject')
    
    all_resources = list(syllabi) + list(notes) + list(question_banks) + list(chapters) + list(vivas) + list(textbooks) + list(practicals)
    
    if not all_resources:
        return []
    
    # Prepare content for similarity calculation
    resource_content = f"{resource.title} {getattr(resource, 'content', '')} {getattr(resource, 'description', '')}"
    
    # Calculate similarities
    similarities = []
    for other_resource in all_resources:
        other_content = f"{other_resource.title} {getattr(other_resource, 'content', '')} {getattr(other_resource, 'description', '')}"
        
        try:
            similarity = get_tfidf_similarity(resource_content, other_content)
            if similarity > 0.1:  # Only include resources with meaningful similarity
                similarities.append((other_resource, similarity))
        except Exception:
            # If similarity calculation fails, skip this resource
            continue
    
    # Sort by similarity score and add explanations
    similarities.sort(key=lambda x: x[1], reverse=True)
    result = []
    for similar_resource, similarity_score in similarities[:limit]:
        # Add resource type information
        if isinstance(similar_resource, Syllabus):
            resource_type = 'syllabus'
        elif isinstance(similar_resource, Note):
            resource_type = 'note'
        elif isinstance(similar_resource, QuestionBank):
            resource_type = 'questionbank'
        elif isinstance(similar_resource, Chapter):
            resource_type = 'chapter'
        elif isinstance(similar_resource, Viva):
            resource_type = 'viva'
        elif isinstance(similar_resource, TextBook):
            resource_type = 'textbook'
        elif isinstance(similar_resource, Practical):
            resource_type = 'practical'
        else:
            resource_type = 'unknown'
        similar_resource.resource_type = resource_type
        
        explanation = f"Similar to '{resource.title}' - {similarity_score:.1%} content match"
        result.append((similar_resource, explanation))
    
    return result


def get_personalized_recommendations(user, limit=5):
    """
    Get personalized recommendations based on user's viewing and download history.
    Falls back to global trending if user's faculty has no content.
    
    Args:
        user: User instance
        limit: Maximum number of recommendations to return
        
    Returns:
        List of tuples (resource, explanation) sorted by relevance
    """
    if not user or not user.is_authenticated:
        return []
    
    # Get user's faculty (from their profile or recent activity)
    user_faculty = get_user_faculty(user)
    
    # Get user's viewing history (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_views = ViewLog.objects.filter(
        user=user,
        viewed_at__gte=thirty_days_ago
    ).order_by('-viewed_at')
    
    # Get user's download history (last 30 days)
    recent_downloads = DownloadLog.objects.filter(
        user=user,
        downloaded_at__gte=thirty_days_ago
    ).order_by('-downloaded_at')
    
    # If no recent activity, return trending resources from user's faculty only
    if not recent_views.exists() and not recent_downloads.exists():
        if user_faculty:
            return get_trending_resources(user_faculty, limit)
        # If no faculty, return empty (strict faculty filtering)
        return []
    
    # Collect all recently accessed resources
    accessed_resources = []
    
    # Process viewed resources
    for view in recent_views:
        resource = get_resource_from_log(view)
        if resource:
            accessed_resources.append(resource)
    
    # Process downloaded resources
    for download in recent_downloads:
        resource = get_resource_from_log(download)
        if resource and resource not in accessed_resources:
            accessed_resources.append(resource)
    
    if not accessed_resources:
        if user_faculty:
            return get_trending_resources(user_faculty, limit)
        # If no faculty, return empty (strict faculty filtering)
        return []
    
    # Get similar resources for each accessed resource
    similar_resources = []
    for resource in accessed_resources[:3]:  # Limit to most recent 3 resources
        similar = get_similar_resources(resource, limit=3)
        similar_resources.extend(similar)
    
    # Remove duplicates and already accessed resources
    seen_ids = set()
    unique_similar = []
    for resource, explanation in similar_resources:
        if resource.id not in seen_ids and resource not in accessed_resources:
            seen_ids.add(resource.id)
            unique_similar.append((resource, explanation))
    
    # If we don't have enough similar resources, add trending ones from user's faculty only
    if len(unique_similar) < limit and user_faculty:
        trending = get_trending_resources(user_faculty, limit)
        for resource, explanation in trending:
            if resource.id not in seen_ids and resource not in accessed_resources:
                seen_ids.add(resource.id)
                unique_similar.append((resource, explanation))
    
    return unique_similar[:limit]


def get_user_faculty(user):
    """
    Get the faculty associated with a user based on their profile or recent activity.
    
    Args:
        user: User instance
        
    Returns:
        Faculty instance or None
    """
    if not user or not user.is_authenticated:
        return None
    
    # Try to get faculty from user profile
    try:
        profile = UserProfile.objects.get(user=user)
        if hasattr(profile, 'faculty') and profile.faculty:
            return profile.faculty
    except UserProfile.DoesNotExist:
        pass
    
    # Try to get faculty from recent activity
    recent_views = ViewLog.objects.filter(user=user).order_by('-viewed_at')[:10]
    for view in recent_views:
        resource = get_resource_from_log(view)
        if resource and resource.subject and resource.subject.faculty:
            return resource.subject.faculty
    
    # Try to get faculty from recent downloads
    recent_downloads = DownloadLog.objects.filter(user=user).order_by('-downloaded_at')[:10]
    for download in recent_downloads:
        resource = get_resource_from_log(download)
        if resource and resource.subject and resource.subject.faculty:
            return resource.subject.faculty
    
    return None


def get_fallback_faculty():
    """
    Get a fallback faculty when user's faculty has no content.
    Returns the faculty with the most content.
    
    Returns:
        Faculty instance or None
    """
    from django.db.models import Count
    
    # Get faculty with most approved resources
    faculty_counts = Faculty.objects.filter(is_active=True).annotate(
        total_resources=Count('subjects__notes', filter=Q(subjects__notes__status='approved')) +
                       Count('subjects__syllabi', filter=Q(subjects__syllabi__status='approved')) +
                       Count('subjects__question_banks', filter=Q(subjects__question_banks__status='approved'))
    ).filter(total_resources__gt=0).order_by('-total_resources')
    
    return faculty_counts.first()


def get_resource_from_log(log_entry):
    """
    Get the actual resource instance from a ViewLog or DownloadLog entry.
    
    Args:
        log_entry: ViewLog or DownloadLog instance
        
    Returns:
        Resource instance (Syllabus, Note, or QuestionBank) or None
    """
    try:
        if hasattr(log_entry, 'content_type'):
            content_type = log_entry.content_type
            content_id = getattr(log_entry, 'content_id', None) or getattr(log_entry, 'object_id', None)
            
            if content_type == 'syllabus' and content_id:
                return Syllabus.objects.get(id=content_id, status='approved')
            elif content_type == 'note' and content_id:
                return Note.objects.get(id=content_id, status='approved')
            elif content_type == 'questionbank' and content_id:
                return QuestionBank.objects.get(id=content_id, status='approved')
            elif content_type == 'chapter' and content_id:
                return Chapter.objects.get(id=content_id, status='approved')
            elif content_type == 'viva' and content_id:
                return Viva.objects.get(id=content_id, status='approved')
            elif content_type == 'textbook' and content_id:
                return TextBook.objects.get(id=content_id, status='approved')
            elif content_type == 'practical' and content_id:
                return Practical.objects.get(id=content_id, status='approved')
    except Exception:
        pass
    
    return None


def get_faculty_recommendations(faculty, limit=10):
    """
    Get comprehensive recommendations for a faculty including all three types.
    
    Args:
        faculty: Faculty instance
        limit: Maximum number of recommendations per type
        
    Returns:
        Dictionary with 'trending', 'similar', and 'personalized' recommendations
    """
    if not faculty:
        return {
            'trending': [],
            'similar': [],
            'personalized': []
        }
    
    # Get trending resources for this faculty
    trending = get_trending_resources(faculty, limit)
    
    # If no trending resources, get global trending
    if not trending:
        trending = get_global_trending_resources(limit)
    
    return {
        'trending': trending,
        'similar': [],  # Will be populated based on user's last viewed resource
        'personalized': []  # Will be populated based on user's history
    }


def get_recommendations_for_faculty_slug(faculty_slug, limit=5):
    """
    Get recommendations for a specific faculty by slug.
    Useful for testing and faculty-specific pages.
    
    Args:
        faculty_slug: Faculty slug (e.g., 'bsccsit', 'bba')
        limit: Maximum number of recommendations
        
    Returns:
        Dictionary with recommendations or empty dict if faculty not found
    """
    try:
        faculty = Faculty.objects.get(slug=faculty_slug, is_active=True)
        return get_faculty_recommendations(faculty, limit)
    except Faculty.DoesNotExist:
        return {
            'trending': [],
            'similar': [],
            'personalized': []
        }


def get_user_recommendations(user, limit=5):
    """
    Get comprehensive recommendations for a user including all three types.
    Provides fallback recommendations when user's faculty has no content.
    
    Args:
        user: User instance
        limit: Maximum number of recommendations per type
        
    Returns:
        Dictionary with 'trending', 'similar', and 'personalized' recommendations
    """
    if not user or not user.is_authenticated:
        return {
            'trending': [],
            'similar': [],
            'personalized': []
        }
    
    user_faculty = get_user_faculty(user)
    
    # Get trending recommendations from user's faculty only (strict filtering)
    trending = get_trending_resources(user_faculty, limit) if user_faculty else []
    
    # Get personalized recommendations (already has fallback built-in)
    personalized = get_personalized_recommendations(user, limit)
    
    # Get similar recommendations based on last viewed resource
    similar = []
    recent_view = ViewLog.objects.filter(user=user).order_by('-viewed_at').first()
    if recent_view:
        last_resource = get_resource_from_log(recent_view)
        if last_resource:
            similar = get_similar_resources(last_resource, limit)
    
    # If no similar resources, use some trending ones from user's faculty
    if not similar and trending:
        similar = trending[:limit]
    
    return {
        'trending': trending,
        'similar': similar,
        'personalized': personalized
    }
