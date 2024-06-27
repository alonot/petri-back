from django.conf import settings
from django.contrib.auth import authenticate,login,logout
from rest_framework.request import Empty
from django.contrib.auth.models import User
from rest_framework.decorators  import api_view
from rest_framework.response import Response 
from django.http import HttpRequest
from django.core.mail import send_mail

from petri_ca.utils import get_profile_data, get_user_from_session, send_error_mail
from .models import Institute, Profile
import datetime
from django.db.utils import IntegrityError
import inspect
from resp import r500, r200


@api_view(['POST'])
def signup(request):
    '''
        Registers a User to the database
    '''
    if request.method != 'POST':
        return Response({
            "status":302,
            "message":"Method Not Allowed.Use POST"
        },302)

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
    '''
    if request.method != "POST":
        return Response({
            "status":302,
            "message":"Method Not Allowed.Use POST"
        },302)
    
    try:
        if request.data is None:
            print("No data")
            return Response({
                'success' : False,
                'message' : "Data not received"
            },status=500)

        email = request.data['email'].strip()
        password = request.data['password']

        # authenticates the user
        user = authenticate(username = email, password = password) 

        if user is None:
            # Credentials given are invalid
            return Response({
                'success' : False,
                'message' : "Invalid Credentials"
            },status=200)
        
        else:
            # logs the user. Creates an entry in Sessions table
            login(request,user)
            try:
                user_profile = Profile.objects.get(email = email)
            except Profile.DoesNotExist:
                user.delete()
                return Response({
                    "status":400,
                    "message":"User authenticated but its Profile Doesn't Exists.\
                    User has been deleted.Please create a new Profile."
                },400)
            
            res =  Response({
                'success' : True,
                'user': user_profile.username
            },200)

            max_age = 60 * 60 * 24 * 15
            expiryDate= datetime.datetime.strftime(
                datetime.datetime.utcnow() +datetime.timedelta(seconds=max_age),
                "%a, %d-%b-%Y %H:%M:%S GMT",
            )

            res.set_cookie('session_token',
                            value=request.session.session_key,
                            max_age=max_age,
                            secure=True,
                            domain=request.get_host().split(':')[0],
                            expires=expiryDate,
                            httponly=True,
                            samesite='None',
                            )
            # print("Logged")
            return res
    except Exception as e:
        send_error_mail(inspect.stack()[0][3],request.data,e)
        return r500("Something went wrong")
    
    

@api_view(['POST'])
def logout_user(request:HttpRequest):
    '''
        Logouts a user
    '''
    if request.method != 'POST':
        return Response({
            "status":302,
            "message":"Method Not Allowed.Use POST"
        },302)
    
    try:
        # deletes the entry from Session table
        logout(request)
        token = request.COOKIES.get('session_token')
        try:
            session = Session.objects.get(session_key= token)
            session.delete()
        except Session.DoesNotExist as e:
            pass

        res = Response({
            'success':True,
            'message':'Done'
        },200)

        
        res.delete_cookie('session_token',domain=request.get_host().split(':')[0])
        return res
    except Exception as e:
        # any exception, the logout function does not throws 
        # error if session not present.
        send_error_mail(inspect.stack()[0][3],request.data,e)
        return Response({
            'success':False,
            'message':'some error occured. Reported to our developers'
        },400)
    
@api_view(['POST'])
def authenticated(request:HttpRequest):
    '''
        Authenticates, send the user info if getUser = True in the data body
        send the user events if getEvents = True in the data body
    '''
    if request.method != 'POST':
        return Response({
            "status":301
        },301)
    
    try:
        getUser = request.data["getUser"]
        getEvent = request.data["getEvents"]
    except Exception as e:
        return Response({
            'success':False,
            'message':'Data not sent as Required'
        },400)

    try:
        user = get_user_from_session(request)
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
                'message':'No'
            },200)  
    
    except Exception as e:
        send_error_mail(inspect.stack()[0][3],request.data,e)
        return Response({
            'success':False,
            'message':'some error occured. Reported to our developers'
        },400)



# @login_required # limits the calls to this function ig
@api_view(['POST'])
def get_event_data(request):
    try:
        data=request.data

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
        print("grievance email sent")
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