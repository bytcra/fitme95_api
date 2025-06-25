from rest_framework import serializers
from ..models.task import Task

class TaskSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = Task
        fields = ['id', 'name', 'status']
