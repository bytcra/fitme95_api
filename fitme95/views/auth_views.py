from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from ..models.user import CustomUser
from ..models.user_profile import UserProfile


@api_view(['POST'])
@permission_classes([])
def google_login(request):
    try:
        id_token_received = request.data.get('id')

        if not id_token_received:
            return Response({'error': 'ID Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate token with Firebase
        google_info = id_token.verify_firebase_token(
            id_token_received,
            requests.Request(),
        )

        # User info
        email = google_info.get('email')
        google_id = google_info.get('sub')
        full_name = google_info.get('name', '')

        # Try to get first and last name directly
        first_name = google_info.get('given_name', '')
        last_name = google_info.get('family_name', '')

        # If first_name or last_name is missing, split full_name
        if not first_name or not last_name:
            name_parts = full_name.split()
            first_name = name_parts[0] if name_parts else ''
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''


        if not email:
            return Response({'error': 'Invalid token, email not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        user, created = CustomUser.objects.get_or_create(
            google_id=google_id,
            defaults={"first_name": first_name, "last_name": last_name, "email": email}
        )

        # Generate authentication token
        token = RefreshToken.for_user(user)

        # Boolean to indicate if the onboarding setup is completed
        user_profile_exists = UserProfile.objects.filter(user=user).exists()

        # Token Expiry Time in Milliseconds
        token_expiry_ms = int(token.access_token.lifetime.total_seconds() * 1000)

        return Response({
            'message': 'Login successful',
            'data': {
                'token': str(token.access_token),
                'refresh_token': str(token),
                'expires_in': token_expiry_ms,
                'user': {
                    'id': google_id,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_onboarded': user_profile_exists,
                }}
        },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_info(request):
    # Get user info
    user = request.user

    # Boolean to indicate if the onboarding setup is completed
    user_profile_exists = UserProfile.objects.filter(user=user).exists()

    return Response(
        {
            "message": 'User Information',
            "data": {
                'user': {
                    'id': user.google_id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_onboarded': user_profile_exists,
                }
            }
        },
        status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")

            # Get token expiry time
            token = AccessToken(access_token)

            expires_in = int(token.lifetime.total_seconds() * 1000)

            return Response({
                "message": "Token refreshed successfully",
                "data": {
                    "token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": expires_in
                }
            }, status=status.HTTP_200_OK)

        return response
