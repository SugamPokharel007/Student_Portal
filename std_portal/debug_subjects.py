#!/usr/bin/env python
"""
Debug script to check subject data and identify issues
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'std_portal.settings')
django.setup()

from student_app.models import Subject, Faculty

def debug_subjects():
    """Debug subject data to identify issues"""
    print("🔍 DEBUGGING SUBJECT DATA")
    print("=" * 50)
    
    # Check all faculties
    print("\n📚 FACULTIES:")
    faculties = Faculty.objects.all()
    for faculty in faculties:
        print(f"  - {faculty.name} (ID: {faculty.id}, Slug: {faculty.slug}, Active: {faculty.is_active})")
        print(f"    Academic Structure: {faculty.academic_structure}, Total Levels: {faculty.total_levels}")
    
    # Check all subjects
    print("\n📖 ALL SUBJECTS:")
    subjects = Subject.objects.all()
    for subject in subjects:
        faculty_name = subject.faculty.name if subject.faculty else "NO FACULTY"
        print(f"  - {subject.name} (ID: {subject.id})")
        print(f"    Faculty: {faculty_name}")
        print(f"    Level: {subject.level}")
        print(f"    Active: {subject.is_active}")
        print(f"    Faculty Null: {subject.faculty is None}")
    
    # Check subjects by faculty
    print("\n🏛️ SUBJECTS BY FACULTY:")
    for faculty in faculties:
        print(f"\n  {faculty.name}:")
        faculty_subjects = Subject.objects.filter(faculty=faculty)
        print(f"    Total subjects: {faculty_subjects.count()}")
        
        # Check by level
        for level in range(1, faculty.total_levels + 1):
            level_subjects = faculty_subjects.filter(level=level)
            print(f"    Level {level}: {level_subjects.count()} subjects")
            for subject in level_subjects:
                print(f"      - {subject.name}")
        
        # Check subjects without level
        no_level_subjects = faculty_subjects.filter(level__isnull=True)
        if no_level_subjects.exists():
            print(f"    No Level: {no_level_subjects.count()} subjects")
            for subject in no_level_subjects:
                print(f"      - {subject.name}")
    
    # Check what the faculty_overview view would see
    print("\n🔍 WHAT FACULTY_OVERVIEW VIEW SEES:")
    for faculty in faculties:
        print(f"\n  {faculty.name} (slug: {faculty.slug}):")
        subjects_by_level = {}
        
        for level in range(1, faculty.total_levels + 1):
            subjects = Subject.objects.filter(
                faculty=faculty, 
                level=level, 
                is_active=True,
                faculty__isnull=False
            ).order_by('name')
            
            if subjects.exists():
                subjects_by_level[level] = subjects
                print(f"    Level {level}: {subjects.count()} subjects")
            else:
                print(f"    Level {level}: 0 subjects")
        
        print(f"    Total levels with subjects: {len(subjects_by_level)}")

if __name__ == '__main__':
    debug_subjects() 