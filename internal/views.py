
import base64
from collections import defaultdict
from functools import lru_cache
import inspect
import io
from PIL import Image as Img
import json
from django.http import HttpRequest, JsonResponse, QueryDict
from app.models import *
from rest_framework.response import Response
from rest_framework.request import Request

from rest_framework.decorators import api_view

from internal.models import Image
from petri_ca.settings import PASSWORD
from utils import ResponseWithCode, method_not_allowed, r200, r500 , send_delete_transaction_mail, send_error_mail, send_event_unverification_mail, send_event_verification_mail


@api_view(['POST'])
def getAllUsers(request):

    data,valid = getUsersData()
    if valid:
        return ResponseWithCode({
            "data":data,
            "success":True
        },"Data Fetched")
    else :
        return r500("Fetch failed")


def getUsersData():
    '''
    Returns a list of users
    '''
    try:
        users = User.objects.all().order_by('date_joined').reverse()
        allUsers = []
        for user in users:
            if not hasattr(user,'profile'):
                continue
            profile:Profile = user.profile # type:ignore
            caprofile :CAProfile | None = None
            if hasattr(user,'caprofile'):
                caprofile = user.caprofile # type:ignore
            institute = profile.instituteID
            userData = {
                "name":profile.username,
                "phone":profile.phone,
                "email":user.email,
                "gradyear":profile.gradYear,
                "stream":profile.stream,
                "joined":profile.joined.strftime("%d/%m/%Y, %H:%M:%S"),
                "verified": profile.verified,
                "college":"",
                "CA":"",
                "CAregistrations":"",
            }
            if institute:
                userData["college"] = institute.instiName
            if caprofile:
                userData["CA"] = caprofile.CACode
                userData["CAregistrations"] = caprofile.registration
            allUsers.append(userData)

        return allUsers,True
    except Exception as e:
        send_error_mail(inspect.stack()[0][3], {"data":"GETUSERS"}, e)
        return [],False


#This is Transaction IDS
#Here i am just iteration through all the transaction ids and marking them true or false or success if that transaction id exists in the req which i will get 
@api_view(['POST'])
def verifyTR(request):
    '''
        send Event verified mail to the users
    '''
    
    if request.method == 'POST':
        data = json.loads(request.body)
        # Here if no transaction id then it will start with a default of the empty list
        transaction_ids = data.get('transaction_ids', [])

        password = data.get("password" , None)
        if password is None:
            return r500("password is missing") 
        
        if (password != PASSWORD):
            return r500("Incorrect password. Event was not added")
        
        failed_transactions = []

        for transaction_id in transaction_ids:
            try:
                transaction = TransactionTable.objects.get(transaction_id=transaction_id)
                if transaction.verified:
                    failed_transactions.append(f"{transaction_id}:  already verified")
                    continue
                transaction.verified = True
                CA = None
                CA = transaction.CACode
                if CA:
                    CA.registration +=1

                # send mail to user
                user = transaction.user_id
                if user and transaction.event_id:
                    if not send_event_verification_mail([user.email] + TransactionTable.deserialize_emails(transaction.participants),
                                                transaction.transaction_id,transaction.event_id.name):
                        failed_transactions.append(f"{transaction_id}:  email not sent")
                        continue       
                #
                if CA is not None:
                    CA.save()
                transaction.save()
            except TransactionTable.DoesNotExist:
                print(transaction_id)
                failed_transactions.append(f"{transaction_id}:  Does Not Exists")

            except Exception as e:
                print(e)
                 # we are taking any exception here to store in failed list and then tell frontend about it
                send_error_mail(inspect.stack()[0][3], {"event":"verify:" + transaction_ids.__str__()}, e)
                failed_transactions.append(f"{transaction_id}:  {e}")

                
        
        return ResponseWithCode({
            'success': True,
            'failed_transactions': failed_transactions
        },"Success")

