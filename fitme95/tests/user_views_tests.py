from django.db.utils import IntegrityError
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from unittest.mock import patch
from rest_framework_simplejwt.tokens import RefreshToken

from ..models.user import CustomUser
from ..models.user_profile import UserProfile


class SetupUserProfileTests(APITestCase):
    def setUp(self):
        # Set up test data and authentication
        # Create a test user with CustomUser model
        self.user = CustomUser.objects.create(
            google_id="test_google_id",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

        # Get token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        # Test data
        self.valid_data = {
            "weight": 70.5,
            "height": 175.0,
            "dob": "18-11-01",
            "gender": "m",
            "weight_unit": "kg",
            "height_unit": "cm",
            "distance_unit": "km",
            "length_unit": "cm",
            "measurable_items": ["weight", "height"]
        }

        self.invalid_data = {
            "weight": "invalid",
            "height": -1,
            "dob": "invalid",
            "gender": "invalid"
        }
        self.onboarding_url = reverse("setup_profile")

    # Clean up after each test
    def tearDown(self):
        CustomUser.objects.all().delete()
        UserProfile.objects.all().delete()

    # Test successful creation of a new user profile
    def test_create_user_profile_successfully(self):
        response = self.client.post(self.onboarding_url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"]["message"], "User Profile Setup Completed")
        self.assertIn("data", response.data)

        # Verify saved data
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.weight, self.valid_data["weight"])
        self.assertEqual(profile.height, self.valid_data["height"])
        self.assertEqual(profile.gender, self.valid_data["gender"])
        self.assertEqual(profile.dob, self.valid_data["dob"])
        self.assertEqual(profile.measurable_items, self.valid_data["measurable_items"])
        self.assertEqual(profile.weight_unit, self.valid_data["weight_unit"])
        self.assertEqual(profile.height_unit, self.valid_data["height_unit"])
        self.assertEqual(profile.distance_unit, self.valid_data["distance_unit"])
        self.assertEqual(profile.length_unit, self.valid_data["length_unit"])

    # Test successful update of an existing user profile
    def test_update_existing_user_profile(self):
        # Create initial profile
        UserProfile.objects.create(
            user=self.user,
            weight=60.0,
            height=170.0,
            dob="18-11-01",
            gender="m",
            weight_unit="kg",
            height_unit="cm",
            distance_unit="km",
            length_unit="cm",
            measurable_items=["weight"]
        )

        update_data = {
            "weight": 70.5,
            "height": 175.0,
            "dob": "18-11-01",
            "gender": "m",
            "weight_unit": "kg",
            "height_unit": "cm",
            "distance_unit": "km",
            "length_unit": "cm",
            "measurable_items": ["weight", "height"]
        }

        response = self.client.post(self.onboarding_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"]["message"], "User Profile Updated Successfully")

        # Verify updated data
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.weight, update_data["weight"])
        self.assertEqual(profile.height, update_data["height"])
        self.assertEqual(profile.dob, update_data["dob"])
        self.assertEqual(profile.gender, update_data["gender"])
        self.assertEqual(profile.measurable_items, update_data["measurable_items"])
        self.assertEqual(profile.weight_unit, update_data["weight_unit"])
        self.assertEqual(profile.height_unit, update_data["height_unit"])
        self.assertEqual(profile.distance_unit, update_data["distance_unit"])
        self.assertEqual(profile.length_unit, update_data["length_unit"])

    # Test handling of invalid data
    def test_invalid_data_returns_400(self):
        response = self.client.post(self.onboarding_url, self.invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"]["message"], "Invalid profile data")
        self.assertIn("errors", response.data["status"])

    # Test handling of empty data
    def test_no_data_provided_returns_400(self):
        response = self.client.post(self.onboarding_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"]["message"], "No data provided")

    # Test access without authentication
    def test_unauthorized_access(self):
        # Remove authentication credentials
        self.client.credentials()
        response = self.client.post(self.onboarding_url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Test partial update of profile
    def test_partial_update(self):
        # Create initial profile
        UserProfile.objects.create(
            user=self.user,
            weight=60.0,
            height=170.0,
            dob="19900101",
            gender="m",
            weight_unit="kg",
            height_unit="cm",
            distance_unit="km",
            length_unit="cm",
            measurable_items=["weight"]
        )

        # Update only weight
        partial_update = {"weight": 62.5}
        response = self.client.post(self.onboarding_url, partial_update, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.weight, partial_update['weight'])
        self.assertEqual(profile.height, 170.0)  # Original value preserved

    # Test handling of database integrity errors
    @patch("fitme95.models.user_profile.UserProfile.objects.get")
    def test_database_integrity_error_returns_500(self, mock_get):
        mock_get.side_effect = IntegrityError("Test Integrity Error")
        response = self.client.post(self.onboarding_url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["status"]["message"],
                         "Database integrity error occurred while saving user profile")
        self.assertIn("errors", response.data["status"])

    # Test handling of invalid measurement units
    def test_invalid_measurement_units(self):
        invalid_units_data = {
            **self.valid_data,
            "weight_unit": "invalid",
            "height_unit": "invalid"
        }
        response = self.client.post(self.onboarding_url, invalid_units_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data["status"])

    # Test handling of invalid measurable items
    def test_invalid_measurable_items(self):
        invalid_measurements_data = {
            **self.valid_data,
            "measurable_items": "not_a_list"
        }
        response = self.client.post(self.onboarding_url, invalid_measurements_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data["status"])
