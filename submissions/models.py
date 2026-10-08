from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from accounts.models import indian_phone_validator
from locations.units import all_units, to_sq_meter, trim_number

from .constants import AGRICULTURAL_TYPES, PIPELINE_ORDER, AreaUnit, PropertyType, Status


class YesNo(models.TextChoices):
    YES = "yes", "Yes"
    NO = "no", "No"
    NOT_SURE = "not_sure", "Not sure"


class PropertySubmission(models.Model):
    class Relation(models.TextChoices):
        OWNER = "owner", "Owner"
        CO_OWNER = "co_owner", "Co-owner"
        POA = "poa", "Power of Attorney holder"
        FAMILY = "family", "Family member"

    class Facing(models.TextChoices):
        EAST = "east", "East"
        WEST = "west", "West"
        NORTH = "north", "North"
        SOUTH = "south", "South"
        NORTH_EAST = "north_east", "North-East"
        NORTH_WEST = "north_west", "North-West"
        SOUTH_EAST = "south_east", "South-East"
        SOUTH_WEST = "south_west", "South-West"

    class WaterSource(models.TextChoices):
        MUNICIPAL = "municipal", "Municipal supply"
        BOREWELL = "borewell", "Borewell / Submersible"
        HANDPUMP = "handpump", "Hand pump"
        NONE = "none", "None"

    class Irrigation(models.TextChoices):
        TUBEWELL = "tubewell", "Tubewell"
        CANAL = "canal", "Canal"
        RAIN = "rain", "Rain-fed"
        NONE = "none", "None"

    class Soil(models.TextChoices):
        ALLUVIAL = "alluvial", "Alluvial (Domat)"
        SANDY = "sandy", "Sandy (Balui)"
        CLAY = "clay", "Clay (Matiyar)"
        MIXED = "mixed", "Mixed"

    class Ownership(models.TextChoices):
        SINGLE = "single", "Single owner"
        JOINT = "joint", "Joint ownership"

    class ApprovalStatus(models.TextChoices):
        ADA = "ada", "ADA approved"
        RERA = "rera", "RERA registered project"
        NOT_APPROVED = "not_approved", "Not approved / unplanned"
        NA = "na", "Not applicable (agricultural)"
        NOT_SURE = "not_sure", "Not sure"

    class Urgency(models.TextChoices):
        ONE_MONTH = "1_month", "Within 1 month"
        THREE_MONTHS = "1_3_months", "1 to 3 months"
        EXPLORING = "exploring", "Just exploring"

    class Source(models.TextChoices):
        WEBSITE = "website", "Website"
        WHATSAPP = "whatsapp", "WhatsApp"
        REFERRAL = "referral", "Referral"
        PARTNER = "partner", "Channel partner"

    class VisitTime(models.TextChoices):
        MORNING = "morning", "Morning (9am - 12pm)"
        AFTERNOON = "afternoon", "Afternoon (12pm - 4pm)"
        EVENING = "evening", "Evening (4pm - 7pm)"
        WEEKEND = "weekend", "Weekends only"

    TITLE_DOCUMENT_CHOICES = [
        ("registry", "Registry / Sale Deed"),
        ("khatauni", "Khatauni"),
        ("gpa", "GPA"),
        ("will", "Will"),
        ("other", "Other"),
    ]

    reference_id = models.CharField(max_length=20, unique=True, blank=True, editable=False)

    # Owner
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions"
    )
    owner_name = models.CharField("Full name", max_length=120)
    phone = models.CharField("Mobile number", max_length=10, validators=[indian_phone_validator])
    whatsapp = models.CharField("WhatsApp number", max_length=10, blank=True, validators=[indian_phone_validator])
    email = models.EmailField(blank=True)
    relation = models.CharField(
        "Your relation to property", max_length=10, choices=Relation.choices, default=Relation.OWNER
    )
    phone_verified = models.BooleanField(default=False)

    # Property type & location
    property_type = models.CharField(max_length=30, choices=PropertyType.choices)
    tehsil = models.ForeignKey("locations.Tehsil", on_delete=models.SET_NULL, null=True, blank=True)
    locality = models.ForeignKey(
        "locations.Locality", on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions"
    )
    village_colony = models.CharField("Village / colony name", max_length=120, blank=True)
    khasra_number = models.CharField("Khasra / Gata number", max_length=60, blank=True)
    landmark = models.CharField(max_length=150, blank=True)
    address = models.TextField("Full address", blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Size
    area_value = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0.01)]
    )
    area_unit = models.CharField(max_length=10, choices=AreaUnit.choices, default=AreaUnit.SQYARD)
    area_sq_meter = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, editable=False)

    # Plot details
    road_width_ft = models.PositiveIntegerField("Road width (ft)", null=True, blank=True)
    frontage_ft = models.PositiveIntegerField("Frontage (ft)", null=True, blank=True)
    facing = models.CharField(max_length=12, choices=Facing.choices, blank=True)
    is_corner = models.BooleanField("Corner plot", default=False)
    has_boundary_wall = models.BooleanField("Boundary wall", default=False)
    has_electricity = models.BooleanField("Electricity connection", default=False)
    water_source = models.CharField(max_length=12, choices=WaterSource.choices, blank=True)
    distance_main_road_m = models.PositiveIntegerField("Distance from main road (metres)", null=True, blank=True)

    # Agricultural
    irrigation_source = models.CharField(max_length=12, choices=Irrigation.choices, blank=True)
    current_crop = models.CharField(max_length=80, blank=True)
    soil_type = models.CharField(max_length=12, choices=Soil.choices, blank=True)
    has_tubewell = models.BooleanField("Tubewell / borewell on land", default=False)

    # Legal
    ownership_type = models.CharField(max_length=10, choices=Ownership.choices, default=Ownership.SINGLE)
    number_of_owners = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    title_documents = models.JSONField(default=list, blank=True)
    mutation_done = models.CharField(
        "Mutation (Dakhil Kharij) done", max_length=10, choices=YesNo.choices, default=YesNo.NOT_SURE
    )
    approval_status = models.CharField(
        "ADA / RERA status", max_length=15, choices=ApprovalStatus.choices, default=ApprovalStatus.NOT_SURE
    )
    has_loan = models.BooleanField("Any loan on property", default=False)
    has_dispute = models.BooleanField("Any court dispute", default=False)
    encumbrance_details = models.TextField(blank=True)

    # Commercial
    expected_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    price_negotiable = models.BooleanField(default=True)
    reason_for_selling = models.TextField(blank=True)
    urgency = models.CharField(max_length=12, choices=Urgency.choices, default=Urgency.THREE_MONTHS)
    preferred_visit_time = models.CharField(max_length=12, choices=VisitTime.choices, blank=True)
    consent = models.BooleanField(default=False)

    # Pipeline
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.WEBSITE)
    referred_by = models.ForeignKey(
        "partners.ChannelPartner", on_delete=models.SET_NULL, null=True, blank=True, related_name="owner_referrals"
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_submissions",
    )
    is_complete = models.BooleanField(default=False, help_text="Full form filled (not only quick lead)")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference_id} - {self.owner_name}"

    def save(self, *args, **kwargs):
        self.area_sq_meter = to_sq_meter(self.area_value, self.area_unit) if self.area_value else None
        super().save(*args, **kwargs)
        if not self.reference_id:
            self.reference_id = self.build_reference_id()
            super().save(update_fields=["reference_id"])

    def build_reference_id(self):
        year = (self.created_at or timezone.now()).year
        return f"BDA-{year}-{self.pk:05d}"

    def get_absolute_url(self):
        return reverse("submissions:owner_submission", args=[self.reference_id])

    def get_dashboard_url(self):
        return reverse("dashboard:lead_detail", args=[self.pk])

    @property
    def is_agricultural(self):
        return self.property_type in AGRICULTURAL_TYPES

    @property
    def title(self):
        place = self.locality.name if self.locality else (self.village_colony or "Agra")
        return f"{self.get_property_type_display()} in {place}"

    @property
    def area_display(self):
        if not self.area_value:
            return "—"
        value = trim_number(self.area_value)
        return f"{value} {self.get_area_unit_display()}"

    @property
    def area_in_units(self):
        return all_units(self.area_sq_meter) if self.area_sq_meter else {}

    @property
    def title_documents_display(self):
        labels = dict(self.TITLE_DOCUMENT_CHOICES)
        return ", ".join(labels.get(doc, doc) for doc in self.title_documents) or "Not specified"

    @property
    def whatsapp_link(self):
        return f"https://wa.me/91{self.whatsapp or self.phone}"

    @property
    def cover_photo(self):
        return self.photos.first()

    @property
    def pipeline_index(self):
        try:
            return PIPELINE_ORDER.index(self.status)
        except ValueError:
            return -1


