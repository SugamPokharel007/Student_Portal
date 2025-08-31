#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'std_portal.settings')
django.setup()

from student_app.models import Subject, Faculty

def organize_subjects_nepal():
    print("🇳🇵 ORGANIZING SUBJECTS - NEPAL STUDY CONTEXT")
    print("=" * 60)
    
    print("\n📊 CURRENT SUBJECT STATUS:")
    for faculty in Faculty.objects.filter(is_active=True):
        print(f"\n🏛️ {faculty.name}:")
        subjects = Subject.objects.filter(faculty=faculty)
        print(f"  Total subjects: {subjects.count()}")
        
        for level in range(1, faculty.total_levels + 1):
            level_subjects = subjects.filter(level=level)
            if level_subjects.exists():
                print(f"  Level {level}: {level_subjects.count()} subjects")
                for subject in level_subjects:
                    print(f"    - {subject.name}")
        
        no_level = subjects.filter(level__isnull=True)
        if no_level.exists():
            print(f"  No Level: {no_level.count()} subjects")
            for subject in no_level:
                print(f"    - {subject.name}")
    
    bsccsit_subjects = {
        1: [
            "C Programming",
            "Digital Logic",
            "Mathematics I",
            "Introduction to IT",
            "Physics"
        ],
        2: [
            "Object Oriented Programming",
            "Mathematics II",
            "English",
            "Microprocessor",
            "Statistics I"
        ],
        3: [
            "Data Structures and Algorithms",
            "Computer Architecture",
            "Mathematics III",
            "Statistics II",
            "Computer Graphics"
        ],
        4: [
            "Computer Networks",
            "Operating Systems",
            "Database Management System",
            "Software Engineering",
            "Web Technology"
        ],
        5: [
            "System Analysis and Design",
            "Computer Security",
            "Cryptography",
            "Artificial Intelligence",
            "E-Governance"
        ],
        6: [
            "Software Project Management",
            "Advanced Java Programming",
            "Advanced Database",
            "Mobile Computing",
            "Distributed Systems"
        ],
        7: [
            "Advanced Computer Architecture",
            "Advanced Computer Networks",
            "Advanced Operating Systems",
            "Advanced Software Engineering",
            "Advanced Database Management"
        ],
        8: [
            "Advanced Web Technology",
            "Advanced Mobile Computing",
            "Advanced Artificial Intelligence",
            "Advanced Cryptography",
            "Advanced Computer Security"
        ]
    }
    
    bba_subjects = {
        1: [
            "Principles of Management",
            "Business English",
            "Microeconomics",
            "Business Mathematics",
            "Computer Applications"
        ],
        2: [
            "Organizational Behavior",
            "Business Communication",
            "Macroeconomics",
            "Business Statistics",
            "Financial Accounting"
        ],
        3: [
            "Human Resource Management",
            "Business Law",
            "Cost Accounting",
            "Marketing Management",
            "Business Research Methods"
        ],
        4: [
            "Financial Management",
            "Operations Management",
            "Management Information System",
            "Business Ethics",
            "Entrepreneurship"
        ],
        5: [
            "Strategic Management",
            "International Business",
            "Investment Management",
            "Consumer Behavior",
            "Production Management"
        ],
        6: [
            "Business Policy",
            "International Marketing",
            "Banking and Insurance",
            "Supply Chain Management",
            "Business Analytics"
        ],
        7: [
            "Corporate Finance",
            "Digital Marketing",
            "Project Management",
            "Business Intelligence",
            "Corporate Governance"
        ],
        8: [
            "Advanced Strategic Management",
            "Advanced Financial Management",
            "Advanced Marketing Management",
            "Advanced Human Resource Management",
            "Business Consulting"
        ]
    }
    
    bbs_subjects = {
        1: [
            "Business English",
            "Business Economics",
            "Principles of Management",
            "Business Statistics",
            "Computer Applications"
        ],
        2: [
            "Financial Accounting",
            "Business Communication",
            "Business Law",
            "Marketing Management",
            "Human Resource Management"
        ],
        3: [
            "Financial Management",
            "Operations Management",
            "Business Research Methods",
            "Management Information System",
            "Business Ethics"
        ],
        4: [
            "Strategic Management",
            "International Business",
            "Investment Management",
            "Business Policy",
            "Entrepreneurship"
        ]
    }
    
    bsc_subjects = {
        1: [
            "Physics",
            "Chemistry",
            "Mathematics",
            "Biology",
            "English"
        ],
        2: [
            "Advanced Physics",
            "Advanced Chemistry",
            "Advanced Mathematics",
            "Advanced Biology",
            "Computer Science"
        ],
        3: [
            "Applied Physics",
            "Applied Chemistry",
            "Applied Mathematics",
            "Applied Biology",
            "Research Methods"
        ],
        4: [
            "Theoretical Physics",
            "Theoretical Chemistry",
            "Theoretical Mathematics",
            "Theoretical Biology",
            "Project Work"
        ]
    }
    
    faculty_subjects = {
        'bsccsit': bsccsit_subjects,
        'bba': bba_subjects,
        'bbs': bbs_subjects,
        'bsc': bsc_subjects
    }
    
    print("\n" + "=" * 60)
    print("🔄 ORGANIZING SUBJECTS:")
    
    for faculty_slug, subjects_by_level in faculty_subjects.items():
        try:
            faculty = Faculty.objects.get(slug=faculty_slug, is_active=True)
            print(f"\n🏛️ {faculty.name.upper()}:")
            
            existing_subjects = Subject.objects.filter(faculty=faculty)
            existing_subjects.update(is_active=False)
            print(f"  Deactivated {existing_subjects.count()} existing subjects")
            
            for level, subject_names in subjects_by_level.items():
                print(f"\n  📖 Level {level}:")
                
                for subject_name in subject_names:
                    subject, created = Subject.objects.get_or_create(
                        name=subject_name,
                        faculty=faculty,
                        defaults={
                            'level': level,
                            'is_active': True
                        }
                    )
                    
                    if created:
                        print(f"    ✅ Created: {subject_name}")
                    else:
                        old_level = subject.level
                        subject.level = level
                        subject.is_active = True
                        subject.save()
                        print(f"    🔄 Updated: {subject_name} (Level {old_level} → {level})")
            
            print(f"\n  📊 Summary for {faculty.name}:")
            active_subjects = Subject.objects.filter(faculty=faculty, is_active=True)
            print(f"    Total active subjects: {active_subjects.count()}")
            
            for level in range(1, faculty.total_levels + 1):
                level_subjects = active_subjects.filter(level=level)
                if level_subjects.exists():
                    print(f"    Level {level}: {level_subjects.count()} subjects")
                
        except Faculty.DoesNotExist:
            print(f"❌ Faculty with slug '{faculty_slug}' not found!")
    
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY:")
    for faculty in Faculty.objects.filter(is_active=True):
        total_subjects = Subject.objects.filter(faculty=faculty, is_active=True).count()
        print(f"  {faculty.name}: {total_subjects} subjects")
        
        for level in range(1, faculty.total_levels + 1):
            level_count = Subject.objects.filter(faculty=faculty, level=level, is_active=True).count()
            if level_count > 0:
                print(f"    Level {level}: {level_count} subjects")

if __name__ == '__main__':
    organize_subjects_nepal() 