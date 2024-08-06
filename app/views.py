import time
from django.conf import settings
from django.forms import ValidationError
from rest_framework.request import Empty, Request
from django.contrib.auth.models import User
from django.core.validators import validate_email
from rest_framework.decorators  import api_view
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.exceptions import AuthenticationFailed

from rest_framework.response import Response 
from django.http import HttpRequest
from django.core.mail import send_mail
from django.contrib.auth.models import AnonymousUser
from django.core.signing import SignatureExpired,BadSignature

from utils import ResponseWithCode, get_email_from_token, get_forget_token, get_profile_data, get_profile_events,\
r500,send_error_mail, method_not_allowed , send_forget_password_mail,error_response
from .models import EMAIL_SEPARATOR, Institute, Profile, TransactionTable,Event,CAProfile,UserRegistrations
from django.db.utils import IntegrityError
import inspect
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.core.mail import send_mail


TokenSerializer = TokenObtainPairSerializer()

def validateSignUpData(data):
    username:str = data['username'].strip()
    email = data['email']
    pass1 = data['password']
    phone:str = data['phone']
    insti_name = data['college']
    gradyear = data['gradyear']
    insti_type = data['institype']
    stream = data['stream']
    valid = False
    message = ""
    try:
        validate_email(email)
    except ValidationError:
        message = "Invalid Email provided"
    else:
        if username.__len__() == 0 or username.__len__() > 9:
            message = "Wrong Username format"
        elif  email.__len__() == 0:
            message = "Email cannot be empty"
        elif isinstance(phone,str) and not phone.isdigit():
            message = "Wrong Phone Format"
        elif phone.__len__() != 10:
            message = "Phone Number must be of length : 10"
        elif pass1.__len__() < 8:
            message = "Password must atleast of 8 characters"
        else:
            if (insti_type == ""):
                message = "Institute type is required"
            elif insti_type != "neither":
                if insti_name == "":
                    message == "Institute Name is required"
                elif (isinstance(gradyear,str) and (not gradyear.isdigit()  or gradyear == "")):
                    message = "GradYear required"
                elif insti_type == "college" and stream == "":
                    message = "Please specify your degree"
                else : 
                    valid = True
            else:
                valid = True
    
    return valid,message


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
        if (not data):
            return r500("Data not provided")

        
        try:
            valid,message = validateSignUpData(data)
            if not valid:
                return r500(message)
        except ValueError:
            return r500("Invalid data provided")

        

        username = data['username'].strip()
        email = data['email']
        pass1 = data['password']
        phone = data['phone']
        insti_name = data['college']
        gradyear = data['gradyear']
        insti_type = data['institype']
        stream = data['stream']
        # Checking if User already exists
        try:
            User.objects.get(username=email)
            return ResponseWithCode({
                "success":False,
                "username":username
            },
            "Email already registered",400)
        except User.DoesNotExist:
            try:
                new_user = User(username=email,email = email)
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
                
                new_user.save()
                user_profile = Profile(username=username, 
                                    user=new_user,
                                    phone=phone,
                                    instituteID=institute,
                                    gradYear=gradyear,
                                    stream=stream)
                
                # saving the profile and user. If any of above steps fails the User/ Profile will not be created
                user_profile.save()

                user_registration = UserRegistrations.objects.filter(email = email).first()
                if user_registration is not None:
                    user_registration.user = new_user
                    user_registration.save()
                else:
                    UserRegistrations.objects.create(
                        user = new_user,
                        email = email,
                        transactionIds =""
                    )
                
                print("User Created")
                return ResponseWithCode({
                    "success":True,
                    "username":username
                },"success")
            
            except IntegrityError as e:
                send_error_mail(inspect.stack()[0][3], request.data, e)  # Leave this commented otherwise every wrong login will send an error mail
                new_user.delete()
                return r500("User already exists. Try something different.")
            except Exception as e:
                new_user.delete()
                send_error_mail(inspect.stack()[0][3], request.data, e)  
                r500("Something failed")

    except KeyError as e:
        return r500("Data received does not contains all the required fields")


    except Exception as e:
        print(e)
        # send_error_mail(inspect.stack()[0][3], request.data, e)
        return r500("Something Bad Happened")



@api_view(['POST'])
def ForgetPassword(request:HttpRequest):
    '''
        Reset Password

    '''
    if request.method != 'POST':
        return method_not_allowed()
    try:
        data:dict = request.data
        if data.__contains__('email'):
            email = data['email'].strip()
        else:
            return r500("Email not received")



        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            return Response({
                'status': 404,
                'message': "No User found with this Email",
                "username": None
            },404)
        
        profile:Profile = user.profile
        
        token = get_forget_token(email)# Generates Token, It lasts for 5 mins
        
        send_forget_password_mail(email , token,profile.username)

        return ResponseWithCode({
            "success":True
        },"An email is sent")

    except Exception as e:
        print(e)
        send_error_mail(inspect.stack()[0][3], request.data, e)
        return r500("Something Bad Happened")
    


