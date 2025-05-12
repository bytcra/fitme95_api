from rest_framework import serializers
from ..models.user_profile import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('user',)

    @staticmethod
    def validate_measurable_items(value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Measurable items must be a list")
        valid_items = ["weight", "height", "chest", "waist", "hips", "thigh", "arm"]
        invalid_items = [item for item in value if item not in valid_items]
        if invalid_items:
            raise serializers.ValidationError(
                f"Invalid measurable items: {', '.join(invalid_items)}. Must be from: {', '.join(valid_items)}")
        return value
