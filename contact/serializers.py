# contact/serializers.py

from rest_framework import serializers
from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    responded_by_name = serializers.CharField(source='responded_by.username', read_only=True)

    class Meta:
        model = ContactMessage
        fields = '__all__'
        read_only_fields = [
            'created_at', 'updated_at', 'resolved_at',
            'responded_by', 'admin_response', 'status', 'user'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class AdminContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']