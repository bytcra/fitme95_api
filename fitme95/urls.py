from django.urls import path
from .views import measurement_views
from .views import user_view

urlpatterns = [
    # Measurement
    path('measurements/create', measurement_views.create_measurement, name='create_measurement'),
    path('measurements', measurement_views.get_measurements, name='get_measurements'),
    path('measurements/update/<int:measurement_id>', measurement_views.update_measurement, name='update_measurement'),
    path('measurements/delete/<int:measurement_id>', measurement_views.delete_measurement, name='delete_measurement'),

    # Authentication
    path('login', user_view.google_login, name='login'),
    path('onboarding', user_view.setup_user_profile, name='setup_profile'),
    path('user-info', user_view.user_info, name='user_info')
]
