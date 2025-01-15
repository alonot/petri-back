import json
import unittest
from django.test import TestCase
from django.test import Client
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from app.models import Event, TransactionTable, User, Profile,CAProfile, UserRegistrations
from django.urls import reverse
from unittest.mock import patch
from rest_framework import status

from petri_ca.settings import COUPON_CODES

headers = {"HTTP_HOST":"petrichor.events"}
testClient= Client(

    enforce_csrf_checks=True,
    headers=headers
    )

class EventApplicationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user= User(username = "csk20020@smail.iitpkd.ac.in", email = "csk20020@smail.iitpkd.ac.in" )

        self.user.set_password("123w123qe")
        self.user.save()
        self.user_non_insti= User(username = "csk20020@gmail.com", email = "csk20020@gmail.com" )
        self.user_non_insti.set_password("123w123qe")
        self.user_non_insti.save()
        
    # Other setup code...

        
        self.profile = Profile.objects.create(
            username='testuser',
            user=self.user,
            verified = True
        )
        self.profile_non_insti = Profile.objects.create(
            username='testuser2',
            user=self.user_non_insti,
            verified = True
        )
        
        self.event_team = Event.objects.create(
            event_id='EVT002',
            name='Team Event',
            fee=100,
            minMember=2,
            maxMember=10,
            isTeam=True
        )
        self.event_team_free = Event.objects.create(
            event_id='EVT005',
            name='Team Event',
            fee=0,
            minMember=1,
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
            'username':'csk20020@smail.iitpkd.ac.in',
            'password':'123w123qe'
        })
        self.token = json.loads(response.content)['token']
        response = self.client.post('/api/auth/CA/create/', {}, format='json',headers={
            'Authorization': f"Bearer {self.token}"
        })
        self.CACode = CAProfile.objects.first().CACode
        response  = testClient.post('/api/login/',{
            'username':'csk20020@gmail.com',
            'password':'123w123qe'
        })
        self.token_non_insti = json.loads(response.content)['token']
        response = self.client.post('/api/auth/CA/create/', {}, format='json',headers={
            'Authorization': f"Bearer {self.token_non_insti}"
        })
        self.CACode2 = CAProfile.objects.all()[1].CACode 


    def test_apply_event_paid_team(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in'],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN002',
            'CACode': self.CACode2,
            "coupon": ""
        }, format='json',HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # print(response.status_code, response.json())  # Debug print
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertTrue(transaction.verified)
        self.assertEqual(transaction.event_id, self.event_team)
        self.assertEqual(len(transaction.get_participants()),2)

    def test_apply_event_paid_null_eventId(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in'],
            'transactionID': 'TXN002',
            'CACode': self.CACode2,
            "coupon": ""
        }, format='json',HTTP_AUTHORIZATION=f"Bearer {self.token}")

        assert response.status_code == 500
        assert response.json()["message"] == "null event Id , key is eventId"
    
    def test_apply_event_paid_null_coupon(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in'],
            'transactionID': 'TXN002',
            'eventId': self.event_individual.event_id,
            'CACode': self.CACode2,
        }, format='json',HTTP_AUTHORIZATION=f"Bearer {self.token}")

        assert response.status_code == 500
        self.assertIn("null coupon , key is coupon", response.json()['message'])
        
        

    def test_apply_event_paid_individual(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': [],
            'eventId': self.event_individual.event_id,
            'transactionID': 'TXN003',
            'CACode': self.CACode2,
            "coupon": ""
        }, format='json',HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # # print(response.status_code, response.json())  # Debug print
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertTrue(transaction.verified)
        self.assertEqual(transaction.event_id, self.event_individual)
        self.assertEqual(len(transaction.get_participants()),0)

    def test_apply_event_paid_with_coupon(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ["test@gmail.com"],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN003',
            'CACode': self.CACode,
            "coupon": COUPON_CODES[0]
        }, format='json',HTTP_AUTHORIZATION=f"Bearer {self.token_non_insti}")

        # print(response.status_code, response.json())  # Debug print
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertFalse(transaction.verified)
        self.assertEqual(transaction.event_id, self.event_team)
        self.assertEqual(transaction.total_fee, round(self.event_team.fee * 0.9))
        self.assertEqual(len(transaction.get_participants()),1)


    def test_apply_event_paid_duplicate_transaction_id(self):
        # Apply event with the same transaction ID twice
        response1 = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@gmail.com'],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN007',
            'CACode': self.CACode2,
            "coupon": ""
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        # print(response1.status_code, response1.json())
        transaction = TransactionTable.objects.first()
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser2@gmail.com'],
            'eventId': self.event_team_2.event_id,
            'transactionID': 'TXN007',
            'CACode': self.CACode2,
            "coupon": ""
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
           # Debugging output
        # print("Response Status Code:", response2.status_code)
        # print("Response Content:", response2.json())
        
        # Check if the second response indicates duplicate transaction ID error
        self.assertEqual(response2.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Duplicate transaction ID", response2.json().get('message'))
        self.assertEqual(len(transaction.get_participants()),1)
    
    
    def test_apply_event_paid_non_iit_palakkad_email(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['noniituser@example.com'],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN005',
            'CACode': self.CACode2,
            "coupon": ""
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        # print(response.status_code, response.json()) 
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertFalse(transaction.verified)
        userReg = UserRegistrations.objects.filter(email = 'noniituser@example.com').first()
        self.assertIsNotNone(userReg)
        self.assertIn("TXN005",userReg.transactionIds) # type:ignore
        self.assertFalse(transaction.verified) # type:ignore
        self.assertEqual(len(transaction.get_participants()),1)

    def test_apply_event_paid_wrong_email_format_in_participants(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['noniituserexample.com',''],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN005',
            'CACode': self.CACode2,
            "coupon": ""
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        # print(response.status_code, response.json()) 
        self.assertEqual(response.status_code, 500)
        self.assertIn("Following Email is invalid",response.json()["message"])
        self.assertEqual(TransactionTable.objects.count(), 0)

    def test_apply_event_paid_non_existent_CAProfile(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in'],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN006',
            'CACode': 'INVALID_CACODE',
            "coupon": ""
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")
        # print(response.status_code, response.json()) 
        self.assertEqual(response.status_code, 439)
        self.assertIn('CA user not found', response.json()['message'])

    def test_apply_event_paid_successful_application_with_CAProfile(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in'],
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN007',
            'CACode': self.CACode2,
            "coupon": ""
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")
        # print(response.status_code, response.json()) 
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertEqual(len(transaction.get_participants()),1) #type:ignore
        self.assertTrue(transaction.verified)
        self.assertEqual(transaction.CACode.CACode, self.CACode2)
    
    
    
    def test_apply_event_paid_participant_exceeds_capacity(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in', 'testuser3@smail.iitpkd.ac.in'],
            'eventId': self.event_team_2.event_id,
            'transactionID': 'TXN010',
            'CACode': self.CACode2,
            "coupon": ""
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # print(response.status_code, response.json())
        self.assertEqual(response.status_code, 500)
        self.assertIn(f"Min ", response.json()['message'])
    
    

    def test_apply_event_paid_individual_event_with_multiple_participants(self):
        response = self.client.post(reverse('applyEventpaid'), {
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in'],
            'eventId': self.event_individual.event_id,
            'transactionID': 'TXN013',
            'CACode': self.CACode2,
            "coupon": ""
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # print(response.status_code, response.json())
        self.assertEqual(response.status_code, 500)
        self.assertIn('Min ', response.json().get('message'))
    
    
    def test_apply_event_paid_duplicate_registration_user_email(self):
    # First registration attempt
        response1 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'participants': ['csk20020@gmail.com'],  # This is not the logged-in user's email
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN008',
            'CACode': self.CACode2,
            "coupon": ""
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        # print(response1.status_code, response1.json())
        
        # Check if the first registration was successful and the transaction is verified
        self.assertEqual(response1.status_code, 200)
        self.assertIn('Event applied successfully', response1.json().get('message'))
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction1 = TransactionTable.objects.first()
        self.assertEqual(len(transaction1.get_participants()),1)
        self.assertFalse(transaction1.verified)
        
        # Second registration attempt with the logged-in user's email as a participant
        response2 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'participants': ['csk20020@smail.iitpkd.ac.in'],  # This is the logged-in user's email
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN009',
            'CACode': self.CACode,
            "coupon": ""
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token_non_insti}")
        
        # print(response2.status_code, response2.json())
        
        # Check for duplicate registration error
        self.assertEqual(response2.status_code, 500)
        self.assertIn('Some/All Participants have already been registered for this event', response2.json().get('message'))

    
    def test_apply_event_paid_duplicate_emails(self):
        response2 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'participants': ['csk20020@smail.iitpkd.ac.in'],  # This is the logged-in user's email
            'eventId': self.event_team.event_id,
            'transactionID': 'TXN009',
            'CACode': self.CACode,
            "coupon": ""
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        self.assertIn('Duplicate emails provided in participants', response2.json().get('message'))
    
    def test_apply_event_paid_null_tr(self):
        response2 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'participants': [],  # This is the logged-in user's email
            'eventId': self.event_team_2.event_id,
            "coupon": ""
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        self.assertIn('null transaction Id , key is transactionID', response2.json().get('message'))
    
    def test_apply_event_paid_null_CACode(self):
        response2 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'transactionID': 'TXN009',
            'participants': [],  # This is the logged-in user's email
            'eventId': self.event_team_2.event_id,
            "coupon": ""
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        self.assertIn('null CAcode , key is CACode', response2.json().get('message'))
    
    def test_apply_event_paid_wrong_event_id(self):
        response2 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'transactionID': 'TXN009',
            "CACode": "",
            'participants': [],  # This is the logged-in user's email
            'eventId': "self.event_team_2.event_id",
            "coupon": ""
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        self.assertIn('No event exists with given event_id', response2.json().get('message'))
    
    def test_apply_event_paid_applying_free_event(self):
        response2 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'transactionID': 'TXN009',
            "CACode": "",
            'participants': [],  # This is the logged-in user's email
            'eventId': self.event_team_free.event_id,
            "coupon": ""
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        self.assertIn('This event is free. Please use api/event/free/', response2.json().get('message'))
    
    def test_apply_event_paid_using_own_cacode(self):
        response2 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'transactionID': 'TXN009',
            "CACode": self.CACode,
            'participants': ["csk20020@gmail.com"],  # This is the logged-in user's email
            'eventId': self.event_team.event_id,
            "coupon": ""
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        self.assertIn('You cannot use your own CA code', response2.json().get('message'))
    
    def test_apply_event_paid_wrong_coupon(self):
        response2 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'transactionID': 'TXN009',
            "CACode": self.CACode,
            'participants': ["csk20020@gmail.com"],  # This is the logged-in user's email
            'eventId': self.event_team.event_id,
            "coupon": "WRONG_ONE"
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        self.assertIn('Invalid coupon code', response2.json().get('message'))
    
    def test_apply_event_paid_null_n_str_participants(self):
        response2 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'transactionID': 'TXN009',
            'participants': "",  # This is the logged-in user's email,
            "CACode": "",
            'eventId': self.event_team_2.event_id,
            "coupon": ""
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        self.assertIn('null participants , key is participants', response2.json().get('message'))
        
        response2 = self.client.post(reverse('applyEventpaid'), json.dumps({
            'transactionID': 'TXN009',
            "CACode": "null",
            'eventId': self.event_team_2.event_id,
            "coupon": ""
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        self.assertIn('null participants , key is participants', response2.json().get('message'))
    
    
    
    
# free event


    def test_apply_event_team_free(self):
        response = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': ['testuser1@example.com', 'testuser2@example.com'],
            'eventId': self.event_team_free.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        # print(response.status_code, response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        
        transaction = TransactionTable.objects.first()
        self.assertEqual(len(transaction.get_participants()),2)
        self.assertTrue(transaction.verified)
        
        
    def test_apply_event_individual_free(self):
        response = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': [],
            'eventId': self.event_individual.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        # print(response.status_code, response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction = TransactionTable.objects.first()
        self.assertEqual(len(transaction.get_participants()),0)
        self.assertTrue(transaction.verified)



    
    def test_multiple_applications_for_free_event(self):
        response1 = self.client.post(reverse('applyEventfree'), {
            'participants': [],
            'eventId': self.event_individual.event_id
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # print(response1.status_code, response1.json())
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        transaction = TransactionTable.objects.first()
        self.assertEqual(len(transaction.get_participants()),0)

        response2 = self.client.post(reverse('applyEventfree'), {
            'participants': [],
            'eventId': self.event_individual.event_id
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # print(response2.status_code, response2.json())
        self.assertEqual(response2.status_code, 500)
        self.assertIn('Some/All Participants have already been registered for this event', response2.json().get('message'))
    
    
    
    def test_non_existent_free_event(self):
        response = self.client.post(reverse('applyEventfree'), {
            'participants': ['testuser1@smail.iitpkd.ac.in'],
            'eventId': 'NON_EXISTENT_FREE_EVENT'
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # print(response.status_code, response.json())
        self.assertEqual(response.status_code, 500)
        self.assertIn('No event exists with given event_id', response.json().get('message'))
    
    
    
    def test_missing_participants_free_event(self):
        response = self.client.post(reverse('applyEventfree'), {
            'eventId': self.event_team.event_id
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # print(response.status_code, response.json())
        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertTrue('participants' in response_data['message'].lower())
    
    def test_apply_event_free_duplicate_registration_user_email(self):
    # First registration attempt
        response1 = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': ['testuser1@smail.iitpkd.ac.in'],  # This is not the logged-in user's email
            'eventId': self.event_team.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        # print(response1.status_code, response1.json())
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction1 = TransactionTable.objects.first()
        self.assertTrue(transaction1.verified)
        self.assertEqual(len(transaction1.get_participants()),1)
        
        # Second registration attempt with the logged-in user's email as a participant
        response2 = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': [self.user.email],  # This is the logged-in user's email
            'eventId': self.event_team.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        # print(response2.status_code, response2.json())
        self.assertEqual(response2.status_code, 500)
        self.assertIn('Duplicate emails provided in participants', response2.json().get('message'))


    def test_free_event_with_multiple_participants(self):
        response = self.client.post(reverse('applyEventfree'), {
            'participants': ['testuser1@smail.iitpkd.ac.in', 'testuser2@smail.iitpkd.ac.in'],
            'eventId': self.event_individual.event_id
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # print(response.status_code, response.json())
        self.assertEqual(response.status_code, 500)
        self.assertIn('Min ', response.json().get('message'))

    
    def test_apply_paid_event_in_free_event_non_insti_user(self):
        response2 = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': ["csk20020@gmail.com"], 
            'eventId': self.event_team_2.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        self.assertIn('This event has some fee assigned with it. Please use api/event/paid/', response2.json().get('message'))
    
    def test_apply_paid_event_in_free_event_insti_user(self):
        ## this must be registered. 
        
        response2 = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': ["csk200200@smail.iitpkd.ac.in"], 
            'eventId': self.event_team_free.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 200) ## server must reject due to duplicate mails
        self.assertIn('Event applied successfully', response2.json().get('message'))
    
    def test_apply_event_free_no_event_id(self):
        response2 = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': [self.user.email],  # This is the logged-in user's email
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        self.assertIn('null event Id , key is eventId', response2.json().get('message'))

    def test_apply_event_free_multiple_event(self):
    # First registration attempt
        response1 = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': ['testuser1@smail.iitpkd.ac.in'],  # This is not the logged-in user's email
            'eventId': self.event_team.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(TransactionTable.objects.count(), 1)
        transaction1 = TransactionTable.objects.first()
        self.assertTrue(transaction1.verified)
        self.assertEqual(len(transaction1.get_participants()),1)
        
        # Second registration attempt with the logged-in user's email as a participant
        response2 = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': [self.user.email],  # This is the logged-in user's email
            'eventId': self.event_team_free.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        self.assertEqual(response2.status_code, 500) ## server must reject due to duplicate mails
        # print(TransactionTable.objects.count())
        # Register registration attempt with the logged-in user's email as a participant
        res = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': [],  # This is the logged-in user's email
            'eventId': self.event_team_free.event_id
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        
        # print(res.json())
        self.assertEqual(res.status_code,200)
        self.assertEqual(TransactionTable.objects.count(), 2)
        # this must be rejected, same user on same event
        resp = self.client.post(reverse('applyEventfree'), json.dumps({
            'participants': ['csk20020@smail.iitpkd.ac.in'],  # This is the logged-in user's email
            'eventId': self.event_team_free.event_id,
            'transactionID': 'TXN009',
            'CACode': "null"
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token_non_insti}")
        
        self.assertEqual(resp.status_code,500)
        self.assertEqual(TransactionTable.objects.count(), 2)
        event = Event.objects.filter(event_id = self.event_team_free.event_id).first()
        transactionSet = event.transactiontable_set # type:ignore   
        self.assertEqual(transactionSet.count(),1)
