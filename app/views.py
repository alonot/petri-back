from collections import OrderedDict
import time
from django.conf import settings
from rest_framework.request import Empty
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.decorators  import api_view
from rest_framework.exceptions import AuthenticationFailed

from rest_framework.response import Response 
from django.http import HttpRequest
from django.core.mail import send_mail

from utils import error_response, get_profile_data, send_error_mail, success_response, method_not_allowed,auth  
from .models import Institute, Profile, TransactionTable,Event
from django.db.utils import IntegrityError
import inspect
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from resp import r500, r200


TokenSerializer = TokenObtainPairSerializer()


@api_view(['POST'])
def signup(request):
    '''
        Registers a User to the database
    '''
    if request.method != 'POST':
        return method_not_allowed()

    try:
        # Retreiving all data
        data = request.data
        username = data['username'].strip()
        email = data['email']
        pass1 = data['password']
        phone = data['phone']
        insti_name = data['college']
        gradyear = data['gradyear']
        insti_type = data['institype']
        stream = data['stream']
        
        # Checking if User already exists
        if User.objects.filter(email=email).first():
            return Response({
                'status': 404,
                "registered": False,
                'message': "Email already registered",
                "username": username
            })


        else:
            try:
                new_user = User(username=email)
                new_user.set_password(pass1)
                new_user.is_active = True
                
            except IntegrityError as e: # Email alreeady exists
                # send_error_mail(inspect.stack()[0][3], request.data, e)  # Leave this commented otherwise every wrong login will send an error mail
                return r500('Email already exists')
            
            try:
                # creates or gets the InstituteId
                if insti_type != "neither":
                    institute = Institute.objects.get_or_create(instiName=insti_name, institutionType=insti_type)[0]
                    # institute = Institute.objects.get(instiName=instituteID)
                else:
                    institute = Institute.objects.get_or_create(instiName='NoInsti', institutionType=insti_type)[0]
                
                institute.save() # Kept for safety {create will automatically save}
                
                user_profile = Profile(username=username, 
                                    email=email,
                                    phone=phone,
                                    instituteID=institute.pk,
                                    gradYear=gradyear,
                                    stream=stream)
                
                # saving the profile and user. If any of above steps fails the User/ Profile will not be created
                user_profile.save()
                new_user.save()

                return Response({
                    'status': 200,
                    "registered": True,
                    'message': "Success",
                    "username": username
                })
            
            except IntegrityError as e:
                # send_error_mail(inspect.stack()[0][3], request.data, e)  # Leave this commented otherwise every wrong login will send an error mail

                return r500("User already exists. Try something different.")
            except Exception as e:
                send_error_mail(inspect.stack()[0][3], request.data, e)  
                r500("Something failed")

    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e)
        return r500("Something Bad Happened")



@api_view(['POST'])
def login_user(request: HttpRequest):
    '''
        Logs the User into the website
        The access token expires in 5mins. So the frontend must store these 
        two values and send it in every request(We are trying to read it from the cookie itself).
        In every request except /register/ and /login/ , Following things will be constant-
        {
            loggedIn: True / False  - If False, frontend must direct user to login first
            refreshed: (if the access token is refreshed) True- "In this case frontend must update the access cookie." 
                                                        : False-"No action needed from frontend"
            access: (if refreshed) ? The refreshed token : None;
        }


    '''
    if request.method != "POST":
        return method_not_allowed()
    
    try:
        if request.data is None:
            
            return Response({
                'success' : False,
                'message' : "Data not received"
            },status=500)
        
        try:
            # authenticates the user
            token = TokenSerializer.validate((OrderedDict)(request.data))
        except AuthenticationFailed as e:
            # Credentials given are invalid
            return Response({
                'success' : False,
                'message' : "Invalid Credentials"
            },status=200)
        user = authenticate(username = request.data['username'], password =  request.data['password'])
        try:
            user_profile = Profile.objects.get(email = user.get_username())
        except Profile.DoesNotExist:
            user.delete()
            return Response({
                "status":400,
                "message":"User authenticated but its Profile Doesn't Exists.\
                User has been deleted.Please create a new Profile."
            },400)
        
        return Response({
            'success' : True,
            'token' : token,
            'user': user_profile.username
        },200)
    except Exception as e:
        print(e)
        # send_error_mail(inspect.stack()[0][3],request.data,e)
        return r500("Something went wrong")
    
    
