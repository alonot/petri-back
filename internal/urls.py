from django.urls import path
from . import views

urlpatterns = [
    path('verifyTR',views.verifyTR,name="verifyTR"),  # under progress  get a list of TRs and verify them Zeeshan
    path('unvertrid',views.unverifyTRs,name="unvertrid"), # get a list of TRs and unverify them Zeeshan
    # UNverify : 
    #   delete TransactionTableEntry,
        # for each participants ->   userRegistration transID remove

    path('events/unconfirmed',views.getUnconfirmed ,name="unconfirmed"),  # new needed Aditya

    # Events 
    path('event/add/',views.addEvent,name="addEvent"),  # requires change Chirag
    path('events/update/',views.updateEvent,name="updateEvent"),  # requires change Chirag
    # 
    path('sheets/view/', views.display_sheet, name="display_sheet"), # review, changes needed add fee Zeeshan
]