@api_view(['POST'])
def ChangePassword(request:HttpRequest , token:str):
    '''
        Changes Password
    '''
    if request.method != 'POST':
        return method_not_allowed()
    
    try:
       
        data = request.data 
        if data.__contains__('new_password'):
            new_password = data['new_password']
        else:
            return r500("Passwords not received")
        
        try:
            email = get_email_from_token(token)
        except SignatureExpired:
            return r500("Token expired")
        except BadSignature:
            return r500("Invalid Token")

        user_obj = User.objects.get(username = email)
        user_obj.set_password(new_password)
        user_obj.save()
        return ResponseWithCode({
            "success":True,
        },"Password changed successfully",200)
    
    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e)
        return Response({
                'status': 404,
                'message': "Invalid URL",
                "username": None
            },404)



class LoginTokenSerializer(TokenObtainPairSerializer):
    '''
        Logs the User into the website
        The access token expires in 5mins. So the frontend must store these 
        two values and send it in every request(We are trying to read it from the cookie itself).
        In every request except /register/ and /login/ , Following things will be constant
        {
            loggedIn: True / False  - If False, frontend must direct user to login first
            refreshed: (if the access token is refreshed) True- "In this case frontend must update the access cookie." 
                                                        : False-"No action needed from frontend"
            access: (if refreshed) ? The refreshed token : None;
        }

        NOTE FOR DEVS: This function must not use ResponseWithCode() 
        as this function just returns the data
    '''
    
    def validate(self, attrs):
        try:
            data = super().validate(attrs)
            user = self.user
            if hasattr(user,'profile'):
                user_profile:Profile = user.profile
            else:
                user.delete()
                return {
                    "status":400,
                    "success":False,
                    "message":"User authenticated but its Profile Doesn't Exists.\
                    User has been deleted.Please create a new Profile."
                }
            
            return {
                "status": 200,
                'success' : True,
                'token' : data['access'],
                'username': user_profile.username,
                "message":"Logged in"
            }

        except AuthenticationFailed:
            return {
                "status":400,
                "success":False,
                "token":None,
                "username":None,
                "message":"Invalid Credentials"
            }
        # We will not handle any other Exception here, like except Exception as e,
        # Let any other exception raised by super.validate() be handled by django itself
   
class LoginUser(TokenObtainPairView):
    '''
        This is a serializer class. 
        Since this is a class in which only post method is defined hence other requests will be automatically refused
        by django. 
    '''
    def post(self, request: Request, *args, **kwargs) -> Response:
        from django.middleware.csrf import get_token
        # print(get_token(request))
        if (not request.data.__contains__("username")):
            return ResponseWithCode({
                "success":False,
            },"Username Not given",400)
        
        if (not request.data.__contains__("password")):
            return ResponseWithCode({
                "success":False,
            },"Password Not given",400)

        result = super().post(request, *args, **kwargs)
        result.status_code = (result.data['status'])
        return result

    serializer_class = LoginTokenSerializer
    
    
@api_view(['POST'])
def authenticated(request:HttpRequest):
    '''
        Authenticates, send the user info if getUser = True in the data body
        send the user events if getEvents = True in the data body
    '''
    if request.method != 'POST':
        return method_not_allowed()

    data = request.data
    if data.__contains__('getUser') and data.__contains__('getEvents'):
        getUser = request.data["getUser"]
        getEvent = request.data["getEvents"]
    else:
        return ResponseWithCode({"success":False},'Data not sent as Required',500)

    try:
        user = request.user
        if type(user) is not AnonymousUser:
            user_profile:Profile = user.profile
            user_data = {}
            user_events = []
            if getUser == True:
                user_data = get_profile_data(user_profile)
                ca_details = {
                    "CACode":"",
                    "registrations":-1
                }
                if hasattr(user,'caprofile'):
                    ca_details = {
                        "CACode":user.caprofile.CACode,
                        "registrations":user.caprofile.registration
                    }

                user_data.update(ca_details)

            if getEvent == True:
                user_events = get_profile_events(user)

            return ResponseWithCode({
                'success':True,
                'username':user_profile.username,
                'user_data': user_data,
                'user_events':user_events,
            },"Yes")
        else:
            # send_error_mail(inspect.stack()[0][3],request.data,e)

            return ResponseWithCode({
                "success":False,
            },"Login completed but User is Anonymous",500)
    
    except Exception as e:
        # send_error_mail(inspect.stack()[0][3],request.data,e)
        print(e)
        return r500("some error occured. Reported to our developers")



