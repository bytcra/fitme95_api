from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from ..models.user_profile import UserProfile
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenRefreshView

User = get_user_model()


class AuthViewsTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            google_id="test_google_id",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        self.token = RefreshToken.for_user(self.user)
        self.auth_headers = {
            'HTTP_AUTHORIZATION': f'Bearer {self.token.access_token}'
        }
        self.valid_token_payload = {
            'email': 'test@example.com',
            'sub': 'test_google_id',
            'name': 'Test User',
            'given_name': 'Test',
            'family_name': 'User',
        }
        self.login = reverse('login')
        self.user_info = reverse('user_info')
        self.refresh_token = reverse('refresh_token')

    # Test successful login with a new user
    @patch('google.oauth2.id_token.verify_firebase_token')
    def test_google_login_success_new_user(self, mock_verify_firebase_token):
        mock_verify_firebase_token.return_value = {
            'email': 'new@example.com',
            'sub': 'new_google_id',
            'name': 'New User',
            'given_name': 'New',
            'family_name': 'User'
        }
        response = self.client.post(self.login, {'id': 'fake_token'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data['data'])
        self.assertIn('refresh_token', response.data['data'])
        self.assertFalse(response.data['data']['user']['is_onboarded'])

    # Test successful login with an existing user
    @patch('google.oauth2.id_token.verify_firebase_token')
    def test_google_login_success_existing_user(self, mock_verify_firebase_token):
        mock_verify_firebase_token.return_value = self.valid_token_payload
        response = self.client.post(self.login, {'id': 'fake_token'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['user']['email'], 'test@example.com')

    # Test login with existing user that has a profile
    @patch('google.oauth2.id_token.verify_firebase_token')
    def test_google_login_success_with_profile(self, mock_verify_firebase_token):
        UserProfile.objects.create(
            user=self.user,
            weight=75.0,
            height=180.0,
            dob="18-11-01",
            gender="m",
            weight_unit="kg",
            height_unit="cm",
            distance_unit="km",
            length_unit="cm",
            measurable_items=["weight", "waist"]
        )
        mock_verify_firebase_token.return_value = self.valid_token_payload
        response = self.client.post(self.login, {'id': 'fake_token'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['user']['is_onboarded'])
        self.assertIsNotNone(response.data['data']['user']['profile'])

    # Test login with missing email in token
    @patch('google.oauth2.id_token.verify_firebase_token')
    def test_google_login_missing_email(self, mock_verify_firebase_token):
        payload = self.valid_token_payload.copy()
        del payload['email']
        mock_verify_firebase_token.return_value = payload
        response = self.client.post(self.login, {'id': 'fake_token'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test login with invalid token
    @patch('google.oauth2.id_token.verify_firebase_token')
    def test_google_login_invalid_token(self, mock_verify_firebase_token):
        mock_verify_firebase_token.side_effect = ValueError("Invalid token")
        response = self.client.post(self.login, {'id': 'fake_token'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Test handling of database errors during login
    @patch('google.oauth2.id_token.verify_firebase_token')
    @patch('django.db.transaction.atomic')
    def test_google_login_db_error(self, mock_atomic, mock_verify_firebase_token):
        mock_verify_firebase_token.return_value = self.valid_token_payload
        mock_atomic.side_effect = IntegrityError("Database error")
        response = self.client.post(self.login, {'id': 'fake_token'})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['status']['message'], "Database error occurred")

    # Test getting user info with existing profile
    def test_user_info_with_profile(self):
        UserProfile.objects.create(
            user=self.user,
            weight=75.0,
            height=180.0,
            dob="18-11-01",
            gender="m",
            weight_unit="kg",
            height_unit="cm",
            distance_unit="km",
            length_unit="cm",
            measurable_items=["weight", "height"]
        )
        response = self.client.get(self.user_info, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['user']['is_onboarded'])
        self.assertEqual(response.data['data']['user']['profile']['height'], 180.0)

    # Test getting user info without profile
    def test_user_info_without_profile(self):
        response = self.client.get(self.user_info, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['data']['user']['is_onboarded'])
        self.assertIsNone(response.data['data']['user']['profile'])

    # Test getting user info with invalid token
    def test_user_info_invalid_token(self):
        headers = {'HTTP_AUTHORIZATION': 'Bearer invalid_token'}
        response = self.client.get(self.user_info, **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Test successful token refresh
    def test_token_refresh_success(self):
        response = self.client.post(self.refresh_token, {'refresh': str(self.token)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data['data'])
        self.assertIn('refresh_token', response.data['data'])
        self.assertIn('expires_in', response.data['data'])

    # Test token refresh with invalid token
    @patch.object(TokenRefreshView, 'post')
    def test_token_refresh_invalid_token(self, mock_post):
        mock_post.side_effect = TokenError("Token is invalid or expired")
        response = self.client.post(self.refresh_token, {'refresh': 'invalid_token'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status']['message'], 'Invalid or expired refresh token')

    # Test token refresh with missing token
    def test_token_refresh_missing_token(self):
        response = self.client.post(self.refresh_token, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('refresh', response.data['status']['errors'])

    # Test token refresh with expired token
    @patch.object(TokenRefreshView, 'post')
    def test_token_refresh_expired_token(self, mock_post):
        mock_post.side_effect = TokenError("Token has expired")
        response = self.client.post(self.refresh_token, {'refresh': str(self.token)})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status']['message'], 'Invalid or expired refresh token')
