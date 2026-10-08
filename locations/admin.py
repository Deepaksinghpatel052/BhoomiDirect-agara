from django.contrib import admin

from .models import CircleRate, Locality, LocalityFAQ, Tehsil


@admin.register(Tehsil)
class TehsilAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


class CircleRateInline(admin.TabularInline):
    model = CircleRate
    extra = 0


class LocalityFAQInline(admin.StackedInline):
    model = LocalityFAQ
    extra = 0


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ("name", "tehsil", "locality_type", "is_featured", "latitude", "longitude")
    list_filter = ("tehsil", "locality_type", "is_featured")
    list_editable = ("is_featured",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CircleRateInline, LocalityFAQInline]


@admin.register(CircleRate)
class CircleRateAdmin(admin.ModelAdmin):
    list_display = ("locality", "property_type", "rate_per_sq_meter", "effective_year", "is_sample")
    list_filter = ("property_type", "effective_year", "is_sample")
    search_fields = ("locality__name",)
