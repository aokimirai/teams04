from django.db import models

# Create your models here.
class CurrentLocation(models.Model):
    long = models.DecimalField(max_digits=9, decimal_places=6)
    lat = models.DecimalField(max_digits=9, decimal_places=6)