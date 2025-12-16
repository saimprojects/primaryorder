from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from cart.models import CartItem


class OrderListView(generics.ListAPIView):
    """List all orders for authenticated user"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    """Retrieve specific order"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderCreateView(APIView):
    """Create new order from cart"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get cart items
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response(
                {'error': 'Your cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Calculate totals
            subtotal = 0
            for item in cart_items:
                if item.variant:
                    price = item.variant.discount_price if item.variant.discount_price else item.variant.price
                else:
                    price = item.product.base_price if item.product.base_price else 0
                subtotal += price * item.quantity

            # Calculate shipping (free for orders above 2000)
            shipping_fee = 200 if subtotal < 2000 else 0
            total_amount = subtotal + shipping_fee

            # Create order
            order = Order.objects.create(
                user=request.user,
                receiver_name=serializer.validated_data['receiver_name'],
                phone=serializer.validated_data['phone'],
                whatsapp=serializer.validated_data.get('whatsapp', ''),
                payment_method=serializer.validated_data.get('payment_method', 'COD'),
                country=serializer.validated_data.get('country', 'Pakistan'),
                province=serializer.validated_data['province'],
                city=serializer.validated_data['city'],
                address1=serializer.validated_data['address1'],
                address2=serializer.validated_data.get('address2', ''),
                total_amount=total_amount,
                shipping_fee=shipping_fee,
                status='pending'
            )

            # Create order items
            for cart_item in cart_items:
                # Get price
                if cart_item.variant:
                    price = cart_item.variant.discount_price if cart_item.variant.discount_price else cart_item.variant.price
                    variant_attrs = {
                        'size': cart_item.variant.size,
                        'color': cart_item.variant.color,
                        'material': cart_item.variant.material,
                        'sku': cart_item.variant.sku
                    }
                else:
                    price = cart_item.product.base_price if cart_item.product.base_price else 0
                    variant_attrs = None
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variant=cart_item.variant,
                    quantity=cart_item.quantity,
                    price=price,
                    variant_attributes=variant_attrs
                )
                
                # Update stock
                if cart_item.variant:
                    if cart_item.variant.stock >= cart_item.quantity:
                        cart_item.variant.stock -= cart_item.quantity
                        cart_item.variant.save()
                    else:
                        raise Exception(f"Insufficient stock for {cart_item.variant.sku}")
                else:
                    if cart_item.product.stock >= cart_item.quantity:
                        cart_item.product.stock -= cart_item.quantity
                        cart_item.product.save()
                    else:
                        raise Exception(f"Insufficient stock for {cart_item.product.title}")

            # Clear cart
            cart_items.delete()

            return Response(
                {
                    'status': 'success',
                    'message': 'Order placed successfully',
                    'order_id': order.id,
                    'total_amount': float(total_amount),
                    'shipping_fee': float(shipping_fee),
                    'order': OrderSerializer(order).data
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderStatusUpdateView(APIView):
    """Update order status (admin only)"""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, id):
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'Status field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = get_object_or_404(Order, id=id)
        
        # Validate status
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save()

        return Response({
            'status': 'success',
            'message': f'Order status updated to {new_status}',
            'order_id': order.id,
            'new_status': new_status
        })