from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from cart.models import CartItem
from products.models import Product, ProductVariant


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)

        if serializer.is_valid():
            cart_items = CartItem.objects.filter(user=request.user)
            if not cart_items.exists():
                return Response(
                    {'error': 'Cart is empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                # Get data from request
                total_amount = request.data.get('total_amount', 0)
                shipping_fee = request.data.get('shipping_fee', 0)
                
                if not total_amount or total_amount <= 0:
                    # Calculate total from cart items
                    total_amount = sum(item.item_total for item in cart_items)
                    shipping_fee = 200 if total_amount < 2000 else 0
                    total_amount += shipping_fee

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

                # Create order items from cart
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
                        cart_item.variant.stock -= cart_item.quantity
                        cart_item.variant.save()
                    else:
                        cart_item.product.stock -= cart_item.quantity
                        cart_item.product.save()

                # Clear cart
                cart_items.delete()

                return Response(
                    {
                        'status': 'success',
                        'order_id': order.id,
                        'message': 'Order placed successfully',
                        'order': OrderSerializer(order).data
                    },
                    status=status.HTTP_201_CREATED
                )

            except Exception as e:
                print(f"Order creation error: {str(e)}")
                return Response(
                    {'error': f'Order creation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderStatusUpdateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, id):
        new_status = request.data.get('status')

        try:
            order = Order.objects.get(id=id)

            if new_status not in dict(Order.STATUS_CHOICES):
                return Response({'error': 'Invalid status'}, status=400)

            order.status = new_status
            order.save()

            return Response({'status': 'Order status updated'})

        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)