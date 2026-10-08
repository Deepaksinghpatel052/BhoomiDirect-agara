from django.contrib import admin

from .models import Acquisition, ActivityLog, Evaluation, InternalNote, LegalChecklist, Offer, SiteVisit, SiteVisitPhoto


class SiteVisitPhotoInline(admin.TabularInline):
    model = SiteVisitPhoto
    extra = 0


@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ("submission", "agent", "scheduled_for", "status", "checks_passed")
    list_filter = ("status", "agent")
    search_fields = ("submission__reference_id", "submission__owner_name", "visit_notes")
    date_hierarchy = "scheduled_for"
    inlines = [SiteVisitPhotoInline]


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("submission", "evaluator", "total_score", "recommendation", "circle_rate_value", "estimated_resale_value", "updated_at")
    list_filter = ("recommendation",)
    search_fields = ("submission__reference_id",)
    readonly_fields = ("total_score", "recommendation", "circle_rate_value")


@admin.register(LegalChecklist)
class LegalChecklistAdmin(admin.ModelAdmin):
    list_display = ("submission", "progress", "title_verified", "khatauni_matched", "no_encumbrance", "mutation_verified", "owner_id_verified", "noc_obtained")
    search_fields = ("submission__reference_id",)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("submission", "amount", "valid_till", "status", "owner_counter_amount", "created_by", "created_at")
    list_filter = ("status",)
    search_fields = ("submission__reference_id", "submission__owner_name")


@admin.register(Acquisition)
class AcquisitionAdmin(admin.ModelAdmin):
    list_display = ("submission", "purchase_price", "total_cost", "purchase_date", "registry_date", "payment_mode")
    list_filter = ("payment_mode",)
    search_fields = ("submission__reference_id",)
    readonly_fields = ("total_cost",)
    date_hierarchy = "purchase_date"


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("action", "submission", "user", "created_at")
    list_filter = ("user",)
    search_fields = ("action", "details", "submission__reference_id")


@admin.register(InternalNote)
class InternalNoteAdmin(admin.ModelAdmin):
    list_display = ("submission", "author", "created_at")
    search_fields = ("text", "submission__reference_id")
