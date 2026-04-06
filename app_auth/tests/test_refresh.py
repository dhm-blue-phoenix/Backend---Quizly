"""Tests for the POST /api/token/refresh/ endpoint."""
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class RefreshHappyPathTest(TestCase):
    """Tests for successful token refresh."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/token/refresh/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )
        self.refresh = RefreshToken.for_user(self.user)

    def test_refresh_returns_200(self):
        """A valid refresh cookie returns 200."""
        self.client.cookies['refresh_token'] = str(self.refresh)
        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_refresh_returns_detail_message(self):
        """Response body contains the expected detail message."""
        self.client.cookies['refresh_token'] = str(self.refresh)
        response = self.client.post(self.url, format='json')
        self.assertEqual(response.data['detail'], 'Token refreshed')

    def test_refresh_sets_new_access_cookie(self):
        """A new access_token cookie is set after refresh."""
        self.client.cookies['refresh_token'] = str(self.refresh)
        response = self.client.post(self.url, format='json')
        self.assertIn('access_token', response.cookies)
        self.assertTrue(response.cookies['access_token']['httponly'])


class RefreshUnhappyPathTest(TestCase):
    """Tests for token refresh failure scenarios."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/token/refresh/'

    def test_missing_refresh_cookie_returns_401(self):
        """No refresh cookie returns 401."""
        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, 401)

    def test_invalid_refresh_token_returns_401(self):
        """A tampered/invalid refresh token returns 401."""
        self.client.cookies['refresh_token'] = 'invalid.token.value'
        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, 401)

    def test_expired_refresh_token_returns_401(self):
        """An expired or blacklisted refresh token returns 401."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )
        refresh = RefreshToken.for_user(user)
        refresh.blacklist()
        self.client.cookies['refresh_token'] = str(refresh)
        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, 401)
