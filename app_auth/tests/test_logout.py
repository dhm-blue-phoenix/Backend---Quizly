"""Tests for the POST /api/logout/ endpoint."""
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class LogoutHappyPathTest(TestCase):
    """Tests for successful logout."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/logout/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access = str(self.refresh.access_token)

    def _login_client(self):
        """Sets cookies on the client to simulate a logged-in state."""
        self.client.cookies['access_token'] = self.access
        self.client.cookies['refresh_token'] = str(self.refresh)

    def test_logout_returns_200(self):
        """A logged-in user can log out with 200."""
        self._login_client()
        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_logout_response_message(self):
        """Response body contains the expected logout message."""
        self._login_client()
        response = self.client.post(self.url, format='json')
        self.assertIn('Log-Out successfully', response.data['detail'])

    def test_logout_deletes_access_cookie(self):
        """access_token cookie is cleared after logout."""
        self._login_client()
        response = self.client.post(self.url, format='json')
        access_cookie = response.cookies.get('access_token')
        self.assertIsNotNone(access_cookie)
        self.assertEqual(access_cookie.value, '')

    def test_logout_deletes_refresh_cookie(self):
        """refresh_token cookie is cleared after logout."""
        self._login_client()
        response = self.client.post(self.url, format='json')
        refresh_cookie = response.cookies.get('refresh_token')
        self.assertIsNotNone(refresh_cookie)
        self.assertEqual(refresh_cookie.value, '')

    def test_blacklisted_token_cannot_refresh(self):
        """After logout, the refresh token cannot be used for refresh."""
        self._login_client()
        self.client.post(self.url, format='json')
        refresh_client = APIClient()
        refresh_client.cookies['refresh_token'] = str(self.refresh)
        response = refresh_client.post('/api/token/refresh/', format='json')
        self.assertEqual(response.status_code, 401)


class LogoutUnhappyPathTest(TestCase):
    """Tests for logout failure scenarios."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/logout/'

    def test_logout_without_cookies_returns_401(self):
        """Attempting logout without any cookies returns 401."""
        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, 401)

    def test_logout_with_invalid_access_token_returns_401(self):
        """An invalid access token returns 401."""
        self.client.cookies['access_token'] = 'invalid.token'
        self.client.cookies['refresh_token'] = 'invalid.token'
        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, 401)
