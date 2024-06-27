from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Institute(models.Model):
    institutionType = models.CharField(max_length=255, default="",null=True)
    instiName = models.CharField(unique=True, max_length=255)
    def __str__(self):
        return self.instiName
    

class Profile(models.Model):
    username = models.TextField()
    email = models.EmailField(default=True,primary_key=True)
    phone = models.CharField(max_length=25)
    instituteID = models.CharField(null=True, max_length=255)
    gradYear = models.IntegerField(default=6969)
    stream = models.TextField(null=True)
    joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class CAProfile(models.Model):
    email = models.ForeignKey(Profile)
    CACode = models.CharField(max_length=8)
    registration = models.IntegerField(default=0)


