from .BaseRepository import BaseRepository
from main.models import *
from django.db.models import *
from django.db.models.functions import *

class ActorRepository(BaseRepository):
    def __init__(self):
        super().__init__(Actor)
        
    def stats_by_play(self):
        return (
            self.model.objects
            .values("actor_id", "name")
            .annotate(
                plays_amount=Count("playactor__play_id")
            )
            .filter(plays_amount__gt=0)
        )
