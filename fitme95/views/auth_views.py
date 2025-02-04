from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

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
        name = google_info.get('name')

        if not email:
            return Response({'error': 'Invalid token, email not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        user, created = CustomUser.objects.get_or_create(
            google_id=google_id,
            defaults={"name": name, "email": email}
        )

        # Generate authentication token
        token = RefreshToken.for_user(user)

        # Boolean to indicate if the onboarding setup is completed
        user_profile_exists = UserProfile.objects.filter(user=user).exists()

        return Response({
            'message': 'Login successful',
            'token': str(token.access_token),
            'refresh_token': str(token),
            'user': {
                'email': email,
                'name': name,
                'onboarding': user_profile_exists,
            }
        },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_info(request):
    # Get user info
    user = request.user
    return Response(
        {
            "message": 'User Information',
            "data": {
                'email': user.email,
                'name': user.name
            }
        },
        status=status.HTTP_200_OK)
