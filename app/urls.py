from django.urls import path
from . import views

urlpatterns = [
    ##
    # path('login/',views.login_user,name="login"),
    path('login/',views.LoginUser.as_view(),name="login"),
    path('register/', views.signup, name="signup"),
    path('forget-password/',views.ForgetPassword , name='forgetpassword'),
    path('change-password/<token>/',views.ChangePassword , name="changepassword"),
    ####

    ####
    path('auth/',views.authenticated,name='checks'),

    ####
    path('auth/event/',views.get_event_data,name="getEvent"),     # add isTeam Aditya
    path('auth/events/apply/paid',views.apply_event_paid ,name="applyEventpaid"), # review  add fee calculation Priyanshu
    path('auth/events/apply/free',views.apply_event_free ,name="applyEventfree"), # review  Aditya
    ###


    path('send_grievance',views.send_grievance,name="send_grievance"),

    ###
    path('auth/CA/create/', views.create_ca_user, name='create_ca_user'),
    # path('CA/verify/', views.verifyCA, name='verifyCA'),  # changes needed Chirag
    ###

]
