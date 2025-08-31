#!/usr/bin/env python
"""
Script to clean up subjects with null faculty values
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

def cleanup_subjects():
    """Clean up subjects with null faculty values"""
    print("Cleaning up subjects with null faculty values...")
    
    # Get subjects with null faculty
    null_faculty_subjects = Subject.objects.filter(faculty__isnull=True)
    count = null_faculty_subjects.count()
    
    if count == 0:
        print("✅ No subjects with null faculty found.")
        return
    
    print(f"Found {count} subjects with null faculty:")
    
    # List the subjects
    for subject in null_faculty_subjects:
        print(f"  - {subject.name} (ID: {subject.id})")
    
    # Ask for confirmation
    response = input("\nDo you want to delete these subjects? (y/N): ")
    if response.lower() == 'y':
        null_faculty_subjects.delete()
        print(f"✅ Deleted {count} subjects with null faculty.")
    else:
        print("❌ No subjects were deleted.")
    
    # Also check for subjects with invalid faculty references
    print("\nChecking for subjects with invalid faculty references...")
    all_subjects = Subject.objects.all()
    invalid_count = 0
    
    for subject in all_subjects:
        if subject.faculty and not Faculty.objects.filter(id=subject.faculty.id).exists():
            print(f"  - {subject.name} (ID: {subject.id}) has invalid faculty reference")
            invalid_count += 1
    
    if invalid_count == 0:
        print("✅ No subjects with invalid faculty references found.")
    else:
        print(f"Found {invalid_count} subjects with invalid faculty references.")
        response = input("Do you want to set their faculty to null? (y/N): ")
        if response.lower() == 'y':
            for subject in all_subjects:
                if subject.faculty and not Faculty.objects.filter(id=subject.faculty.id).exists():
                    subject.faculty = None
                    subject.save()
            print(f"✅ Set faculty to null for {invalid_count} subjects.")

if __name__ == '__main__':
    cleanup_subjects() 