from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .models import CartItem
from .serializers import CartItemSerializer, CartItemUpdateSerializer
from django.db.models import Sum
from products.models import Product
from products.models import ProductVariant
from django.views.decorators.http import require_http_methods

class CartListView(generics.ListAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Calculate cart totals
        cart_total = sum(item.item_total for item in queryset)
        items_count = queryset.aggregate(total=Sum('quantity'))['total'] or 0
        
        return Response({
            'items': serializer.data,
            'summary': {
                'items_count': items_count,
                'subtotal': cart_total,
                'shipping': 200 if cart_total < 2000 else 0,
                'total': cart_total + (200 if cart_total < 2000 else 0)
            }
        })


class CartItemCreateView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))
        
        # Validate product exists
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate variant if provided
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product)
            except ProductVariant.DoesNotExist:
                return Response(
                    {'error': 'Variant not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check variant stock
            if variant.stock < quantity:
                return Response(
                    {'error': f'Only {variant.stock} items available in stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            if product.has_variants:
                return Response(
                    {'error': 'This product has variants. Please select variant options.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if hasattr(product, 'stock'):
                if product.stock < quantity:
                    return Response(
                        {'error': f'Only {product.stock} items available in stock'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
        # Check if item already exists in cart
        cart_item = CartItem.objects.filter(
            user=request.user,
            product=product,
            variant=variant
        ).first()
        
        if cart_item:
            new_quantity = cart_item.quantity + quantity
            
            # Check stock for updated quantity
            if variant:
                if variant.stock < new_quantity:
                    return Response(
                        {'error': f'Only {variant.stock} items available in stock'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif hasattr(product, 'stock') and product.stock < new_quantity:
                return Response(
                    {'error': f'Only {product.stock} items available in stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                user=request.user,
                product=product,
                variant=variant,
                quantity=quantity
            )
        
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# 🔥 NEW: Simple APIView for update
class CartUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        item_id = request.data.get('id')
        new_quantity = request.data.get('quantity')
        
        if not item_id:
            return Response(
                {'error': 'Cart item ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not new_quantity or int(new_quantity) < 1:
            return Response(
                {'error': 'Quantity must be at least 1'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_quantity = int(new_quantity)
        
        # Check stock
        if cart_item.variant:
            if cart_item.variant.stock < new_quantity:
                return Response(
                    {'error': f'Only {cart_item.variant.stock} items available'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif hasattr(cart_item.product, 'stock') and cart_item.product.stock < new_quantity:
            return Response(
                {'error': f'Only {cart_item.product.stock} items available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart_item.quantity = new_quantity
        cart_item.save()
        
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)


# 🔥 NEW: Simple APIView for remove
class CartRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        item_id = request.data.get('id')
        
        if not item_id:
            return Response(
                {'error': 'Cart item ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
            cart_item.delete()
            return Response({'message': 'Item removed from cart'})
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ClearCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        CartItem.objects.filter(user=request.user).delete()
        return Response({'message': 'Cart cleared successfully'})


# For backward compatibility
class CartAddView(CartItemCreateView):
    """Alias for CartItemCreateView"""
    pass


class CartSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        local_cart = request.data.get('items', [])
        
        # Clear existing cart
        CartItem.objects.filter(user=request.user).delete()
        
        # Add items from local cart
        for item in local_cart:
            product_id = item.get('product_id')
            variant_id = item.get('variant_id')
            quantity = item.get('quantity', 1)
            
            try:
                product = Product.objects.get(id=product_id)
                variant = None
                
                if variant_id:
                    variant = ProductVariant.objects.get(id=variant_id, product=product)
                
                CartItem.objects.create(
                    user=request.user,
                    product=product,
                    variant=variant,
                    quantity=quantity
                )
            except (Product.DoesNotExist, ProductVariant.DoesNotExist):
                continue
        
        return Response({'message': 'Cart synced successfully'})