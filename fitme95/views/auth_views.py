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
from django.db.utils import IntegrityError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models.user import CustomUser
from ..models.user_profile import UserProfile
from ..serializers.user_profile_serializer import UserProfileSerializer
from ..utils import fm_response


@swagger_auto_schema(
    method='post',
    operation_description="Login a user using a Google ID token. Returns access & refresh tokens.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['id'],
        properties={
            'id': openapi.Schema(type=openapi.TYPE_STRING, description='Google ID Token')
        }
    ),
    responses={
        200: "Login successful",
        201: "User created and login successful",
        400: "Bad request (e.g. missing ID token)",
        401: "Invalid token or authentication failed",
        500: "Internal server or database error"
    }
)
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

        try:
            # Atomic transaction to avoid partial updates
            with transaction.atomic():
                user, created = CustomUser.objects.get_or_create(
                    google_id=google_id,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email
                    }
                )

                # Generate authentication token
                token = RefreshToken.for_user(user)

                # Check if onboarding is completed
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    profile_data = UserProfileSerializer(user_profile).data  # Serialize profile data
                except UserProfile.DoesNotExist:
                    profile_data = None

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
                        'is_onboarded': profile_data is not None,
                        'profile': profile_data,
                    },
                },
            )

        except IntegrityError as e:
            return fm_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Database error occurred",
                errors=str(e)
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


@swagger_auto_schema(
    method='get',
    operation_description="Fetch current authenticated user profile information.",
    responses={
        200: "User info retrieved successfully",
        401: "Unauthorized access",
        404: "User not found",
        500: "Server error"
    }
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

        try:
            user_profile = UserProfile.objects.get(user=user)
            profile_data = UserProfileSerializer(user_profile).data  # Serialize profile data
        except UserProfile.DoesNotExist:
            profile_data = None

        return fm_response(
            status_code=status.HTTP_200_OK,
            message="User Information Retrieved",
            data={
                'user': {
                    'id': user.google_id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_onboarded': profile_data is not None,
                    'profile': profile_data,
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


@swagger_auto_schema(
    operation_description="Refresh the access token using a valid refresh token.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['refresh'],
        properties={
            'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token')
        }
    ),
    responses={
        200: "Token refreshed successfully",
        400: "Missing refresh token",
        401: "Invalid or expired refresh token",
        500: "Internal server error"
    }
)
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            # Check if refresh token is provided
            if 'refresh' not in request.data:
                return fm_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Missing refresh token",
                    errors={'refresh': 'This field is required'}
                )

            try:
                response = super().post(request, *args, **kwargs)
            except TokenError as e:
                return fm_response(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message="Invalid or expired refresh token",
                    errors=str(e)
                )

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

        except Exception as e:
            return fm_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Token refresh failed",
                errors=str(e)
            )
