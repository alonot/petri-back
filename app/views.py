import json
import re
import time
from django.conf import settings
from django.forms import ValidationError
from django.http import QueryDict
from django.shortcuts import redirect
from rest_framework.request import Empty, Request
from django.contrib.auth.models import User
from django.core.validators import validate_email
from rest_framework.decorators  import api_view
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.exceptions import AuthenticationFailed

from rest_framework.response import Response 
from django.core.mail import send_mail
from django.contrib.auth.models import AnonymousUser
from django.core.signing import SignatureExpired,BadSignature

from petri_ca.settings import FRONTEND_LINK
from utils import ResponseWithCode, get_email_from_token, get_forget_token, get_profile_data, get_profile_events,\
r500,send_error_mail, method_not_allowed, send_event_registration_mail , send_forget_password_mail,error_response, send_user_verification_mail
from .models import EMAIL_SEPARATOR, Institute, Profile, TransactionTable,Event,CAProfile,UserRegistrations
from django.db.utils import IntegrityError
from django.utils.datastructures import MultiValueDictKeyError
import inspect
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.core.mail import send_mail


TokenSerializer = TokenObtainPairSerializer()

def validateSignUpData(data: QueryDict | dict):
    username = data.get('username', '').strip()
    email = data.get('email', '')
    pass1 = data.get('password', '')
    phone = data.get('phone', '')
    insti_name = data.get('college', '')
    gradyear = data.get('gradyear', '')
    insti_type = data.get('institype', '')
    stream = data.get('stream', '')

    def is_valid_string(s, pattern):
        return bool(re.match(pattern, s))

    valid = False
    message = ""

    try:
        validate_email(email)
    except ValidationError:
        return False, "Invalid Email provided"
    
    if not isinstance(username, str):
        message = "Wrong Username format: must be str"
    elif not (1 <= len(username) <= 25):
        message = "Wrong Username format: Username must be between 1 and 25 characters"
    elif not is_valid_string(username, r"^[a-zA-Z0-9_\s]+$"):
        message = "Wrong Username format: can contain only {a-z, A-Z, 0-9, _, space}"
    elif not email:
        message = "Email cannot be empty"
    elif isinstance(phone, str) and not phone.isdigit():
        message = "Wrong Phone Format"
    elif len(phone) != 10:
        message = "Phone Number must be of length: 10"
    elif len(pass1) < 8:
        message = "Password must be at least 8 characters"
    elif not is_valid_string(pass1, r"^[a-zA-Z0-9_\s\.]+$"):
        message = "Password can contain only {a-z, A-Z, 0-9, _, space, .}"
    elif insti_type and insti_type != "neither":
        if not insti_name:
            message = "Institute Name is required"
        elif len(insti_name) > 100:
            message = "Institute Name must be at most 100 characters"
        elif not is_valid_string(insti_name, r"^[a-zA-Z0-9_\s\.,\-]+$"):
            message = "Institute Name can contain only {a-z, A-Z, 0-9, _, space, .}"
        elif isinstance(gradyear, str) and (not gradyear.isdigit() or not gradyear):
            message = "GradYear required and must be numeric"
        elif insti_type == "college":
            if not stream:
                message = "Please specify your degree"
            elif len(stream) > 100:
                message = "Degree must be at most 100 characters"
            elif not is_valid_string(stream, r"^[a-zA-Z0-9_\s\.\-,]+$"):
                message = "Degree can contain only {a-z, A-Z, 0-9, _, space, .}"
            else:
                valid = True
        else:
            valid = True
    else:
        valid = True

    return valid, message


