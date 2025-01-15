import re
import time
from django.conf import settings
from django.forms import ValidationError
from django.http import QueryDict
from django.shortcuts import redirect
from rest_framework.request import Request
from django.contrib.auth.models import User
from django.core.validators import validate_email
from rest_framework.decorators  import api_view
from rest_framework.exceptions import AuthenticationFailed

from rest_framework.response import Response 
from django.core.mail import send_mail
from django.contrib.auth.models import AnonymousUser
from django.core.signing import SignatureExpired,BadSignature

from petri_ca.settings import COUPON_CODES, FRONTEND_LINK
from petri_pydantic.models import AuthRequest, CARequest, EmailRequest, EventFree, EventPaid, Grievance, LoginRequest, NewPasswordRequest, PasswordRequest, SignUp
from pydantic import ValidationError as VLError
from utils import CLOSED_REGISTRATIONS, CLOSED_REGISTRATIONS, ResponseWithCode, get_email_from_token, get_forget_token, get_profile_data, get_profile_events, has_duplicate,\
r500,send_error_mail, method_not_allowed, send_event_registration_mail , send_forget_password_mail,error_response, send_user_verification_mail
from .models import EMAIL_SEPARATOR, Institute, Profile, TransactionTable,Event,CAProfile,UserRegistrations
from django.db.utils import IntegrityError
import inspect
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.core.mail import send_mail


TokenSerializer = TokenObtainPairSerializer()

@api_view(['POST'])
def signup(request:Request):
    '''
        Registers a User to the database
    '''
    if request.method != 'POST':
        return method_not_allowed()

    data = request.data
    if (not data) or not isinstance(data,(dict,QueryDict)):
        return r500("Data not provided")
    
    if isinstance(data, QueryDict):
        data = data.dict()

    try:
        # Retreiving all data
        try:
            request_data = SignUp.model_validate(data)
        except VLError as e:
            return r500(f"{e}")
        
        # Checking if User already exists
        user_exists = User.objects.filter(username=request_data.email).exists()
        if user_exists:
            return ResponseWithCode({
                "success":False,
                "username":request_data.username
            },
            "Email already registered",400)
    
        try:
            new_user = User(username=request_data.email,email = request_data.email)
            new_user.set_password(request_data.password)
            new_user.is_active = True
        except IntegrityError as e: # Email alreeady exists
            # send_error_mail(inspect.stack()[0][3], request.data, e)  # Leave this commented otherwise every wrong login will send an error mail
            return r500('Email already exists')
        
        user_registration = None
        user_profile = None
        user_saved = False
        profile_saved = False
        userreg_saved = False
        try:
            # creates or gets the InstituteId
            if request_data.institype != "neither":
                institute = Institute.objects.get_or_create(instiName=request_data.college, institutionType=request_data.institype)[0]
                # institute = Institute.objects.get(instiName=instituteID)
            else:
                institute = Institute.objects.get_or_create(instiName='NoInsti', institutionType=request_data.institype)[0]
            institute.save() # Kept for safety {create will automatically save}
            
            new_user.save()
            user_saved =True
            user_profile = Profile(username=request_data.username, 
                                user=new_user,
                                phone=request_data.phone,
                                instituteID=institute,
                                gradYear=request_data.gradyear,
                                stream=request_data.stream,
                                verified = False)
            
            # saving the profile and user. If any of above steps fails the Profile will not be created
            user_profile.save()
            profile_saved = True

            user_registration = UserRegistrations.objects.filter(email = request_data.email).first()
            if user_registration is not None:
                user_registration.user = new_user
                user_registration.save()
            else:
                UserRegistrations.objects.create(
                    user = new_user,
                    email = request_data.email,
                    transactionIds =""
                )
            userreg_saved = True


            token = get_forget_token(request_data.email)# Generates Token, It lasts for 5 mins
            if not send_user_verification_mail(request_data.email,token):
                if user_saved:
                    new_user.delete()
                if userreg_saved and user_registration is not None:
                    user_registration.delete()
                if profile_saved:
                    user_profile.delete()
                send_error_mail(inspect.stack()[0][3], request.data, f"Unable to send verification email. {data}")  
                return r500(f"Unable to send verification email to {request_data.email}. Please check the email or re-try after sometime.")


            # print("User Created")
            return ResponseWithCode({
                "success":True,
                "username":request_data.username
            },"We have sent an verification request to your email. Please verify the registration.")
        
        except IntegrityError as e:
            if user_saved:
                new_user.delete()
            if userreg_saved and user_registration is not None:
                user_registration.delete()
            if profile_saved and user_profile is not None:
                user_profile.delete()
            # send_error_mail(inspect.stack()[0][3], request.data, e)  # Leave this commented otherwise every wrong login will send an error mail
            return r500("User already exists. Try something different.")
        except Exception as e:
            if user_saved:
                new_user.delete()
            if userreg_saved and user_registration is not None:
                user_registration.delete()
            if profile_saved and user_profile is not None:
                user_profile.delete()
            send_error_mail(inspect.stack()[0][3], request.data, e)  
            r500("Something failed")


    except Exception as e:
        print(e)
        send_error_mail(inspect.stack()[0][3], data, e)
        return r500("Something Bad Happened")