# @login_required # limits the calls to this function ig
@api_view(['POST'])
def get_event_data(request):

    if request.method != 'POST':
        return method_not_allowed()

    try:
        data=request.data

        if data is None:
            return r500("invalid form")
        
        if data.__contains__('id'):
            event_id = data["id"]
        else:
            return r500("Send an eventID")
        
        try:
            event = Event.objects.get(eventId = event_id)
        except Event.DoesNotExist:
            return r500(f"Invalid Event ID = {event_id}")
        
        return ResponseWithCode({
            "success":True,
            "name": event['name'],
            "fee": event['fee'],
            "minMemeber": event['minMember'],
            "maxMemeber": event['maxMember']
        },"Data fetched")
    except Exception as e:
            send_error_mail(inspect.stack()[0][3], request.data, e)
            return r500("Something Bad Happened")



@api_view(['POST'])
def apply_event_paid(request: Request):
    try:
        data = request.data
        if not data:
            return r500("Invalid form")
        

        try:
            participants = data['participants']
            event_id = data['eventId'].strip()
            transactionId = data['transactionID'].strip()
            CAcode = data['CAcode'].strip()

        except KeyError as e:
            send_error_mail(inspect.stack()[0][3], request.data, e) 
            return error_response("Missing required fields: participants, eventId, and transactionId")

        
        
        # Check if participants' emails are from IIT Palakkad
        verified=False
        if all(map(lambda x: x.endswith("smail.iitpkd.ac.in"), participants)): 
            verified=True
            transactionId=f"IIT Palakkad Student+{time.time()}"

        # Check for duplicate transaction ID
        if TransactionTable.objects.filter(transactionId=transactionId).exists():
            return r500("Duplicate transaction ID used for another event")

        try:
            event = Event.objects.get(event_id = event_id)
        except Event.DoesNotExist:
            return r500("No event exists with given event_id")
        
        user = request.user
        if isinstance(user,AnonymousUser):
            return r500("Some error occured")
        ca_profile = None
        try:
            if CAcode != "null":
                ca_profile = CAProfile.objects.get(CACode = CAcode)
        except User.DoesNotExist:
            return ResponseWithCode({"success":False},"CA user not found",439)  # frontend need to check for this code, and display appropiate message
        

        # Create a new event record
        eventpaidTableObject = TransactionTable(
            event_id=event,
            user_id = user,
            participants= TransactionTable.serialise_emails(participants),
            transaction_id=transactionId,
            verified=verified,
            CACode=ca_profile
        )

        for participant in participants:
            user_registration:UserRegistrations = UserRegistrations.objects.filter(email = participant).first()
            if user_registration is not None:
                user_registration.transactionIds = user_registration.transactionIds + EMAIL_SEPARATOR + transactionId
                user_registration.asave()
            else:
                UserRegistrations.objects.acreate(
                    user = None, email = participant, 
                    transactionIds = transactionId
                )


        eventpaidTableObject.save()
        return ResponseWithCode({
            "success":True
        },"Event applied successfully")
    except Exception as e:
        return r500("Unexpected error occurred")

    

@api_view(['POST'])
def apply_event_free(request: HttpRequest):
    data = request.data
    if not data:
        return r500("Invalid form")

    try:

        user_id = data['user_id'].strip()
        participants = data['participants']
        event_id = data['eventId'].strip()

    except KeyError as e:
        send_error_mail(inspect.stack()[0][3], request.data, e) 
        return error_response("Missing required fields: participants and eventId")

    
    try:
        transaction_id = f"{user_id}+free+{time.time()}"

        try:
            event = Event.objects.get(event_id = event_id)
        except Event.DoesNotExist:
            return r500("No event exists with given event_id")
        
        try:
            user = User.objects.get(username = user_id)
        except User.DoesNotExist:
            return r500("No user exists with given user_id")
    

        # Create a new event record
        eventfreeTableObject = TransactionTable(
            event_id=event,
            user_id = user,
            participants=TransactionTable.serialise_emails(participants),
            transaction_id = transaction_id,
            verified=True
        )


        for participant in participants:
            user_registration:UserRegistrations = UserRegistrations.objects.filter(email = participant).first()
            if user_registration is not None:
                user_registration.transactionIds = user_registration.transactionIds + EMAIL_SEPARATOR + transaction_id
                user_registration.asave()
            else:
                UserRegistrations.objects.acreate(
                    user = None, email = participant, 
                    transactionIds = transaction_id
                )

        eventfreeTableObject.save()
        return ResponseWithCode({
            "success":True
        },"Event applied successfully")

    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e) 
        return error_response(f"Something went wrong: {str(e)}")


