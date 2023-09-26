# resources.py
from import_export import resources
from .models import PlayerInfo

class PlayerInfoResource(resources.ModelResource):
    class Meta:
        model = PlayerInfo