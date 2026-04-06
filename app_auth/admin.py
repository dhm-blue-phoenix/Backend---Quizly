from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

# Unregister the default User admin
admin.site.unregister(User)

# Re-register User with customized clear dashboard UI
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    ordering = ('-date_joined',)
