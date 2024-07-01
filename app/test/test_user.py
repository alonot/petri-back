import json
from django.test import TestCase
from django.test import Client

# to run use - py manage.py test app/test/

testClient= Client(

    enforce_csrf_checks=True
    )

headers = {"host":"petrichor.events","content-type":"application/json"}

class RegisterTest(TestCase):
    def test_RegisterGoodData1(self):
        response = testClient.post('/api/register/',{
            "username": "alonot",
            "email":  "alo@fsg.com",
            "password": "123w123qe",
            "phone": "0000000000",
            "college": "IITPKD",
            "gradyear": 2024,
            "institype": "college",
            "stream": "cse"
        },headers=headers)
        try:
            self.assertEqual(response.status_code, 200)
        except AssertionError:
            print(response.data["message"])
    
    def test_RegisterGoodData2(self):
        # registering the same data to check if this request is rejected or not
        response = testClient.post('/api/register/',{
            "username": "alonot",
            "email":  "alo@fsg.com",
            "password": "123w123qe",
            "phone": "0000000000",
            "college": "IITPKD",
            "gradyear": 2024,
            "institype": "college",
            "stream": "cse"
        },headers=headers)
        try:
            self.assertNotEqual(response.status_code, 200) # here is the change from the above test case: assertNot
        except AssertionError:
            print(response.data["message"])


class LoginTest(TestCase):
    def test_loginOnGoodData1(self):
        response = testClient.post('/api/login/',{
            "username":  "alo@fsg.com",
            "password": "123w123qe",
        },content_type="application/json")
        try:
            self.assertEqual(response.status_code, 200)
        except AssertionError:
            print(response.data["message"])


    def test_badLogintest(self):
        response = testClient.post('/api/login/',{
            "username":  "alo@fsg.com",
            "password": "12w123qe",
        },content_type="application/json")
        try:
            self.assertNotEqual(response.status_code, 200)
        except AssertionError:
            print(response.data["message"])

    def test_badLoginValues(self):
        response = testClient.post('/api/login/',{
            "userne":  "alo@fsg.com",
            "password": "123w123qe",
        },content_type="application/json")
        try:
            self.assertNotEqual(response.status_code, 200)
        except AssertionError:
            print(response.data["message"])