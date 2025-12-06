from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user_name', 'stars', 'text', 'image_url', 'created_at']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
