from django.urls import path
from . import views

urlpatterns = [
    # path('events/',views.getEventUsers ,name="event"),  # under progress
    path('verifyTR',views.verifyTR,name="verifyTR"),  # under progress   get a list of TRs and verify them Zeeshan
    path('unvertrid',views.unverifTR,name="unvertrid"), # get a list of TRs and unverify them Zeeshan
    # path('events/unconfirmed',views.getUnconfirmed ,name="unconfirmed"),  # new needed
    path('events/add/',views.addEvent,name="addEvent"),
    path('events/update/',views.updateEvent,name="updateEvent"),
    path('sheets/view/', views.display_sheet, name="display_sheet"),
    # path('unverifTR',views.unverifTR , name="unverifTR"),
    # path('cancelTR',views.cancelTR , name="cancelTR")
]