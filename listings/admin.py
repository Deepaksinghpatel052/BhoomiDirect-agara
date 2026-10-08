from django.contrib import admin

from .models import BuyerInquiry, Listing, ListingPhoto


class ListingPhotoInline(admin.TabularInline):
    model = ListingPhoto
    extra = 0


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "property_type", "locality", "price", "area_display", "status", "is_featured", "created_at")
    list_filter = ("status", "property_type", "is_featured", "locality")
    list_editable = ("status", "is_featured")
    search_fields = ("title", "description", "locality__name")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ListingPhotoInline]


@admin.register(BuyerInquiry)
class BuyerInquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "listing", "budget", "status", "referred_by", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "phone", "listing__title")