def submission_photo_path(instance, filename):
    return f"submissions/{instance.submission_id}/photos/{filename}"


def private_storage():
    """Documents live outside MEDIA_ROOT and are served only via a permission-checked view."""
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)


def submission_doc_path(instance, filename):
    return f"submissions/{instance.submission_id}/{filename}"


class SubmissionPhoto(models.Model):
    submission = models.ForeignKey(PropertySubmission, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to=submission_photo_path)
    caption = models.CharField(max_length=120, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Photo for {self.submission.reference_id}"


class SubmissionDocument(models.Model):
    class DocType(models.TextChoices):
        REGISTRY = "registry", "Registry / Sale Deed"
        KHATAUNI = "khatauni", "Khatauni"
        GPA = "gpa", "GPA"
        WILL = "will", "Will"
        ID_PROOF = "id_proof", "Owner ID proof"
        MAP = "map", "Site map / Naksha"
        OTHER = "other", "Other"

    submission = models.ForeignKey(PropertySubmission, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=12, choices=DocType.choices, default=DocType.OTHER)
    file = models.FileField(upload_to=submission_doc_path, storage=private_storage)
    visible_only_to_company = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.get_doc_type_display()} - {self.submission.reference_id}"

    @property
    def filename(self):
        return self.file.name.rsplit("/", 1)[-1]


class StatusHistory(models.Model):
    submission = models.ForeignKey(PropertySubmission, on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField(max_length=20, choices=Status.choices, blank=True)
    new_status = models.CharField(max_length=20, choices=Status.choices)
    note = models.TextField(blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["timestamp", "id"]
        verbose_name_plural = "status history"

    def __str__(self):
        return f"{self.submission.reference_id}: {self.old_status} -> {self.new_status}"
