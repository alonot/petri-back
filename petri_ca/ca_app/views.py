from django.shortcuts import render
from django.http import JsonResponse
from .models import CAUser
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def verify_ca_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        try:
            ca_user = CAUser.objects.get(user_id=user_id)
            return JsonResponse({'status': 'success', 'random_string': ca_user.random_string})
        except CAUser.DoesNotExist:
            return JsonResponse({'status': 'failure', 'message': 'User not found'})        #Here just sending that the user is not found for the verification process 

@csrf_exempt
def create_ca_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        ca_user, created = CAUser.objects.get_or_create(user_id=user_id)
        if created:
            ca_user.save()
        return JsonResponse({'status': 'success', 'random_string': ca_user.random_string})
