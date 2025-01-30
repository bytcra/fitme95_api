from django.urls import path
from .views import measurement_views

urlpatterns = [
    path('measurements', measurement_views.get_measurements),
]