@api_view(['POST'])
def signup(request:Request):
    '''
        Registers a User to the database
    '''
    if request.method != 'POST':
        return method_not_allowed()

    try:
        # Retreiving all data
        data = request.data
        if (not data) or not isinstance(data,(dict,QueryDict)):
            return r500("Data not provided")

        username = data.get('username',None) 
        email = data.get('email',None) 
        password = data.get('password',None) 
        phone = data.get('phone',None) 
        college = data.get('college',None) 
        gradyear = data.get('gradyear',None) 
        institype = data.get('institype',None) 
        stream = data.get('stream',None) 
        if username is None:
            return r500("username required")
        elif email is None:
            return r500("email required")
        elif password is None:
            return r500("password required")
        elif phone is None:
            return r500("phone required")
        elif gradyear is None:
            return r500("gradyear required")
        elif institype is None:
            return r500("institype required")
        username = username.strip()
        
        try:
            valid,message = validateSignUpData(data)  
            if not valid:
                return r500(message)
        except MultiValueDictKeyError or ValueError or KeyError:
            return r500("Data received does not contains all the required fields")

        
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
                new_user.set_password(password)
                new_user.is_active = True
            except IntegrityError as e: # Email alreeady exists
                # send_error_mail(inspect.stack()[0][3], request.data, e)  # Leave this commented otherwise every wrong login will send an error mail
                return r500('Email already exists')
            
            user_registration = None
            user_profile = None
            try:
                # creates or gets the InstituteId
                if institype != "neither":
                    institute = Institute.objects.get_or_create(instiName=college, institutionType=institype)[0]
                    # institute = Institute.objects.get(instiName=instituteID)
                else:
                    institute = Institute.objects.get_or_create(instiName='NoInsti', institutionType=institype)[0]
                institute.save() # Kept for safety {create will automatically save}
                
                new_user.save()
                user_profile = Profile(username=username, 
                                    user=new_user,
                                    phone=phone,
                                    instituteID=institute,
                                    gradYear=gradyear,
                                    stream=stream,
                                    verified = False)
                
                # saving the profile and user. If any of above steps fails the Profile will not be created
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

                token = get_forget_token(email)# Generates Token, It lasts for 5 mins
                send_user_verification_mail(email,token)



                # print("User Created")
                return ResponseWithCode({
                    "success":True,
                    "username":username
                },"We have sent an verification request to your email. Please verify the registration.")
            
            except IntegrityError as e:
                if new_user:
                    new_user.delete()
                if user_registration:
                    user_registration.delete()
                if user_profile:
                    user_profile.delete()
                # send_error_mail(inspect.stack()[0][3], request.data, e)  # Leave this commented otherwise every wrong login will send an error mail
                return r500("User already exists. Try something different.")
            except Exception as e:
                if new_user:
                    new_user.delete()
                if user_registration:
                    user_registration.delete()
                if user_profile:
                    user_profile.delete()
                send_error_mail(inspect.stack()[0][3], request.data, e)  
                r500("Something failed")


    except Exception as e:
        print(e)
        send_error_mail(inspect.stack()[0][3], request.data, e)
        return r500("Something Bad Happened")



@api_view(['POST'])
def ForgetPassword(request:Request):
    '''
        Reset Password

    '''
    if request.method != 'POST':
        return method_not_allowed()
    try:
        data = request.data
        if not isinstance(data,(dict,QueryDict)):
            return r500("Data not sent")
        email = data.get('email',None) 
        if email is None:
            return r500("Email not received") 
        email = email.strip()

        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            return Response({
                'status': 404,
                'message': "No User found with this Email",
                "username": None
            },404)
        
        profile:Profile = user.profile # type:ignore
        
        token = get_forget_token(email)# Generates Token, It lasts for 5 mins
        
        send_forget_password_mail(email , token,profile.username)

        return ResponseWithCode({
            "success":True
        },"An email is sent")

    except Exception as e:
        # print(e)
        send_error_mail(inspect.stack()[0][3], request.data, e)
        return r500("Something Bad Happened")
    