@api_view(['POST'])
def resend_verification(request:Request):
    data = request.data
    if (not data) or not isinstance(data,(dict,QueryDict)):
        return r500("Data not provided")
    
    if isinstance(data, QueryDict):
        data = data.dict()
    
    try:
        try:
            request_data = EmailRequest.model_validate(data)
        except VLError as e:
            return r500(f"{e}")

        email = request_data.email 
        if email is None:
            return r500("Email not received") 
        email = email.strip()
        
        try:
            new_user = User.objects.get(username = email)
        except User.DoesNotExist:
            return r500("User Does not exists for given email. Please re-register.")


        token = get_forget_token(email)# Generates Token, It lasts for 5 mins
        if not send_user_verification_mail(email,token):
            send_error_mail(inspect.stack()[0][3], request.data, f"Reverification: Unable to send verification email. {data}")  
            return r500("Unable to send verification email. Please re-try after sometime.")
        
        return ResponseWithCode({
            "success": True,
        },f"A new verification email has been sent to given email: {email}")
    
    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e)
        return r500("Something Bad Happened")



@api_view(['POST'])
def ForgetPassword(request:Request):
    '''
        Reset Password

    '''
    if request.method != 'POST':
        return method_not_allowed()
    data = request.data
    if (not data) or not isinstance(data,(dict,QueryDict)):
        return r500("Data not provided")
    
    if isinstance(data, QueryDict):
        data = data.dict()
    try:
        try:
            request_data = EmailRequest.model_validate(data)
        except VLError as e:
            return r500(f"{e}")

        email = request_data.email 
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
    
    data = request.data
    if (not data) or not isinstance(data,(dict,QueryDict)):
        return r500("Data not provided")
    
    if isinstance(data, QueryDict):
        data = data.dict()
    
    try:
        try:
            request_data = NewPasswordRequest.model_validate(data)
        except VLError as e:
            return r500(f"{e}")
        
        new_password = request_data.new_password
        new_password = new_password.strip()

        if len(new_password) < 8:
            return Response({"error": "Password does not meet complexity requirements"}, status=400)
        
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
                    "status":511,
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
        data = request.data
        if (not data) or not isinstance(data,(dict,QueryDict)):
            return r500("Data not provided")
        
        if isinstance(data, QueryDict):
            data = data.dict()

        try:
            request_data = LoginRequest.model_validate(data)
        except VLError as e:
            return r500(f"{e}")
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
    if (not data) or not isinstance(data,(dict,QueryDict)):
        return r500("Data not provided")
    
    if isinstance(data, QueryDict):
        data = data.dict()

    try:
        request_data = AuthRequest.model_validate(data)
    except VLError as e:
        return r500(f"{e}")
    
    getUser = request_data.getUser
    getEvent = request_data.getEvents 

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
        '''
        performs email validation
        checks if event have already regsitered by any of the participants
        '''
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
                    tr = TransactionTable.objects.filter(transaction_id= trId, archived = False).only("event_id").first()
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
            return f"Some/All Participants have already been registered for this event. Those emails are: {AlreadyPresentIn}",AlreadyPresentIn


        tableObject.save()
        for reg in AllUsers:
            reg.save()

        return "",[]


