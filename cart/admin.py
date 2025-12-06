# cart/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import CartItem

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 
        'product_title', 
        'variant_display', 
        'quantity', 
        'item_price_display', 
        'item_total_display', 
        'created_at_formatted'
    ]
    
    list_filter = [
        'created_at',
        'user',
        'product',
        ('variant', admin.RelatedOnlyFieldListFilter),
    ]
    
    search_fields = [
        'user__email',
        'user__username',
        'product__title',
        'variant__sku',
        'variant__color',
        'variant__size'
    ]
    
    readonly_fields = [
        'user_email_display',
        'created_at',
        'updated_at',
        'item_price_display',
        'item_total_display'
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_email_display'),
            'classes': ('wide',)
        }),
        ('Product Information', {
            'fields': ('product', 'variant', 'quantity'),
            'classes': ('wide',)
        }),
        ('Pricing', {
            'fields': ('item_price_display', 'item_total_display'),
            'classes': ('collapse', 'wide')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    # Custom methods for display
    def user_email(self, obj):
        return obj.user.email if obj.user else 'No User'
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def user_email_display(self, obj):
        return obj.user.email if obj.user else 'No User'
    user_email_display.short_description = 'Email'
    
    def product_title(self, obj):
        return obj.product.title if obj.product else 'No Product'
    product_title.short_description = 'Product'
    product_title.admin_order_field = 'product__title'
    
    def variant_display(self, obj):
        if obj.variant:
            variant_info = []
            
            if obj.variant.sku:
                variant_info.append(f"SKU: {obj.variant.sku}")
            
            if obj.variant.size:
                variant_info.append(f"Size: {obj.variant.size}")
            
            if obj.variant.color:
                variant_info.append(f"Color: {obj.variant.color}")
            
            if obj.variant.material:
                variant_info.append(f"Material: {obj.variant.material}")
            
            if variant_info:
                return ", ".join(variant_info)
        
        return "No Variant"
    variant_display.short_description = 'Variant'
    
    def item_price_display(self, obj):
        # Try to get item_price from the object
        # If it's a property/method, call it; if it's a field, access it
        try:
            price = obj.item_price
        except AttributeError:
            # If item_price doesn't exist as a property, try to calculate it
            if hasattr(obj, 'product') and obj.product and hasattr(obj.product, 'price'):
                price = obj.product.price
            else:
                price = 0
        if price:
            return f"PKR {price:,.2f}"
        return "PKR 0.00"
    item_price_display.short_description = 'Unit Price'
    
    def item_total_display(self, obj):
        # Try to get item_total from the object
        # If it's a property/method, call it
        try:
            total = obj.item_total
        except AttributeError:
            # Calculate total manually
            try:
                price = obj.item_price if hasattr(obj, 'item_price') else (obj.product.price if obj.product and hasattr(obj.product, 'price') else 0)
                total = price * obj.quantity if price else 0
            except:
                total = 0
        if total:
            return f"PKR {total:,.2f}"
        return "PKR 0.00"
    item_total_display.short_description = 'Total'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M")
    created_at_formatted.short_description = 'Added On'
    created_at_formatted.admin_order_field = 'created_at'
    
    # Optimize database queries
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'user',
            'product',
            'variant'
        )
    
    # Custom actions
    actions = ['update_quantities_to_one', 'clear_cart_items']
    
    def update_quantities_to_one(self, request, queryset):
        """Set quantity to 1 for selected cart items"""
        updated = queryset.update(quantity=1)
        self.message_user(
            request, 
            f"Successfully updated {updated} cart item(s) quantity to 1."
        )
    update_quantities_to_one.short_description = "Set quantity to 1"
    
    def clear_cart_items(self, request, queryset):
        """Delete selected cart items"""
        deleted_count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            f"Successfully deleted {deleted_count} cart item(s)."
        )
    clear_cart_items.short_description = "Delete selected cart items"
    
    # Change list view customization - NO CUSTOM TEMPLATE
    def changelist_view(self, request, extra_context=None):
        # Add summary information
        extra_context = extra_context or {}
        
        # Calculate totals
        cart_items = self.get_queryset(request)
        
        total_items = cart_items.count()
        total_quantity = cart_items.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
        
        # Calculate total value
        total_value = 0
        for item in cart_items:
            try:
                if item.item_total:
                    total_value += item.item_total
            except AttributeError:
                # Calculate manually if item_total property doesn't exist
                try:
                    price = item.item_price if hasattr(item, 'item_price') else (item.product.price if item.product and hasattr(item.product, 'price') else 0)
                    total_value += price * item.quantity if price else 0
                except:
                    continue
        
        extra_context.update({
            'total_items': total_items,
            'total_quantity': total_quantity,
            'total_value': f"PKR {total_value:,.2f}" if total_value else "PKR 0.00",
            'summary_title': 'Cart Summary',
        })
        
        return super().changelist_view(request, extra_context=extra_context)
    
    # Remove the custom template reference - use default Django admin template
    # change_list_template = 'admin/cart/cartitem/change_list.html'  # REMOVED
    
    # Add custom CSS only if you have the file
    # class Media:
    #     css = {
    #         'all': ('admin/css/cart_admin.css',)
    #     }