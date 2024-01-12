from django.db import models
from django.contrib.auth import get_user_model
from rest_framework.response import Response

# Create your models here.
User=get_user_model()


class Institute(models.Model):
    institutionType = models.CharField(max_length=255, null=True)
    instiName = models.CharField(unique=True, max_length=255)
    def __str__(self):
        return self.instiName


class Profile(models.Model):
    # objects = None

    # userId=models.IntegerField()
    username = models.TextField()
    email = models.EmailField(primary_key=True)
    phone = models.CharField(max_length=25)
    instituteID = models.CharField(null=True, max_length=255)
    gradYear = models.IntegerField(default=6969)
    stream = models.TextField(null=True)


    def __str__(self):
        return self.username
    

class Event(models.Model):
    eventId=models.CharField(max_length=10,default="", primary_key=True)
    name=models.CharField(max_length=200,default="")
    fee = models.IntegerField(default=0)
    minMember = models.IntegerField(default=1)
    maxMember = models.IntegerField(default=1)


sep = '\n'
class EventTable(models.Model):
    eventId=models.CharField(max_length=10,null=True)
    emails = models.TextField(default="")
    transactionId=models.TextField(primary_key=True)
    verified=models.BooleanField()
    CACode=models.CharField(max_length=10, null=True)

    def cult_checker(self):
        email_ls = self.emails.split(sep)
        unregistered_ls =  [email for email in email_ls[1:] if not Profile.objects.filter(email=email).exists()]
        if not len(unregistered_ls):
            return False
        return Response({
                'status':401,
                'message': 'some emails are not registered',
                'unregistered_emails': unregistered_ls
            })

    @staticmethod
    def serialise_emails(emails: list[str]):
        return sep.join(emails)
    
    def get_emails(self) -> list[str]:
        return self.emails.split(sep)
