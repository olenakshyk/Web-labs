from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import Play
import os

@receiver(pre_delete, sender=Play)
def delete_play_image(sender, instance, **kwargs):
    if instance.image and os.path.isfile(instance.image.path):
        os.remove(instance.image.path)