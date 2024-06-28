
import json
from django.core.mail import send_mail

from app.models import Institute, Profile,TransactionTable
from petri_ca import settings
from rest_framework.response import Response 
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from custom.authorizor import PetrichorJWTAuthentication


Refreshserializer = TokenRefreshSerializer()
PetrichorAuthenticator = PetrichorJWTAuthentication()

AUTH_EXEMPT = ['/admin/','/internal/','/api/register/','/api/login/']

# Helper functions
def error_response(message):
    return Response({"error": message}, status=500)

def success_response(message):
    return Response({"message": message}, status=200)

def ResponseWithCode(data:dict,message:str,status=200)-> Response:
    '''
        returns a response after appending status and message to its data
        as specified in readme.md
    '''
    data.update({
        "status":status,
        "message":message
    })
    return Response(data,status)


def r500(msg: str) -> Response:
    return Response({
        'status': 500,
        'message': msg
    },500)

def r200(msg: str) -> Response:
    return Response({
        'status': 200,
        'message': msg
    },200)

def send_error_mail(name, data, e):
    '''
        Sends a mail to website developers
    '''
    if "password" in data.keys():
        data["password"]=""
    send_mail(f'Website Error in: {name}',
                message= f'Exception: {e}\nData: {json.dumps(data)}',
                recipient_list=['112201024@smail.iitpkd.ac.in','112201020@smail.iitpkd.ac.in'],
                from_email=settings.EMAIL_HOST_USER)

def get_profile_data(user_profile:Profile):
    '''
        returns the profile data as a dict
        NOTE- Any None handled error raised by this functions is/must be handled by the caller function.
    '''
    user_data = {}
    user_data['username'] = user_profile.username
    user_data['phone'] = user_profile.phone
    user_data['stream'] = user_profile.stream
    user_data['gradYear'] = user_profile.gradYear
    int_id = user_profile.instituteID
    try:
        institute = Institute.objects.get(pk = int_id)
        institute = institute.instiName
    except Institute.DoesNotExist:
        institute = ""     
    user_data['institute'] = institute
    return user_data
    
def get_profile_events(user_email:str):
    '''
        returns the eventIds of events in which this user has registered
        NOTE- Any None handled error raised by this functions is/must be handled by the caller function.
    '''
    events=[]
    # to be Fixed
    eventEntries=TransactionTable.objects.all() # type: ignore
    for eventEntry in eventEntries:
        if user_email in eventEntry.get_participants():
            events.append({
                "eventId":eventEntry.event_id,
                "status":eventEntry.verified})
    return events


def method_not_allowed():
    return ResponseWithCode({},"Method Not Allowed.Use Post")





    