@api_view(['POST'])
def authenticated(request:HttpRequest):
    '''
        Authenticates, send the user info if getUser = True in the data body
        send the user events if getEvents = True in the data body
    '''
    if request.method != 'POST':
        return method_not_allowed()
    
    response_data = auth(request)

    try:
        getUser = request.data["getUser"]
        getEvent = request.data["getEvents"]
    except Exception as e:
        return Response({
            'success':False,
            'message':'Data not sent as Required'
        },400)

    try:
        user = request.user
        if user is not None:
            user_profile = Profile.objects.get(email = user.username)
            user_data = {}
            user_events = []
            if getUser == True:
                user_data = get_profile_data(user_profile)
            if getEvent == True:
                user_events = get_event_data(user.get_username())

            return Response({
                'success':True,
                'message':'Yes',
                'username':user_profile.username,
                'user_data': user_data,
                'user_events':user_events
            },200)
    
        else:
            
            return Response({
                'success':False,
                'message':'Not logged in'
            },200)  
    
    except Exception as e:
        send_error_mail(inspect.stack()[0][3],request.data,e)
        return r500("some error occured. Reported to our developers")



# @login_required # limits the calls to this function ig
@api_view(['POST'])
def get_event_data(request):
    try:
        data=request.data

        return r200("Here")

        if data is None:
            return r500("invalid form")
        try:
            event_id = data["id"]
        except KeyError as e:
            return r500("Send an eventID")
        
        try:
            event = Event.objects.get(eventId = event_id)
        except:
            return r500(f"Invalid Event ID = {event_id}")
        
        return Response({
            "name": event['name'],
            "fee": event['fee'],
            "minMemeber": event['minMember'],
            "maxMemeber": event['maxMember']
        })
    except Exception as e:
            send_error_mail(inspect.stack()[0][3], request.data, e)
            return r500("Something Bad Happened")


@api_view(['POST'])
def send_grievance(request: HttpRequest):
    try:
        data = request.data
        if isinstance(data, Empty) or data is None:
            return r500("Invalid Form")
        
        name = data['name'] # type: ignore
        email = data['email'] # type: ignore
        content = data['content'] # type: ignore

        send_mail(
            subject=f"WEBSITE MAIL: Grievance from '{name}'",
            message=f"From {name} ({email}).\n\n{content}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=["112201020@smail.iitpkd.ac.in","112201024@smail.iitpkd.ac.in", "petrichor@iitpkd.ac.in"]
        )
        # print("grievance email sent")
        return Response({
                'status':200,
                'success': True
            })

    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e)
        return Response({
                'status':400,
                'success': False
            })





@api_view(['POST'])
def apply_event_paid(request: HttpRequest):
    try:
        data = request.data
        if not data:
            return error_response("Invalid form")
        

        try:
            user_id = data['user_id']
            participants = data['participants']
            event_id = data['eventId'].strip()
            transactionId = data['transactionID'].strip()
            CAcode = data['CAcode'].strip()
        except KeyError as e:
            return error_response("Missing required fields: participants, eventId, and transactionId")
        
        try:
            # Check if participants' emails are from IIT Palakkad
            verified=False
            if all(map(lambda x: x.endswith("smail.iitpkd.ac.in"), participants)): 
                verified=True
                transactionId=f"IIT Palakkad Student+{time.time()}"

            # Check for duplicate transaction ID
            if TransactionTable.objects.filter(transactionId=transactionId).exists():
                return error_response("Duplicate transaction ID used for another event")



            # Create a new event record
            eventpaidTableObject = TransactionTable(
                event_id=event_id,
                user_id = user_id,
                participants= TransactionTable.serialise_emails(participants),
                transaction_id=transactionId,
                verified=verified,
                CACode=CAcode
            )


            eventpaidTableObject.save()
            return success_response("Event applied successfully")
        except Exception as e:
            return error_response("Unexpected error occurred while processing the event application")
    except Exception as e:
        return error_response("Unexpected error occurred")

    

@api_view(['POST'])
def apply_event_free(request: HttpRequest):
    data = request.data
    if not data:
        return error_response("Invalid form")

    try:

        user_id = data['user_id']
        participants = data['participants']
        event_id = data['eventId'].strip()

    except KeyError as e:
        return error_response("Missing required fields: participants and eventId")
    
    try:
        transaction_id = f"{user_id}+free+{time.time()}"

    

        # Create a new event record
        eventfreeTableObject = TransactionTable(
        event_id=event_id,
        user_id = user_id,
        participants=TransactionTable.serialise_emails(participants),
        transaction_id = transaction_id,
        verified=True
        )

        eventfreeTableObject.save()
        return success_response("Event applied successfully")

    except Exception as e:
        return error_response(f"Something went wrong: {str(e)}")
    


