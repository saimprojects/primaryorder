from django.db import models
from cloudinary.models import CloudinaryField

class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

# products/models.py میں
class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    # Base price (optional, agar variants nahi hain to ye use hoga)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # 🔥 **YEH NAYA FIELD ADD KARO:**
    stock = models.PositiveIntegerField(default=0)  # Non-variant products ke liye
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Variants ke liye attributes (jaise: Size, Color, etc.)
    has_variants = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
    @property
    def min_price(self):
        """Returns minimum price from all variants"""
        if self.has_variants and self.variants.exists():
            return min(variant.price for variant in self.variants.all())
        return self.base_price or 0
    
    @property
    def total_stock(self):
        """Returns total stock from all variants or product stock"""
        if self.has_variants and self.variants.exists():
            return sum(variant.stock for variant in self.variants.all())
        return self.stock
    
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, unique=True)
    
    # Variant attributes (customize according to your needs)
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    material = models.CharField(max_length=100, blank=True, null=True)
    # Add more attributes as needed
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'size', 'color', 'material']
        ordering = ['size', 'color']

    def __str__(self):
        attrs = []
        if self.size:
            attrs.append(f"Size: {self.size}")
        if self.color:
            attrs.append(f"Color: {self.color}")
        if self.material:
            attrs.append(f"Material: {self.material}")
        return f"{self.product.title} - {', '.join(attrs)}"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    # Agar variant-specific images chahiye, to variant foreign key add karein
    variant = models.ForeignKey(ProductVariant, related_name='images', on_delete=models.SET_NULL, null=True, blank=True)
    image = CloudinaryField('image')
    position = models.PositiveIntegerField(default=0)
    # Color association agar images color se match karein
    color = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        if self.variant:
            return f"{self.product.title} - Variant Image"
        return f"{self.product.title} Image"