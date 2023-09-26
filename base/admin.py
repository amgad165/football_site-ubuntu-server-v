from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(team_data_modes)
admin.site.register(PlayerInfo)