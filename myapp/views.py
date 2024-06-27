from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import EventTable, EventFreeTable, EventPaidTable, TransactionTable
import json

@csrf_exempt
def getEventUsers(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        eventid = data.get('eventid')
        
        try:
            event = EventTable.objects.get(id=eventid)
        except EventTable.DoesNotExist:
            return JsonResponse({'error': 'Petrichor event not found'}, status=404)
        
        if event.fee == 0:
            participants = EventFreeTable.objects.filter(event=event).values_list('email', flat=True)
        else:
            participants = EventPaidTable.objects.filter(event=event).values_list('email', flat=True)
        
        #Here we will be returning the list of all the participants in the list format 
        return JsonResponse(list(participants), safe=False)

@csrf_exempt

#This is Transaction IDS
#Here i am just iteration through all the transaction ids and marking them true or false or success if that transaction id exists in the req which i will get 
def verifyTR(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        #Here if no transaction id then it will start with a default of hte empty list 
        transaction_ids = data.get('transaction_ids', [])
        
        for transaction_id in transaction_ids:
            try:
                transaction = TransactionTable.objects.get(transaction_id=transaction_id)
                transaction.verified = True
                transaction.save()
            except TransactionTable.DoesNotExist:
                continue
        
        return JsonResponse({'status': 'success'})
