from django.db import models

class EventTable(models.Model):
    name = models.CharField(max_length=100)                 #Set the length for the name of the eventsss
    fee = models.IntegerField()  
    min_members = models.IntegerField(default=0)            #Random number for the min member 
    max_members = models.IntegerField(default=1000)         #Maximum member for the event 

    def __str__(self):
        return self.name


class Extras(models.Model):
    extra_id = models.AutoField(primary_key=True)  # Here I have set this to the autofild mode whcih will  auto-generate primary key
    price = models.IntegerField()

    def __str__(self):
        return f"Extra ID: {self.extra_id}, Price: {self.price}"

class EventFreeTable(models.Model):
    event = models.ForeignKey(EventTable, on_delete=models.CASCADE)
    email = models.EmailField()

class EventPaidTable(models.Model):
    event = models.ForeignKey(EventTable, on_delete=models.CASCADE)
    email = models.EmailField()

class TransactionTable(models.Model):
    transaction_id = models.CharField(max_length=100, unique=True)          #i have taken randomly
    verified = models.BooleanField(default=False)
