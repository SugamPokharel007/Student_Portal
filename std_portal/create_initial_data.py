#!/usr/bin/env python
"""
Script to create initial data for Sikshya Kendra Student Portal
Run this script to set up faculties, subjects, and sample data
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'std_portal.settings')
django.setup()

from student_app.models import Faculty, Subject, Notice
from django.contrib.auth.models import User

def create_faculties():
    """Create initial faculties"""
    print("Creating faculties...")
    
    faculties_data = [
        {
            'name': 'BSc CSIT',
            'description': 'Bachelor of Science in Computer Science and Information Technology',
            'code': 'BSCSIT'
        },
        {
            'name': 'BBS',
            'description': 'Bachelor of Business Studies',
            'code': 'BBS'
        },
        {
            'name': 'BBA',
            'description': 'Bachelor of Business Administration',
            'code': 'BBA'
        },
        {
            'name': 'BSc',
            'description': 'Bachelor of Science',
            'code': 'BSC'
        }
    ]
    
    for faculty_data in faculties_data:
        faculty, created = Faculty.objects.get_or_create(
            code=faculty_data['code'],
            defaults={
                'name': faculty_data['name'],
                'description': faculty_data['description'],
                'is_active': True
            }
        )
        if created:
            print(f"✓ Created faculty: {faculty.name}")
        else:
            print(f"✓ Faculty already exists: {faculty.name}")
    
    return Faculty.objects.all()

def create_subjects():
    """Create sample subjects for each faculty"""
    print("\nCreating subjects...")
    
    subjects_data = {
        'BSc CSIT': [
            {'name': 'Programming Fundamentals', 'year': 'first', 'semester': 'first'},
            {'name': 'Digital Logic', 'year': 'first', 'semester': 'first'},
            {'name': 'Mathematics I', 'year': 'first', 'semester': 'first'},
            {'name': 'English', 'year': 'first', 'semester': 'first'},
            {'name': 'Physics', 'year': 'first', 'semester': 'first'},
            {'name': 'Data Structures and Algorithms', 'year': 'first', 'semester': 'second'},
            {'name': 'Computer Architecture', 'year': 'first', 'semester': 'second'},
            {'name': 'Mathematics II', 'year': 'first', 'semester': 'second'},
            {'name': 'Statistics', 'year': 'first', 'semester': 'second'},
            {'name': 'Web Technology', 'year': 'first', 'semester': 'second'},
        ],
        'BBS': [
            {'name': 'Business English', 'year': 'first', 'semester': 'first'},
            {'name': 'Business Mathematics', 'year': 'first', 'semester': 'first'},
            {'name': 'Microeconomics', 'year': 'first', 'semester': 'first'},
            {'name': 'Principles of Management', 'year': 'first', 'semester': 'first'},
            {'name': 'Business Statistics', 'year': 'first', 'semester': 'first'},
            {'name': 'Financial Accounting', 'year': 'first', 'semester': 'second'},
            {'name': 'Macroeconomics', 'year': 'first', 'semester': 'second'},
            {'name': 'Business Communication', 'year': 'first', 'semester': 'second'},
            {'name': 'Computer Applications', 'year': 'first', 'semester': 'second'},
            {'name': 'Business Law', 'year': 'first', 'semester': 'second'},
        ],
        'BBA': [
            {'name': 'Business Communication', 'year': 'first', 'semester': 'first'},
            {'name': 'Business Mathematics', 'year': 'first', 'semester': 'first'},
            {'name': 'Microeconomics', 'year': 'first', 'semester': 'first'},
            {'name': 'Principles of Management', 'year': 'first', 'semester': 'first'},
            {'name': 'Business Statistics', 'year': 'first', 'semester': 'first'},
            {'name': 'Financial Accounting', 'year': 'first', 'semester': 'second'},
            {'name': 'Macroeconomics', 'year': 'first', 'semester': 'second'},
            {'name': 'Marketing Management', 'year': 'first', 'semester': 'second'},
            {'name': 'Computer Applications', 'year': 'first', 'semester': 'second'},
            {'name': 'Business Law', 'year': 'first', 'semester': 'second'},
        ],
        'BSc': [
            {'name': 'Physics', 'year': 'first', 'semester': 'first'},
            {'name': 'Chemistry', 'year': 'first', 'semester': 'first'},
            {'name': 'Mathematics', 'year': 'first', 'semester': 'first'},
            {'name': 'Biology', 'year': 'first', 'semester': 'first'},
            {'name': 'English', 'year': 'first', 'semester': 'first'},
            {'name': 'Advanced Physics', 'year': 'first', 'semester': 'second'},
            {'name': 'Advanced Chemistry', 'year': 'first', 'semester': 'second'},
            {'name': 'Advanced Mathematics', 'year': 'first', 'semester': 'second'},
            {'name': 'Advanced Biology', 'year': 'first', 'semester': 'second'},
            {'name': 'Computer Science', 'year': 'first', 'semester': 'second'},
        ]
    }
    
    for faculty_name, subjects in subjects_data.items():
        try:
            faculty = Faculty.objects.get(name=faculty_name)
            for subject_data in subjects:
                subject, created = Subject.objects.get_or_create(
                    name=subject_data['name'],
                    faculty=faculty,
                    year=subject_data['year'],
                    defaults={
                        'semester': subject_data['semester'],
                        'is_active': True
                    }
                )
                if created:
                    print(f"✓ Created subject: {subject.name} ({faculty.name})")
                else:
                    print(f"✓ Subject already exists: {subject.name} ({faculty.name})")
        except Faculty.DoesNotExist:
            print(f"✗ Faculty not found: {faculty_name}")

def create_sample_notices():
    """Create sample notices"""
    print("\nCreating sample notices...")
    
    notices_data = [
        {
            'title': 'Welcome to Sikshya Kendra',
            'content': 'Welcome to our Student Portal! This is a comprehensive platform for accessing educational resources, study materials, and academic support.',
            'is_general': True,
            'is_important': True
        },
        {
            'title': 'New Resources Available',
            'content': 'We have added new study materials for BSc CSIT, BBS, and BBA programs. Check out the latest syllabus, notes, and question banks.',
            'is_general': True,
            'is_important': True
        },
        {
            'title': 'Contributor Program Launch',
            'content': 'Students can now become contributors and share their study materials. Apply through the "Become Contributor" section.',
            'is_general': True,
            'is_important': False
        }
    ]
    
    for notice_data in notices_data:
        notice, created = Notice.objects.get_or_create(
            title=notice_data['title'],
            defaults={
                'content': notice_data['content'],
                'is_general': notice_data['is_general'],
                'is_important': notice_data['is_important']
            }
        )
        if created:
            print(f"✓ Created notice: {notice.title}")
        else:
            print(f"✓ Notice already exists: {notice.title}")

def create_superuser():
    """Create a superuser if none exists"""
    print("\nChecking for superuser...")
    
    if not User.objects.filter(is_superuser=True).exists():
        print("Creating superuser...")
        username = 'admin'
        email = 'admin@sikshyakendra.edu.np'
        password = 'admin123'
        
        user = User.objects.create_superuser(username, email, password)
        print(f"✓ Created superuser: {username} (password: {password})")
        print("⚠️  Please change the password after first login!")
    else:
        print("✓ Superuser already exists")

def main():
    """Main function to run all setup tasks"""
    print("🚀 Setting up Sikshya Kendra Student Portal...")
    print("=" * 50)
    
    try:
        # Create faculties
        faculties = create_faculties()
        
        # Create subjects
        create_subjects()
        
        # Create sample notices
        create_sample_notices()
        
        # Create superuser
        create_superuser()
        
        print("\n" + "=" * 50)
        print("✅ Setup completed successfully!")
        print("\n📋 Summary:")
        print(f"   • {Faculty.objects.count()} faculties created")
        print(f"   • {Subject.objects.count()} subjects created")
        print(f"   • {Notice.objects.count()} notices created")
        print(f"   • {User.objects.filter(is_superuser=True).count()} superuser(s)")
        
        print("\n🎯 Next steps:")
        print("   1. Run 'python manage.py runserver' to start the development server")
        print("   2. Visit http://127.0.0.1:8000 to access the portal")
        print("   3. Login with admin credentials if needed")
        print("   4. Start adding more content and customizing the portal")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 