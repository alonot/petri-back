import json
import unittest
from django.test import TestCase
from django.test import Client
from app.models import Institute, User,Profile,CAProfile,UserRegistrations,Event,TransactionTable,Institute
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from unittest.mock import patch
from utils import get_forget_token 




headers = {"HTTP_HOST":"petrichor.events"}
testClient= Client(

    enforce_csrf_checks=True,
    headers=headers
    )


class ChangePasswordTest(TestCase):

    def setUp(self) -> None:
        self.client = Client()
        self.inst = Institute.objects.create(institutionType="college",
                                             instiName="IITPKD")
        user = User(username="csk20020@gmail.com")
        user.set_password("123w123qe")
        user.save()
        self.profile = Profile.objects.create(
            username='testuser',
            user=user,
            phone='1234567890',
            instituteID=self.inst,
            gradYear=2023,
            stream='Engineering',
        )
        self.token = get_forget_token(user.username)  # Generate a valid token for the user
        return super().setUp()

    def test_change_password_good(self):
        response = self.client.post(f'/api/change-password/{self.token}/', {
            "new_password": "newpassword123"
        }, content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_change_password_bad(self):
        response = self.client.post(f'/api/change-password/invalidtoken/', {
            "new_password": "newpassword123"
        }, content_type="application/json")
        self.assertEqual(response.status_code, 500)  # Adjust the expected status code based on your view logic
        
        
    def test_change_password_with_weak_password(self):
        response = self.client.post(f'/api/change-password/{self.token}/', {
            "new_password": "123"
        }, content_type="application/json")
        self.assertEqual(response.status_code, 400)  # Assuming 400 for bad request due to weak password

    # def test_change_password_with_mismatched_confirmation(self):
    #     response = self.client.post(f'/api/change-password/{self.token}/', {
    #         "new_password": "newpassword123",
    #         "confirm_password": "differentpassword123"
    #     }, content_type="application/json")
    #     self.assertEqual(response.status_code, 400)  # Assuming 400 for bad request due to mismatched passwords

    def test_change_password_with_expired_token(self):
        expired_token = "112201020@smail.iitpkd.ac.in:1sbH4C:gY_cneW4Miv1hAaHI1TSaDBSYp1D-Br3tdAITw9nong"  # Simulate an expired token
        response = self.client.post(f'/api/change-password/{expired_token}/', {
            "new_password": "newpassword123"
        }, content_type="application/json")
        self.assertEqual(response.status_code, 401)









class EventApplicationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')
    # Other setup code...

        
        self.profile = Profile.objects.create(
            username='testuser',
            user=self.user
        )
        
        self.event = Event.objects.create(
            event_id='EVT001',
            name='Test Event',
            fee=100,
            minMember=1,
            maxMember=5
        )


    def test_apply_event_paid(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('applyEventpaid'), {
            'user_id': 'testuser',
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in'],
            'eventId': self.event.event_id,
            'transactionID': 'TXN001',
            'CAcode': 'CA001'
        }, content_type="application/json")

        print(response.status_code, response.json())  # Debug print
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertTrue(transaction.verified)


    def test_apply_event_free(self):
        response = self.client.post(reverse('applyEventfree'), {
            'user_id': 'testuser',
            'participants': ['testuser1@example.com', 'testuser2@example.com'],
            'eventId': self.event.event_id
        }, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertTrue(transaction.verified)


    def test_missing_fields(self):
        # Test missing fields for paid event application
        response = testClient.post(reverse('applyEventpaid'), {
            'user_id': 'testuser',
            'participants': ['testuser1@smail.iitpkd.ac.in']
        }, content_type="application/json")

        self.assertNotEqual(response.status_code, 200)
        self.assertIn('error', response.json())

        # Test missing fields for free event application
        response = testClient.post(reverse('applyEventfree'), {
            'user_id': 'testuser'
        }, content_type="application/json")

        self.assertNotEqual(response.status_code, 200)
        self.assertIn('error', response.json())

    def test_duplicate_transaction_id(self):
        # Create an initial transaction
        TransactionTable.objects.create(
            event_id=self.event,
            user_id=self.profile.user,
            participants=TransactionTable.serialise_emails(['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in']),
            transaction_id='TXN001',
            verified=True
        )

        # Attempt to create a duplicate transaction
        response = testClient.post(reverse('applyEventpaid'), {
            'user_id': 'testuser',
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in'],
            'eventId': self.event.event_id,
            'transactionID': 'TXN001',
            'CAcode': 'CA001'
        }, content_type="application/json")

        self.assertNotEqual(response.status_code, 200)
        self.assertIn('error', response.json())









class CreateCAUserTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)  # Authenticate the test user

    def test_create_ca_user(self):
        # Sending a POST request to create CA user
        response = self.client.post('/auth/CA/create/', {}, format='json')  # Passing empty payload
        self.assertEqual(response.status_code, 200)
        ca_profile = CAProfile.objects.filter(user=self.user).first()
        self.assertTrue(ca_profile is not None)
        self.assertTrue('CACode' in response.data)
        self.assertEqual(ca_profile.registration, 0)
        self.assertTrue(response.data['success'])

        # Asserting the CACode matches the one in CAProfile
        self.assertEqual(response.data['CACode'], ca_profile.CACode)

    def test_create_ca_user_unauthenticated(self):
        # Create a new APIClient instance without authentication
        unauthenticated_client = APIClient()
        response = unauthenticated_client.post('/auth/CA/create/', {}, format='json')
        self.assertEqual(response.status_code, 403)  

    def test_create_ca_user_invalid_method(self):
        # Sending a GET request instead of POST
        response = self.client.get('/auth/CA/create/', {}, format='json')
        self.assertEqual(response.status_code, 405)

    def test_create_ca_user_server_error(self):
        # Simulating an exception during CAProfile creation
        with patch('app.models.CAProfile.save', side_effect=Exception('Database error')):
            response = self.client.post('/auth/CA/create/', {}, format='json')
            self.assertEqual(response.status_code, 500)
            self.assertIn('Something went wrong', response.data['detail'])

    def test_create_ca_user_already_exists(self):
        # Create a CAProfile for the user before making the request
        existing_profile = CAProfile.objects.create(user=self.user, registration=0)
        response = self.client.post('/auth/CA/create/')

        # Verifying that no new CAProfile is created
        ca_profile_count = CAProfile.objects.filter(user=self.user).count()
        self.assertEqual(ca_profile_count, 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)
#         self.assertEqual(response.data['CACode'], existing_profile.CACode)















