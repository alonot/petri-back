from django.urls import path
from .views import verify_ca_user, create_ca_user

urlpatterns = [
    path('verify/', verify_ca_user, name='verify_ca_user'),
    path('create/', create_ca_user, name='create_ca_user'),
]
