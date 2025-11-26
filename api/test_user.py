from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from api.models import Activity
from rest_framework.test import APITestCase
import pytest
from datetime import date




User = get_user_model()


class TestUserRegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        """
        Test that a new user can register successfully.
        URL: /api/auth/register/
        """
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass123",
            "password2": "StrongPass123"  # required by serializer
        }
        response = self.client.post("/api/auth/register/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.check_password("StrongPass123"))

class TestUserLogin(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/auth/login/"  # Make sure this matches your login endpoint
        # Create a test user for login
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123",
            first_name="Test",
            last_name="User"
        )

    def test_login_success(self):
        """
        Test that a user can login with correct credentials and receive JWT tokens
        """
        data = {
            "username": "testuser",
            "password": "StrongPass123"
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self):
        """
        Test login fails with wrong password
        """
        data = {
            "username": "testuser",
            "password": "WrongPass123"
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_nonexistent_user(self):
        """
        Test login fails for a non-existent user
        """
        data = {
            "username": "nouser",
            "password": "StrongPass123"
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

class TestUserLogout(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.logout_url = "/api/auth/logout/"
        self.login_url = "/api/auth/login/"
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123",
            first_name="Test",
            last_name="User"
        )

    def test_logout_success(self):
        """
        Test that a logged-in user can logout successfully and the refresh token is blacklisted
        """
        # 1. Login to get JWT tokens
        login_data = {"username": "testuser", "password": "StrongPass123"}
        login_response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(login_response.status_code, 200)

        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        # 2. Authenticate client with access token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 3. Call logout endpoint
        response = self.client.post(self.logout_url, {"refresh": refresh_token}, format="json")
        self.assertEqual(response.status_code, 205)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "User logged out successfully.")

        # 4. Optional: Ensure refresh token is blacklisted
        with self.assertRaises(TokenError):
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()

class TestActivityCreate(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123"
        )
        # Generate JWT access token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # Set Authorization header for API client
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # URL for creating activity
        self.url = "/api/activities/create/"

    def test_create_activity(self):
        """
        Test creating a new activity using the API.
        """
        data = {
            "activity_type": "workout",
            "description": "Morning run 5km",
            "date": "2025-11-04",
            "status": "planned"
        }
        response = self.client.post(self.url, data, format="json")

        # Assert response is 201 CREATED
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert activity is saved in the database
        self.assertEqual(Activity.objects.count(), 1)
        activity = Activity.objects.first()
        self.assertEqual(activity.description, "Morning run 5km")
        self.assertEqual(activity.activity_type, "workout")
        self.assertEqual(str(activity.date), "2025-11-04")
        self.assertEqual(activity.status, "planned")

@pytest.mark.django_db
def test_list_activities():
    client = APIClient()

    # Create a test user
    user = User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="StrongPass123"
    )

    # Authenticate
    client.force_authenticate(user=user)

    # Create multiple activities
    Activity.objects.create(
        user=user,
        activity_type="workout",
        description="Morning run 5km",
        date=date(2025, 11, 4),
        status="planned"
    )
    Activity.objects.create(
        user=user,
        activity_type="meal",
        description="Lunch",
        date=date(2025, 11, 4),
        status="completed"
    )

    # API GET request to list activities
    response = client.get("/api/activities/")

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    descriptions = [activity["description"] for activity in response.data]
    assert "Morning run 5km" in descriptions
    assert "Lunch" in descriptions






# Create your tests here.
