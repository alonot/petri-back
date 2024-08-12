
from django.test import TestCase
from django.test import Client
from app.models import Institute, User,Profile
from django.urls import reverse

from utils import get_forget_token

# to run use - py manage.py test app/test/


headers = {"HTTP_HOST":"petrichor.events"}
testClient= Client(

    enforce_csrf_checks=True,
    headers=headers
    )

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
        expired_token = "csk20020@gmail.com:1sdVox:rLDr9ATr2Ao5zbullIhE90SG_T2oV4LPGUXshDT4ftg"  # Simulate an expired token
        response = self.client.post(f'/api/change-password/{expired_token}/', {
            "new_password": "newpassword123"
        }, content_type="application/json")
        self.assertEqual(response.status_code, 401)


