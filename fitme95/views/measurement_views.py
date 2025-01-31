from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models.measurement import Measurement
from ..serializers.measurement_serializer import MeasurementSerializer


@api_view(['Get'])
def get_measurements(request):
    try:
        measurements = Measurement.objects.all()
        serializer = MeasurementSerializer(data=measurements, many=True)
        if not serializer.is_valid():
            return Response({'message': 'No measurements found. Please add a measurement', 'data': '[]'},
                            status=status.HTTP_200_OK)

        return Response({'message': 'Your measurements', 'data': serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_measurement(request):
    serializer = MeasurementSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def update_measurement(request, pk):
    try:
        measurement = Measurement.objects.get(pk=pk)
    except Measurement.DoesNotExist:
        return Response({"error": "Measurement not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = MeasurementSerializer(measurement, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_measurement(request, pk):
    try:
        measurement = Measurement.objects.get(pk=pk)
    except Measurement.DoesNotExist:
        return Response({"error": "Measurement not found"}, status=status.HTTP_404_NOT_FOUND)

    measurement.delete()
    return Response({"message": "Measurement deleted successfully"}, status=status.HTTP_204_NO_CONTENT)