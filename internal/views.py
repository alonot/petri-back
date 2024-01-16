import inspect
import json
import sys

from django.http import JsonResponse

# sys.path.append('/updatepetrichor/petrichor.backend/app') # CHANGE REQUIRED!
# from petrichor
# from updatepetrichor.petrichor.backend.app.models import *


from rest_framework.decorators import api_view
from app.models import *
from rest_framework.response import Response
from app.views import send_error_mail
# from app.views import send_error_mail
from resp import r200, r500
# Create your views here.
@api_view(['GET'])
def getUnconfirmed(request):
    try:
        unconfirmed_users=set(EventTable.objects.exclude(transactionId="Internal Student").values_list('user_id'))
        print(unconfirmed_users)
        unconfirmed_list=[]
        for user in unconfirmed_users:
            user_id=user[0]

            events=EventTable.objects.filter(user_id=user_id)
            event_dict=dict()
            for event in events:
                if not event.verified:
                    event_dict[Event.objects.get(eventId=event.eventId).name]=event.transactionId

            user_name=Profile.objects.get(userId=user_id).username
            unconfirmed_list.append({user_name:event_dict})

        return Response(
            {
                "data":unconfirmed_list
            }
        )
    except Exception as e:
        return r500("Oopsie Doopsie")


@api_view(['GET'])
def getTR(req):
    unconfirmed = EventTable.objects.filter(verified = False)
    data = []
    for u in unconfirmed:
        if 'test' in u.transactionId:
            continue
        try:
            event = Event.objects.get(eventId=u.eventId)
        except Exception as e:
            if u.eventId:
                print(u.eventId, "doesnt exist")
            continue
        
        emails = u.get_emails()
        if not emails:
            continue
        main_guy = emails[0]
        try:
            main_user = Profile.objects.get(email=main_guy)
        except Exception as e:
            if main_guy:
                print(main_guy, "doesnt exist")
            continue
        

        data.append({
            'transID': u.transactionId,
            'amount': event.fee,
            'name': main_user.username,
            'phone': main_user.phone,
            'parts': len(emails)
        })
    
    return Response(data)


@api_view(['GET'])
def getEventUsers(request):
    if request.method == "GET":
        events=[]
        try:
            allEvents=Event.objects.all()
            for event in allEvents:
                participantsId=set(EventTable.objects.filter(eventId=event.eventId).values_list('user_id'))
                participants=[]
                for id in participantsId:
                    user=Profile.objects.get(userId=id[0])
                    participants.append({
                        "name":user.username,
                        "email":user.email,
                        "phone":user.phone,
                    })
                events.append({
                    "name": event.name,
                    "participants":participants
                })


            print("Coreect")
            return Response({
                'status': 200,
                'data':["name","email","phone"],
                "events":events
            })
        except Exception as e:
            return r500("Opps!! Unable to complete the request!!!")


@api_view(['POST'])
def verifyTR(request):
    try:
        if request.data == None:
            return r500("Invalid Form")

        data=request.data
        print("print:",data)

        inputTRId=data['TransactionId'].strip()
        try:
            event=EventTable.objects.get(transactionId=inputTRId)
        except Exception as e:
            return Response({
                'status':404,
                'verified': False,
                'msg':"Not found in our db"
            })
        event.verified = True
        event.save()
        return Response({
            'status' : 200,
            'verified': True
        })




    except Exception as e:
        send_error_mail(inspect.stack()[0][3], request.data, e)
        return Response({
                'status':400,
                'verified': False,
                'msg':"Opps!! Unable to complete the request!!!"
            })

@api_view(['POST'])
def addEvent(request):
    try:
        data=request.data
        if data == None:
            return r500("Please send some info about the event")
        event = Event.objects.create(
            eventId=data["id"],
            name=data["name"],
            fee=data["fees"],
            minMember=data["minMemeber"],
            maxMember=data["maxMemeber"]
        )
        event.save()
        print('done')
        return r200("Event saved successfully")

    except Exception as e:
        print(e)
        return r500(f'Error: {e}')


@api_view(["POST"])
def updateEvent(request):
    try:
        data=request.data
        if data:
            dt_eventId=data['eventId']
            if dt_eventId is not None:
                return r500('Please provide an eventId')
            dt_name=data['name']
            dt_fee=data['fee']
            dt_minMember=data['minMember']
            dt_maxMember=data['maxMember']

            event= Event.objects.get(eventId=dt_eventId)
            print(event.name,event.fee,dt_fee)
            if dt_name is not None:
                event.name=dt_name
            if dt_fee is not None:
                event.fee=dt_fee
            if dt_minMember is not None:
                event.minMember=dt_minMember
            if dt_maxMember is not None:
                event.maxMember=dt_maxMember

            event.save()

            return r200("Event Updated")

    except Exception as e:
        print(e)
        # send_error_mail(inspect.stack()[0][3], request.data, e)
        return r500(f'Error: {e}')

'''
Takes in eventID from the request and returns the the participants of that event in json

'''
@api_view(['POST'])
def display_sheet(request):
    data = request.data
    eventID = data['id'] if data != None else None
    if eventID:
        teamlst = EventTable.objects.filter(eventId=eventID)
        teamdict = {}  # info of each team
        participants = []  # participants to be added

        for i, team in enumerate(teamlst):
            partis = list(team.emails.split("\n"))
            teamdict['team'] = f"Team{i + 1}"
            teamdict["details"] = []
            for part in partis:
                try:
                    prof = Profile.objects.get(email=part)
                    detail = {
                        "name": f"{prof.username}",
                        "email": f"{part}",
                        "phone": f"{prof.phone}",
                        "CA": f"{team.CACode}",
                        "verified":f"{team.verified}"
                    }
                except:
                    detail = {
                        "name": f"not registered",
                        "email": f"{part}",
                        "phone": f"not registered",
                        "CA": f"{team.CACode}",
                        "verified":f"{team.verified}"
                    }
                teamdict["details"].append(detail.copy())

            participants.append(teamdict.copy())

        event = {
            "name": f"{Event.objects.get(eventId=eventID).name}",
            "participants": participants
        }

        response = json.dumps(event)
        print(type(Response(event)))

        return Response(event)
