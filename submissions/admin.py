from django.contrib import admin

from .models import PropertySubmission, StatusHistory, SubmissionDocument, SubmissionPhoto


class PhotoInline(admin.TabularInline):
    model = SubmissionPhoto
    extra = 0


class DocumentInline(admin.TabularInline):
    model = SubmissionDocument
    extra = 0


class HistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = ("old_status", "new_status", "note", "changed_by", "timestamp")


@admin.register(PropertySubmission)
class PropertySubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "reference_id",
        "owner_name",
        "phone",
        "property_type",
        "locality",
        "area_display",
        "expected_price",
        "status",
        "urgency",
        "source",
        "assigned_agent",
        "created_at",
    )
    list_filter = ("status", "property_type", "urgency", "source", "locality__tehsil", "is_complete")
    search_fields = ("reference_id", "owner_name", "phone", "khasra_number", "village_colony", "locality__name")
    readonly_fields = ("reference_id", "area_sq_meter", "created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = [PhotoInline, DocumentInline, HistoryInline]


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("submission", "old_status", "new_status", "changed_by", "timestamp")
    list_filter = ("new_status",)
    search_fields = ("submission__reference_id", "note")


@admin.register(SubmissionPhoto)
class SubmissionPhotoAdmin(admin.ModelAdmin):
    list_display = ("submission", "caption", "uploaded_at")
    search_fields = ("submission__reference_id",)


@admin.register(SubmissionDocument)
class SubmissionDocumentAdmin(admin.ModelAdmin):
    list_display = ("submission", "doc_type", "visible_only_to_company", "uploaded_at")
    list_filter = ("doc_type",)
    search_fields = ("submission__reference_id",)
