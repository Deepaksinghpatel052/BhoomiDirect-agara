"""Small factories shared by the test suites."""
from decimal import Decimal

from accounts.models import User
from locations.models import CircleRate, Locality, Tehsil
from submissions.constants import CircleCategory
from submissions.models import PropertySubmission


def make_locality(name="Fatehabad Road"):
    tehsil, _ = Tehsil.objects.get_or_create(name="Agra Sadar")
    loc = Locality.objects.create(name=name, tehsil=tehsil, latitude=27.16, longitude=78.05)
    CircleRate.objects.create(locality=loc, property_type=CircleCategory.RESIDENTIAL, rate_per_sq_meter=30000)
    CircleRate.objects.create(locality=loc, property_type=CircleCategory.AGRICULTURAL, rate_per_sq_meter=1000)
    return loc


def make_user(username, role, phone, password="pass1234", **extra):
    return User.objects.create_user(username=username, password=password, role=role, phone=phone, **extra)


def make_submission(locality, **kwargs):
    data = {
        "owner_name": "Ramesh Kumar",
        "phone": "9876500001",
        "property_type": "residential_plot",
        "tehsil": locality.tehsil,
        "locality": locality,
        "area_value": Decimal("200"),
        "area_unit": "sqyard",
        "expected_price": Decimal("5000000"),
        "is_complete": True,
    }
    data.update(kwargs)
    return PropertySubmission.objects.create(**data)
