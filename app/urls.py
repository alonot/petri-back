from django.urls import path
from . import views

urlpatterns = [
    ##
    path('login/',views.login_user,name="login"),
    path('register/', views.signup, name="signup"),
    path('logout/',views.logout_user,name='logout_user'),
    path('auth/',views.authenticated,name='checks'),
    ####
    path('event/',views.get_event_data,name="getEvent"),    
    path('events/apply/paid',views.apply_event_paid ,name="applyEventpaid"), # to be added
    path('events/apply/free',views.apply_event_free ,name="applyEventfree"), # to be added
    path('send_grievance',views.send_grievance,name="send_grievance"),
]