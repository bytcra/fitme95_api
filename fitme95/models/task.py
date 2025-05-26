from django.db import models
import uuid
from .routine import Routine

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('notCompleted', 'Not Completed'),
        ('skipped', 'Skipped'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return self.name
