
from django.urls import path
from .views import (
    CategoryListView, ProductListView, ProductDetailView, 
    ProductCreateView, ProductUpdateView, ProductImageCreateView,
    ProductVariantCreateView, ProductVariantListView
)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('', ProductListView.as_view(), name='product-list'),
    path('<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('<slug:slug>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('<slug:slug>/variants/', ProductVariantListView.as_view(), name='product-variants'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('images/create/', ProductImageCreateView.as_view(), name='product-image-create'),
    path('variants/create/', ProductVariantCreateView.as_view(), name='product-variant-create'),
]