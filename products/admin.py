from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductImage
from django.utils.html import format_html

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['sku', 'size', 'color', 'material', 'price', 'discount_price', 'stock', 'is_active']
    readonly_fields = ['sku']

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px;" />', obj.image.url)
        return ""

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'has_variants', 'min_price', 'stock_summary', 'is_active', 'category']
    list_filter = ['category', 'is_active', 'has_variants']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductVariantInline, ProductImageInline]
    
    def stock_summary(self, obj):
        if obj.has_variants:
            total_stock = sum(variant.stock for variant in obj.variants.all())
            return f"{total_stock} total"
        return obj.base_price
    stock_summary.short_description = 'Stock/Price'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'color', 'price', 'stock', 'is_active']
    list_filter = ['is_active', 'size', 'color']
    search_fields = ['product__title', 'sku']