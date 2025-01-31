from rest_framework import serializers
from ..models.measurement import Measurement, Waist


class WaistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waist
        fields = '__all__'


class MeasurementSerializer(serializers.ModelSerializer):
    waist = WaistSerializer()

    class Meta:
        model = Measurement
        fields = '__all__'

    def create(self, validated_data):
        waist_data = validated_data.pop('waist')
        waist_instance = Waist.objects.create(**waist_data)
        return Measurement.objects.create(waist=waist_instance, **validated_data)

    def update(self, instance, validated_data):
        waist_data = validated_data.pop('waist', None)

        # Update Waist if new data is provided
        if waist_data:
            waist = instance.waist
            for key, value in waist_data.items():
                setattr(waist, key, value)
            waist.save()

        # Update Measurement fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
