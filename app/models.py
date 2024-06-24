from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Profile(models.Model):
    username = models.TextField()
    email = models.EmailField(default=True,primary_key=True)
    



