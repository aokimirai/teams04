from django.db import models

# Create your models here.
class CurrentLocation(models.Model):
    longitude = models.CharField(max_length=128)
    latitude = models.IntegerField()