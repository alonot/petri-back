from django.db import models
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from functools import lru_cache

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
    eventId=models.CharField(max_length=10,null=True, db_index=True)
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

events = {'CF01': {'name': 'BRUSHED BRILLIANCE', 'fee': 49.0, 'maxMember': 2, 'minMember': 2}, 'CP02': {'name': 'Meta Monologues', 'fee': 99.0, 'maxMember': 1, 'minMember': 1}, 'CF05': {'name': 'Waste to wow', 'fee': 49.0, 'maxMember': 2, 'minMember': 1}, 'CF12': {'name': 'DROP THE BEAT', 'fee': 149.0, 'maxMember': 1, 'minMember': 1}, 'CF13': {'name': 'Pixel Palette', 'fee': 0.0, 'maxMember': 1, 'minMember': 1}, 'TF00': {'name': 'Treasure Hunt', 'fee': 0.0, 'maxMember': 3, 'minMember': 1}, 'TF01': {'name': 'Simulate To The Moon', 'fee': 0.0, 'maxMember': 3, 'minMember': 2}, 'TF03': {'name': 'AlgoTrek', 'fee': 0.0, 'maxMember': 1, 'minMember': 1}, 'TF04': {'name': 'Drone Dash', 'fee': 79.0, 'maxMember': 6, 'minMember': 1}, 'TF05': {'name': 'Game Forge', 'fee': 0.0, 'maxMember': 4, 'minMember': 1}, 'TF06': {'name': 'Kampan ', 'fee': 79.0, 'maxMember': 2, 'minMember': 1}, 'TF07': {'name': 'Trade-a-thon 2.0', 'fee': 0.0, 'maxMember': 1, 'minMember': 1}, 'TF08': {'name': 'WebMosiac', 'fee': 0.0, 'maxMember': 1, 'minMember': 1}, 'TF11': {'name': 'Hover hero challenge', 'fee': 79.0, 'maxMember': 3, 'minMember': 1}, 'TF13': {'name': 'Robowar', 'fee': 79.0, 'maxMember': 6, 'minMember': 4}, 'WP00': {'name': 'AI Workshop', 'fee': 1299.0, 'maxMember': 1, 'minMember': 1}, 'WP01': {'name': 'Robotics', 'fee': 1299.0, 'maxMember': 1, 'minMember': 1}, 'WP02': {'name': 'Product Management', 'fee': 1199.0, 'maxMember': 1, 'minMember': 1}, 'CP00': {'name': 'F3: Fireless Food Fiesta', 'fee': 49.0, 'maxMember': 3, 'minMember': 1}, 'TF10': {'name': 'Eggstravaganza Drop Challenge', 'fee': 79.0, 'maxMember': 2, 'minMember': 1}, 'CP09': {'name': 'KATHA - where words become world', 'fee': 0.0, 'maxMember': 1, 'minMember': 1}, 'CF11': {'name': 'KAVYA - weaving verses, crafting dreams', 'fee': 0.0, 'maxMember': 1, 'minMember': 1}, 'WP03': {'name': 'Reinforcement Learning', 'fee': 1199.0, 'maxMember': 1, 'minMember': 1}, 'CF15': {'name': "Click n' Roll: A Showcase of Frames", 'fee': 0.0, 'maxMember': 2, 'minMember': 1}, 'CF16': {'name': 'Enigma - The General Quiz', 'fee': 49.0, 'maxMember': 1, 'minMember': 1}, 'CF18': {'name': 'Sportify - The SpEnt Quiz', 'fee': 49.0, 'maxMember': 1, 'minMember': 1}, 'WP04': {'name': 'Startup and Entrepreneurship', 'fee': 1199.0, 'maxMember': 1, 'minMember': 1}, 'WP05': {'name': 'Measurement Principles and Uncertainty Analysis', 'fee': 1199.0, 'maxMember': 1, 'minMember': 1}, 'WP06': {'name': 'Competitive Programming', 'fee': 1299.0, 'maxMember': 1, 'minMember': 1}, 'CP06': {'name': 'Dynamic Duet', 'fee': 0.0, 'maxMember': 2, 'minMember': 1}, 'CP03': {'name': 'Voicestra', 'fee': 0.0, 'maxMember': 1, 'minMember': 1}, 'CP17': {'name': 'Bandwagon', 'fee': 0.0, 'maxMember': 20, 'minMember': 4}, 'CP14': {'name': 'Groove Mania', 'fee': 0.0, 'maxMember': 1, 'minMember': 1}, 'CP07': {'name': 'ChoreoClash', 'fee': 0.0, 'maxMember': 25, 'minMember': 3}, 'CF04': {'name': 'Fashion Frenzy', 'fee': 0.0, 'maxMember': 15, 'minMember': 10}, 'TF14': {'name': 'ChipCraft', 'fee': 0.0, 'maxMember': 3, 'minMember': 1}, 'TF09': {'name': 'Labyrinth 2.0', 'fee': 79.0, 'maxMember': 4, 'minMember': 1}, 'TF12': {'name': 'Quizzanaire - School Quiz', 'fee': 0.0, 'maxMember': 2, 'minMember': 1}, 'CP10': {'name': 'CODM: Clash of Champions', 'fee': 49.0, 'maxMember': 5, 'minMember': 1}, 'CF08': {'name': 'BGMI Showdown', 'fee': 49.0, 'maxMember': 4, 'minMember': 1}, 'CF19': {'name': 'Valorant', 'fee': 49.0, 'maxMember': 5, 'minMember': 1}, 'TF02': {'name': 'ClenchBot', 'fee': 79.0, 'maxMember': 3, 'minMember': 2}}
@lru_cache()
def get_event_from_id(id):
    return events[id]
    # return Event.objects.get(eventId=id)

@lru_cache()
def get_eventtable_from_id(id):
    return EventTable.objects.get(transactionId=id)

@lru_cache(maxsize=1024)
def get_profile_from_email(email):
    return Profile.objects.get(email=email)