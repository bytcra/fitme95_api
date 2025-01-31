from django.urls import path
from .views import measurement_views

urlpatterns = [
    path('measurements/create', measurement_views.create_measurement, name='create_measurement'),
    path('measurements', measurement_views.get_measurements, name='get_measurements'),
    path('measurements/update/<int:pk>', measurement_views.update_measurement, name='update_measurement'),
    path('measurements/delete/<int:pk>', measurement_views.delete_measurement, name='delete_measurement'),
]