@api_view(['POST'])
def ChangePassword(request:Request , token:str):
    '''
        Changes Password
    '''
    if request.method != 'POST':
        return method_not_allowed()
    
    try:
       
        data = request.data
        if not isinstance(data,(dict,QueryDict)):
            return r500("Data not sent")
        new_password = data.get('new_password',None) 
        if new_password is None:
            return r500("new_password not received") 
        new_password = new_password.strip()

        if len(new_password) < 8:
            return Response({"error": "Password does not meet complexity requirements"}, status=400)
        
        # if len(new_password) < 8 or not any(char.isdigit() for char in new_password) or not any(char.isupper() for char in new_password) or not any(char.islower() for char in new_password) or not any(char in "!@#$%^&*()_+" for char in new_password):
        #     return Response({"error": "Password does not meet complexity requirements"}, status=400)
        
        try:
            email = get_email_from_token(token)
        except SignatureExpired:
            return Response({"error": "Token expired"}, status=401)
        except BadSignature:
            return r500("Invalid Token")
        
        user_obj = User.objects.filter(username = email).first()
        if user_obj is None:
            return r500("No user exists with this email.")
        
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
                user_profile:Profile = user.profile #type:ignore
            else:
                if user:
                    user.delete()
                return {
                    "status":400,
                    "success":False,
                    "message":"User authenticated but its Profile Doesn't Exists.\
                    User has been deleted.Please create a new Profile."
                }
            if not user_profile.verified:
                return {
                    "status":400,
                    "success":False,
                    "message":"Please verify you account first. We would have sent you an verification email to the provided email address."
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
        if not isinstance(request.data,(dict,QueryDict)):
            return r500("Data not sent")
        if (not request.data.__contains__("username")): 
            return ResponseWithCode({
                "success":False,
            },"Username Not given",400)
        
        if (not request.data.__contains__("password")): 
            return ResponseWithCode({
                "success":False,
            },"Password Not given",400)

        result = super().post(request, *args, **kwargs)
        if (result.data):
            result.status_code = (result.data['status'])
        return result

    serializer_class = LoginTokenSerializer
    

@api_view(['GET'])
def verifyUser(request:Request , token:str):
    '''
        Verifies user
    '''
    
    try:
        
        try:
            email = get_email_from_token(token)
        except SignatureExpired:
            actual_email = token.split(':')[0]
            new_token = get_forget_token(actual_email)
            send_user_verification_mail(actual_email,new_token)
            return redirect(f"{FRONTEND_LINK}message/Token expired. A new mail may have been sent to your email address.If not please contact the team.")
        except BadSignature:
            return redirect(f"{FRONTEND_LINK}message/You entered an Invalid token. Please check the link carefully.")
        
        user_obj = User.objects.filter(username = email).first()
        if user_obj is None:
            return redirect(f"{FRONTEND_LINK}message/No user exists with this email.Please try re-registering.")

        
        if (not hasattr(user_obj,'profile')):
            send_error_mail(inspect.stack()[0][3],{"event":"verifyUser"}, f"User exists but no profile...{user_obj.email}")
            if user_obj:
                user_obj.delete()
            return redirect(f"{FRONTEND_LINK}message/User authenticated but its Profile Doesn't Exists.\
                    User has been deleted.Please create a new Profile.")

        profile:Profile = user_obj.profile # type:ignore
        profile.verified = True
        profile.save()

        return redirect(f"{FRONTEND_LINK}message/We have verified your account successfully.Now, you can login and explore Petrichor 25")

    
    except Exception as e:
        send_error_mail(inspect.stack()[0][3],{"event":"verifyUser"}, e)
        return redirect(f"{FRONTEND_LINK}message/We encountered some error in verifying your account. Reported this event to the team")

    
@api_view(['POST'])
def authenticated(request:Request):
    '''
        Authenticates, send the user info if getUser = True in the data body
        send the user events if getEvents = True in the data body
    '''
    if request.method != 'POST':
        return method_not_allowed()

    data = request.data
    if data is None or not isinstance(data,(dict,QueryDict)):
        return ResponseWithCode({"success":False},'Data not sent as Required',500)
    getUser = data.get("getUser",None)  
    getEvent = data.get("getEvents",None) 

    if getUser is None:
        return ResponseWithCode({"success":False},'getUser not sent.',500)

    if getEvent is None:
        return ResponseWithCode({"success":False},'getEvnt not sent.',500)

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
        send_error_mail(inspect.stack()[0][3],request.data,e)
        print(e)
        return r500("some error occured. Reported to our developers")


def updateUserRegTable(tableObject:TransactionTable,participants:list[str],transactionId:str,event_id:str) -> tuple[str,list]:
    # this checks if the participant is already registered for the event or not
        AlreadyPresentIn = []
        #####
        AllUsers: list[UserRegistrations] = []
        for participant in participants:
            try:
                validate_email(participant)
            except ValidationError:
                return "Following Email is invalid", [participant]
            user_registration = UserRegistrations.objects.filter(email = participant).first()
            if user_registration is not None:
                trIds = TransactionTable.deserialize_emails(user_registration.transactionIds)
                for trId in trIds:
                    tr = TransactionTable.objects.filter(transaction_id= trId).first()
                    if tr is not None and  tr.event_id and tr.event_id.event_id == event_id:
                        AlreadyPresentIn.append(participant)
                        break
                user_registration.transactionIds = user_registration.transactionIds + EMAIL_SEPARATOR + transactionId

                AllUsers.append(user_registration)
            else:
                user_reg = UserRegistrations(
                    user = None, email = participant, 
                    transactionIds = transactionId
                ) 
                AllUsers.append(user_reg)

        # Check this above .save() to cancel any save operation
        if len(AlreadyPresentIn) != 0:
            return "Some/All Participants have already been registered for this event",AlreadyPresentIn


        tableObject.save()
        for reg in AllUsers:
            reg.save()

        return "",[]


@api_view(['POST'])
def apply_event_paid(request: Request):
    try:
        data = request.data
        if not data or not isinstance(data,(dict,QueryDict)):
            return r500("Invalid form")

        try:
            part = data.get('participants',None) # type:ignore
            event_id = data.get('eventId',None) 
            transactionId = data.get('transactionID',None) 
            CAcode = data.get('CACode',None) 
            if event_id is None:
                return r500("null event Id , key is eventId")
            elif transactionId is None:
                return r500("null transaction Id , key is transactionID")
            elif CAcode is None:
                return r500("null CAcode , key is CACode")
            elif part is None or not isinstance(part,list):
                return r500("null participants , key is participants")
            participants :list[str] = part

        except KeyError as e:
            send_error_mail(inspect.stack()[0][3], request.data, e) 
            return error_response("Missing required fields: participants, eventId, and transactionId")
        

        user = request.user
        if isinstance(user,AnonymousUser):
            return r500("Some error occured")
        
        
        # Check if participants' emails are from IIT Palakkad
        verified=False
        if all(map(lambda x: x.endswith("smail.iitpkd.ac.in"), participants + [user.email])): 
            verified=True
            transactionId=f"IIT Palakkad Student+{time.time()}{event_id}{user.id}"

        # Check for duplicate transaction ID
        if TransactionTable.objects.filter(transaction_id=transactionId).exists():
            return r500("Duplicate transaction ID used for another event")

        try:
            event = Event.objects.get(event_id = event_id)
        except Event.DoesNotExist:
            return r500("No event exists with given event_id")
        
                
        # Total participants including the authenticated user
        total_participants = len(participants) + 1

        
        if not (event.minMember <= total_participants <= event.maxMember):
            return r500(f"Number of participants must be - Min Paticipants: {event.minMember}, max Participants: {event.maxMember} ")


        # # Fees Calculation
        
        if event.isTeam:
            total_fee = event.fee * total_participants  
        else:
            total_fee = event.fee
        
        ca_profile = None
        try:
            if CAcode != "null" and CAcode != "":
                ca_profile = CAProfile.objects.get(CACode = CAcode)
                # we do not increase CA registrations here. Instead we do it when this transaction verifies
                try:
                    if user.caprofile is not None and user.caprofile.CACode == CAcode:
                        return r500("You cannot use your own CA code")
                except CAProfile.DoesNotExist:
                    pass
        except CAProfile.DoesNotExist:
            return ResponseWithCode({"success":False},"CA user not found",439)  # frontend need to check for this code, and display appropiate message
        

        # Create a new event record
        eventpaidTableObject = TransactionTable(
            event_id=event,
            user_id = user,
            participants= TransactionTable.serialise_emails(participants),
            transaction_id=transactionId,
            verified=verified,
            CACode=ca_profile,
            total_fee = total_fee
        )

        # Check this above .save() to cancel any save operation
        message,regUsers =  updateUserRegTable(eventpaidTableObject,participants + [user.email], transactionId,event_id)
        if len(regUsers) != 0:
            return ResponseWithCode({
                "success":False,
                "registered_users": regUsers
            },message,500)

        send_event_registration_mail(participants + [user.email],event.name,verified)

        return ResponseWithCode({
            "success":True
        },"Event applied successfully")
    except Exception as e:
        print(e)
        return r500("Unexpected error occurred")

    

@api_view(['POST'])
def apply_event_free(request: Request):
    data = request.data
    if not isinstance(data,(dict,QueryDict)):
        return r500("Data not sent")

    try:
        part = data.get('participants',None)   #type:ignore
        event_id = data.get('eventId',None) 
        if event_id is None:
            return r500("null event Id , key is eventId")
        elif part is None or not isinstance(part,list):
            return r500("null participants , key is participants")
        participants :list[str] = part
        event_id = event_id.strip()

    except KeyError as e:
        send_error_mail(inspect.stack()[0][3], request.data, e) 
        return error_response("Missing required fields: participants and eventId")

    user = request.user
    
    try:
        transaction_id = f"{user.id}{event_id}free{time.time()}"

        try:
            event = Event.objects.get(event_id = event_id)
        except Event.DoesNotExist:
            return r500("No event exists with given event_id")
        
        
        
        # Total participants including the authenticated user
        total_participants = len(participants) + 1

        # Check for Participants
        if not (event.minMember <= total_participants <= event.maxMember):
            return r500(f"Number of participants must be - Min Paticipants: {event.minMember}, max Participants: {event.maxMember} ")
            
            
        # Create a new event record
        eventfreeTableObject = TransactionTable(
            event_id=event,
            user_id = user,
            participants=TransactionTable.serialise_emails(participants),
            transaction_id = transaction_id,
            verified=True
        )

        # Check this above .save() to cancel any save operation
        message,regUsers =  updateUserRegTable(eventfreeTableObject,participants + [user.email], transaction_id,event_id)
        if len(regUsers) != 0:
            return ResponseWithCode({
                "success":False,
                "registered_users": regUsers
            },message,500)

        send_event_registration_mail(participants + [user.email],event.name,True)

        return ResponseWithCode({
            "success":True
        },"Event applied successfully")

    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e) 
        print(e)
        return error_response(f"Something went wrong: {str(e)}")



