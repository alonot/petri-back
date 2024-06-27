from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
EMAIL_SEPARATOR = '\n'


class Profile(models.Model):
    username = models.TextField()
    email = models.EmailField(default=True,primary_key=True)
    
    
class Event(models.Model):
    event_id = models.CharField(max_length=10, default="", primary_key=True)
    name = models.CharField(max_length=200, default="")
    fee = models.IntegerField(default=0)
    minMember = models.IntegerField(default=1)
    maxMember = models.IntegerField(default=1)

class EventTablePaid(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, default="1")
    emails = models.TextField(default="")
    transaction_id = models.TextField(primary_key=True)
    verified = models.BooleanField()
    CACode = models.CharField(max_length=10, null=True)

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

class EventTableFree(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, default="1")
    emails = models.TextField(default="")
    table_id = models.TextField(primary_key=True)
    verified = models.BooleanField()
    CACode = models.CharField(max_length=10, null=True)

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



