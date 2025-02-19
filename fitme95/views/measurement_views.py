from rest_framework.decorators import api_view
from rest_framework import status
from ..models.measurement import Measurement
from ..serializers.measurement_serializer import MeasurementSerializer
from django.db.utils import IntegrityError
from ..utils import fm_response


@api_view(['POST'])
def create_measurement(request):
    if not request.data:
        return fm_response(
            message="No data provided",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    serializer = MeasurementSerializer(data=request.data)

    if serializer.is_valid():
        try:
            serializer.save(user=request.user)
            return fm_response(
                message="Measurement created successfully",
                data={'measurement': serializer.data},
                status_code=status.HTTP_201_CREATED
            )
        except IntegrityError as e:
            return fm_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Database error occurred while saving measurement",
                errors=str(e)
            )

    return fm_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Invalid measurement data",
        errors=serializer.errors
    )


@api_view(['GET'])
def get_measurements(request):
    try:
        measurements = Measurement.objects.filter(user=request.user)
        if not measurements.exists():
            return fm_response(
                status_code=status.HTTP_200_OK,
                message="No measurements found. Please add a measurement",
                data=[],
            )

        serializer = MeasurementSerializer(instance=measurements, many=True)
        return fm_response(
            status_code=status.HTTP_200_OK,
            message="Your measurements",
            data={'measurements': serializer.data}
        )

    except Exception as e:
        return fm_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An error occurred while fetching measurements",
            errors=str(e)
        )


@api_view(['PUT'])
def update_measurement(request, measurement_id):
    if not request.data:
        return fm_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="No data provided"
        )

    try:
        measurement = Measurement.objects.get(id=measurement_id, user=request.user)
    except Measurement.DoesNotExist as e:
        return fm_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Measurement not found",
            errors=str(e)
        )

    serializer = MeasurementSerializer(measurement, data=request.data, partial=True)

    if serializer.is_valid():
        try:
            serializer.save()
            return fm_response(
                status_code=status.HTTP_200_OK,
                message="Measurement updated successfully",
                data={'measurement': serializer.data}
            )
        except IntegrityError as e:
            return fm_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Database error occurred while updating measurement",
                errors=str(e)
            )

    return fm_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Invalid measurement data",
        errors=serializer.errors
    )


@api_view(['DELETE'])
def delete_measurement(request, measurement_id):
    try:
        measurement = Measurement.objects.get(id=measurement_id, user=request.user)
    except Measurement.DoesNotExist as e:
        return fm_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Measurement not found",
            errors=str(e)
        )

    try:
        measurement.delete()
        return fm_response(
            status_code=status.HTTP_200_OK,
            message="Measurement deleted successfully"
        )
    except Exception as e:
        return fm_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to delete measurement",
            errors=str(e)
        )
