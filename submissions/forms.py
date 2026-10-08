import os

from django import forms
from django.conf import settings

from accounts.models import indian_phone_validator
from core.forms import BootstrapFormMixin
from locations.models import Locality, Tehsil

from .constants import PropertyType
from .models import PropertySubmission, SubmissionDocument

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
DOC_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png")
MAX_FILES = 10


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """File field that accepts several files and validates each one."""

    def __init__(self, *args, kind="image", **kwargs):
        self.kind = kind
        kwargs.setdefault("widget", MultipleFileInput())
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        files = [f for f in (data if isinstance(data, (list, tuple)) else [data]) if f]
        if not files:
            if self.required:
                raise forms.ValidationError("Please upload at least one file.")
            return []
        if len(files) > MAX_FILES:
            raise forms.ValidationError(f"You can upload up to {MAX_FILES} files at a time.")
        return [self._validate(f) for f in files]

    def _validate(self, f):
        ext = os.path.splitext(f.name)[1].lower()
        if self.kind == "image":
            allowed, max_mb = IMAGE_EXTENSIONS, settings.MAX_IMAGE_UPLOAD_MB
        else:
            allowed, max_mb = DOC_EXTENSIONS, settings.MAX_DOC_UPLOAD_MB
        if ext not in allowed:
            raise forms.ValidationError(f"{f.name}: only {', '.join(allowed)} files are allowed.")
        if f.size > max_mb * 1024 * 1024:
            raise forms.ValidationError(f"{f.name} is larger than {max_mb} MB.")
        if self.kind == "image" or ext in IMAGE_EXTENSIONS:
            # Checks the file really is an image (Pillow verify).
            forms.ImageField().clean(f)
            f.seek(0)
        return f


