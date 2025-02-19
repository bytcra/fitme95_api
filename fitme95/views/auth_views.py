from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import AccessToken

from ..models.user import CustomUser
from ..models.user_profile import UserProfile
from ..utils import fm_response


@api_view(['POST'])
@permission_classes([])
def google_login(request):
    try:
        id_token_received = request.data.get('id')

        if not id_token_received:
            return fm_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="ID Token is required"
            )

        # Validate token with Firebase
        try:
            google_info = id_token.verify_firebase_token(id_token_received, requests.Request())
        except ValueError as e:
            return fm_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid ID token",
                errors=str(e)
            )

        # Extract user info
        email = google_info.get('email')
        google_id = google_info.get('sub')
        full_name = google_info.get('name')

        # Get first and last name
        first_name = google_info.get('given_name', '')
        last_name = google_info.get('family_name', '')

        # If first_name or last_name is missing, split full_name
        if not first_name or not last_name:
            name_parts = full_name.split()
            first_name = name_parts[0] if name_parts else ''
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        if not email:
            return fm_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Email not found in token"
            )

            # Atomic transaction to avoid partial updates
        with transaction.atomic():
            user, created = CustomUser.objects.get_or_create(
                google_id=google_id,
                defaults={"first_name": first_name, "last_name": last_name, "email": email}
            )

            # Generate authentication token
            token = RefreshToken.for_user(user)

            # Check if onboarding is completed
            user_profile_exists = UserProfile.objects.filter(user=user).exists()

            # Token Expiry Time in Milliseconds
            token_expiry_ms = int(token.access_token.lifetime.total_seconds() * 1000)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return fm_response(
            status_code=status_code,
            message="Login successful",
            data={
                'token': str(token.access_token),
                'refresh_token': str(token),
                'expires_in': token_expiry_ms,
                'user': {
                    'id': google_id,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_onboarded': user_profile_exists,
                },
            },
        )

    except AuthenticationFailed as e:
        return fm_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Login Failed",
            errors=str(e),
        )

    except Exception as e:
        return fm_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal Server Error",
            errors=str(e)
        )


@api_view(['GET'])
def user_info(request):
    try:
        # Get user info
        user = request.user
        if not user:
            return fm_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Unauthorized access",
                errors=["User authentication failed"]
            )

        # Boolean to indicate if the onboarding setup is completed
        user_profile_exists = UserProfile.objects.filter(user=user).exists()

        return fm_response(
            status_code=status.HTTP_200_OK,
            message="User Information Retrieved",
            data={
                'user': {
                    'id': user.google_id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_onboarded': user_profile_exists,
                },
            }
        )

    except ObjectDoesNotExist as e:
        return fm_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User Not Found",
            errors=str(e)
        )

    except Exception as e:
        return fm_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal Server Error",
            errors=str(e)
        )


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                access_token = response.data.get("access")
                refresh_token = response.data.get("refresh")

                # Get token expiry time in milliseconds
                token = AccessToken(access_token)
                expires_in = int(token.lifetime.total_seconds() * 1000)

                return fm_response(
                    status_code=status.HTTP_200_OK,
                    message="Token refreshed successfully",
                    data={
                        "token": access_token,
                        "refresh_token": refresh_token,
                        "expires_in": expires_in
                    }
                )

            return fm_response(
                status_code=response.status_code,
                message="Token refresh failed",
                errors=response.data.get("detail", "Unknown error")
            )

        except TokenError as e:
            return fm_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid or expired refresh token",
                errors=str(e)
            )

        except Exception as e:
            return fm_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Token refresh failed",
                errors=str(e)
            )
