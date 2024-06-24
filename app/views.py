from django.conf import settings
from django.shortcuts import render
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from rest_framework.decorators  import api_view
from rest_framework.response import Response 
# Create your views here.
from django.http import HttpRequest
from .models import Profile
import datetime

@api_view(['POST'])
def login_user(request: HttpRequest):
    if request.method != "POST":
        return
    print("K")
    if request.data is None:
        print("No data")
        return Response({
            'success' : False,
            'message' : "Data not received"
        },status=500)

    email = request.data['email'].strip()
    password = request.data['password']

    print("Hello")
    user = authenticate(username = email, password = password)
    if user is None:
        # print("user:","Not")
        return Response({
            'success' : False,
            'message' : "Invalid Credentials"
        },status=200)
    else:
        login(request,user)
        user_profile = Profile.objects.get(email = email)
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
        print("Logged")
        return res

@api_view(['POST'])
def logout_user(request:HttpRequest):
    if request.method == 'POST':
        try:
            logout(request)
            return Response({
                'success':True,
                'message':'Done'
            },200)
        except Exception as e:
            # any exception, the logout function does not throws 
            # error if session not present.
            return Response({
                'success':False,
                'message':'some error occured. Reported to our developers'
            },400)
    
@api_view(['POST'])
def authenticated(request:HttpRequest):
    if request.method != 'POST':
        return Response({
            "status":301
        },301)
        # print(request.user.is_authenticated)
    # print(request.get_host())
    token = request.COOKIES.get('session_token')
    print(request.COOKIES)
    print(token)
    try:
        session = Session.objects.get(session_key= token)
        session_data = session.get_decoded()    
        uid = session_data.get('_auth_user_id')
        user = User.objects.get(id=uid)
        user_profile = Profile.objects.get(email = user.username)
        return Response({
            'success':True,
            'message':'Yes',
            'username':user_profile.username
        },200)
    except Session.DoesNotExist:
        
        return Response({
            'success':False,
            'message':'No'
        },200)  