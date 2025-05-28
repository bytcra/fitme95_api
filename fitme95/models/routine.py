from django.db import models
from django.conf import settings
import uuid

class Routine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='routines')
    name = models.CharField(max_length=255)
    selected_routine_days = models.JSONField(default=list)  # e.g. ["mon", "wed", "fri"]

    def __str__(self):
        return self.name
