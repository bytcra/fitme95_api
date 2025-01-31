from django.db import models
from .user import User


class Waist(models.Model):
    waist = models.FloatField()
    is_above = models.BooleanField()
    is_below = models.BooleanField()


class Measurement(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="measurements", null=True, blank=True)
    weight = models.FloatField()
    waist = models.OneToOneField(Waist, on_delete=models.CASCADE, related_name='measurement')
    fat = models.FloatField()
    chest = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        self.waist.delete()
        super().delete(*args, **kwargs)
