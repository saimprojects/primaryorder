from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


# --------------------------
# Inline for Order Items
# --------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'subtotal']
    can_delete = False

    def subtotal(self, obj):
        # Make sure price and quantity exist
        if obj.price is not None and obj.quantity is not None:
            return obj.quantity * obj.price
        return 0  # ya "N/A" bhi likh sakte ho

    subtotal.short_description = "Subtotal"


# --------------------------
# Main Order Admin
# --------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    # List page columns
    list_display = [
        'id',
        'user',
        'colored_status',
        'total_amount',
        'payment_method',
        'created_at',
    ]

    # Filters
    list_filter = [
        'status',
        'payment_method',
        'created_at'
    ]

    # Search
    search_fields = [
        'id',
        'user__email',
        'user__username'
    ]

    # Show related items inline
    inlines = [OrderItemInline]

    # Readonly fields on order detail page
    readonly_fields = [
        'total_amount',
        'created_at',
        'updated_at'
    ]

    # Ordering
    ordering = ['-created_at']

    # Clickability
    list_display_links = ['id', 'user']

    # Status coloring
    def colored_status(self, obj):
        color = {
            'pending': 'orange',
            'processing': 'blue',
            'shipped': 'purple',
            'delivered': 'green',
            'cancelled': 'red',
        }.get(obj.status, 'black')

        return format_html(
            f'<span style="color:{color}; font-weight:600">{obj.status.title()}</span>'
        )

    colored_status.short_description = "Status"


