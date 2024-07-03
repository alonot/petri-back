
import json
from django.core.mail import send_mail
from django.conf import settings
from django.core.signing import TimestampSigner,SignatureExpired,BadSignature

from django.contrib.auth.models import User
from app.models import Event, Institute, Profile,TransactionTable
from petri_ca import settings
from rest_framework.response import Response 
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from custom.authorizor import PetrichorJWTAuthentication


Refreshserializer = TokenRefreshSerializer()
PetrichorAuthenticator = PetrichorJWTAuthentication()
PetrichroSigner = TimestampSigner(salt=settings.FORGET_SALT_KEY)

AUTH_EXEMPT = ['/admin/','/internal/','/api/register/','/api/login/','/api/forget-password/','/api/change-password']

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
    user_data['email'] = user_profile.user.get_username()
    user_data['phone'] = user_profile.phone
    user_data['stream'] = user_profile.stream
    user_data['gradYear'] = user_profile.gradYear    
    user_data['institute'] = user_profile.instituteID.instiName
    return user_data
    
def get_profile_events(user:User):
    '''
        returns the eventIds of events in which this user has registered
        NOTE- Any None handled error raised by this functions is/must be handled by the caller function.
    '''
    events = []
    user_registration = user.userregistrations
    trIds=TransactionTable.deserialize_emails(user_registration.transactionIds)
    for trId in trIds:
        transaction = TransactionTable.objects.filter(transaction_id = trId).first()
        if transaction is not None:
            events.append({
                "eventId": transaction.event_id,
                "verified": transaction.verified
            })

    return events


def method_not_allowed():
    return ResponseWithCode({},"Method Not Allowed.Use Post")


def send_forget_password_mail(email , token):
    subject = 'Your forget password link'
    message = f'Hi , Click on the link to reset your password http://127.0.0.1:8000/api/change-password/{token}/'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject , message , email_from , recipient_list)
    return True


def send_forget_password_mail(email , token):
    subject = 'Your forget password link'
    message = f'Hi , Click on the link to reset your password http://127.0.0.1:8000/api/change-password/{token}/'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject , message , email_from , recipient_list)
    return True

def send_delete_transaction_mail(email , event_name):
    subject = 'Transaction not verified!'
    message = f'Hi , Your transaction_id is not verified for the event {event_name}. Kindly contact admin of Petrichor '
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject , message ,email_from , recipient_list)
    return True

def get_forget_token(email):
    return PetrichroSigner.sign(email)

def get_email_from_token(token:str):
    token = PetrichroSigner.unsign(token,max_age=settings.FORGET_TOKEN_MAX_AGE)
    return token




    