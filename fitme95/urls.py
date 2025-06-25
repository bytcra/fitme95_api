from django.urls import path
from .views import measurement_views, routine_view
from .views import auth_views, user_views
from .views.auth_views import CustomTokenRefreshView
from .views import health_check

urlpatterns = [
    # Measurement
    path('measurements/create', measurement_views.create_measurement, name='create_measurement'),
    path('measurements', measurement_views.get_measurements, name='get_measurements'),
    path('measurements/update/<int:measurement_id>', measurement_views.update_measurement, name='update_measurement'),
    path('measurements/delete/<int:measurement_id>', measurement_views.delete_measurement, name='delete_measurement'),

    # Authentication
    path('login', auth_views.google_login, name='login'),
    path('user-info', auth_views.user_info, name='user_info'),
    path('refresh-token', CustomTokenRefreshView.as_view(), name='refresh_token'),

    path('onboarding', user_views.setup_user_profile, name='setup_profile'),

    path('health', health_check, name='health_check'),

    # Routines
    path('routines', routine_view.get_routines, name='get-routines'),
    path('routines/create', routine_view.create_routine, name='create-routines'),
    path('routines/tasks/update/<uuid:task_id>', routine_view.update_routine_task, name='update_task_status'),
    path('routines/update/<uuid:pk>', routine_view.update_routine, name='update-routines'),
    path('routines/delete/<uuid:pk>', routine_view.delete_routine, name='delete-routines'),
]
