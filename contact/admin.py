# contact/admin.py
from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'name', 'email', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['subject', 'name', 'email', 'message']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Message Details', {
            'fields': ('name', 'email', 'phone', 'subject', 'message', 'category')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Admin Response', {
            'fields': ('admin_response', 'responded_by')
        }),
        ('System Info', {
            'fields': ('user', 'created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data and obj.status == 'resolved' and not obj.resolved_at:
            from django.utils import timezone
            obj.resolved_at = timezone.now()
            if not obj.responded_by:
                obj.responded_by = request.user
        super().save_model(request, obj, form, change)