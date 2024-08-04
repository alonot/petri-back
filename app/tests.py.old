import json
import unittest
from django.test import TestCase
from django.test import Client
from app.models import Institute, User,Profile,CAProfile,UserRegistrations
from django.urls import reverse

# to run use - py manage.py test app/test/

'''
Login 
Register
Forget Password
change Password
auth
CA/Create
Events/apply/
'''


# headers = {
#             'HTTP_HOST': 'example.com',
#             'HTTP_ORIGIN': 'https://example.com',
#         }
headers = {"HTTP_HOST":"petrichor.events"}
testClient= Client(

    enforce_csrf_checks=True,
    headers=headers
    )


class RegisterTest(TestCase):

    register_url = reverse('signup')
    def test_RegisterGoodData1(self):
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
        self.assertEqual(response.status_code, 200)
        profile = Profile.objects.filter(user = user).first()
        self.assertNotEqual(profile,None)
        user_regs = UserRegistrations.objects.filter(user = user).first()
        self.assertNotEqual(user_regs,None)
        
    def test_RegisterGoodData2(self):
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

        self.assertEqual(response.status_code, 200) # here is the change from the above test case: assertNot
        user = User.objects.filter(username = "alonot@fsg.com").first()
        self.assertNotEqual(user,None)
        profile = Profile.objects.filter(user = user).first()
        self.assertNotEqual(profile,None)
        user_regs = UserRegistrations.objects.filter(user = user).first()
        self.assertNotEqual(user_regs,None)        

    def test_RegisterWrongEmail(self):
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
        try:
            response = testClient.post('/api/login/',{
                "userne":  "alo@fsg.com",
                "password": "123w123qe",
            },content_type="application/json")
            
        except Exception as e:
            self.fail("Error")

        self.assertNotEqual(response.status_code, 200)

    ### Login Test ends

class ForgetTest(TestCase):

    def setUp(self) -> None:
        self.inst = Institute.objects.create(institutionType = "college",
                                            instiName ="IITPKD" )
        user= User(username = "csk20020@gmail.com" )

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
        return super().setUp()
        
    def test_good(self):
        try:
            response = testClient.post('/api/forget-password/',{
                "email":  "csk20020@gmail.com"
            },content_type="application/json")
            
        except Exception as e:
            self.fail("Error")

        self.assertEqual(response.status_code, 200)

    def test_bad(self):
        try:
            response = testClient.post('/api/forget-password/',{
                "email":  "csk200200@gmail.com"
            },content_type="application/json")
            
        except Exception as e:
            self.fail("Error")

        self.assertEqual(response.status_code, 404)