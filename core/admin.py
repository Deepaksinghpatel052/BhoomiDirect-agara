from django.contrib import admin

from .models import FAQ, ContactMessage, SiteSettings, Testimonial


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("__str__", "properties_acquired", "acres_evaluated", "payout_crore", "avg_days_to_close")

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "property_sold", "rating", "is_active", "order")
    list_filter = ("is_active", "rating")
    list_editable = ("is_active", "order")
    search_fields = ("name", "location", "quote")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "show_on_home", "order")
    list_filter = ("category", "show_on_home")
    list_editable = ("show_on_home", "order")
    search_fields = ("question", "answer")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "subject", "is_resolved", "created_at")
    list_filter = ("is_resolved",)
    search_fields = ("name", "phone", "email", "message")