#This is Transaction IDS
#Here i am just iteration through all the transaction ids and marking them true or false or success if that transaction id exists in the req which i will get 
@api_view(['POST'])
def unverifyTRs(request):
    '''
        send Event unverified mail to the users
    '''
    
    if request.method == 'POST':
        data = json.loads(request.body)
        # Here if no transaction id then it will start with a default of the empty list
        transaction_ids = data.get('transaction_ids', [])   

        password = data.get("password" , None)
        if password is None:
            return r500("password is missing") 
        
        if (password != PASSWORD):
            return r500("Incorrect password. Event was not added")
        
        failed_transactions = []

        for transaction_id in transaction_ids:
            try:
                transaction = TransactionTable.objects.get(transaction_id=transaction_id)

                transaction.verified = False
                transaction.archived = True ## equivalent to deleting. This will also ensure no-one puts this trId again in website

                # send mail to user
                user = transaction.user_id
                if user and transaction.event_id:
                    if not send_event_unverification_mail([user.email] + TransactionTable.deserialize_emails(transaction.participants),
                                                transaction.transaction_id,transaction.event_id.name):
                        failed_transactions.append(f"{transaction_id}:  email not sent")
                        continue

                transaction.save()
            except TransactionTable.DoesNotExist:
                print(transaction_id)
                failed_transactions.append(f"{transaction_id}:  does not exists")

            except Exception as e:
                print(e)
                 # we are taking any exception here to store in failed list and then tell frontend about it
                send_error_mail(inspect.stack()[0][3], {"event":"verify:" + transaction_ids.__str__()}, e)
                failed_transactions.append(f"{transaction_id}:  {e}")
                
        
        return ResponseWithCode({
            'success': True,
            'failed_transactions': failed_transactions
        },"Success")

@api_view(['GET'])
def unverifTR(request):
    try:
        transaction_ids = []
        transaction = TransactionTable.objects.filter(verified = False)
        for user in transaction:
            transaction_ids.append(user.transaction_id)
        return JsonResponse({
            'status' : 'success',
            'unverified_transactions' : transaction_ids 
        })
    except Exception as e:
        return r500("Opps!! Unable to complete the request!!!")


@api_view(['POST'])
def cancelTR(request):
    try:
        data = json.loads(request.body)
        transaction_notfound = []
        for item in data:
            # Process each JSON object in the array
            transaction_id = item.get('transaction_id')
            email = item.get('email')
            transaction = TransactionTable.objects.get(transaction_id=transaction_id)
            if transaction is not None :
                event_id = transaction.event_id
                event_name = Event.objects.filter(event_id = event_id).name
                transaction.delete()
                send_delete_transaction_mail(email , event_name)
            else:
                transaction_notfound.append(transaction_id)
        if len(transaction_notfound) == 0:
            return JsonResponse({
                'success' : True,
                'message' : 'All mails sent'
            })
        else:
            return JsonResponse({
                'success' : False ,
                'message' : 'Some ids were not found',
                'transaction_notfound' : transaction_notfound
            })
    except TransactionTable.DoesNotExist:
        return JsonResponse({
            'success' : False ,
            'error': 'Transaction not found'
            }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success' : False ,
            'error': 'Invalid JSON'
            }, status=400)



@api_view(['POST'])
def addEvent(request:Request):
    try:
        data=request.data
        if data == None or not isinstance(data,(dict,QueryDict)):
            return r500("Please send some info about the event")
        eventId = data.get("eventId" , None)
        if eventId is None:
            return r500("Event Id is missing")
        name = data.get("name" , None)
        if name is None:
            return r500("Event name is missing")
        fee = data.get("fee" , None)
        if fee is None:
            return r500("Event fees is missing")
        minMember = data.get("minMember", None)
        if minMember is None:
            return r500("minMember is missing")
        maxMember = data.get("maxMember" , None)
        if maxMember is None:
            return r500("maxMember is missing")
        isTeam = data.get("isTeam" , None)
        if isTeam is None:
            return r500("isTeam is missing")
        markdown = data.get("markdown" , None)
        if markdown is None:
            return r500("markdown is missing")
        image_url = data.get("image_url" , None)
        if image_url is None:
            return r500("image_url is missing")
        dt_organizers: list[str] | None = data.get("organizers" , None)
        if dt_organizers is None:
            return r500("organizers is missing")
        dt_tags: list[str] | None = data.get("tags" , None)
        if dt_tags is None:
            return r500("organizers is missing")
        
        password = data.get("password" , None)
        if password is None:
            return r500("password is missing") 
        
        if (password != PASSWORD):
            return r500("Incorrect password. Event was not added")
        
        
        if (name.lower() in ["tutorial", "tutorial_event"]):
            return r500(f'Cannot Edit Tutorial')
        
        if (minMember > maxMember):
            return r500("minMember cannot exceed maxMember")

        dt_fee = int(fee)
        if dt_fee == 0:
            eventId = f'{eventId[0]}F{eventId[2:]}'
        else:
            eventId = f'{eventId[0]}P{eventId[2:]}'
        
        event = Event.objects.create(
            event_id = eventId ,
            name =  name ,
            fee = fee ,
            minMember = minMember ,
            maxMember = maxMember ,
            isTeam = isTeam,
            markdown = markdown,
            tags = TransactionTable.serialise_emails(dt_tags),
            image_url = image_url)
        
        organisers = [o[0] for o in dt_organizers]
        update_organizers(dt_organizers)


        event.organizers= TransactionTable.serialise_emails(organisers)
        event.save()
        # print('done')
        return r200("Event saved successfully")

    except Exception as e:
        print(e)
        return r500(f'Error: {e}')  


