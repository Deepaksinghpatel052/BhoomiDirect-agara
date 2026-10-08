"""
Indian land area unit conversion.

Everything is normalised to square metres. Bigha / biswa values vary by state
and even by district, so they come from settings (AREA_BIGHA_SQ_METER,
AREA_BISWA_PER_BIGHA) and default to the Agra / western UP "pucca bigha".
"""
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings


def unit_factors():
    bigha = Decimal(str(settings.AREA_BIGHA_SQ_METER))
    return {
        "sqft": Decimal("0.09290304"),
        "sqyard": Decimal("0.83612736"),
        "sqm": Decimal("1"),
        "biswa": bigha / Decimal(settings.AREA_BISWA_PER_BIGHA),
        "bigha": bigha,
        "acre": Decimal("4046.8564224"),
        "hectare": Decimal("10000"),
    }


def to_sq_meter(value, unit):
    if value in (None, ""):
        return None
    factors = unit_factors()
    if unit not in factors:
        raise ValueError(f"Unknown area unit: {unit}")
    result = Decimal(str(value)) * factors[unit]
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def from_sq_meter(sq_meter, unit):
    factors = unit_factors()
    return (Decimal(str(sq_meter)) / factors[unit]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def convert(value, from_unit, to_unit):
    # Use raw factors (no intermediate rounding) so 1 gaj is exactly 9 sq ft.
    factors = unit_factors()
    result = Decimal(str(value)) * factors[from_unit] / factors[to_unit]
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def all_units(sq_meter):
    """Return the area in every supported unit (used for display tables)."""
    return {unit: from_sq_meter(sq_meter, unit) for unit in unit_factors()}


def factors_for_js():
    """Factors as floats so the browser unit converter uses the same numbers."""
    return {k: float(v) for k, v in unit_factors().items()}


def trim_number(value):
    """Decimal('800') -> '800', Decimal('2.50') -> '2.5' (only strips zeros after a decimal point)."""
    text = f"{Decimal(str(value)):f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text
