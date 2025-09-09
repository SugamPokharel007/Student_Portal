#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'std_portal.settings')
django.setup()

from student_app.models import Faculty, MCQQuiz, User

def create_sample_quizzes():
    print("Creating sample quizzes...")
    
    # Get first faculty
    faculty = Faculty.objects.first()
    if not faculty:
        print("No faculty found!")
        return
    
    print(f"Using faculty: {faculty.name}")
    
    # Get first admin user
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("No admin user found!")
        return
    
    print(f"Using admin: {admin_user.username}")
    
    # Create quizzes for this faculty
    quizzes_data = [
        {"quiz_number": 1, "title": "Basic Concepts"},
        {"quiz_number": 2, "title": "Advanced Topics"},
        {"quiz_number": 3, "title": "Final Exam"},
    ]
    
    created_quizzes = []
    for quiz_data in quizzes_data:
        quiz, created = MCQQuiz.objects.get_or_create(
            faculty=faculty,
            quiz_number=quiz_data["quiz_number"],
            defaults={
                "title": quiz_data["title"],
                "created_by": admin_user,
                "is_active": True
            }
        )
        if created:
            created_quizzes.append(quiz)
            print(f"Created: {quiz.display_name}")
        else:
            print(f"Already exists: {quiz.display_name}")
    
    print(f"\nTotal quizzes created: {len(created_quizzes)}")
    print("Sample quizzes created successfully!")

if __name__ == "__main__":
    create_sample_quizzes()