@lru_cache
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
        
        password = data.get("password" , None)
        if password is None:
            return r500("password is missing") 

        if (password != PASSWORD):
            return r500("Incorrect password. Event was not updated")
        try:
            event = Event.objects.get(event_id = event_id)
        except Event.DoesNotExist:
            return r500(f"Invalid Event ID = {event_id}")
        return ResponseWithCode({
            "success":True,
            "eventId": event_id,
            "name": event.name,
            "fee": event.fee,
            "minMember": event.minMember,
            "maxMember": event.maxMember,
            "isTeam": event.isTeam,
            "markdown": event.markdown,
            "image_url": event.image_url,
            "organizers": TransactionTable.deserialize_emails(event.organizers),
            "tags": event.tags.split(EMAIL_SEPARATOR),
        },"Data fetched")
    except Exception as e:
            send_error_mail(inspect.stack()[0][3], request.data, e)
            return r500("Something Bad Happened")

@api_view(['POST'])
def get_image_data(request):

    if request.method != 'POST':
        return method_not_allowed()

    try:
        data=request.data

        if data is None:
            return r500("invalid form")
        
        if data.__contains__('name'):
            image_name = data["name"]
        else:
            return r500("Send a name")
        
        # password = data.get("password" , None)
        # if password is None:
        #     return r500("password is missing") 

        # if (password != PASSWORD):
        #     return r500("Incorrect password. Event was not updated")
        # try:
        image = Image.objects.filter(name = image_name).first()
        if image is None:
            return r500(f"Invalid image name = {image_name}")

        # except Image.DoesNotExist:
        
        # base64_data = base64.b64encode(output_image.getvalue()).decode('utf-8')
        base64_data = base64.b64encode(image.image).decode('utf-8')
        return ResponseWithCode({
            "success":True,
            "image": base64_data,
            "name": image.name,
        },"Data fetched")
    except Exception as e:
            send_error_mail(inspect.stack()[0][3], request.data, e)
            return r500("Something Bad Happened")

@api_view(['POST'])
def get_next_id(request):

    if request.method != 'POST':
        return method_not_allowed()

    try:
        data=request.data

        if data is None:
            return r500("invalid form")
        
        if data.__contains__('type'):
            event_type = data["type"]
        else:
            return r500("Send a type")
        
        password = data.get("password" , None)
        if password is None:
            return r500("password is missing") 

        if (password != PASSWORD):
            return r500("Incorrect password. Event was not updated")
        
        if not event_type in ["Workshop", "Informal", "Technical", "Cultural"]:
            return r500(f"Invalid Event type : {event_type}")
        
        number = 0
        events = Event.objects.filter(event_id__startswith=event_type[0]).values('event_id')

        if events.exists():
            event_ids = [int(event['event_id'][2:]) for event in events]
            number = sorted(event_ids)[-1]
        number +=1
        
        
        return ResponseWithCode({
            "success":True,
            "data": number
        },"Data fetched")
    except Exception as e:
            send_error_mail(inspect.stack()[0][3], request.data, e)
            return r500("Something Bad Happened")


@api_view(['POST'])
def allEvents(request: Request):
    try:
        data=request.data
        if isinstance(data, (dict, QueryDict)):
            password = data.get("password" , None)
            # print(password)
            if password is None:
                return ResponseWithCode({}, "password is missing", 502)
            if (password != PASSWORD):
                return ResponseWithCode({}, "Wrong Password", 501)
            
            # print("wd")
            events = Event.objects.only("name","event_id")
            res = []
            for event in events:
                res.append({
                    "name":event.name,
                    "eventId":event.event_id,
                    "tags": event.tags.split(EMAIL_SEPARATOR)
                })

            return ResponseWithCode({
                "data" : res
            }, "events fetchted")
        else:
            return r500("Empty Data recieved")
    except Exception as e:
        print(e)
        send_error_mail(inspect.stack()[0][3], request.data, e)
        return r500(f'Error: {e}')

