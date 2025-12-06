from rest_framework import serializers
from .models import CartItem
from products.serializers import ProductSerializer, ProductVariantSerializer
from products.models import Product, ProductVariant

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    # Display calculated prices
    item_price = serializers.SerializerMethodField()
    item_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_id', 'variant', 'variant_id', 
            'quantity', 'item_price', 'item_total', 'created_at', 'updated_at'
        ]
    
    def get_item_price(self, obj):
        if obj.variant:
            return obj.variant.discount_price if obj.variant.discount_price else obj.variant.price
        return obj.product.base_price if obj.product.base_price else 0
    
    def get_item_total(self, obj):
        price = self.get_item_price(obj)
        return price * obj.quantity

    def create(self, validated_data):
        user = self.context['request'].user
        product_id = validated_data.pop('product_id')
        variant_id = validated_data.pop('variant_id', None)
        
        # Check if item already exists with same variant
        cart_item = CartItem.objects.filter(
            user=user, 
            product_id=product_id, 
            variant_id=variant_id
        ).first()
        
        if cart_item:
            cart_item.quantity += validated_data.get('quantity', 1)
            cart_item.save()
            return cart_item
        else:
            return CartItem.objects.create(
                user=user,
                product_id=product_id,
                variant_id=variant_id,
                **validated_data
            )

class CartItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'quantity']