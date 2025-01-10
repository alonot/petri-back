from django.urls import path
from . import views

urlpatterns = [
    ##
    # path('login/',views.login_user,name="login"),
    path('login/',views.LoginUser.as_view(),name="login"), # Priyanshu
    path('login/verify/<token>/',views.verifyUser,name="loginVerify"), # Zeeshan
    path('register/', views.signup, name="signup"), # Zeeshan
    path('login/reverify/', views.resend_verification, name="resend_verification"), # Zeeshan
    path('forget-password/',views.ForgetPassword , name='forgetpassword'), # Zeeshan
    path('change-password/<token>/',views.ChangePassword , name="changepassword"), # Aditya
    ####

    ####
    path('auth/',views.authenticated,name='checks'), # Chirag

    ####
    path('auth/events/apply/paid/',views.apply_event_paid ,name="applyEventpaid"), # review   Zeeshan
    path('auth/events/apply/free/',views.apply_event_free ,name="applyEventfree"), # review  Aditya
    # path('auth/events/deregister/', views.deregister_event,name="event_deregister"),
    ###


    path('send_grievance',views.send_grievance,name="send_grievance"),

    ###
    path('auth/CA/create/', views.create_ca_user, name='create_ca_user'), # Chirag
    path('CA/verify/', views.verifyCA, name='verifyCA'),  # changes needed Chirag
    ###

]