@api_view(['POST'])
def send_grievance(request: Request):
    try:
        data = request.data
        if not isinstance(data,(dict,QueryDict)):
            return r500("Data not sent")
        
        if data.__contains__('name') and data.__contains__('email') and data.__contains__('content'): 
            name = data.get('name',"") # type:ignore
            email = data.get('email',"") # type:ignore
            content = data.get('content',"") # type:ignore
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
def create_ca_user(request:Request):
    if request.method != 'POST':
        return method_not_allowed()
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
            ca_profile = user.caprofile # type:ignore

        return Response({'success': True, 'CACode': ca_profile.CACode})
    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e) 
        return error_response(f"Something went wrong: {str(e)}")

@api_view(['POST'])
def get_ca_user(request:Request):
    if request.method != 'POST':
        return method_not_allowed()
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
    if request.method != 'POST':
        return method_not_allowed()
    try:
        data = request.data

        if data is None or not isinstance(data,(dict,QueryDict)):
            return error_response("Invalid Form")
        

        inputCAcode = data.get('CACode','').strip() # type:ignore
        try:
            ca_profile = CAProfile.objects.get(CACode=inputCAcode)

            return Response({
                'status': 200,
                'verified': True,
                'message': "CACode verified."
            })
        except CAProfile.DoesNotExist:
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
        data = request.data

        if data is None or not isinstance(data,(dict,QueryDict)):
            return error_response("Invalid Form")
        

        inputCAcode = data.get('CACode','').strip() # type:ignore

        try:
            ca_profile = CAProfile.objects.get(CACode=inputCAcode)
            user_email = ca_profile.user.email
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
