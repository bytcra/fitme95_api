from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import measurement_views
from .views import auth_views, user_views

urlpatterns = [
    # Measurement
    path('measurements/create', measurement_views.create_measurement, name='create_measurement'),
    path('measurements', measurement_views.get_measurements, name='get_measurements'),
    path('measurements/update/<int:measurement_id>', measurement_views.update_measurement, name='update_measurement'),
    path('measurements/delete/<int:measurement_id>', measurement_views.delete_measurement, name='delete_measurement'),

    # Authentication
    path('login', auth_views.google_login, name='login'),
    path('user-info', auth_views.user_info, name='user_info'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('onboarding', user_views.setup_user_profile, name='setup_profile'),
]
