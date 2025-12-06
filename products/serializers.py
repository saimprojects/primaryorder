from rest_framework import serializers
from .models import Category, Product, ProductVariant, ProductImage
from reviews.models import Review
from reviews.serializers import ReviewSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'position', 'color', 'variant']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

class ProductVariantSerializer(serializers.ModelSerializer):
    # Variant ki images
    images = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'size', 'color', 'material', 'price', 
            'discount_price', 'stock', 'is_active', 'images'
        ]
    
    def get_images(self, obj):
        # Variant-specific images
        variant_images = obj.images.all()
        if variant_images.exists():
            return ProductImageSerializer(variant_images, many=True).data
        
        # Agar variant-specific images nahi hain, to product ki default images return karein
        product_images = obj.product.images.filter(variant__isnull=True)
        return ProductImageSerializer(product_images, many=True).data

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)

    # Available attributes for variants (for filter UI)
    available_sizes = serializers.SerializerMethodField()
    available_colors = serializers.SerializerMethodField()
    
    # ⭐ Reviews fields
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    # Price display
    display_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'description', 'base_price', 'display_price',
            'discount_price', 'is_active', 'has_variants', 'category', 
            'category_name', 'category_slug', 'images', 'variants',
            'available_sizes', 'available_colors', 'average_rating', 
            'review_count', 'reviews', 'created_at'
        ]
    
    def get_display_price(self, obj):
        if obj.has_variants and obj.variants.exists():
            return obj.min_price
        return obj.base_price
    
    def get_available_sizes(self, obj):
        if obj.has_variants:
            sizes = obj.variants.filter(is_active=True, stock__gt=0)\
                .exclude(size__isnull=True).exclude(size='')\
                .values_list('size', flat=True).distinct()
            return list(sizes)
        return []
    
    def get_available_colors(self, obj):
        if obj.has_variants:
            colors = obj.variants.filter(is_active=True, stock__gt=0)\
                .exclude(color__isnull=True).exclude(color='')\
                .values_list('color', flat=True).distinct()
            return list(colors)
        return []
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return round(sum(r.stars for r in reviews) / reviews.count(), 1)
        return 0.0
    
    def get_review_count(self, obj):
        return obj.reviews.count()

class ProductCreateSerializer(serializers.ModelSerializer):
    # Variants bhi create karne ke liye
    variants = ProductVariantSerializer(many=True, required=False)
    
    class Meta:
        model = Product
        fields = '__all__'
        extra_kwargs = {
            'base_price': {'required': False}
        }
    
    def create(self, validated_data):
        variants_data = validated_data.pop('variants', [])
        product = Product.objects.create(**validated_data)
        
        for variant_data in variants_data:
            ProductVariant.objects.create(product=product, **variant_data)
        
        return product
    
    def update(self, instance, validated_data):
        variants_data = validated_data.pop('variants', None)
        
        # Update product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update variants if provided
        if variants_data is not None:
            # Delete existing variants and create new ones
            instance.variants.all().delete()
            for variant_data in variants_data:
                ProductVariant.objects.create(product=instance, **variant_data)
        
        return instance

class ProductVariantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'