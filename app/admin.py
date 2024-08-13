from django.contrib import admin
from .models import Profile
from .models import Event,TransactionTable,Institute,CAProfile,UserRegistrations, Extras

# Register your models here.
admin.site.register(Profile)
admin.site.register(Event)
admin.site.register(TransactionTable)
admin.site.register(Institute)
admin.site.register(CAProfile)
admin.site.register(UserRegistrations)
admin.site.register(Extras)
