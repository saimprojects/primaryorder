from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product, ProductVariant

User = get_user_model()

class CartItem(models.Model):
    user = models.ForeignKey(User, related_name='cart_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)  # 🔥 NEW
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product', 'variant')  # 🔥 UPDATED

    def __str__(self):
        if self.variant:
            return f"{self.user.email} - {self.product.title} ({self.variant})"
        return f"{self.user.email} - {self.product.title}"
    
    @property
    def item_price(self):
        """Get price based on variant or product"""
        if self.variant:
            return self.variant.discount_price if self.variant.discount_price else self.variant.price
        return self.product.base_price if self.product.base_price else 0
    
    @property
    def item_total(self):
        return self.item_price * self.quantity