from django.db import models


class Measurement(models.Model):
    weight = models.FloatField()
    chest = models.FloatField()
    waist = models.FloatField()
    fat = models.SmallIntegerField()
