from django.urls import path
from . import views

urlpatterns = [
    path('events/',views.getEventUsers ,name="event"),
    path('verifyTR',views.verifyTR,name="verifyTR"),
    path('unvertrid',views.getTR,name="unvertrid"),
    path('events/unconfirmed',views.getUnconfirmed ,name="unconfirmed"),
    path('event/add/',views.addEvent,name="addEvent"),
    path('events/update/',views.updateEvent,name="updateEvent"),
   path('sheets/view/', views.display_sheet, name="display_sheet")
]
