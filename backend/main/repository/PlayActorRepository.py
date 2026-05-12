from .BaseRepository import BaseRepository
from main.models import *

class PlayActorRepository(BaseRepository):
    def __init__(self):
        super().__init__(PlayActor)