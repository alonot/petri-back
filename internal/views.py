
from collections import defaultdict
from functools import lru_cache
import inspect
import json
from django.http import HttpRequest, JsonResponse, QueryDict
from app.models import *
from rest_framework.response import Response
from rest_framework.request import Request

from rest_framework.decorators import api_view

from petri_ca.settings import PASSWORD
from utils import ResponseWithCode, method_not_allowed, r200, r500 , send_delete_transaction_mail, send_error_mail, send_event_verification_mail


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
        users = User.objects.all()
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
        
        failed_transactions = []

        for transaction_id in transaction_ids:
            try:
                transaction = TransactionTable.objects.get(transaction_id=transaction_id)
                if transaction.verified:
                    failed_transactions.append(transaction_id)
                    continue
                transaction.verified = True
                CA = transaction.CACode
                if CA:
                    CA.registration +=1
                    CA.save()

                # send mail to user
                user = transaction.user_id
                if user and transaction.event_id:
                    send_event_verification_mail([user.email] + TransactionTable.deserialize_emails(transaction.participants),
                                                transaction.transaction_id,transaction.event_id.name)
                #
                transaction.save()
            except TransactionTable.DoesNotExist:
                print(transaction_id)
                failed_transactions.append(transaction_id)

            except Exception as e:
                print(e)
                 # we are taking any exception here to store in failed list and then tell frontend about it
                send_error_mail(inspect.stack()[0][3], {"event":"verify:" + transaction_ids.__str__()}, e)
                failed_transactions.append(transaction_id)
                
        
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
        password = data.get("password" , None)
        if password is None:
            return r500("password is missing") 
        
        if (password != PASSWORD):
            return r500("Incorrect password. Event was not added")
        
        event = Event.objects.create(
            event_id = eventId ,
            name =  name ,
            fee = fee ,
            minMember = minMember ,
            maxMember = maxMember ,
            isTeam = isTeam,
            markdown = markdown)
        event.save()
        # print('done')
        return r200("Event saved successfully")

    except Exception as e:
        print(e)
        return r500(f'Error: {e}')


@api_view(['POST'])
def allEvents(request: Request):
    try:
        data=request.data
        if isinstance(data, (dict, QueryDict)):
            password = data.get("password" , None)
            print(password)
            if password is None:
                return ResponseWithCode({}, "password is missing", 502)
            
            if (password != PASSWORD):
                return ResponseWithCode({}, "Wrong Password", 501)
            
            # print("wd")
            events = Event.objects.all()
            res = []
            for event in events:
                res.append({
                    "name":event.name,
                    "eventId":event.event_id
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
        },"Data fetched")
    except Exception as e:
            send_error_mail(inspect.stack()[0][3], request.data, e)
            return r500("Something Bad Happened")


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
            password = data.get("password" , None)
            if password is None:
                return r500("password is missing") 

            if (password != PASSWORD):
                return r500("Incorrect password. Event was not updated")
            
            # print("wd")
            event = Event.objects.filter(event_id=dt_eventId).first()
            if event is None:
                return r500(f'No event found with eventId {dt_eventId}')
            # print(event.name,event.fee,dt_fee)

            if dt_name is not None and dt_name!= "":
                event.name=dt_name
            if dt_fee is not None:
                event.fee=int(dt_fee)
            if dt_minMember is not None:
                event.minMember=int(dt_minMember)
            if dt_maxMember is not None:
                event.maxMember=int(dt_maxMember)
            if dt_isTeam is not None:
                event.isTeam=bool(dt_isTeam)
            if dt_markdown is not None:
                event.markdown=(dt_markdown)

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
        teamlst = TransactionTable.objects.all()
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