class QuickLeadForm(BootstrapFormMixin, forms.Form):
    owner_name = forms.CharField(label="Your name", max_length=120)
    phone = forms.CharField(label="Mobile number", max_length=10, validators=[indian_phone_validator])
    property_type = forms.ChoiceField(label="Property type", choices=PropertyType.choices)
    locality = forms.ModelChoiceField(
        label="Area / locality", queryset=Locality.objects.all(), required=False, empty_label="Select area (optional)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields["owner_name"].widget.attrs["placeholder"] = "e.g. Ramesh Kumar"
        self.fields["phone"].widget.attrs.update(
            {"placeholder": "10 digit mobile", "inputmode": "numeric", "data-phone": "1"}
        )


class Step1OwnerForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = PropertySubmission
        fields = ("owner_name", "phone", "whatsapp", "email", "relation")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        for name in ("phone", "whatsapp"):
            self.fields[name].widget.attrs.update(
                {"inputmode": "numeric", "data-phone": "1", "maxlength": "10", "placeholder": "10 digit mobile"}
            )
        self.fields["whatsapp"].help_text = "Leave blank if same as mobile number."


class Step2LocationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = PropertySubmission
        fields = (
            "property_type",
            "tehsil",
            "locality",
            "village_colony",
            "khasra_number",
            "landmark",
            "address",
            "latitude",
            "longitude",
        )
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
            "property_type": forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields["property_type"].choices = PropertyType.choices
        self.fields["tehsil"].required = True
        self.fields["tehsil"].queryset = Tehsil.objects.all()
        self.fields["locality"].required = True
        self.fields["locality"].empty_label = "Select locality / area"
        self.fields["khasra_number"].help_text = "Optional. Found on your Khatauni."
        self.fields["locality"].widget.attrs["data-map-locality"] = "1"

    def clean(self):
        data = super().clean()
        tehsil, locality = data.get("tehsil"), data.get("locality")
        if tehsil and locality and locality.tehsil_id != tehsil.pk:
            self.add_error("locality", f"{locality.name} is not in {tehsil.name} tehsil.")
        return data


class Step3SizeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = PropertySubmission
        fields = (
            "area_value",
            "area_unit",
            "road_width_ft",
            "frontage_ft",
            "facing",
            "is_corner",
            "has_boundary_wall",
            "has_electricity",
            "water_source",
            "distance_main_road_m",
            "irrigation_source",
            "current_crop",
            "soil_type",
            "has_tubewell",
        )

    AGRI_FIELDS = ("irrigation_source", "current_crop", "soil_type", "has_tubewell")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields["area_value"].required = True
        self.fields["area_value"].widget.attrs.update({"data-area-value": "1", "step": "0.01", "min": "0.01"})
        self.fields["area_unit"].widget.attrs["data-area-unit"] = "1"


class Step4LegalForm(BootstrapFormMixin, forms.ModelForm):
    title_documents = forms.MultipleChoiceField(
        label="Title documents available",
        choices=PropertySubmission.TITLE_DOCUMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = PropertySubmission
        fields = (
            "ownership_type",
            "number_of_owners",
            "title_documents",
            "mutation_done",
            "approval_status",
            "has_loan",
            "has_dispute",
            "encumbrance_details",
        )
        widgets = {"encumbrance_details": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields["encumbrance_details"].label = "Loan / dispute details"

    def clean(self):
        data = super().clean()
        if data.get("ownership_type") == PropertySubmission.Ownership.SINGLE:
            data["number_of_owners"] = 1
        elif (data.get("number_of_owners") or 1) < 2:
            self.add_error("number_of_owners", "Joint ownership needs at least 2 owners.")
        if (data.get("has_loan") or data.get("has_dispute")) and not data.get("encumbrance_details"):
            self.add_error("encumbrance_details", "Please share a few details about the loan or dispute.")
        return data


class Step5PriceForm(BootstrapFormMixin, forms.ModelForm):
    photos = MultipleFileField(label="Property photos", kind="image")
    document_type = forms.ChoiceField(
        label="Document type", choices=SubmissionDocument.DocType.choices, required=False
    )
    documents = MultipleFileField(label="Documents (PDF / image)", kind="document")

    class Meta:
        model = PropertySubmission
        fields = (
            "expected_price",
            "price_negotiable",
            "reason_for_selling",
            "urgency",
            "preferred_visit_time",
            "consent",
        )
        widgets = {"reason_for_selling": forms.Textarea(attrs={"rows": 2})}
        labels = {"expected_price": "Expected price (₹)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields["expected_price"].required = True
        self.fields["expected_price"].widget.attrs.update({"min": "10000", "data-price-input": "1"})
        self.fields["consent"].required = True
        self.fields["consent"].label = (
            "I confirm the details are true and allow the company to contact me on call/WhatsApp."
        )
        self.fields["photos"].widget.attrs.update({"accept": "image/*", "class": "d-none", "data-dropzone-input": "photos"})
        self.fields["documents"].widget.attrs.update(
            {"accept": ".pdf,image/*", "class": "form-control", "data-doc-input": "1"}
        )


class OTPForm(forms.Form):
    otp = forms.CharField(
        label="Enter 4 digit OTP",
        max_length=4,
        min_length=4,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg text-center otp-input", "inputmode": "numeric"}),
    )


class TrackForm(BootstrapFormMixin, forms.Form):
    reference_id = forms.CharField(label="Reference ID", max_length=20)
    phone = forms.CharField(label="Registered mobile number", max_length=10, validators=[indian_phone_validator])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields["reference_id"].widget.attrs["placeholder"] = "BDA-2026-00042"
        self.fields["phone"].widget.attrs.update({"inputmode": "numeric", "data-phone": "1"})

    def clean_reference_id(self):
        return self.cleaned_data["reference_id"].strip().upper()


class OwnerUploadForm(BootstrapFormMixin, forms.Form):
    photos = MultipleFileField(label="Add photos", kind="image")
    document_type = forms.ChoiceField(choices=SubmissionDocument.DocType.choices, required=False)
    documents = MultipleFileField(label="Add documents", kind="document")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()

    def clean(self):
        data = super().clean()
        if not data.get("photos") and not data.get("documents"):
            raise forms.ValidationError("Choose at least one photo or document to upload.")
        return data


class OfferResponseForm(forms.Form):
    ACTIONS = (("accept", "Accept"), ("reject", "Reject"), ("counter", "Counter"))
    action = forms.ChoiceField(choices=ACTIONS)
    counter_amount = forms.DecimalField(required=False, min_value=1, max_digits=14, decimal_places=2)
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def clean(self):
        data = super().clean()
        if data.get("action") == "counter" and not data.get("counter_amount"):
            self.add_error("counter_amount", "Enter your counter price.")
        return data
