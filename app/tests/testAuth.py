

import json
import unittest
from django.test import TestCase
from django.test import Client
from app.models import Institute, User,Profile,CAProfile,UserRegistrations
from django.urls import reverse

# to run use - py manage.py test app/test/

# coverage run manage.py test app/tests --keepdb
# coverage report
# OR
# coverage html


headers = {"HTTP_HOST":"petrichor.events"}
testClient= Client(

    enforce_csrf_checks=True,
    headers=headers
    )


class RegisterTest(TestCase):

    register_url = reverse('signup')
    def test_RegisterGoodData1(self):
        '''
            Test on a correct data
        '''
        response = testClient.post(self.register_url,{
            "username": "alonot",
            "email":  "alo@fsg.com",
            "password": "123w123qe",
            "phone": "0000000000",
            "college": "IITPKD",
            "gradyear": 2024,
            "institype": "college",
            "stream": "cse"
        }) 
        user = User.objects.filter(username = "alo@fsg.com").first()
        self.assertNotEqual(user,None)
        self.assertEqual(response.status_code, 100)
        profile = Profile.objects.filter(user = user).first()
        self.assertNotEqual(profile,None)
        user_regs = UserRegistrations.objects.filter(user = user).first()
        self.assertNotEqual(user_regs,None)
        institute = Institute.objects.count()
        self.assertEqual(institute,1)
        
    def test_RegisterGoodData2(self):
        '''
            Test2 on a correct data but institute is already created
        '''
        Institute.objects.create(instiName = "IITPKD", institutionType = "college")
        # registering the same data to check if this request is rejected or not
        response = testClient.post('/api/register/',{
            "username": "alonot",
            "email":  "alonot@fsg.com",
            "password": "123w123qe",
            "phone": "0000000000",
            "college": "IITPKD",
            "gradyear": 2024,
            "institype": "college",
            "stream": "bse"
        })

        self.assertEqual(response.status_code, 200) 
        user = User.objects.filter(username = "alonot@fsg.com").first()
        self.assertNotEqual(user,None)
        profile = Profile.objects.filter(user = user).first()
        self.assertNotEqual(profile,None)
        user_regs = UserRegistrations.objects.filter(user = user).first()
        self.assertNotEqual(user_regs,None)   
        institute = Institute.objects.count()
        self.assertEqual(institute,1)     

    def test_RegisterDuplicateUser(self):
        '''
            Test2 on a correct data but institute is already created
        '''
        Institute.objects.create(instiName = "IITPKD", institutionType = "college")
        # registering the username once
        self.test_RegisterGoodData1()

        # registering the same data to check if this request is rejected or not
        response = testClient.post('/api/register/',{
            "username": "alonot",
            "email":  "alo@fsg.com",
            "password": "123w123qe",
            "phone": "0000000000",
            "college": "IITPKD",
            "gradyear": 2024,
            "institype": "college",
            "stream": "bse"
        })

        self.assertEqual(response.status_code, 400) 
        user = User.objects.filter(username = "alo@fsg.com").first()
        # checking that previous datas must be same even after duplicate emails
        self.assertNotEqual(user,None)
        profile = Profile.objects.filter(user = user).first()
        self.assertNotEqual(profile,None)
        user_regs = UserRegistrations.objects.filter(user = user).first()
        self.assertNotEqual(user_regs,None)   
        institute = Institute.objects.count()
        self.assertEqual(institute,1)  

    def test_RegisterWrongEmail(self):
        '''
            Test on a wrong email
        '''
        response = testClient.post('/api/register/',{
            "username": "alonot1",
            "email":  "alo@fsg",
            "password": "123w123qe",
            "phone": "0000000000",
            "college": "IITPKD",
            "gradyear": 2024,
            "institype": "college",
            "stream": "cse"
        })

        self.assertNotEqual(response.status_code, 200) # here is the change from the above test case: assertNot
        user = User.objects.filter(username = "alo@fsg").first()
        self.assertEqual(user,None)
        profile = Profile.objects.filter(username = "alonot1").first()
        self.assertEqual(profile,None)
        user_regs = UserRegistrations.objects.filter(user = user).first()
        self.assertEqual(user_regs,None)

    ### Login tests

    def test_loginOnGoodData1(self):
        '''
            Test on a correct data
        '''
        self.test_RegisterGoodData1()
        try:
            response = testClient.post('/api/login/',{
                "username":  "alo@fsg.com",
                "password": "123w123qe",
            },content_type="application/json")
        except Exception as e:
            self.fail("Error")

        user = User.objects.filter(username = "alo@fsg.com").first()
        self.assertNotEqual(user,None) 
        self.assertEqual(response.status_code, 200)


    def test_InvalidCredentials(self):
        '''
            Test on a wrong credentials
        '''
        self.test_RegisterGoodData1()
        try:
            response = testClient.post('/api/login/',{
                "username":  "alo@fsg.com",
                "password": "12w123qe",
            },content_type="application/json")
        except Exception as e:
            self.fail("Error")

        self.assertNotEqual(response.status_code, 200)
            
        

    def test_badLoginValues(self):
        '''
            Test on a Invalid values 
        '''
        try:
            response = testClient.post('/api/login/',{
                "userne":  "alo@fsg.com",
                "password": "123w123qe",
            },content_type="application/json")
            
        except Exception as e:
            self.fail("Error")

        self.assertNotEqual(response.status_code, 200)

    ### Login Test ends

