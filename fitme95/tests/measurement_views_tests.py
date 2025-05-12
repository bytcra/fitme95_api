from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from ..models.measurement import Measurement, Waist
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse

User = get_user_model()


class MeasurementViewsTest(APITestCase):
    def setUp(self):
        # Create test user

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

        # Create another user for testing isolation
        self.other_user = User.objects.create_user(
            google_id="other_google_id",
            email="other@example.com",
            first_name="Other",
            last_name="User"
        )

        # Test data
        self.valid_measurement_data = {
            "body_weight": 75.5,
            "body_fat": 15.0,
            "chest": 95.0,
            "waist": {
                "waist": 80.0,
                "above_below": 1
            }
        }

        # Create test measurement
        waist1 = Waist.objects.create(waist=80.0, above_below=1)
        waist2 = Waist.objects.create(waist=80.5, above_below=0)
        self.test_measurement = Measurement.objects.create(
            user=self.user,
            body_weight=75.5,
            body_fat=15.0,
            chest=95.0,
            waist=waist1
        )
        self.test_measurement2 = Measurement.objects.create(
            user=self.user,
            body_weight=75,
            body_fat=15.5,
            chest=95.0,
            waist=waist2
        )

        # URLs
        self.create_url = reverse('create_measurement')
        self.get_url = reverse('get_measurements')
        self.update_url = reverse('update_measurement', args=[self.test_measurement.id])
        self.delete_url = reverse('delete_measurement', args=[self.test_measurement.id])

    def tearDown(self):
        Measurement.objects.all().delete()
        Waist.objects.all().delete()
        User.objects.all().delete()

    # Create Measurement Tests
    # Test successful creation of a measurement
    def test_create_measurement_success(self):
        response = self.client.post(
            self.create_url,
            self.valid_measurement_data,
            format='json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status']['message'], 'Measurement created successfully')
        self.assertIn('measurement', response.data['data'])

        # Verify data
        measurement = response.data['data']['measurement']
        self.assertEqual(measurement['body_weight'], self.valid_measurement_data['body_weight'])
        self.assertEqual(measurement['body_fat'], self.valid_measurement_data['body_fat'])
        self.assertEqual(measurement['chest'], self.valid_measurement_data['chest'])
        self.assertEqual(measurement['waist']['waist'], self.valid_measurement_data['waist']['waist'])
        self.assertEqual(measurement['waist']['above_below'], self.valid_measurement_data['waist']['above_below'])

    # Test measurement creation with no data
    def test_create_measurement_no_data(self):
        response = self.client.post(
            self.create_url,
            {},
            format='json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status']['message'], 'No data provided')

    # Test measurement creation with invalid data
    def test_create_measurement_invalid_data(self):
        invalid_data = {
            "body_weight": "invalid",
            "body_fat": -1,
            "chest": "invalid",
            "waist": {
                "waist": "invalid",
                "above_below": "invalid"
            }
        }
        response = self.client.post(
            self.create_url,
            invalid_data,
            format='json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status']['message'], 'Invalid measurement data')
        self.assertIn('errors', response.data['status'])

    # Test measurement creation without authentication
    def test_create_measurement_unauthorized(self):
        response = self.client.post(
            self.create_url,
            self.valid_measurement_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Test database error handling during measurement creation
    @patch('django.db.models.Model.save')
    def test_create_measurement_db_error(self, mock_save):
        mock_save.side_effect = IntegrityError("Database error")
        response = self.client.post(
            self.create_url,
            self.valid_measurement_data,
            format='json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['status']['message'], 'Database error occurred while saving measurement')

    # Get Measurements Tests
    # Test successful retrieval of measurements
    def test_get_measurements_success(self):
        response = self.client.get(
            self.get_url,
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status']['message'], 'Your measurements')
        self.assertIn('measurements', response.data['data'])
        self.assertEqual(len(response.data['data']['measurements']), 2)

    # Test getting measurements when none exist
    def test_get_measurements_empty(self):
        # Delete existing measurements
        Measurement.objects.all().delete()
        response = self.client.get(
            self.get_url,
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status']['message'], 'No measurements found. Please add a measurement')
        self.assertEqual(response.data['data']['measurements'], [])

    # Test getting measurements without authentication
    def test_get_measurements_unauthorized(self):
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Update Measurement Tests
    # Test successful measurement update
    def test_update_measurement_success(self):
        update_data = {
            "body_weight": 76.5,
            "waist": {
                "waist": 81.0,
                "above_below": 0
            }
        }
        response = self.client.put(
            self.update_url,
            update_data,
            format='json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status']['message'], 'Measurement updated successfully')

        # Verify updated data
        measurement = response.data['data']['measurement']
        self.assertEqual(measurement['body_weight'], update_data['body_weight'])
        self.assertEqual(measurement['waist']['waist'], update_data['waist']['waist'])
        self.assertEqual(measurement['waist']['above_below'], update_data['waist']['above_below'])

    # Test updating non-existent measurement
    def test_update_measurement_not_found(self):
        non_existent_url = reverse('update_measurement', args=[99999])
        response = self.client.put(
            non_existent_url,
            self.valid_measurement_data,
            format='json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status']['message'], 'Measurement not found')

    # Test updating another user's measurement
    def test_update_other_user_measurement(self):
        # Create measurement for other user
        waist = Waist.objects.create(waist=82.0, above_below=1)
        other_measurement = Measurement.objects.create(
            user=self.other_user,
            body_weight=70.0,
            body_fat=14.0,
            chest=90.0,
            waist=waist
        )
        update_url = reverse('update_measurement', args=[other_measurement.id])
        response = self.client.put(
            update_url,
            self.valid_measurement_data,
            format='json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Test measurement update with no data
    def test_update_measurement_no_data(self):
        response = self.client.put(
            self.update_url,
            {},
            format='json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status']['message'], 'No data provided')

    # Test measurement update with invalid data
    def test_update_measurement_invalid_data(self):
        invalid_data = {
            "body_weight": "invalid",
            "waist": {
                "waist": "invalid",
                "above_below": "invalid"
            }
        }
        response = self.client.put(
            self.update_url,
            invalid_data,
            format='json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status']['message'], 'Invalid measurement data')

    # Delete Measurement Tests
    # Test successful measurement deletion
    def test_delete_measurement_success(self):
        response = self.client.delete(
            self.delete_url,
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status']['message'], 'Measurement deleted successfully')

        # Verify deletion
        self.assertFalse(Measurement.objects.filter(id=self.test_measurement.id).exists())
        self.assertFalse(Waist.objects.filter(id=self.test_measurement.waist.id).exists())

    # Test deleting non-existent measurement
    def test_delete_measurement_not_found(self):
        non_existent_url = reverse('delete_measurement', args=[99999])
        response = self.client.delete(
            non_existent_url,
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status']['message'], 'Measurement not found')

    # Test deleting another user's measurement
    def test_delete_other_user_measurement(self):
        # Create measurement for other user
        waist = Waist.objects.create(waist=82.0, above_below=1)
        other_measurement = Measurement.objects.create(
            user=self.other_user,
            body_weight=70.0,
            body_fat=14.0,
            chest=90.0,
            waist=waist
        )
        delete_url = reverse('delete_measurement', args=[other_measurement.id])
        response = self.client.delete(
            delete_url,
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify measurement still exists
        self.assertTrue(Measurement.objects.filter(id=other_measurement.id).exists())

    # Test deleting measurement without authentication
    def test_delete_measurement_unauthorized(self):
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
