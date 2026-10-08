from decimal import Decimal

from django.conf import settings

from submissions.constants import PROPERTY_TO_CIRCLE

from .units import to_sq_meter


def estimate_price(locality, property_type, area_value, area_unit):
    """
    Indicative price range = sample circle rate x area x market multiplier.
    Returns None when no sample rate exists for that locality/category.
    """
    category = PROPERTY_TO_CIRCLE.get(property_type)
    rate = locality.rate_for(category) if category else None
    sq_meter = to_sq_meter(area_value, area_unit)
    if not rate or not sq_meter:
        return None
    circle_value = rate.rate_per_sq_meter * sq_meter
    low = circle_value * Decimal(str(settings.ESTIMATOR_MARKET_MULTIPLIER_LOW))
    high = circle_value * Decimal(str(settings.ESTIMATOR_MARKET_MULTIPLIER_HIGH))
    return {
        "rate_per_sq_meter": rate.rate_per_sq_meter,
        "rate_year": rate.effective_year,
        "sq_meter": sq_meter,
        "circle_value": circle_value.quantize(Decimal("1")),
        "low": (low / 1000).quantize(Decimal("1")) * 1000,
        "high": (high / 1000).quantize(Decimal("1")) * 1000,
    }
