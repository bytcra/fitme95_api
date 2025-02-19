from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    # Measurement unit preferences
    weight_unit = models.CharField(max_length=10, choices=[("kg", "Kilograms"), ("lbs", "Pounds")], default="kg")
    height_unit = models.CharField(max_length=10, choices=[("cm", "Centimeters"), ("ft", "Feet")], default="cm")
    distance_unit = models.CharField(max_length=10, choices=[("km", "Kilometers"), ("mi", "Miles")], default="cm")
    length_unit = models.CharField(max_length=10, choices=[("cm", "Centimeters"), ("in", "Inches")], default="cm")

    # User Info
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    weight = models.FloatField()
    height = models.FloatField()
    age = models.FloatField()
    gender = models.CharField(max_length=10, choices=[('m', 'Male'), ('f', 'Female')], blank=True, null=True)

    # Selected Measurements
    selected_measurements = models.JSONField(default=list)
