from django.db import models
from products.models import Product
from cloudinary.models import CloudinaryField

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user_name = models.CharField(max_length=255, default="Anonymous") # Or link to User if desired, prompt said "admin can add" so maybe just a name field is enough or admin user.
    # Prompt: "all the things only admin can add via django admin panel"
    # So it doesn't strictly need to be linked to a frontend user submitting it.
    stars = models.PositiveIntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    text = models.TextField()
    image = CloudinaryField('image', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stars} Stars - {self.product.title}"
