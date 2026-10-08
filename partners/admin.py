from django.contrib import admin

from .models import ChannelPartner


@admin.register(ChannelPartner)
class ChannelPartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "firm_name", "phone", "rera_agent_number", "experience_years", "is_approved", "created_at")
    list_filter = ("is_approved", "areas_covered")
    list_editable = ("is_approved",)
    search_fields = ("name", "firm_name", "phone", "email", "rera_agent_number")
    filter_horizontal = ("areas_covered",)
