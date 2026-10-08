from django import forms

from accounts.models import indian_phone_validator
from core.forms import BootstrapFormMixin
from locations.models import Locality
from submissions.constants import PropertyType

from .models import BuyerInquiry, Listing

BUDGET_CHOICES = [
    ("", "Any budget"),
    ("0-2500000", "Up to ₹25 Lakh"),
    ("2500000-5000000", "₹25 - 50 Lakh"),
    ("5000000-10000000", "₹50 Lakh - 1 Crore"),
    ("10000000-30000000", "₹1 - 3 Crore"),
    ("30000000-0", "Above ₹3 Crore"),
]
AREA_CHOICES = [
    ("", "Any size"),
    ("0-200", "Up to 200 sq m"),
    ("200-1000", "200 - 1,000 sq m"),
    ("1000-5000", "1,000 - 5,000 sq m (≈ 0.4 - 2 bigha)"),
    ("5000-0", "Above 5,000 sq m"),
]
SORT_CHOICES = [
    ("newest", "Newest first"),
    ("price_asc", "Price: low to high"),
    ("price_desc", "Price: high to low"),
    ("area_desc", "Largest area"),
]


class ListingFilterForm(forms.Form):
    property_type = forms.ChoiceField(choices=[("", "All types")] + PropertyType.choices, required=False)
    locality = forms.ModelChoiceField(queryset=Locality.objects.all(), required=False, empty_label="All areas")
    budget = forms.ChoiceField(choices=BUDGET_CHOICES, required=False)
    area = forms.ChoiceField(choices=AREA_CHOICES, required=False)
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select"

    @staticmethod
    def _range(value):
        low, high = (int(x) for x in value.split("-"))
        return low, high

    def filter(self, queryset):
        if not self.is_valid():
            return queryset
        data = self.cleaned_data
        if data.get("property_type"):
            queryset = queryset.filter(property_type=data["property_type"])
        if data.get("locality"):
            queryset = queryset.filter(locality=data["locality"])
        if data.get("budget"):
            low, high = self._range(data["budget"])
            queryset = queryset.filter(price__gte=low)
            if high:
                queryset = queryset.filter(price__lte=high)
        if data.get("area"):
            low, high = self._range(data["area"])
            queryset = queryset.filter(area_sq_meter__gte=low)
            if high:
                queryset = queryset.filter(area_sq_meter__lte=high)
        order = {
            "price_asc": "price",
            "price_desc": "-price",
            "area_desc": "-area_sq_meter",
        }.get(data.get("sort"), "-created_at")
        return queryset.order_by(order)


class InquiryForm(BootstrapFormMixin, forms.ModelForm):
    phone = forms.CharField(max_length=10, validators=[indian_phone_validator])

    class Meta:
        model = BuyerInquiry
        fields = ("name", "phone", "email", "budget", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 3})}
        labels = {"budget": "Your budget (₹)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields["phone"].widget.attrs.update({"inputmode": "numeric", "data-phone": "1"})
        self.fields["message"].widget.attrs["placeholder"] = "I am interested in this property. Please call me."


class ListingEditForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Listing
        fields = ("title", "description", "price", "features", "status", "is_featured", "meta_title", "meta_description")
        widgets = {"description": forms.Textarea(attrs={"rows": 4}), "features": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
