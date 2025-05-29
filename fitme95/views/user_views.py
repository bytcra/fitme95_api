from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view

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
        # Check if a profile exists
        try:
            user_profile = UserProfile.objects.get(user=user)
            created = False
        except UserProfile.DoesNotExist:
            # For new profiles, validate all required fields
            serializer = UserProfileSerializer(data=request.data)
            if not serializer.is_valid():
                return fm_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Invalid profile data",
                    errors=serializer.errors
                )
            # Create new profile with validated data
            serializer.save(user=user)
            return fm_response(
                status_code=status.HTTP_201_CREATED,
                message="User Profile Setup Completed",
                data=serializer.data
            )

        if not created:
            # If the profile already exists, update it with provided data
            serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return fm_response(
                    status_code=status.HTTP_200_OK,
                    message="User Profile Updated Successfully",
                    data={'profile': serializer.data}
                )
            return fm_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid profile data",
                errors=serializer.errors,
            )

    except IntegrityError as e:
        return fm_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database integrity error occurred while saving user profile",
            errors=str(e)
        )
    except Exception as e:
        return fm_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An error occurred while processing your request",
            errors=str(e)
        )
