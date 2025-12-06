from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer, ProductVariantSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)  # 🔥 NEW
    variant_info = serializers.SerializerMethodField()  # 🔥 NEW
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'variant', 'variant_info', 'quantity', 'price', 'item_total']
    
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


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True, source='items.all')
    subtotal = serializers.SerializerMethodField()  # 🔥 NEW
    is_free_shipping = serializers.SerializerMethodField()  # 🔥 NEW
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'receiver_name', 'phone', 'whatsapp',
            'country', 'province', 'city',
            'address1', 'address2',
            'total_amount', 'shipping_fee', 'subtotal', 'is_free_shipping',
            'payment_method', 'status',
            'created_at', 'items'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'status']
    
    def get_subtotal(self, obj):
        return obj.subtotal
    
    def get_is_free_shipping(self, obj):
        return obj.is_free_shipping


class OrderCreateSerializer(serializers.ModelSerializer):
    cart_items = serializers.JSONField(required=False)  # 🔥 NEW
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)  # 🔥 NEW
    shipping_fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)  # 🔥 NEW
    
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
            'address2',
            'cart_items',  # 🔥 NEW
            'total_amount',  # 🔥 NEW
            'shipping_fee'  # 🔥 NEW
        ]