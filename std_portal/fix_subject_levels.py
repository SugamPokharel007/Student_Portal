#!/usr/bin/env python
"""
Script to fix subject levels for subjects that don't have them set
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

def fix_subject_levels():
    """Fix subject levels for subjects that don't have them set"""
    print("🔧 FIXING SUBJECT LEVELS")
    print("=" * 50)
    
    # Get all subjects without levels
    subjects_without_level = Subject.objects.filter(level__isnull=True, faculty__isnull=False)
    print(f"Found {subjects_without_level.count()} subjects without levels:")
    
    for subject in subjects_without_level:
        print(f"  - {subject.name} (Faculty: {subject.faculty.name})")
    
    if subjects_without_level.count() == 0:
        print("✅ All subjects have levels set.")
        return
    
    # Ask for confirmation
    response = input("\nDo you want to set these subjects to level 1? (y/N): ")
    if response.lower() == 'y':
        subjects_without_level.update(level=1)
        print(f"✅ Set {subjects_without_level.count()} subjects to level 1.")
    else:
        print("❌ No changes made.")
    
    # Show summary
    print("\n📊 SUBJECT SUMMARY BY FACULTY:")
    for faculty in Faculty.objects.filter(is_active=True):
        print(f"\n  {faculty.name}:")
        faculty_subjects = Subject.objects.filter(faculty=faculty, is_active=True)
        print(f"    Total subjects: {faculty_subjects.count()}")
        
        for level in range(1, faculty.total_levels + 1):
            level_subjects = faculty_subjects.filter(level=level)
            if level_subjects.exists():
                print(f"    Level {level}: {level_subjects.count()} subjects")
                for subject in level_subjects:
                    print(f"      - {subject.name}")

if __name__ == '__main__':
    fix_subject_levels() 