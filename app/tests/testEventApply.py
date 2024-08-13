import json
import unittest
from django.test import TestCase
from django.test import Client
from app.models import Event, TransactionTable, User,Profile
from django.urls import reverse

# to run use - py manage.py test app/test/


headers = {"HTTP_HOST":"petrichor.events"}
testClient= Client(

    enforce_csrf_checks=True,
    headers=headers
    )

@DeprecationWarning
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


