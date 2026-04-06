"""Tests for the POST /api/register/ endpoint."""
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User


class RegisterHappyPathTest(TestCase):
    """Tests for successful user registration."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/register/'
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'confirmed_password': 'SecurePass123!',
        }

    def test_register_success_returns_201(self):
        """A valid registration returns 201 and creates the user."""
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['detail'], 'User created successfully!')
        self.assertTrue(User.objects.filter(username='testuser').exists())


class RegisterUnhappyPathTest(TestCase):
    """Tests for registration failure scenarios."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/register/'

    def test_passwords_do_not_match_returns_400(self):
        """Mismatched passwords return 400."""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'confirmed_password': 'WrongPass456!',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_duplicate_username_returns_400(self):
        """A duplicate username returns 400."""
        User.objects.create_user(
            username='testuser', email='first@example.com', password='pass',
        )
        data = {
            'username': 'testuser',
            'email': 'second@example.com',
            'password': 'SecurePass123!',
            'confirmed_password': 'SecurePass123!',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_duplicate_email_returns_400(self):
        """A duplicate email returns 400."""
        User.objects.create_user(
            username='firstuser', email='test@example.com', password='pass',
        )
        data = {
            'username': 'seconduser',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'confirmed_password': 'SecurePass123!',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_missing_fields_returns_400(self):
        """Missing required fields return 400."""
        data = {'username': 'testuser'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_empty_body_returns_400(self):
        """An empty request body returns 400."""
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, 400)
