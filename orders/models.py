from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product, ProductVariant

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHODS = (
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment'),
    )

    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    receiver_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    payment_method = models.CharField(max_length=30, default='COD', choices=PAYMENT_METHODS)
    country = models.CharField(max_length=100, default='Pakistan')
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address1 = models.TextField()
    address2 = models.TextField(blank=True, null=True)
    
    # 🔥 FIXED: Added default values
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.email} ({self.status})"
    
    @property
    def subtotal(self):
        """Calculate subtotal from order items"""
        return float(self.total_amount) - float(self.shipping_fee)
    
    @property
    def is_free_shipping(self):
        return self.shipping_fee == 0


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    variant_attributes = models.JSONField(null=True, blank=True)

    def __str__(self):
        if self.variant:
            return f"{self.quantity} x {self.product.title} ({self.variant})"
        return f"{self.quantity} x {self.product.title}"
    
    @property
    def item_total(self):
        return float(self.price) * self.quantity
    
    def save(self, *args, **kwargs):
        # Ensure price is set
        if not self.price:
            if self.variant:
                self.price = self.variant.discount_price if self.variant.discount_price else self.variant.price
            else:
                self.price = self.product.base_price if self.product.base_price else 0
        super().save(*args, **kwargs)