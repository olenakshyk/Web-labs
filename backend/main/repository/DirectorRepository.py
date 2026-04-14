from .BaseRepository import BaseRepository
from main.models import *

class DirectorRepository(BaseRepository):
    def __init__(self):
        super().__init__(Director)