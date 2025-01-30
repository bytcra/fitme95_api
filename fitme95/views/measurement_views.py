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
