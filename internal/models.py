from django.db import models

# Create your models here.

class Image(models.Model):
    name = models.TextField(primary_key=True)
    image = models.BinaryField()