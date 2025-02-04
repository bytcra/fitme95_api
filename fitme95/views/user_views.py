from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models.user_profile import UserProfile
from ..serializers.user_profile_serializer import UserProfileSerializer


@api_view(['POST'])
def setup_user_profile(request):
    user = request.user

    # Check if a profile exists, else create one with defaults
    user_profile, created = UserProfile.objects.get_or_create(user=user, defaults=request.data)

    if not created:
        # If the profile already exists, update it with provided data
        serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": 'User Profile Updated Successfully', "data": serializer.data},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # If a new profile was created, return the created profile data
    serializer = UserProfileSerializer(instance=user_profile)
    return Response({"message": "User Profile Setup is completed", "data": serializer.data},
                    status=status.HTTP_201_CREATED)