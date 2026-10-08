from datetime import timedelta

from django import forms
from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from core.forms import BootstrapFormMixin
from locations.models import Locality
from submissions.constants import PropertyType, Status
from submissions.forms import MultipleFileField
from submissions.models import PropertySubmission

from .models import Acquisition, Evaluation, LegalChecklist, Offer, SiteVisit


def staff_users():
    return User.objects.filter(role__in=User.STAFF_ROLES, is_active=True)


class DateInput(forms.DateInput):
    input_type = "date"


class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, attrs=None):
        super().__init__(attrs, format="%Y-%m-%dT%H:%M")


class LeadFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
    status = forms.ChoiceField(choices=[("", "All statuses")] + Status.choices, required=False)
    property_type = forms.ChoiceField(choices=[("", "All types")] + PropertyType.choices, required=False)
    locality = forms.ModelChoiceField(queryset=Locality.objects.all(), required=False, empty_label="All localities")
    urgency = forms.ChoiceField(
        choices=[("", "Any urgency")] + PropertySubmission.Urgency.choices, required=False
    )
    agent = forms.ModelChoiceField(queryset=staff_users(), required=False, empty_label="Any agent")
    date_from = forms.DateField(required=False, widget=DateInput)
    date_to = forms.DateField(required=False, widget=DateInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["agent"].queryset = staff_users()
        for field in self.fields.values():
            css = "form-select form-select-sm" if isinstance(field.widget, forms.Select) else "form-control form-control-sm"
            field.widget.attrs["class"] = css
        self.fields["q"].widget.attrs["placeholder"] = "Ref ID, name, phone, khasra"

    def filter(self, qs):
        if not self.is_valid():
            return qs
        d = self.cleaned_data
        if d.get("q"):
            q = d["q"].strip()
            qs = qs.filter(
                Q(reference_id__icontains=q)
                | Q(owner_name__icontains=q)
                | Q(phone__icontains=q)
                | Q(khasra_number__icontains=q)
                | Q(village_colony__icontains=q)
            )
        for field in ("status", "property_type", "urgency"):
            if d.get(field):
                qs = qs.filter(**{field: d[field]})
        if d.get("locality"):
            qs = qs.filter(locality=d["locality"])
        if d.get("agent"):
            qs = qs.filter(assigned_agent=d["agent"])
        if d.get("date_from"):
            qs = qs.filter(created_at__date__gte=d["date_from"])
        if d.get("date_to"):
            qs = qs.filter(created_at__date__lte=d["date_to"])
        return qs


class AssignAgentForm(BootstrapFormMixin, forms.Form):
    agent = forms.ModelChoiceField(queryset=User.objects.none(), empty_label="Unassigned", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["agent"].queryset = staff_users()
        self._apply_bootstrap()


class StatusForm(BootstrapFormMixin, forms.Form):
    status = forms.ChoiceField(choices=[c for c in Status.choices if c[0] != Status.ACQUIRED])
    note = forms.CharField(required=False, max_length=500)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class SiteVisitForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SiteVisit
        fields = ("agent", "scheduled_for")
        widgets = {"scheduled_for": DateTimeInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["agent"].queryset = staff_users()
        self.fields["agent"].required = True
        if not self.is_bound and not self.initial.get("scheduled_for"):
            self.initial["scheduled_for"] = (timezone.localtime() + timedelta(days=2)).replace(
                hour=11, minute=0, second=0, microsecond=0
            )
        self._apply_bootstrap()


class SiteVisitReportForm(BootstrapFormMixin, forms.ModelForm):
    photos = MultipleFileField(kind="image", label="Visit photos")

    class Meta:
        model = SiteVisit
        fields = (
            "status",
            "visit_notes",
            "boundary_matches_documents",
            "road_access_confirmed",
            "no_encroachment",
            "owner_met_in_person",
            "neighbour_feedback",
        )
        widgets = {"visit_notes": forms.Textarea(attrs={"rows": 3}), "neighbour_feedback": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class EvaluationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = Evaluation.SCORE_FIELDS + ("estimated_resale_value", "remarks")
        widgets = {"remarks": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        for name in Evaluation.SCORE_FIELDS:
            self.fields[name].widget = forms.NumberInput(
                attrs={"type": "range", "min": 1, "max": 10, "class": "form-range score-input", "data-score": name}
            )
        self.fields["estimated_resale_value"].label = "Estimated resale value (₹)"


class LegalChecklistForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = LegalChecklist
        fields = [key for key, _ in LegalChecklist.ITEMS] + ["notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}
        labels = dict(LegalChecklist.ITEMS)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        for key, _ in LegalChecklist.ITEMS:
            self.fields[key].widget.attrs["data-legal-item"] = "1"


class OfferForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Offer
        fields = ("amount", "valid_till", "terms")
        widgets = {"valid_till": DateInput(), "terms": forms.Textarea(attrs={"rows": 2})}
        labels = {"amount": "Offer amount (₹)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial.setdefault("valid_till", timezone.localdate() + timedelta(days=10))
        self._apply_bootstrap()
        self.fields["amount"].widget.attrs["data-price-input"] = "1"

    def clean_valid_till(self):
        value = self.cleaned_data["valid_till"]
        if value < timezone.localdate():
            raise forms.ValidationError("Validity date cannot be in the past.")
        return value


class AcquisitionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Acquisition
        fields = (
            "purchase_price",
            "purchase_date",
            "registry_date",
            "payment_mode",
            "stamp_duty",
            "registration_fee",
            "other_costs",
            "notes",
        )
        widgets = {
            "purchase_date": DateInput(),
            "registry_date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class NoteForm(BootstrapFormMixin, forms.Form):
    text = forms.CharField(widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Add an internal note..."}), label="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
