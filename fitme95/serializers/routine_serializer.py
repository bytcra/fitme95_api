from rest_framework import serializers

from fitme95.models.routine import Routine
from fitme95.models.task import Task
from fitme95.serializers.task_serializer import TaskSerializer


class RoutineSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True)
    id = serializers.UUIDField(required=False)

    class Meta:
        model = Routine
        fields = ['id', 'name', 'selected_routine_days', 'tasks']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data.pop('user', None)
        tasks_data = validated_data.pop('tasks')
        routine = Routine.objects.create(**validated_data, user=user)
        for task_data in tasks_data:
            Task.objects.create(routine=routine, **task_data)
        return routine

    def update(self, instance, validated_data):
        tasks_data = validated_data.pop('tasks', None)
        instance.name = validated_data.get('name', instance.name)
        instance.selected_routine_days = validated_data.get('selected_routine_days', instance.selected_routine_days)
        instance.save()

        if tasks_data is not None:
            instance.tasks.all().delete()
            for task_data in tasks_data:
                Task.objects.create(routine=instance, **task_data)
        return instance
