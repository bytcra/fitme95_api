from django.db import IntegrityError
from rest_framework.decorators import api_view
from rest_framework import status

from fitme95.utils import fm_response
from ..models.routine import Routine
from ..serializers.routine_serializer import RoutineSerializer

@api_view(['GET'])
def get_routines(request):
    try:
        routines = Routine.objects.filter(user=request.user)
        if not routines.exists():
            return fm_response(
                status_code=status.HTTP_200_OK,
                message="No routines found. Please add a routine",
                data={'routines': []}
            )
        serializer = RoutineSerializer(routines, many=True)
        return fm_response(
            status_code=status.HTTP_200_OK,
            message="Your routines",
            data={'routines': serializer.data}
        )
    except Exception as e:
        return fm_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An error occurred while fetching routines",
            errors=str(e)
        )

@api_view(['POST'])
def create_routine(request):
    if not request.data:
        return fm_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="No data provided"
        )
    serializer = RoutineSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        try:
            serializer.save(user=request.user)
            return fm_response(
                status_code=status.HTTP_201_CREATED,
                message="Routine created successfully",
                data={'routine': serializer.data}
            )
        except IntegrityError as e:
            return fm_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Database error occurred while saving routine",
                errors=str(e)
            )
    return fm_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Invalid routine data",
        errors=serializer.errors
    )

@api_view(['PUT'])
def update_routine(request, pk):
    if not request.data:
        return fm_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="No data provided"
        )
    try:
        routine = Routine.objects.get(pk=pk, user=request.user)
    except Routine.DoesNotExist as e:
        return fm_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Routine not found",
            errors=str(e)
        )
    serializer = RoutineSerializer(routine, data=request.data, context={'request': request})
    if serializer.is_valid():
        try:
            serializer.save()
            return fm_response(
                status_code=status.HTTP_200_OK,
                message="Routine updated successfully",
                data={'routine': serializer.data}
            )
        except IntegrityError as e:
            return fm_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Database error occurred while updating routine",
                errors=str(e)
            )
    return fm_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Invalid routine data",
        errors=serializer.errors
    )

@api_view(['DELETE'])
def delete_routine(request, pk):
    try:
        routine = Routine.objects.get(pk=pk, user=request.user)
    except Routine.DoesNotExist as e:
        return fm_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Routine not found",
            errors=str(e)
        )
    try:
        routine.delete()
        return fm_response(
            status_code=status.HTTP_200_OK,
            message="Routine deleted successfully"
        )
    except Exception as e:
        return fm_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to delete routine",
            errors=str(e)
        )