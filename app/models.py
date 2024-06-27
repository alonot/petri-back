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


class EventTable(models.Model):
    name = models.CharField(max_length=100)                 #Set the length for the name of the eventsss
    fee = models.IntegerField()  
    min_members = models.IntegerField(default=0)            #Random number for the min member 
    max_members = models.IntegerField(default=1000)         #Maximum member for the event 

    def __str__(self):
        return self.name


class Extras(models.Model):
    extra_id = models.AutoField(primary_key=True)  # Here I have set this to the autofild mode whcih will  auto-generate primary key
    price = models.IntegerField()

    def __str__(self):
        return f"Extra ID: {self.extra_id}, Price: {self.price}"

