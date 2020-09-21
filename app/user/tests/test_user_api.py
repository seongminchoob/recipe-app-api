from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

PAYLOAD = {
    'email': 'seongmin@choo.com',
    'password': 'testpass',
    'name': 'name of test'
}

def create_user(**params):
    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):
    """Test the user's API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        res = self.client.post(CREATE_USER_URL, PAYLOAD)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(PAYLOAD['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test creating user that already exists fails"""
        create_user(**PAYLOAD)

        res = self.client.post(CREATE_USER_URL, PAYLOAD)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that password must be more than five characters"""
        PAYLOAD = {
            'email': 'seongmin@choo.com',
            'password': 'ts',
            'name': 'na'
        }
        res = self.client.post(CREATE_USER_URL, PAYLOAD)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
        email=PAYLOAD['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""
        PAYLOAD = {
            'email': 'seongmin@choo.com',
            'password': 'testpass',
        }
        create_user(**PAYLOAD)
        res = self.client.post(TOKEN_URL, PAYLOAD)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that token is not created if invalid credentials are given"""
        create_user(email='test@test.com', password='hi yo', name='kiff')
        PAYLOAD = {
            'email': 'test@test.com',
            'password': 'wrong',
        }
        res = self.client.post(TOKEN_URL, PAYLOAD)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is not created if user doesn't exist"""
        PAYLOAD = {
            'email': 'test@test.com',
            'password': 'wrong',
        }
        res = self.client.post(TOKEN_URL, PAYLOAD)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):

    def setUp(self):
        self.user = create_user(
            email="seongmin@nav.com",
            password="testpass",
            name="client"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retriveing profile for logged in users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_not_allowed(self):
        """Test that post is not allowed"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile"""
        payload = {'name': 'new name', 'password': 'kiffabab'}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
