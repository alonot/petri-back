from django.urls import path
from . import views

urlpatterns = [
    path('login/',views.user_login,name="login"),
    path('register/', views.signup, name="signup"),
    path('logout/',views.user_logout,name="logout"),
    path('user/',views.getUserInfo,name="userInfo"),
    path('event/',views.get_event_data,name="getEvent"),
    path('whoami/',views.whoami,name="whoami"),
    path('events/apply/paid',views.apply_event_paid ,name="applyEventpaid"),
    path('events/apply/free',views.apply_event_free ,name="applyEventfree"),
    path('send_grievance',views.send_grievance,name="send_grievance"),
    # path('sheets/view', views.display_sheet,name="sheets")
]