class AuthTest(TestCase):
    def setUp(self) -> None:
        '''
            registering a user and login it in for the Auth test case
        '''
        try:
            testClient.post('/api/register/',{
                "username": "alonot1",
                "email":  "alo@fsg.com",
                "password": "123w123qe",
                "phone": "0000000000",
                "college": "IITPKD",
                "gradyear": 2024,
                "institype": "college",
                "stream": "cse"
            })

            response = testClient.post('/api/login/',{
                    "username":  "alo@fsg.com",
                    "password": "123w123qe",
                },content_type="application/json")

            self.token = json.loads(response.content)['token']

        except Exception as e:
            self.fail("Error")
        return super().setUp()
    
    def test_authOnGoodData1(self):
        '''
            Test on a correct data
        '''
        try:
            response = testClient.post('/api/auth/',{
                "getUser":  True,
                "getEvents": True,
            },content_type="application/json",headers={
            'Authorization': f"Bearer {self.token}"
        })
        except Exception as e:
            self.fail("Error")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        user_data = data['user_data']
        self.assertNotEqual(user_data,{})

    def test_authOnGoodData2(self):
        '''
            Test2 on a correct data
        '''
        try:
            response = testClient.post('/api/auth/',{
                "getUser":  False,
                "getEvents": False,
            },content_type="application/json",headers={
            'Authorization': f"Bearer {self.token}"
        })
        except Exception as e:
            self.fail("Error")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        user_data = data['user_data']
        user_events = data['user_events']
        self.assertEqual(user_data,{})
        self.assertEqual(user_events,[])

    def test_authOnGoodData3(self):
        '''
            Test3 on a correct data
        '''
        try:
            response = testClient.post('/api/auth/',{
                "getUser":  False,
                "getEvents": True,
            },content_type="application/json",headers={
            'Authorization': f"Bearer {self.token}"
        })
        except Exception as e:
            self.fail("Error")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        user_data = data['user_data']
        user_events = data['user_events']
        self.assertEqual(user_data,{})

    def test_authOnGoodData4(self):
        '''
            Test4 on a correct data
        '''
        try:
            response = testClient.post('/api/auth/',{
                "getUser":  True,
                "getEvents": False,
            },content_type="application/json",headers={
            'Authorization': f"Bearer {self.token}"
        })
        except Exception as e:
            self.fail("Error")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        user_data = data['user_data']
        user_events = data['user_events']
        self.assertNotEqual(user_data,{})
        self.assertEqual(user_events,[])

    def test_authOnGoodData5(self):
        '''
            Test5 on a correct data where CAAccount have been created so CACode must be returned
        '''
        # creating a CA for this person
        self.client.post('/api/auth/CA/create/', {}, format='json',headers={
            'Authorization': f"Bearer {self.token}"
        })

        try:
            response = testClient.post('/api/auth/',{
                "getUser":  True,
                "getEvents": False,
            },content_type="application/json",headers={
            'Authorization': f"Bearer {self.token}"
        })
        except Exception as e:
            self.fail("Error")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        user_data = data['user_data']
        user_events = data['user_events']
        self.assertNotEqual(user_data,{})
        self.assertEqual(user_events,[])
        self.assertNotEqual(user_data['CACode'],"")


    def test_notLoggedIn(self):
        '''
            Test on a invalid login
        '''
        try:
            response = testClient.post('/api/auth/',{
                "getUser":  True,
                "getEvents": True,
            },content_type="application/json",headers={
            'Authorization': f"Bearer not_loggedIn"
        })
        except Exception as e:
            self.fail("Error")

        self.assertNotEqual(response.status_code, 200)
            
        

    def test_badAuthValues(self):
        '''
            Test on a Invalid values
        '''
        try:
            response = testClient.post('/api/auth/',{
                "getUser":  True,
                "getEvent": True,
            },content_type="application/json",headers={
            'Authorization': f"Bearer {self.token}"
        })
            
        except Exception as e:
            self.fail("Error")

        self.assertNotEqual(response.status_code, 200)

    def test_wrongMethod(self):
        '''
            Test on a Invalid values
        '''
        try:
            response = testClient.get('/api/auth/',content_type="application/json",headers={
            'Authorization': f"Bearer {self.token}"
        })
            
        except Exception as e:
            self.fail("Error")

        self.assertNotEqual(response.status_code, 200)
