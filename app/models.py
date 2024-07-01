import datetime
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
    user = models.OneToOneField(User,primary_key=True,on_delete=models.CASCADE)
    phone = models.CharField(max_length=25)
    instituteID = models.ForeignKey(Institute,on_delete=models.SET_NULL,null=True, max_length=255)
    gradYear = models.IntegerField(default=6969)
    stream = models.TextField(null=True)
    joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class CAProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    CACode = models.CharField(max_length=8,unique=True)
    registration = models.IntegerField(default=0)

class UserRegistrations(models.Model):
    user = models.OneToOneField(User,on_delete=models.SET_NULL,null=True)
    email = models.EmailField(primary_key=True)  # use Transaction table's static functions to serialize or deserialize
    transactionIds = models.TextField(default="")

class Extras(models.Model):
    extra_id = models.AutoField(primary_key=True)  # Here I have set this to the autofild mode whcih will  auto-generate primary key
    price = models.IntegerField()

    def __str__(self):
        return f"Extra ID: {self.extra_id}, Price: {self.price}"
       
class Event(models.Model):
    event_id = models.CharField(max_length=10, default="", primary_key=True)
    name = models.CharField(max_length=200, default="")
    fee = models.IntegerField(default=0)
    minMember = models.IntegerField(default=1)
    maxMember = models.IntegerField(default=1)
    isTeam = models.BooleanField(default = False)
    
EMAIL_SEPARATOR = '\n'

class TransactionTable(models.Model):
    event_id = models.ForeignKey(Event, on_delete=models.PROTECT,null=True)
    user_id = models.ForeignKey(User,on_delete=models.PROTECT,null=True)
    participants = models.TextField()
    transaction_id = models.TextField(primary_key=True)
    verified = models.BooleanField()
    CACode = models.ForeignKey(CAProfile,on_delete=models.SET_NULL,max_length=10, null=True)

    def get_participants(self):
        return TransactionTable.deserialize_emails(self.participants)

    @staticmethod
    def serialise_emails(emails: list[str]) -> str:
        """
        Serializes a list of emails into a single string separated by EMAIL_SEPARATOR.
        """
        return EMAIL_SEPARATOR.join(emails)

    @staticmethod
    def deserialize_emails(emails_str: str) -> list[str]:
        """
        Deserializes a single string of emails separated by EMAIL_SEPARATOR into a list of emails.
        """
        return emails_str.split(EMAIL_SEPARATOR)





