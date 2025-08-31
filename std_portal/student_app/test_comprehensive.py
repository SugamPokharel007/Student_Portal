import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from student_app.models import Faculty, Subject, Notice, UserProfile


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.faculty = Faculty.objects.create(
            name='Test Faculty',
            slug='test-faculty',
            description='Test Description'
        )

    def test_faculty_creation(self):
        self.assertEqual(self.faculty.name, 'Test Faculty')
        self.assertEqual(str(self.faculty), 'Test Faculty')

    def test_subject_creation(self):
        subject = Subject.objects.create(
            name='Test Subject',
            faculty=self.faculty,
            level=1
        )
        self.assertEqual(subject.name, 'Test Subject')
        self.assertEqual(subject.faculty, self.faculty)

    def test_user_profile_creation(self):
        profile = UserProfile.objects.create(user=self.user, faculty=self.faculty)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.faculty, self.faculty)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.faculty = Faculty.objects.create(
            name='Test Faculty',
            slug='test-faculty'
        )

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_with_login(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to faculty selection


class FormTests(TestCase):
    def test_user_registration_form_valid(self):
        from student_app.forms import UserRegistrationForm
        
        form_data = {
            'username': 'newuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_user_registration_form_invalid(self):
        from student_app.forms import UserRegistrationForm
        
        form_data = {
            'username': 'newuser',
            'password1': 'pass',
            'password2': 'differentpass'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())


class IntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_complete_user_flow(self):
        # Test registration
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        })
        self.assertEqual(response.status_code, 302)
        
        # Test login
        response = self.client.post(reverse('login'), {
            'username': 'newuser',
            'password': 'complexpassword123'
        })
        self.assertEqual(response.status_code, 302)


@pytest.mark.django_db
class TestUserModel:
    def test_user_creation(self):
        user = User.objects.create_user(
            username='pytest_user',
            email='pytest@example.com',
            password='testpass123'
        )
        assert user.username == 'pytest_user'
        assert user.email == 'pytest@example.com'

    def test_user_profile_creation(self):
        user = User.objects.create_user(
            username='pytest_user',
            email='pytest@example.com',
            password='testpass123'
        )
        faculty = Faculty.objects.create(
            name='Pytest Faculty',
            slug='pytest-faculty'
        )
        profile = UserProfile.objects.create(user=user, faculty=faculty)
        assert profile.user == user
        assert profile.faculty == faculty