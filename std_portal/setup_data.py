#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'std_portal.settings')
django.setup()

from student_app.models import Faculty, Subject, Notice
from django.contrib.auth.models import User

def setup_data():
    print("Setting up initial data...")
    
    # Create faculties
    faculties_data = [
        {'name': 'BSc CSIT', 'description': 'Computer Science & Information Technology'},
        {'name': 'BBS', 'description': 'Bachelor of Business Studies'},
        {'name': 'BBA', 'description': 'Bachelor of Business Administration'},
        {'name': 'BSc', 'description': 'Bachelor of Science'},
    ]
    
    for data in faculties_data:
        faculty, created = Faculty.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        print(f"{'Created' if created else 'Exists'}: {faculty.name}")
    
    # Create comprehensive subjects for each faculty
    subjects_data = {
        'BSc CSIT': {
            'first': [
                'Programming Fundamentals',
                'Digital Logic',
                'Mathematics I',
                'English',
                'Physics',
                'Computer Architecture',
                'Data Structures and Algorithms',
                'Mathematics II',
                'Statistics',
                'Web Technology',
                'Object Oriented Programming'
            ],
            'second': [
                'Database Management System',
                'Computer Networks',
                'Software Engineering',
                'Operating System',
                'Computer Graphics',
                'Numerical Methods',
                'System Analysis and Design',
                'Computer Organization',
                'Data Communication',
                'Microprocessor',
                'Programming in Java',
                'Web Programming'
            ],
            'third': [
                'Advanced Database',
                'Computer Security',
                'Artificial Intelligence',
                'Software Project Management',
                'Mobile Computing',
                'Distributed Systems',
                'Advanced Java Programming',
                'Network Security',
                'Machine Learning',
                'Cloud Computing',
                'Software Testing',
                'E-Commerce'
            ],
            'fourth': [
                'Advanced Web Technology',
                'Big Data Analytics',
                'Internet of Things',
                'Advanced Software Engineering',
                'Computer Vision',
                'Natural Language Processing',
                'Project Work',
                'Internship',
                'Advanced Topics in CS',
                'Research Methodology',
                'Professional Practice',
                'Seminar'
            ]
        },
        'BBS': {
            'first': [
                'Business English',
                'Business Mathematics',
                'Microeconomics',
                'Principles of Management',
                'Business Statistics',
                'Computer Applications',
                'Financial Accounting',
                'Macroeconomics',
                'Business Communication',
                'Business Law',
                'Business Environment'
            ],
            'second': [
                'Cost and Management Accounting',
                'Business Finance',
                'Marketing Management',
                'Human Resource Management',
                'Business Research Methods',
                'Business Ethics',
                'Financial Management',
                'Operations Management',
                'Organizational Behavior',
                'Business Information System',
                'Business Taxation',
                'Entrepreneurship'
            ],
            'third': [
                'Advanced Financial Management',
                'Strategic Management',
                'International Business',
                'Business Policy',
                'Research Project',
                'Business Law II',
                'Investment Management',
                'Business Strategy',
                'Corporate Finance',
                'Business Analytics',
                'Project Work',
                'Seminar'
            ],
            'fourth': [
                'Advanced Business Research',
                'Business Consulting',
                'International Marketing',
                'Corporate Governance',
                'Business Innovation',
                'Professional Practice',
                'Thesis',
                'Internship',
                'Advanced Business Topics',
                'Business Leadership',
                'Professional Ethics',
                'Capstone Project'
            ]
        },
        'BBA': {
            'first': [
                'Business Communication',
                'Business Mathematics',
                'Microeconomics',
                'Principles of Management',
                'Business Statistics',
                'Computer Applications',
                'Financial Accounting',
                'Macroeconomics',
                'Marketing Management',
                'Business Law',
                'Business Environment'
            ],
            'second': [
                'Cost and Management Accounting',
                'Business Finance',
                'Marketing Management',
                'Human Resource Management',
                'Business Research Methods',
                'Business Ethics',
                'Financial Management',
                'Operations Management',
                'Organizational Behavior',
                'Business Information System',
                'Business Taxation',
                'Entrepreneurship'
            ],
            'third': [
                'Advanced Financial Management',
                'Strategic Management',
                'International Business',
                'Business Policy',
                'Research Project',
                'Business Law II',
                'Investment Management',
                'Business Strategy',
                'Corporate Finance',
                'Business Analytics',
                'Project Work',
                'Seminar'
            ],
            'fourth': [
                'Advanced Business Research',
                'Business Consulting',
                'International Marketing',
                'Corporate Governance',
                'Business Innovation',
                'Professional Practice',
                'Thesis',
                'Internship',
                'Advanced Business Topics',
                'Business Leadership',
                'Professional Ethics',
                'Capstone Project'
            ]
        },
        'BSc': {
            'first': [
                'Physics',
                'Chemistry',
                'Mathematics',
                'Biology',
                'English',
                'Computer Science',
                'Advanced Physics',
                'Advanced Chemistry',
                'Advanced Mathematics',
                'Advanced Biology',
                'Environmental Science'
            ],
            'second': [
                'Mechanics',
                'Organic Chemistry',
                'Calculus',
                'Genetics',
                'Programming',
                'Statistics',
                'Electromagnetism',
                'Inorganic Chemistry',
                'Linear Algebra',
                'Ecology',
                'Data Structures',
                'Probability'
            ],
            'third': [
                'Quantum Physics',
                'Physical Chemistry',
                'Differential Equations',
                'Microbiology',
                'Database Systems',
                'Research Methods',
                'Thermodynamics',
                'Analytical Chemistry',
                'Numerical Methods',
                'Biochemistry',
                'Software Engineering',
                'Project Work'
            ],
            'fourth': [
                'Advanced Physics Lab',
                'Advanced Chemistry Lab',
                'Advanced Mathematics',
                'Advanced Biology Lab',
                'Advanced Programming',
                'Research Project',
                'Thesis',
                'Internship',
                'Advanced Topics',
                'Professional Practice',
                'Seminar',
                'Capstone Project'
            ]
        }
    }
    
    for faculty_name, years in subjects_data.items():
        try:
            faculty = Faculty.objects.get(name=faculty_name)
            print(f"\nCreating subjects for {faculty.name}:")
            
            for year, subjects in years.items():
                for subject_name in subjects:
                    subject, created = Subject.objects.get_or_create(
                        name=subject_name,
                        faculty=faculty,
                        year=year,
                        defaults={
                            'is_active': True
                        }
                    )
                    if created:
                        print(f"  ✓ Created: {subject.name} ({year} year)")
                    else:
                        print(f"  ✓ Exists: {subject.name} ({year} year)")
                        
        except Faculty.DoesNotExist:
            print(f"✗ Faculty not found: {faculty_name}")
    
    # Create sample notices
    notices_data = [
        {
            'title': 'Welcome to Sikshya Kendra',
            'content': 'Welcome to our Student Portal! This is a comprehensive platform for accessing educational resources.',
            'is_general': True,
            'is_important': True
        },
        {
            'title': 'New Resources Available',
            'content': 'We have added new study materials for various faculties. Check out the latest syllabus, notes, and question banks.',
            'is_general': True,
            'is_important': True
        },
        {
            'title': 'Faculty-Specific Subjects Added',
            'content': 'Each faculty now has its own unique subjects. BSc CSIT students will see programming and computer science subjects, while BBS/BBA students will see business and management subjects.',
            'is_general': True,
            'is_important': False
        }
    ]
    
    for data in notices_data:
        notice, created = Notice.objects.get_or_create(
            title=data['title'],
            defaults=data
        )
        print(f"{'Created' if created else 'Exists'}: {notice.title}")
    
    # Create superuser if none exists
    if not User.objects.filter(is_superuser=True).exists():
        user = User.objects.create_superuser('admin', 'admin@sikshyakendra.edu.np', 'admin123')
        print(f"Created superuser: admin (password: admin123)")
    else:
        print("Superuser already exists")
    
    print("\n" + "="*50)
    print("✅ Setup completed successfully!")
    print("\n📋 Summary:")
    print(f"   • {Faculty.objects.count()} faculties created")
    print(f"   • {Subject.objects.count()} subjects created")
    print(f"   • {Notice.objects.count()} notices created")
    print(f"   • {User.objects.filter(is_superuser=True).count()} superuser(s)")
    
    print("\n🎯 Faculty-Specific Subjects:")
    for faculty in Faculty.objects.all():
        subject_count = Subject.objects.filter(faculty=faculty).count()
        print(f"   • {faculty.name}: {subject_count} subjects")
    
    print("\n🚀 Next steps:")
    print("   1. Run 'python manage.py runserver' to start the development server")
    print("   2. Visit http://127.0.0.1:8000 to access the portal")
    print("   3. Login with admin credentials if needed")
    print("   4. Each faculty now has its own unique subjects!")

if __name__ == '__main__':
    setup_data() 