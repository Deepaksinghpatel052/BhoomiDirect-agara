from django import forms

from core.forms import BootstrapFormMixin
from submissions.constants import AreaUnit, PropertyType

from .models import CircleRate, Locality


class EstimatorForm(BootstrapFormMixin, forms.Form):
    locality = forms.ModelChoiceField(queryset=Locality.objects.all(), empty_label="Select area / locality")
    property_type = forms.ChoiceField(choices=PropertyType.choices)
    area_value = forms.DecimalField(label="Area", min_value=0.01, max_digits=12, decimal_places=2)
    area_unit = forms.ChoiceField(label="Unit", choices=AreaUnit.choices, initial=AreaUnit.SQYARD)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        for name in ("locality", "property_type", "area_unit"):
            self.fields[name].widget.attrs["class"] = "form-select form-select-lg"
        self.fields["area_value"].widget.attrs["class"] = "form-control form-control-lg"


class LocalityForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Locality
        fields = (
            "name",
            "tehsil",
            "locality_type",
            "latitude",
            "longitude",
            "description",
            "connectivity",
            "landmarks",
            "is_featured",
            "meta_title",
            "meta_description",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "connectivity": forms.Textarea(attrs={"rows": 3}),
            "landmarks": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class CircleRateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CircleRate
        fields = ("locality", "property_type", "rate_per_sq_meter", "effective_year")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
