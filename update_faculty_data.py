#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'std_portal.settings')
django.setup()

from student_app.models import Faculty, Subject

def update_faculty_data():
    print("Updating faculty data with new structure...")
    
    # Update existing faculties with slugs and academic structure
    faculty_updates = {
        'BSc CSIT': {
            'slug': 'bsccsit',
            'academic_structure': 'semester',
            'total_levels': 8,
            'description': 'Computer Science & Information Technology'
        },
        'BBS': {
            'slug': 'bbs',
            'academic_structure': 'year',
            'total_levels': 4,
            'description': 'Bachelor of Business Studies'
        },
        'BBA': {
            'slug': 'bba',
            'academic_structure': 'semester',
            'total_levels': 8,
            'description': 'Bachelor of Business Administration'
        },
        'BSc': {
            'slug': 'bsc',
            'academic_structure': 'semester',
            'total_levels': 8,
            'description': 'Bachelor of Science'
        }
    }
    
    for faculty_name, data in faculty_updates.items():
        try:
            faculty = Faculty.objects.get(name=faculty_name)
            faculty.slug = data['slug']
            faculty.academic_structure = data['academic_structure']
            faculty.total_levels = data['total_levels']
            faculty.description = data['description']
            faculty.save()
            print(f"✓ Updated {faculty_name}: {data['slug']} ({data['academic_structure']} system, {data['total_levels']} levels)")
        except Faculty.DoesNotExist:
            print(f"✗ Faculty not found: {faculty_name}")
    
    # Update existing subjects to have proper level values
    print("\nUpdating subject levels...")
    
    # Map old year values to new level values
    year_to_level_mapping = {
        'first': 1,
        'second': 2,
        'third': 3,
        'fourth': 4,
    }
    
    subjects_updated = 0
    for subject in Subject.objects.all():
        if hasattr(subject, 'year') and subject.year in year_to_level_mapping:
            subject.level = year_to_level_mapping[subject.year]
            subject.save()
            subjects_updated += 1
            print(f"✓ Updated {subject.name}: {subject.year} → level {subject.level}")
    
    print(f"\n✅ Updated {subjects_updated} subjects")
    
    # Now add the unique_together constraint back
    print("\nRe-adding unique_together constraint...")
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS student_app_subject_name_faculty_id_level_uniq 
            ON student_app_subject (name, faculty_id, level) 
            WHERE faculty_id IS NOT NULL AND level IS NOT NULL
        """)
    
    print("✅ Database structure updated successfully!")
    
    # Show summary
    print("\n📋 Summary:")
    for faculty in Faculty.objects.all():
        subject_count = Subject.objects.filter(faculty=faculty).count()
        print(f"   • {faculty.name} ({faculty.slug}): {subject_count} subjects, {faculty.academic_structure} system")

if __name__ == '__main__':
    update_faculty_data() 