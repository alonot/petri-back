from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models import Profile, Event, TransactionTable, CAProfile 
from django.contrib.auth.models import User
from unittest.mock import patch
from itsdangerous import SignatureExpired, BadSignature

class EventApplicationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        
        # Create a user profile
        self.profile = Profile.objects.create(
            username='testuser',
            email='testuser@example.com'
        )
        
        # Create an event
        self.event = Event.objects.create(
            event_id='EVT001',
            name='Test Event',
            fee=100,
            minMember=1,
            maxMember=5
        )

    def test_apply_event_paid(self):
        url = reverse('apply_event_paid')
        data = {
            'user_id': 'testuser',
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in'],
            'eventId': self.event.event_id,
            'transactionID': 'TXN001',
            'CAcode': 'CA001'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TransactionTable.objects.count(), 1)
        self.assertTrue(TransactionTable.objects.get().verified)

    def test_apply_event_free(self):
        url = reverse('apply_event_free')
        data = {
            'user_id': 'testuser',
            'participants': ['testuser1@example.com', 'testuser2@example.com'],
            'eventId': self.event.event_id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TransactionTable.objects.count(), 1)
        self.assertTrue(TransactionTable.objects.get().verified)

    def test_missing_fields(self):
        url_paid = reverse('apply_event_paid')
        url_free = reverse('apply_event_free')

        # Test missing fields for paid event application
        data = {
            'user_id': 'testuser',
            'participants': ['testuser1@smail.iitpkd.ac.in']
        }
        response = self.client.post(url_paid, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)

        # Test missing fields for free event application
        data = {
            'user_id': 'testuser'
        }
        response = self.client.post(url_free, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)

    def test_duplicate_transaction_id(self):
        url = reverse('apply_event_paid')
        data = {
            'user_id': 'testuser',
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in'],
            'eventId': self.event.event_id,
            'transactionID': 'TXN001',
            'CAcode': 'CA001'
        }
        
        # Create an initial transaction
        TransactionTable.objects.create(
            event_id=self.event,
            user_id=data['user_id'],
            participants=TransactionTable.serialize_emails(data['participants']),
            transaction_id=data['transactionID'],
            verified=True,
            CA_code=data['CAcode']
        )

        # Attempt to create a duplicate transaction
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)




class CATest(TestCase):
    def setUp(self):
        # Create necessary instances for testing
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='testpassword')
        self.profile = Profile.objects.create(
            username='testuser',
            email=self.user.email,
            phone='1234567890',
            instituteID='ABC123',
            gradYear=2023,
            stream='Engineering',
        )
        self.ca_profile = CAProfile.objects.create(
            email=self.profile,
            CACode='CA123',
            registration=1,
        )

    def test_verifyCA(self):
        url = reverse('verifyCA')  # Assuming 'verifyCA' is the correct name in your urls.py
        response = self.client.post(url, {'CAcode': self.ca_profile.CACode})
        # Add assertions to test the response status code, content, etc.
        self.assertEqual(response.status_code, 200)
        # Add more assertions as per your requirements

    def test_unverifyCA(self):
        url = reverse('unverifyCA')  # Assuming 'unverifyCA' is the correct name in your urls.py
        response = self.client.post(url, {'CAcode': self.ca_profile.CACode})
        # Add assertions to test the response status code, content, etc.
        self.assertEqual(response.status_code, 200)
        # Add more assertions as per your requirements








class CreateCAUserTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)  # Authenticate the test user

    def test_create_ca_user(self):
        response = self.client.post('/auth/CA/create/', {}, format='json')  # Passing empty payload
        self.assertEqual(response.status_code, 200)
        ca_profile = CAProfile.objects.filter(user=self.user).first()

        # Asserting CAProfile is created and linked to the user
        self.assertTrue(ca_profile is not None)

        # Checking the 'CACode' is returned in the response
        self.assertTrue('CACode' in response.data)

        # Asserting the registration value is set to 0 (not verified)
        self.assertEqual(ca_profile.registration, 0)

        # Confirming the response contains success=True
        self.assertTrue(response.data['success'])

        # Asserting the CACode matches the one in CAProfile
        self.assertEqual(response.data['CACode'], ca_profile.CACode)

    def test_create_ca_user_unauthenticated(self):
        unauthenticated_client = APIClient()

        # Sending a POST request without authentication
        response = unauthenticated_client.post('/auth/CA/create/', {}, format='json')

        # Asserting the response status code is 403 Forbidden (or 401 Unauthorized depending on your setup)
        self.assertEqual(response.status_code, 403)  # Adjust to 401 if your API returns Unauthorized

    def test_create_ca_user_invalid_method(self):
        # Sending a GET request instead of POST
        response = self.client.get('/auth/CA/create/', {}, format='json')

        # Asserting the response status code is 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)

    def test_create_ca_user_server_error(self):
        # Simulating an exception during CAProfile creation
        with patch('yourapp.models.CAProfile.save', side_effect=Exception('Database error')):
            response = self.client.post('/auth/CA/create/', {}, format='json')

            self.assertEqual(response.status_code, 500)
            self.assertIn('Something went wrong', response.data['detail'])

    def test_create_ca_user_already_exists(self):
        # Create a CAProfile for the user before making the request
        existing_profile = CAProfile.objects.create(user=self.user, registration=0)

        # Sending a POST request to create CA user
        response = self.client.post('/auth/CA/create/')

        # Verifying that no new CAProfile is created
        ca_profile_count = CAProfile.objects.filter(user=self.user).count()
        self.assertEqual(ca_profile_count, 1)

        # Asserting the response still indicates success and returns the same CACode
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['CACode'], existing_profile.CACode)





class ChangePasswordTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a test user
        self.user = User.objects.create_user(username='testuser@example.com', password='oldpassword')
        
        # Assume this function generates a valid token for the user
        self.valid_token = 'validtoken'
        self.expired_token = 'expiredtoken'
        self.invalid_token = 'invalidtoken'

    def test_change_password_success(self):
        # Mocking get_email_from_token to return user's email
        with patch('yourapp.views.get_email_from_token', return_value=self.user.username):
            response = self.client.post(
                f'/change-password/{self.valid_token}/',
                {'new_password': 'newpassword123'},
                format='json'
            )

            # Assert the response status code is 200
            self.assertEqual(response.status_code, 200)

            # Assert success message
            self.assertEqual(response.data['message'], 'Password changed successfully')
            self.assertTrue(response.data['success'])

            # Verify the password was changed
            self.user.refresh_from_db()
            self.assertTrue(self.user.check_password('newpassword123'))

    def test_change_password_missing_password(self):
        response = self.client.post(
            f'/change-password/{self.valid_token}/',
            {},  # No password provided
            format='json'
        )

        # Assert the response status code is 500 (or adjust according to your API behavior)
        self.assertEqual(response.status_code, 500)
        self.assertIn('Passwords not received', response.data['message'])

    def test_change_password_expired_token(self):
        # Mocking get_email_from_token to raise SignatureExpired
        with patch('yourapp.views.get_email_from_token', side_effect=SignatureExpired):
            response = self.client.post(
                f'/change-password/{self.expired_token}/',
                {'new_password': 'newpassword123'},
                format='json'
            )

            # Assert the response status code is 500 (or adjust according to your API behavior)
            self.assertEqual(response.status_code, 500)
            self.assertIn('Token expired', response.data['message'])

    def test_change_password_invalid_token(self):
        # Mocking get_email_from_token to raise BadSignature
        with patch('yourapp.views.get_email_from_token', side_effect=BadSignature):
            response = self.client.post(
                f'/change-password/{self.invalid_token}/',
                {'new_password': 'newpassword123'},
                format='json'
            )

            # Assert the response status code is 500 (or adjust according to your API behavior)
            self.assertEqual(response.status_code, 500)
            self.assertIn('Invalid Token', response.data['message'])

    def test_change_password_unauthenticated(self):
        # You can customize this test if your endpoint requires authentication
        unauthenticated_client = APIClient()
        response = unauthenticated_client.post(
            f'/change-password/{self.valid_token}/',
            {'new_password': 'newpassword123'},
            format='json'
        )

        # Assert the response status code is 403 Forbidden or 401 Unauthorized
        self.assertEqual(response.status_code, 403)  # Adjust if your API uses 401

    def test_change_password_invalid_method(self):
        response = self.client.get(f'/change-password/{self.valid_token}/')

        # Assert the response status code is 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)

    def test_change_password_user_not_found(self):
        # Mocking get_email_from_token to return an email not associated with any user
        with patch('yourapp.views.get_email_from_token', return_value='nonexistent@example.com'):
            response = self.client.post(
                f'/change-password/{self.valid_token}/',
                {'new_password': 'newpassword123'},
                format='json'
            )

            # Assert the response status code is 404 Not Found
            self.assertEqual(response.status_code, 404)
            self.assertIn('Invalid URL', response.data['message'])
