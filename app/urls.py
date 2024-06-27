from django.urls import path
from . import views

urlpatterns = [
    path('login/',views.login_user,name="login"),
    path('logout/',views.logout_user,name='logout_user'),
    path('api/apply_event_paid/', apply_event_paid, name='apply_event_paid'),
    path('api/apply_event_free/', apply_event_free, name='apply_event_free'),
    path('auth/',views.authenticated,name='checks')
    # path('refresh/')
]
