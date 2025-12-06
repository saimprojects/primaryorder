from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'stars', 'user_name', 'created_at']
    list_filter = ['stars', 'product']
    search_fields = ['text', 'user_name']
