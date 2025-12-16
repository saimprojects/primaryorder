from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


# --------------------------
# Inline for Order Items
# --------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'variant', 'quantity', 'price', 'variant_attributes', 'item_total_display']
    can_delete = False

    def item_total_display(self, obj):
        # Make sure price and quantity exist
        if obj.price is not None and obj.quantity is not None:
            return f"Rs {obj.quantity * obj.price:.2f}"
        return "Rs 0.00"
    
    item_total_display.short_description = "Item Total"


# --------------------------
# Main Order Admin
# --------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    # List page columns
    list_display = [
        'id',
        'user',
        'receiver_name',
        'colored_status',
        'total_amount_display',
        'payment_method',
        'created_at',
    ]

    # Filters
    list_filter = [
        'status',
        'payment_method',
        'created_at',
        'province',
        'city'
    ]

    # Search
    search_fields = [
        'id',
        'user__email',
        'user__username',
        'receiver_name',
        'phone',
        'whatsapp'
    ]

    # Show related items inline
    inlines = [OrderItemInline]

    # Fields for detail page
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'receiver_name', 'phone', 'whatsapp', 'payment_method', 'status')
        }),
        ('Order Amount', {
            'fields': ('total_amount', 'shipping_fee', 'subtotal_display')
        }),
        ('Shipping Address', {
            'fields': ('country', 'province', 'city', 'address1', 'address2')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Readonly fields
    readonly_fields = [
        'total_amount',
        'shipping_fee',
        'subtotal_display',
        'created_at',
        'updated_at'
    ]

    # Ordering
    ordering = ['-created_at']

    # Clickability
    list_display_links = ['id', 'user']

    # Status coloring
    def colored_status(self, obj):
        color_map = {
            'pending': 'orange',
            'confirmed': 'blue',
            'shipped': 'purple',
            'delivered': 'green',
            'cancelled': 'red',
        }
        color = color_map.get(obj.status, 'black')
        
        return format_html(
            f'<span style="color:{color}; font-weight:600; padding: 2px 8px; border-radius: 4px; background-color:{color}10;">{obj.get_status_display()}</span>'
        )
    
    colored_status.short_description = "Status"

    # Formatted total amount
    def total_amount_display(self, obj):
        return f"Rs {obj.total_amount:.2f}"
    
    total_amount_display.short_description = "Total Amount"

    # Subtotal display in admin
    def subtotal_display(self, obj):
        return f"Rs {obj.subtotal:.2f}"
    
    subtotal_display.short_description = "Subtotal"