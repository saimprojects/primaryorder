from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer, ProductVariantSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    variant_info = serializers.SerializerMethodField()
    item_total = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'variant', 'variant_info', 
            'quantity', 'price', 'item_total'
        ]
        read_only_fields = ['item_total']
    
    def get_variant_info(self, obj):
        if obj.variant_attributes:
            info = []
            if obj.variant_attributes.get('size'):
                info.append(f"Size: {obj.variant_attributes['size']}")
            if obj.variant_attributes.get('color'):
                info.append(f"Color: {obj.variant_attributes['color']}")
            if obj.variant_attributes.get('material'):
                info.append(f"Material: {obj.variant_attributes['material']}")
            if obj.variant_attributes.get('sku'):
                info.append(f"SKU: {obj.variant_attributes['sku']}")
            return ', '.join(info)
        return None
    
    def get_item_total(self, obj):
        return obj.item_total


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True, source='items.all')
    subtotal = serializers.SerializerMethodField()
    is_free_shipping = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'receiver_name', 'phone', 'whatsapp',
            'country', 'province', 'city',
            'address1', 'address2',
            'total_amount', 'shipping_fee', 'subtotal', 'is_free_shipping',
            'payment_method', 'status',
            'created_at', 'updated_at', 'items'
        ]
        read_only_fields = [
            'id', 'user', 'total_amount', 'shipping_fee',
            'created_at', 'updated_at', 'status'
        ]
    
    def get_subtotal(self, obj):
        return obj.subtotal
    
    def get_is_free_shipping(self, obj):
        return obj.is_free_shipping


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'receiver_name',
            'phone',
            'whatsapp',
            'payment_method',
            'country',
            'province',
            'city',
            'address1',
            'address2'
        ]
    
    def validate(self, data):
        # Custom validation
        required_fields = ['receiver_name', 'phone', 'province', 'city', 'address1']
        for field in required_fields:
            if field not in data or not data[field]:
                raise serializers.ValidationError(
                    {field: "This field is required."}
                )
        
        # Phone validation
        phone = data.get('phone', '')
        if not phone.isdigit() or len(phone) < 10:
            raise serializers.ValidationError(
                {'phone': 'Please enter a valid phone number.'}
            )
        
        return data