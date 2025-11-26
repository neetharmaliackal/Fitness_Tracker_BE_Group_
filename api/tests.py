from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserRegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/login/"
        self.logout_url = "/api/auth/logout/"

        # Create a test user for login tests
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123",
            first_name="Test",
            last_name="User"
        )

    # -------------------------
    # User Registration Test
    # -------------------------
    def test_user_registration(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass123",
            "password2": "StrongPass123"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.check_password("StrongPass123"))

    # -------------------------
    # JWT Login Tests
    # -------------------------
    def test_jwt_login_success(self):
        data = {
            "username": "testuser",
            "password": "StrongPass123"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_jwt_login_failure_wrong_password(self):
        data = {
            "username": "testuser",
            "password": "WrongPass123"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_jwt_login_failure_nonexistent_user(self):
        data = {
            "username": "nouser",
            "password": "StrongPass123"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
    #Logout testing

    def test_user_logout(self):
        # Step 1: Login to get access + refresh tokens
        login_data = {"username": "testuser", "password": "StrongPass123"}
        login_response = self.client.post(self.login_url, login_data, format='json')

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        # Step 2: Authenticate using the access token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # Step 3: Hit logout endpoint with the refresh token
        response = self.client.post(self.logout_url, {"refresh": refresh_token}, format='json')

        # Step 4: Assert logout successful
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        # Update here: check for 'detail' instead of 'message'
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "User logged out successfully.")




