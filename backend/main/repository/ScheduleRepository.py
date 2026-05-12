from .BaseRepository import BaseRepository
from main.models import *


class ScheduleRepository(BaseRepository):
    def __init__(self):
        super().__init__(Schedule)

    def get_stats(self):
        return {"total": len(super().get_all())}

    def get_with_play(self, city=None, schedule_id=None):
        qs = (
            Schedule.objects
            .select_related("play", "hall__theatre")
            .order_by("date", "time")
        )

        if city:
            qs = qs.filter(hall__theatre__city__iexact=city)

        if schedule_id:
            qs = qs.filter(schedule_id=schedule_id)

        return qs.values(
            "schedule_id",
            "date",
            "time",
            "play_id",
            "play__name",
            "play__description",
            "play__author",
            "play__duration",
            "hall_id",
            "hall__name",
            "hall__theatre__name",
            "hall__theatre__city",
        )
