from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone', 'address')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('name', 'email', 'phone', 'address')}),
    )
    list_display = ('email', 'username', 'name', 'is_staff')
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)
