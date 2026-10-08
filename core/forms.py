from django import forms

from accounts.models import indian_phone_validator

from .models import ContactMessage


class BootstrapFormMixin:
    """Adds Bootstrap classes to every widget."""

    def _apply_bootstrap(self):
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput,)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                continue
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
            if field.required:
                widget.attrs.setdefault("required", "required")


class ContactForm(BootstrapFormMixin, forms.ModelForm):
    phone = forms.CharField(max_length=10, validators=[indian_phone_validator])

    class Meta:
        model = ContactMessage
        fields = ("name", "phone", "email", "subject", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields["phone"].widget.attrs.update({"inputmode": "numeric", "data-phone": "1"})
