from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Notification, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "get_full_name", "phone", "email", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "phone", "email")
    fieldsets = BaseUserAdmin.fieldsets + (("Business profile", {"fields": ("role", "phone", "whatsapp", "city")}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (("Business profile", {"fields": ("role", "phone")}),)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("title", "message", "user__username")
