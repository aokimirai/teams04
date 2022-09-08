from django.contrib import admin

# Register your models here.
from .models import CurrentLocation
@admin.register(CurrentLocation)
class CurrentLocationAdmin(admin.ModelAdmin):
    pass