from django.contrib import admin
from .models import Profile
from .models import Event,TransactionTable

# Register your models here.
admin.site.register(Profile)
admin.site.register(Event)
admin.site.register(TransactionTable)