@api_view(['POST'])
def send_grievance(request: HttpRequest):
    try:
        data = request.data
        if isinstance(data, Empty) or data is None:
            return r500("Invalid Form")
        
        if data.__contains__('name') and data.__contains__('email') and data.__contains__('content'):
            name = data['name'] 
            email = data['email'] 
            content = data['content'] 
        else:
            return r500("Data not received as required")

        send_mail(
            subject=f"WEBSITE MAIL: Grievance from '{name}'",
            message=f"From {name} ({email}).\n\n{content}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=["112201020@smail.iitpkd.ac.in","112201024@smail.iitpkd.ac.in", "petrichor@iitpkd.ac.in"]
        )
        # print("grievance email sent")
        return ResponseWithCode({
                'success': True
            },"Email sent")

    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e)
        return ResponseWithCode({
                'success': False
            },"Something bad happened",500)

#########################
# CA Profile views

@api_view(['POST'])
def create_ca_user(request:HttpRequest):
    if request.method != 'POST':
        return r500("Method not allowed")
    try:
        user:User = request.user
        if not hasattr(user,'caprofile'):
            # print("Here")
            ca_profile = CAProfile(
                user = user,
                registration = 0  # -1 means not verified
            )
            ca_profile.save()
        else:
            ca_profile = user.caprofile

        return Response({'success': True, 'CACode': ca_profile.CACode})
    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e) 
        return error_response(f"Something went wrong: {str(e)}")

@api_view(['POST'])
def get_ca_user(request:HttpRequest):
    if request.method != 'POST':
        return r500("Method not allowed")
    try:
        user = request.user
        ca_profile:CAProfile = user.caprofile
        if ca_profile is None:
            return r500("CAProfile not found")

        return Response({'status': 200,"success":True, 
                         '  ': ca_profile.CACode,
                         "registrations":ca_profile.registration})
    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e) 
        return error_response(f"Something went wrong: {str(e)}")


@api_view(['POST'])
def verifyCA(request: Request):
    try:
        if request.data is None:
            return error_response("Invalid Form")
        
        data = request.data
        # print("print:", data)

        inputCAcode = data['CAcode'].strip()
        try:
            ca_profile = CAProfile.objects.get(CACode=inputCAcode)
            if ca_profile.registration == -1:
                ca_profile.registration = 0
                user_email = ca_profile.user.get_username()
                profile = Profile.objects.get(email = user_email)
                username = profile.username
                
                # Send a confirmation email to the user
                subject = "Petrichor Fest - Campus Ambassador Programme Verification"
                message = f"Hello {username},\n\nCongratulations! Your Campus Ambassador account with CA code {inputCAcode} has been successfully verified."
                from_mail = settings.EMAIL_HOST_USER
                to_mail_ls = [user_email]
                
                send_mail(subject, message, from_mail, to_mail_ls, fail_silently=False)
            
            return Response({
                'status': 200,
                'verified': True,
                'message': "CA account has been verified and the user has been notified."
            })
        except Profile.DoesNotExist:
            return Response({
                'status': 404,
                'verified': False,
                'message': "CA code not found in our database."
            })
        except Exception as e:
            send_error_mail(inspect.stack()[0][3], request.data, e)
            return error_response("Something bad happened")

    except Exception as e:
        return Response({
            'status': 400,
            'verified': False,
            'message': "Oops! Unable to complete the request."
        })




@api_view(['POST'])
def unverifyCA(request: Request):
    try:
        if request.data is None:
            return error_response("Invalid Form")
        
        data = request.data
        # print("print:", data)

        inputCAcode = data['CAcode'].strip()
        try:
            ca_profile = CAProfile.objects.get(CACode=inputCAcode)
            user_email = ca_profile.email
            profile = Profile.objects.get(email = user_email)
            username = profile.username
            
            # Delete the profile
            ca_profile.delete()
            
            # Send an email to the user
            subject = "Petrichor Fest - Campus Ambassador Programme Unverification"
            message = f"Hello {username},\n\nYour Campus Ambassador account with CA code {inputCAcode} has not been verified and has been removed from our system."
            from_mail = settings.EMAIL_HOST_USER
            to_mail_ls = [user_email]
            
            send_mail(subject, message, from_mail, to_mail_ls, fail_silently=False)
            
            return Response({
                'status': 200,
                'unverified': True,
                'message': "CA account has been removed and the user has been notified."
            })
        except Profile.DoesNotExist:
            return Response({
                'status': 404,
                'unverified': False,
                'message': "CA code not found in our database."
            })
        except Exception as e:
            send_error_mail(inspect.stack()[0][3], request.data, e)
            return error_response("Something bad happened")

    except Exception as e:
        return Response({
            'status': 400,
            'unverified': False,
            'message': "Oops! Unable to complete the request."
        })
