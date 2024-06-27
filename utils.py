import inspect
import json
from django.contrib.sessions.models import Session
from django.core.mail import send_mail

from petri_ca.app.models import Institute, Profile, User
from petri_ca.petri_ca import settings


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
    
def get_user_from_session(request):
    '''
        gets a user from the request
        returns none if not logged In
    '''
    try:
        token = request.COOKIES.get('session_token')
    except KeyError:
        return None
    try:
        session = Session.objects.get(session_key= token)
        session_data = session.get_decoded()    
        uid = session_data.get('_auth_user_id')
        user = User.objects.get(id=uid)
    except Session.DoesNotExist:
        return None
    except User.DoesNotExist:
        # User doesn't exists so delete this Entry from session Table
        
        return None
    return user

def get_profile_data(user_profile:Profile):
    try:
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
    except Exception as e:
        send_error_mail(inspect.stack()[0][3], user_profile, e)
        return {}
    
def get_profile_events(user_email:str):
    try:
        events=[]
        # to be Fixed
        eventEntries=EventTable.objects.all() # type: ignore
        for eventEntry in eventEntries:
            if user_email in eventEntry.get_emails():
                events.append({
                    "eventId":eventEntry.eventId,
                    "status":eventEntry.verified})
        return events
    except Exception as e:
        send_error_mail(inspect.stack()[0][3], user_email, e)
        return []