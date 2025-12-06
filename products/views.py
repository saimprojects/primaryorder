from rest_framework import generics, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import Category, Product, ProductVariant, ProductImage
from .serializers import (
    CategorySerializer, ProductSerializer, ProductCreateSerializer, 
    ProductImageSerializer, ProductVariantCreateSerializer
)

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        
        # Category filter
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Size filter
        size = self.request.query_params.get('size')
        if size:
            queryset = queryset.filter(
                Q(variants__size=size, variants__is_active=True) | 
                Q(has_variants=False)
            ).distinct()
        
        # Color filter
        color = self.request.query_params.get('color')
        if color:
            queryset = queryset.filter(
                Q(variants__color=color, variants__is_active=True) | 
                Q(has_variants=False)
            ).distinct()
        
        return queryset

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateSerializer
    permission_classes = [permissions.IsAdminUser]

class ProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'slug'

class ProductImageCreateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        product_id = request.data.get('product')
        variant_id = request.data.get('variant')
        images = request.data.get('images', [])
        color = request.data.get('color')
        
        if isinstance(images, list):
            created_images = []
            for img_data in images:
                url = img_data if isinstance(img_data, str) else img_data.get('url')
                if url:
                    image = ProductImage.objects.create(
                        product_id=product_id,
                        variant_id=variant_id if variant_id else None,
                        color=color,
                        image=url
                    )
                    created_images.append(image)
            
            return Response({'status': 'success', 'count': len(created_images)})
        
        return Response({'error': 'Invalid data'}, status=400)

class ProductVariantCreateView(generics.CreateAPIView):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantCreateSerializer
    permission_classes = [permissions.IsAdminUser]

class ProductVariantListView(generics.ListAPIView):
    serializer_class = ProductVariantCreateSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        product_slug = self.kwargs.get('product_slug')
        return ProductVariant.objects.filter(
            product__slug=product_slug, 
            product__is_active=True,
            is_active=True
        )