@api_view(['POST'])
def apply_event_paid(request: Request):
    data = request.data
    if (not data) or not isinstance(data,(dict,QueryDict)):
        return r500("Data not provided")
    
    if isinstance(data, QueryDict):
        data = data.dict()

    try:

        try: 
            request_data = EventPaid.model_validate(data)
        except VLError as e:
            return r500(f"{e}")
        
        participants :list[str] = request_data.participants # type:ignore
        event_id = request_data.eventId 
        transactionId = request_data.transactionID
        CAcode = request_data.CACode
        coupon = request_data.coupon

        try:
            event = Event.objects.get(event_id = event_id)
        except Event.DoesNotExist:
            return r500("No event exists with given event_id")
        
        if event.event_id in CLOSED_REGISTRATIONS:
            return r500(f"Registrations for the event: {event.name} is closed.")

        user = request.user
        if isinstance(user,AnonymousUser):
            return r500("Some error occured")
        
        if has_duplicate(participants + [user.email]):
            return r500("Duplicate emails provided in participants")
        
        
        # Check if participants' emails are from IIT Palakkad
        verified=False
        if all(map(lambda x: x.endswith("iitpkd.ac.in"), participants + [user.email])): 
            verified=True
            transactionId=f"IIT Palakkad Student+{time.time()}{event_id}{user.id}"

        # Check for duplicate transaction ID
        if TransactionTable.objects.filter(transaction_id=transactionId).exists():
            return r500("Duplicate transaction ID used for another event")

        if event.fee == 0:
            return r500("This event is free. Please use api/event/free/")
                
        # Total participants including the authenticated user
        total_participants = len(participants) + 1

        
        if not (event.minMember <= total_participants <= event.maxMember):
            return r500(f"Number of participants must be - Min Paticipants: {event.minMember}, max Participants: {event.maxMember} ")


        # # Fees Calculation
        
        if not event.isTeam:
            total_fee = event.fee * total_participants  
        else:
            # the fees is treated as team fee
            total_fee = event.fee
        
        # verify coupon
        if coupon != "" and coupon != "null":
            if coupon not in COUPON_CODES:
                return r500(f"Invalid coupon code: {coupon}")
        
            total_fee = 0.9 * total_fee
            total_fee = round(total_fee)

        if coupon == "":
            coupon = "null"
        
        
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
            total_fee = total_fee,
            coupon = coupon,
            archived = False
        )


        # Check this above .save() to cancel any save operation
        message,regUsers =  updateUserRegTable(eventpaidTableObject,participants + [user.email], transactionId,event_id)
        if len(regUsers) != 0:
            return ResponseWithCode({
                "success":False,
                "registered_users": regUsers
            },message,500)

        if not send_event_registration_mail(participants + [user.email],event.name,verified):
            send_error_mail(inspect.stack()[0][3], request.data, f"Mail not sent while registering for paid event.") 
            return ResponseWithCode({
            "success":False
        },"Event applied successfully. We will verify the transaction in some time. You can check the status in your profile.")

        return ResponseWithCode({
            "success":True
        },"Event applied successfully")
    except Exception as e:
        print(e)
        return r500("Unexpected error occurred")

    

