from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models.user_profile import UserProfile
from ..serializers.user_profile_serializer import UserProfileSerializer
from ..utils import fm_response


@api_view(['POST'])
def setup_user_profile(request):
    user = request.user

    if not request.data:
        return fm_response(
            message="No data provided",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Check if a profile exists, else create one with defaults
        user_profile, created = UserProfile.objects.get_or_create(user=user, defaults=request.data)

        if not created:
            # If the profile already exists, update it with provided data
            serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return fm_response(
                    status_code=status.HTTP_200_OK,
                    message="User Profile Updated Successfully",
                    data=serializer.data
                )
            return fm_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid profile data",
                errors=serializer.errors,
            )

        # If a new profile was created, return the created profile data
        serializer = UserProfileSerializer(instance=user_profile)
        return fm_response(
            status_code=status.HTTP_201_CREATED,
            message="User Profile Setup Completed",
            data=serializer.data
        )
    except IntegrityError as e:
        return fm_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database integrity error occurred while saving user profile",
            errors=str(e)
        )