@api_view(['POST'])
def allImages(request: Request):
    try:
        data = request.data
        if not data or not isinstance(data, (dict, QueryDict)):
            return r500("Invalid or empty data received")
        
        password = data.get("password")
        if not password:
            return ResponseWithCode({}, "Password is missing", 502)
        
        if password != PASSWORD:  # Replace with secure comparison
            return ResponseWithCode({}, "Wrong Password", 501)
        
        events = Image.objects.all()
        if not events:
            return ResponseWithCode({}, "No events found", 204)
        
        res = []
        for image in events:
            if not image.image:
                continue
            try:
                base64_data = base64.b64encode(image.image).decode('utf-8')
            except Exception as encode_error:
                print(f"Encoding error for event {image.name}: {encode_error}")
                send_error_mail(inspect.stack()[0][3], request.data, encode_error)
                continue
            res.append({
                "name": image.name,
                "image": base64_data
            })
        
        return ResponseWithCode({
            "data": res
        }, "Events fetched successfully")
    except Exception as e:
        print(f"Unexpected error: {e}")
        res = send_error_mail(inspect.stack()[0][3], request.data, e)
        return r500(f"Mail: {res} . Error: {e}")

@api_view(['POST'])
def allImagesInfo(request: Request):
    try:
        data = request.data
        if not data or not isinstance(data, (dict, QueryDict)):
            return r500("Invalid or empty data received")
        
        password = data.get("password")
        if not password:
            return ResponseWithCode({}, "Password is missing", 502)
        
        if password != PASSWORD:  # Replace with secure comparison
            return ResponseWithCode({}, "Wrong Password", 501)
        
        images = Image.objects.only("name")
        if not images:
            return ResponseWithCode({}, "No images found", 204)
        
        res = []
        for image in images:
            res.append(image.name)
        
        return ResponseWithCode({
            "data": res
        }, "Events fetched successfully")
    except Exception as e:
        print(f"Unexpected error: {e}")
        res = send_error_mail(inspect.stack()[0][3], request.data, e)
        return r500(f"Mail: {res} . Error: {e}")

def update_organizers(dt_organizers):
    # print(dt_organizers)
    for name, buffer_data in dt_organizers:
        old_name = buffer_data['old_name']
        buffer : str | dict = buffer_data['buffer']
        buffer_binary = None
        if (buffer != ""):
            buffer_binary = bytes(buffer['data'])
            image_pil = Img.open(io.BytesIO(buffer_binary))
            output_image = io.BytesIO()
            image_pil.save(output_image, format='WEBP')
            buffer_binary = output_image.getvalue()

        if old_name != "" :
            old_image = Image.objects.filter(name=old_name).first()
            if old_image is None: 
                if buffer == "":
                    return r500(f"{old_name}'s image does not exists with us. Please reupload with overwrite 'On' .")
                old_image = Image(name = name, image =buffer_binary)
                
            if old_name.lower() != name.lower():
                prev_image = Image.objects.filter(name=old_name).first()
                prev_image.delete()

                old_image.name = name
                
            if buffer != "":
                old_image.image =buffer_binary
                
            old_image.save()
        else:
            new_image = Image.objects.filter(name = name).first()
            if (new_image is None):
                new_image = Image(name = name, image =buffer_binary)
            else:
                new_image.image =buffer_binary

            new_image.save()

