import json
import unittest
from django.test import TestCase
from django.test import Client
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from app.models import Event, TransactionTable, User, Profile,CAProfile
from django.urls import reverse
from unittest.mock import patch
from rest_framework import status

headers = {"HTTP_HOST":"petrichor.events"}
testClient= Client(

    enforce_csrf_checks=True,
    headers=headers
    )

class EventApplicationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user= User(username = "csk20020@gmail.com", email = "csk20020@smail.iitpkd.ac.in" )

        self.user.set_password("123w123qe")
        self.user.save()
        
    # Other setup code...

        
        self.profile = Profile.objects.create(
            username='testuser',
            user=self.user
        )
        
        self.event_team = Event.objects.create(
            event_id='EVT002',
            name='Team Event',
            fee=100,
            minMember=2,
            maxMember=10,
            isTeam=True
        )
        self.event_team_2 = Event.objects.create(
            event_id='EVT004',
            name='Team Event',
            fee=100,
            minMember=1,
            maxMember=3,
            isTeam=True
        )

        self.event_individual = Event.objects.create(
            event_id='EVT003',
            name='Individual Event',
            fee=50,
            minMember=1,
            maxMember=1,
            isTeam=False
        )
        response  = testClient.post('/api/login/',{
            'username':'csk20020@gmail.com',
            'password':'123w123qe'
        })
        self.token = json.loads(response.content)['token']
        response = self.client.post('/api/auth/CA/create/', {}, format='json',headers={
            'Authorization': f"Bearer {self.token}"
        })
        self.CACode = CAProfile.objects.first().CACode


    def test_apply_event_team(self):
        # response = self.client.post('/api/auth/events/apply/paid', {}, format='json',headers={
        #     'Authorization': f"Bearer {self.token}"
        # })
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in'],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN002',
            'CACode': self.CACode,
        }, format='json',HTTP_AUTHORIZATION=f"Bearer {self.token}")

        print(response.status_code, response.json())  # Debug print
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertTrue(transaction.verified)
        self.assertEqual(transaction.event_id, self.event_team)
        
        

    def test_apply_event_individual(self):
        response = self.client.post('/api/auth/events/apply/paid', {}, format='json',headers={
            'Authorization': f"Bearer {self.token}"
        })
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': [ ],
            'eventId': self.event_individual.event_id,
            'transactionID': 'TXN003',
            'CACode': self.CACode
        }, format='json',HTTP_AUTHORIZATION=f"Bearer {self.token}")

        print(response.status_code, response.json())  # Debug print
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertTrue(transaction.verified)
        self.assertEqual(transaction.event_id, self.event_individual)


    def test_apply_event_paid_duplicate_transaction_id(self):
        # Apply event with the same transaction ID twice
        response1 = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@gmail.com'],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN007',
            'CACode': self.CACode
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        print(response1.status_code, response1.json())
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser2@gmail.com'],
            'eventId': self.event_team_2.event_id,
            'transactionID': 'TXN007',
            'CACode': self.CACode
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
           # Debugging output
        print("Response Status Code:", response2.status_code)
        print("Response Content:", response2.json())
        
        # Check if the second response indicates duplicate transaction ID error
        self.assertEqual(response2.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Duplicate transaction ID", response2.json().get('message'))
    
    
    def test_non_iit_palakkad_email(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['noniituser@example.com'],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN005',
            'CACode': self.CACode
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        print(response.status_code, response.json()) 
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertFalse(transaction.verified)

    def test_non_existent_CAProfile(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in'],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN006',
            'CACode': 'INVALID_CACODE'
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")
        print(response.status_code, response.json()) 
        self.assertEqual(response.status_code, 439)
        self.assertIn('CA user not found', response.json()['message'])

    def test_successful_application_with_CAProfile(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in'],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN007',
            'CACode': self.CACode
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")
        print(response.status_code, response.json()) 
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertTrue(transaction.verified)
        self.assertEqual(transaction.CACode.CACode, self.CACode)
    
    
    
    def test_participant_exceeds_capacity(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in', 'testuser3@smail.iitpkd.ac.in'],
            'eventId': self.event_team_2.event_id,
            'transactionID': 'TXN010',
            'CACode': self.CACode
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        print(response.status_code, response.json())
        self.assertEqual(response.status_code, 500)
        self.assertIn(f"Team events require between {self.event_team_2.minMember} and {self.event_team_2.maxMember} participants.", response.json()['message'])
    
    

    def test_individual_event_with_multiple_participants(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in'],
            'eventId': self.event_individual.event_id,
            'transactionID': 'TXN013',
            'CACode': self.CACode
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        print(response.status_code, response.json())
        self.assertEqual(response.status_code, 500)
        self.assertIn('Individual events require exactly 1 participant.', response.json().get('message'))
    
    
    def test_apply_event_paid_duplicate_registration_user_email(self):
    # First registration attempt
        response1 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'participants': ['testuser1@smail.iitpkd.ac.in'],  # This is not the logged-in user's email
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN008',
            'CACode': self.CACode
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        print(response1.status_code, response1.json())
        
        # Check if the first registration was successful and the transaction is verified
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction1 = TransactionTable.objects.first()
        self.assertTrue(transaction1.verified)
        
        # Second registration attempt with the logged-in user's email as a participant
        response2 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'participants': [self.user.email],  # This is the logged-in user's email
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN009',
            'CACode': self.CACode
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        print(response2.status_code, response2.json())
        
        # Check for duplicate registration error
        self.assertEqual(response2.status_code, 500)
        self.assertIn('Some/All Participants have already been registered for this event', response2.json().get('message'))

    
    
    
    
    
# free event


    def test_apply_event_team_free(self):
        response = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': ['testuser1@example.com', 'testuser2@example.com'],
            'eventId': self.event_team.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        print(response.status_code, response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertTrue(transaction.verified)
        
        
    def test_apply_event_individual_free(self):
        response = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': [],
            'eventId': self.event_individual.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        print(response.status_code, response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertTrue(transaction.verified)



    
    def test_multiple_applications_for_free_event(self):
        response1 = self.client.post(reverse('applyEventfree'), {
            'participants': [],
            'eventId': self.event_individual.event_id
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        print(response1.status_code, response1.json())
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(reverse('applyEventfree'), {
            'participants': [],
            'eventId': self.event_individual.event_id
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        print(response2.status_code, response2.json())
        self.assertEqual(response2.status_code, 500)
        self.assertIn('Some/All Participants have already been registered for this event', response2.json().get('message'))
    
    
    
    def test_non_existent_free_event(self):
        response = self.client.post(reverse('applyEventfree'), {
            'participants': ['testuser1@smail.iitpkd.ac.in'],
            'eventId': 'NON_EXISTENT_FREE_EVENT'
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        print(response.status_code, response.json())
        self.assertEqual(response.status_code, 500)
        self.assertIn('No event exists with given event_id', response.json().get('message'))
    
    
    
    def test_missing_participants_free_event(self):
        response = self.client.post(reverse('applyEventfree'), {
            'eventId': self.event_team.event_id
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        print(response.status_code, response.json())
        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertTrue('participants' in response_data['error'].lower())
    
    def test_apply_event_free_duplicate_registration_user_email(self):
    # First registration attempt
        response1 = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': ['testuser1@smail.iitpkd.ac.in'],  # This is not the logged-in user's email
            'eventId': self.event_team.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        print(response1.status_code, response1.json())
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction1 = TransactionTable.objects.first()
        self.assertTrue(transaction1.verified)
        
        # Second registration attempt with the logged-in user's email as a participant
        response2 = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': [self.user.email],  # This is the logged-in user's email
            'eventId': self.event_team.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        print(response2.status_code, response2.json())
        self.assertEqual(response2.status_code, 500)
        self.assertIn('Some/All Participants have already been registered for this event', response2.json().get('message'))






    

