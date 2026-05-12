from .BaseRepository import BaseRepository
from main.models import *

class HallRepository(BaseRepository):
    def __init__(self):
        super().__init__(Hall)