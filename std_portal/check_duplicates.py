#!/usr/bin/env python
"""
Script to check for duplicate subjects
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'std_portal.settings')
django.setup()

from student_app.models import Subject
from django.db.models import Count

def check_duplicates():
    """Check for duplicate subjects"""
    print("🔍 CHECKING FOR DUPLICATE SUBJECTS")
    print("=" * 50)
    
    # Check for duplicates based on name, faculty, and level
    duplicates = Subject.objects.values('name', 'faculty_id', 'level').annotate(count=Count('id')).filter(count__gt=1)
    
    if duplicates.exists():
        print(f"Found {duplicates.count()} duplicate combinations:")
        for dup in duplicates:
            print(f"  - {dup['name']} (Faculty ID: {dup['faculty_id']}, Level: {dup['level']}, Count: {dup['count']})")
            
            # Show the actual subjects
            subjects = Subject.objects.filter(name=dup['name'], faculty_id=dup['faculty_id'], level=dup['level'])
            for subject in subjects:
                print(f"    * ID: {subject.id}, Name: {subject.name}, Faculty: {subject.faculty.name if subject.faculty else 'None'}")
    else:
        print("✅ No duplicate subjects found.")
    
    # Check for subjects with same name in same faculty but different levels
    print("\n📊 SUBJECTS BY FACULTY:")
    from student_app.models import Faculty
    for faculty in Faculty.objects.filter(is_active=True):
        print(f"\n  {faculty.name}:")
        faculty_subjects = Subject.objects.filter(faculty=faculty).order_by('name', 'level')
        
        current_name = None
        for subject in faculty_subjects:
            if subject.name == current_name:
                print(f"    ⚠️  DUPLICATE: {subject.name} (Level: {subject.level}, ID: {subject.id})")
            else:
                print(f"    - {subject.name} (Level: {subject.level}, ID: {subject.id})")
                current_name = subject.name

if __name__ == '__main__':
    check_duplicates() 