@api_view(['POST'])
def apply_event_free(request: Request):
    data = request.data
    if (not data) or not isinstance(data,(dict,QueryDict)):
        return r500("Data not provided")
    
    if isinstance(data, QueryDict):
        data = data.dict()

    try:
        try: 
            request_data = EventFree.model_validate(data)
        except VLError as e:
            return r500(f"{e}")
        
        participants :list[str] = request_data.participants # type:ignore
        event_id = request_data.eventId

        event_id = event_id.strip()

    except KeyError as e:
        send_error_mail(inspect.stack()[0][3], request.data, e) 
        return error_response("Missing required fields: participants and eventId")

    user = request.user
    
    try:

        try:
            event = Event.objects.get(event_id = event_id)
        except Event.DoesNotExist:
            return r500("No event exists with given event_id")
        
        if event.event_id in CLOSED_REGISTRATIONS:
            return r500(f"Registrations for the event: {event.name} is closed.")

        if has_duplicate(participants + [user.email]):
            return r500("Duplicate emails provided in participants")
        
        transaction_id = f"{user.id}{event_id}free{time.time()}"
        
        # Check if participants' emails are from IIT Palakkad
        verified=False
        if all(map(lambda x: x.endswith("iitpkd.ac.in"), participants + [user.email])): 
            verified=True

        if event.fee != 0 and not verified:
            return r500("This event has some fee assigned with it. Please use api/event/paid/")

        
        
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
            verified=True,
            archived = False
        )

        # Check this above .save() to cancel any save operation
        message,regUsers =  updateUserRegTable(eventfreeTableObject,participants + [user.email], transaction_id,event_id)
        if len(regUsers) != 0:
            return ResponseWithCode({
                "success":False,
                "registered_users": regUsers
            },message,500)

        if not send_event_registration_mail(participants + [user.email],event.name,True):
            send_error_mail(inspect.stack()[0][3], request.data, f"Mail not sent while registering for free event.") 
            return ResponseWithCode({
            "success":False
        },"Event applied successfully. You can check the status in your profile.")

        return ResponseWithCode({
            "success":True
        },"Event applied successfully")

    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e) 
        print(e)
        return error_response(f"Something went wrong: {str(e)}")

@PendingDeprecationWarning
@api_view(['POST'])
def deregister_event(request: Request):
    data = request.data
    if not isinstance(data,(dict,QueryDict)):
        return r500("Data not sent")

    try:
        event_id = data.get('eventId',None) 
        if event_id is None:
            return r500("null event Id , key is eventId")

        event_id = event_id.strip()

    except KeyError as e:
        send_error_mail(inspect.stack()[0][3], request.data, e) 
        return error_response("Missing required fields: participants and eventId")

    user = request.user
    
    try:

        try:
            event = Event.objects.get(event_id = event_id)
        except Event.DoesNotExist:
            return r500("No event exists with given event_id")
        
        if not user.hasattr('userregistrations'):
            return r500("Not registered to the event")
        
        user_registration = user.userregistrations # type:ignore
        trIds=TransactionTable.deserialize_emails(user_registration.transactionIds)
        event_transaction = None

        for trId in trIds:
            transaction = TransactionTable.objects.filter(transaction_id = trId, archived = False).only("user_id", "verified", "event_id", "transaction_id").first()
            if transaction is not None and transaction.event_id == event_id:
                event_transaction = transaction

        if event_transaction is None:
            return r500("Not registered to the event")
        
        event_user = event_transaction.user_id

        if event_user is None:
            send_error_mail(inspect.stack()[0][3], request.data, f"Unable to find who registered for this event: tr: {event_transaction.transaction_id}") 
            return r500("Unable to find who registered for this event. Please contact the team.")
        
        if event_transaction.verified and "free" not in event_transaction.transaction_id and "IIT Palakkad Student+" not in event_transaction.transaction_id:
            return r500("Your transaction have been verified. Cannot de-register from verified event registrations.")

        if (event_user.username != user.username):
            return r500(f"This event have been registered by {event_user.username}. Please use that account to de-register from the event.")
        
        event_transaction.delete()

        return ResponseWithCode({
            "success":True
        },"Event applied successfully")

    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e) 
        print(e)
        return error_response(f"Something went wrong: {str(e)}")



@api_view(['POST'])
def send_grievance(request: Request):
    data = request.data
    if (not data) or not isinstance(data,(dict,QueryDict)):
        return r500("Data not provided")
    
    if isinstance(data, QueryDict):
        data = data.dict()

    try:
        try: 
            request_data = Grievance.model_validate(data)
        except VLError as e:
            return r500(f"{e}")
        
        name = request_data.name
        email = request_data.email
        content = request_data.content

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
    data = request.data
    if (not data) or not isinstance(data,(dict,QueryDict)):
        return r500("Data not provided")
    
    if isinstance(data, QueryDict):
        data = data.dict()
    try:
        try:
            request_data = CARequest.model_validate(data)
        except VLError as e:
            return r500(f"{e}")
        
        inputCAcode = request_data.CACode.strip() # type:ignore
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
