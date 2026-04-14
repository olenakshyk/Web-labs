from .BaseRepository import BaseRepository
from main.models import *

class PlayDirectorRepository(BaseRepository):
    def __init__(self):
        super().__init__(PlayDirector)