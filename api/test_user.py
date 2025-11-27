from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from api.models import Activity
from rest_framework.test import APITestCase





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


class TestActivityList(APITestCase):
    def setUp(self):
        # Setup API client is already available as self.client from APITestCase
        # Create two users
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="StrongPass123"
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="StrongPass123"
        )

        # Generate JWT access token for user1
        refresh = RefreshToken.for_user(self.user1)
        self.access_token_user1 = str(refresh.access_token)

        # Create activities for user1
        self.activity1_u1 = Activity.objects.create(
            user=self.user1,
            activity_type="workout",
            description="Run 5km",
            date="2025-11-01",
            status="completed",
        )
        self.activity2_u1 = Activity.objects.create(
            user=self.user1,
            activity_type="yoga",
            description="Morning yoga",
            date="2025-11-03",  # later date so this should come first
            status="planned",
        )

        # Activity for user2 (should NOT appear)
        self.activity_u2 = Activity.objects.create(
            user=self.user2,
            activity_type="workout",
            description="User2 activity",
            date="2025-11-02",
            status="planned",
        )

        self.url = "/api/activities/"

    def test_list_activities_requires_authentication(self):
        """
        Unauthenticated request should be rejected with 401.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_activities_for_authenticated_user(self):
        """
        Authenticated user should get only their own activities,
        ordered by date descending.
        """
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token_user1}")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only 2 activities for user1
        self.assertEqual(len(response.data), 2)

        first = response.data[0]
        second = response.data[1]

        # Newest first
        self.assertEqual(first["description"], "Morning yoga")
        self.assertEqual(first["activity_type"], "yoga")
        self.assertEqual(first["status"], "planned")
        self.assertEqual(first["date"], "2025-11-03")

        self.assertEqual(second["description"], "Run 5km")
        self.assertEqual(second["activity_type"], "workout")
        self.assertEqual(second["status"], "completed")
        self.assertEqual(second["date"], "2025-11-01")

        descriptions = [a["description"] for a in response.data]
        self.assertNotIn("User2 activity", descriptions)

    def test_update_activity_success(self):
        """
        Authenticated user can update their own activity.
        View: ActivityDetailView (PUT/PATCH on /api/activities/<pk>/)
        """
        client = APIClient()

        # 1. Create user
        user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123",
        )

        # 2. JWT access token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # 3. Authenticate
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 4. Create an activity for this user
        activity = Activity.objects.create(
            user=user,
            activity_type="workout",
            description="Morning run 5km",
            date="2025-11-04",
            status="planned",
        )

        # 5. URL for detail/update
        url = f"/api/activities/{activity.id}/"

        # 6. Data to update (partial update, since your view uses partial=True)
        update_data = {
            "description": "Evening run 10km",
            "status": "completed",
        }

        # Use PATCH (since your update method uses partial=True)
        response = client.patch(url, update_data, format="json")

        # 7. Check response
        assert response.status_code == 200
        assert response.data["detail"] == "Activity updated successfully!"

        # 8. Check DB
        activity.refresh_from_db()
        assert activity.description == "Evening run 10km"
        assert activity.status == "completed"

# Create your tests here.
    def test_delete_activity_success(self):
        """
        Authenticated user can delete their own activity and gets a custom message.
        """
        # Create a user
        user = User.objects.create_user(
            username="deleteuser",
            email="deleteuser@example.com",
            password="StrongPass123",
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Use self.client from APITestCase
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # Create an activity for this user
        activity = Activity.objects.create(
            user=user,
            activity_type="workout",
            description="Activity to delete",
            date="2025-11-10",
            status="planned",
        )

        # URL for detail/delete (same as update: /api/activities/<pk>/)
        url = f"/api/activities/{activity.id}/"

        # Send DELETE request
        response = self.client.delete(url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Activity deleted successfully!")

        # Ensure activity is removed from the database
        self.assertFalse(Activity.objects.filter(id=activity.id).exists())

