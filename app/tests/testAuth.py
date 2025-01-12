

import json
import unittest
from django.test import TestCase
from django.test import Client
from app.models import Institute, User,Profile,CAProfile,UserRegistrations
from django.urls import reverse

from utils import get_forget_token

# to run use - py manage.py test app/tests/

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
            "phone": "1000000000",
            "college": "IITPKD",
            "gradyear": 2024,
            "institype": "college",
            "stream": "cse"
        })
        user = User.objects.filter(username = "alo@fsg.com").first()
        self.assertNotEqual(user,None)
        self.assertEqual(response.status_code, 200)
        profile = Profile.objects.filter(user = user).first()
        self.assertNotEqual(profile,None)
        user_regs = UserRegistrations.objects.filter(user = user).first()
        self.assertNotEqual(user_regs,None)
        institute = Institute.objects.count()
        self.assertEqual(institute,1)

    def test_RegisterTestData4(self):
        '''Testing on crooked data based on model'''
        response = testClient.post(self.register_url, {
            "username": "Dhruvadeep_Cli.asent_0001<h1>p</h1>", # wrong format
            "email": "dhruvadeep.dev",
            "password": "qwerty123",
            # Phone length to 25 length
            "phone": 127612123,
            "college": "<strong>Test HTML</strong>",
            "gradeyear": 1970,
            "institype": "college",
            "stream": "<h1>Hello Motto</h1>"
        })
        self.assertEqual(response.status_code, 500)

    def test_RegisterTestData3(self):
        '''Testing on crooked data based on model'''
        response = testClient.post(self.register_url, {
            "username": "Dhruvadeep_Client_0001",
            "email": "dhruvadeep@gmail.dev",
            "password": "1.>12234123132",
            # Phone length to 25 length
            "phone": "1213412134",
            "college": "<strong>Test HTML</strong>",
            "gradyear": 1970,
            "institype": "college",
            "stream": "<h1>Hello Motto</h1>"
        })
        self.assertEqual(response.status_code, 500)

    def test_RegisterTestData5(self):
        '''Testing on crooked data based on model'''
        response = testClient.post(self.register_url, {
            "username": "Dhruvadeep_Client_0001",
            "email": "dhruvadeep@gmail.dev",
            "password": "112234123132",
            # Phone length to 25 length
            "phone": "1213412134",
            "college": "<strong>Test HTML</strong>",
            "gradyear": 1970,
            "institype": "college",
            "stream": "<h1>Hello Motto</h1>"
        })
        self.assertEqual(response.status_code, 500)
        
    def test_RegisterTestData6(self):
        '''Testing on crooked data based on model'''
        response = testClient.post(self.register_url, {
            "username": "Dhruvadeep_Client_0001",
            "email": "dhruvadeep@gmail.dev",
            "password": "112234123132",
            # Phone length to 25 length
            "phone": "1213412134",
            "college": "asdasd",
            "gradyear": 1970,
            "institype": "college",
            "stream": "<h1>Hello Motto</h1>"
        })
        self.assertEqual(response.status_code, 500)

    def test_RegisterTestData7(self):
        '''Testing on crooked data based on model'''
        response = testClient.post(self.register_url, {
            "username": "Dhruvadeep_Client_0001",
            "email": "dhruvadeep@gmail.dev",
            "passrd": "112234123132",
            # Phone length to 25 length
            "phone": "1213412134",
            "college": "<strong>Test HTML</strong>",
            "gradear": 1970,
            "institype": "college",
            "stream": "<h1>Hello Motto</h1>"
        })
        # print(response.content)
        self.assertEqual(response.status_code, 500)

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
            "phone": "1000000000",
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
            "phone": "1000000000",
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

    def test_RegisterDuplicateCollegeName(self):
        '''
            Test2 on a correct data but institute is already created
        '''
        Institute.objects.create(instiName = "IIT PKD", institutionType = "college")

        # registering the same data to check if this request is rejected or not
        response = testClient.post('/api/register/',{
            "username": "alonot",
            "email":  "alonot@fsg.com",
            "password": "123w123qe",
            "phone": "1000000000",
            "college": "IITPKD",
            "gradyear": 2024,
            "institype": "school",
            "stream": "bse"
        })

        self.assertEqual(response.status_code, 200) 
        user = User.objects.filter(username = "alonot@fsg.com").first()
        # checking that previous datas must be same even after duplicate emails
        self.assertNotEqual(user,None)
        profile = Profile.objects.filter(user = user).first()
        self.assertNotEqual(profile,None)
        user_regs = UserRegistrations.objects.filter(user = user).first()
        self.assertNotEqual(user_regs,None)   
        institute = Institute.objects.count()
        self.assertEqual(institute,2)  

    def test_RegisterWrongEmail(self):
        '''
            Test on a wrong email
        '''
        response = testClient.post('/api/register/',{
            "username": "alonot1",
            "email":  "alo@fsg",
            "password": "123w123qe",
            "phone": "1000000000",
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
        token = get_forget_token("alo@fsg.com")
        response  = testClient.get(f'/api/login/verify/{token}/',{
            },content_type="application/json")
        self.assertEqual(response.status_code, 302) # redirect
        self.assertIn("success",response.url) # type: ignore
        try:
            response = testClient.post('/api/login/',{
                "username":  "alo@fsg.com",
                "password": "123w123qe",
            },content_type="application/json")
        except Exception as e:
            print(e)
            self.fail("Error")

        user = User.objects.filter(username = "alo@fsg.com").first()
        self.assertNotEqual(user,None) 
        self.assertEqual(response.status_code, 200)


    def test_InvalidCredentials(self):
        '''
            Test on a wrong credentials
        '''
        self.test_RegisterGoodData1()
        token = get_forget_token("alo@fsg.com")
        response  = testClient.get(f'/api/login/verify/{token}/',{
            },content_type="application/json")
        self.assertEqual(response.status_code, 302)
        self.assertIn("success",response.url) # type: ignore
        try:
            response = testClient.post('/api/login/',{
                "username":  "alo@fsg.com",
                "password": "12w123qe",
            },content_type="application/json")
        except Exception as e:
            print(e)
            self.fail("Error")

        self.assertNotEqual(response.status_code, 200)

    def test_NotVerified(self):
        '''
            Test on a wrong credentials
        '''
        self.test_RegisterGoodData1()
        try:
            response = testClient.post('/api/login/',{
                "username":  "alo@fsg.com",
                "password": "123w123qe", # correct credentials but not verified
            },content_type="application/json")
        except Exception as e:
            print(e)
            self.fail("Error")

        self.assertNotEqual(response.status_code, 200)
        self.assertIn("verif",response.json()["message"])
            
        

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
            print(e)
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
                "phone": "1000000000",
                "college": "IITPKD",
                "gradyear": 2024,
                "institype": "college",
                "stream": "cse"
            })

            # verifying the register
            token = get_forget_token("alo@fsg.com")
            response  = testClient.get(f'/api/login/verify/{token}/',{
                },content_type="application/json")
            self.assertEqual(response.status_code, 302)
            self.assertIn("success",response.url) # type: ignore

            response = testClient.post('/api/login/',{
                    "username":  "alo@fsg.com",
                    "password": "123w123qe",
                },content_type="application/json")

            self.token = json.loads(response.content)['token']

        except Exception as e:
            print(e)
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
            print(e)
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
            print(e)
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
            print(e)
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
            print(e)
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
            print(e)
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
            print(e)
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
            print(e)
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
            print(e)
            self.fail("Error")

        self.assertNotEqual(response.status_code, 200)
