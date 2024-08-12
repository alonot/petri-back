
import json
from django.test import TestCase
from django.test import Client
from app.models import Institute, User,Profile,CAProfile
from rest_framework.test import APIClient
from unittest.mock import patch

# to run use - py manage.py test app/test/


headers = {"HTTP_HOST":"petrichor.events"}
testClient= Client(

    enforce_csrf_checks=True,
    headers=headers
    )


class CreateCAUserTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a test user
        self.inst = Institute.objects.create(institutionType = "college",
                                            instiName ="IITPKD" )
        user= User(username = "csk20020@gmail.com", email = "csk20020@gmail.com" )

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
        self.user = user
        response  = testClient.post('/api/login/',{
            'username':'csk20020@gmail.com',
            'password':'123w123qe'
        })
        self.token = json.loads(response.content)['token']
        

    def test_create_ca_user(self):
        # Sending a POST request to create CA user
        response = self.client.post('/api/auth/CA/create/', {}, format='json',headers={
            'Authorization': f"Bearer {self.token}"
        })  # Passing empty payload
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
        response = unauthenticated_client.post('/api/auth/CA/create/', {}, format='json')
        self.assertEqual(response.status_code, 403) 

    def test_create_ca_user_invalid_method(self):
        # Sending a GET request instead of POST
        response = self.client.get('/api/auth/CA/create/', {}, format='json',headers={
            'Authorization': f"Bearer {self.token}"
        })
        self.assertEqual(response.status_code, 405)

    def test_create_ca_user_server_error(self):
        # Simulating an exception during CAProfile creation
        with patch('app.models.CAProfile.save', side_effect=Exception('Database error')):
            response = self.client.post('/api/auth/CA/create/', {}, format='json',headers={
                'Authorization': f"Bearer {self.token}"
            })
            self.assertIn('Something went wrong', response.content.__str__())
            self.assertEqual(response.status_code, 500)

    def test_create_ca_user_already_exists(self):
        # Create a CAProfile for the user before making the request
        response = self.client.post('/api/auth/CA/create/',headers={
            'Authorization': f"Bearer {self.token}"
        })

        # Verifying that no new CAProfile is created
        ca_profile_count = CAProfile.objects.filter(user=self.user).count()
        self.assertEqual(ca_profile_count, 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)
#         self.assertEqual(response.data['CACode'], existing_profile.CACode)