@api_view(["POST"])
def updateEvent(request: Request):
    try:
        data=request.data
        if isinstance(data, (dict, QueryDict)):
            dt_eventId = data.get("eventId")
            if dt_eventId is None:
                return r500('Please provide an eventId')
            dt_name=data.get("name")
            dt_fee=data.get("fee")
            dt_minMember=data.get("minMember")
            dt_maxMember=data.get("maxMember")
            dt_isTeam=data.get("isTeam")
            dt_markdown=data.get("markdown")
            dt_image_url=data.get("image_url")
            dt_organizers =data.get("organizers")
            dt_tags =data.get("tags")
            password = data.get("password" , None)
            if password is None:
                return r500("password is missing") 

            if (password != PASSWORD):
                return r500("Incorrect password. Event was not updated")
            
            if (dt_eventId in ["TF01", "WF01"]):
                return r500(f'Cannot Edit Tutorial')
            
            # print("wd")
            event = Event.objects.filter(event_id=dt_eventId).first()
            if event is None:
                return r500(f'No event found with eventId {dt_eventId}')
            # print(event.name,event.fee,dt_fee)

            if dt_name is not None and dt_name!= "":
                event.name=dt_name
            if dt_fee is not None:
                event.fee=int(dt_fee)
                if event.fee == 0 and event.event_id[1] == 'P':
                    prev_event = Event.objects.get(event_id = event.event_id)
                    prev_event.delete()
                    event.event_id = f'{event.event_id[0]}F{event.event_id[2:]}'
                elif event.fee != 0 and event.event_id[1] == 'F':
                    prev_event = Event.objects.get(event_id = event.event_id)
                    prev_event.delete()
                    event.event_id = f'{event.event_id[0]}P{event.event_id[2:]}'
            if dt_minMember is not None:
                event.minMember=int(dt_minMember)
                if (event.minMember > event.maxMember):
                    if dt_maxMember is not None and event.minMember <= int(dt_maxMember):
                        pass
                    else:
                        return r500(f"provided minMembers:{dt_minMember} cannot exceed maxMembers: {event.maxMember}")
            if dt_maxMember is not None:
                event.maxMember=int(dt_maxMember)
                if (event.minMember > event.maxMember):
                    return r500(f"provided maxMembers:{dt_maxMember} cannot be less than minMembers: {event.minMember}")
            if dt_isTeam is not None:
                event.isTeam=bool(dt_isTeam)
            if dt_markdown is not None:
                event.markdown=(dt_markdown)
            if dt_image_url is not None:
                event.image_url=(dt_image_url)
            if dt_organizers is not None:
                organisers = [o[0] for o in dt_organizers]
                update_organizers(dt_organizers)

                event.organizers= TransactionTable.serialise_emails(organisers)
            if dt_tags is not None:
                event.tags = (TransactionTable.serialise_emails(dt_tags))
            # print(dt_organizers)
            event.save()

            return r200("Event Updated")
        else:
            return r500("Empty Data recieved")
    except Exception as e:
        print(e)
        send_error_mail(inspect.    stack()[0][3], request.data, e)
        return r500(f'Error: {e}')

@api_view(['POST'])
# @lru_cache()
def display_sheet(request:Request):
    '''
    Returns the
    participants of all events in json
    '''
    # eventID = data['id'] if data != None else None
    
    data,valid = (getDataFromID())
    if valid:
        return ResponseWithCode({
            "data":data,
            "success":True
        },"Data Fetched")
    else :
        return r500("Fetch failed")
    

# @lru_cache()
# this lru cache is leading to wrong(previous data) there in finanace page
def getDataFromID() -> tuple[dict,bool]:
    '''
        
    '''
    try:
        ## get all transactions which are not archived
        teamlst = TransactionTable.objects.filter(archived = False)
        allEvents = defaultdict(list)
        
        for i, team in enumerate(teamlst):
            partis = team.get_participants()
            CACode = None
            if team.CACode:
                CACode = team.CACode.CACode
            payment = {
                "name":team.user_id.profile.username, #type:ignore
                "transId":team.transaction_id,
                "amount":team.total_fee,
                "CA":CACode,
                "parts":len(partis) + 1,
                "verified": team.verified
            }
            members = []
            if team.user_id:
                members.append({
                    "name":team.user_id.profile.username, # type:ignore
                    "email":team.user_id.email,
                    "phone":team.user_id.profile.phone, # type:ignore
                })
            for part in partis:
                if part == "": continue
                user = User.objects.filter(username=part).first() # indexing by User as username is its rimary key so faster access
                
                if user is not None:
                    prof:Profile = user.profile # type:ignore
                    members.append({
                        "name":prof.username, # type:ignore
                        "email":part,
                        "phone":prof.phone,
                    })
                else:
                    members.append( {
                        "name":"******",
                        "email":part,
                        "phone":"********"
                    })
            if team.event_id:
                allEvents[team.event_id.event_id +":" + team.event_id.name].append({
                    "members":members,
                    "payment":payment
                })
            else:
                allEvents["Deleted Events"].append({
                    "members":members,
                    "payment":payment
                }) 
               
        return allEvents,True
    except Exception as e:
        send_error_mail(inspect.stack()[0][3], {"event":"GETEVENTS"}, e)
        return {},False
