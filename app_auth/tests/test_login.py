"""Tests for the POST /api/login/ endpoint."""
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User


class LoginHappyPathTest(TestCase):
    """Tests for successful login."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/login/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )

    def test_login_success_returns_200(self):
        """Valid credentials return 200."""
        data = {'username': 'testuser', 'password': 'SecurePass123!'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 200)

    def test_login_response_contains_user_data(self):
        """Response body includes user id, username, and email."""
        data = {'username': 'testuser', 'password': 'SecurePass123!'}
        response = self.client.post(self.url, data, format='json')
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertIn('id', response.data['user'])

    def test_login_response_contains_detail_message(self):
        """Response body includes the success detail message."""
        data = {'username': 'testuser', 'password': 'SecurePass123!'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.data['detail'], 'Login successfully!')

    def test_login_sets_httponly_access_cookie(self):
        """Login sets an httponly access_token cookie."""
        data = {'username': 'testuser', 'password': 'SecurePass123!'}
        response = self.client.post(self.url, data, format='json')
        self.assertIn('access_token', response.cookies)
        self.assertTrue(response.cookies['access_token']['httponly'])

    def test_login_sets_httponly_refresh_cookie(self):
        """Login sets an httponly refresh_token cookie."""
        data = {'username': 'testuser', 'password': 'SecurePass123!'}
        response = self.client.post(self.url, data, format='json')
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['refresh_token']['httponly'])

    def test_login_does_not_expose_tokens_in_body(self):
        """Tokens must not appear in the JSON response body."""
        data = {'username': 'testuser', 'password': 'SecurePass123!'}
        response = self.client.post(self.url, data, format='json')
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)
        self.assertNotIn('access_token', response.data)
        self.assertNotIn('refresh_token', response.data)


class LoginUnhappyPathTest(TestCase):
    """Tests for login failure scenarios."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/login/'
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )

    def test_wrong_password_returns_401(self):
        """Wrong password returns 401 with generic message."""
        data = {'username': 'testuser', 'password': 'WrongPassword!'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_unknown_user_returns_401(self):
        """Unknown username returns 401 with generic message."""
        data = {'username': 'unknownuser', 'password': 'AnyPassword!'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_generic_error_message_on_failure(self):
        """Error message is generic to prevent user enumeration."""
        data = {'username': 'testuser', 'password': 'WrongPassword!'}
        response = self.client.post(self.url, data, format='json')
        self.assertIn('Invalid credentials', str(response.data))

    def test_empty_credentials_returns_401(self):
        """Empty credentials return 401."""
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_missing_password_returns_401(self):
        """Missing password field returns 401."""
        data = {'username': 'testuser'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 401)
