import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core.seo import breadcrumb_schema
from submissions.constants import STATUS_COLORS, Status

register = template.Library()


def _to_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def indian_grouping(number):
    """12345678 -> '1,23,45,678' (Indian digit grouping)."""
    negative = number < 0
    s = str(abs(int(number)))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if negative else "") + s


@register.simple_tag
def asset(path):
    """Static URL for custom CSS/JS, using the .min version when enabled and built."""
    if getattr(settings, "USE_MINIFIED_ASSETS", False):
        p = Path(path)
        min_path = str(p.with_name(f"{p.stem}.min{p.suffix}")).replace("\\", "/")
        if (Path(settings.BASE_DIR) / "static" / min_path).exists():
            return static(min_path)
    return static(path)


@register.filter
def inr(value):
    """₹ 45,00,000"""
    amount = _to_decimal(value)
    if amount is None:
        return "—"
    return f"₹ {indian_grouping(amount.quantize(Decimal('1')))}"


@register.filter
def inr_short(value):
    """45 Lakh / 1.2 Crore / 85,000"""
    amount = _to_decimal(value)
    if amount is None:
        return "—"
    if abs(amount) >= 10_000_000:
        num = (amount / Decimal(10_000_000)).quantize(Decimal("0.01"))
        return f"₹ {_trim(num)} Crore"
    if abs(amount) >= 100_000:
        num = (amount / Decimal(100_000)).quantize(Decimal("0.01"))
        return f"₹ {_trim(num)} Lakh"
    return inr(amount)


def _trim(num):
    text = f"{num:f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


@register.filter
def indian_number(value):
    amount = _to_decimal(value)
    return "—" if amount is None else indian_grouping(amount)


@register.filter
def jsonld(data):
    """Render a dict as a JSON-LD <script>, escaping characters unsafe inside HTML."""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')


@register.simple_tag
def breadcrumb_jsonld(items):
    return jsonld(breadcrumb_schema(items or []))


@register.simple_tag
def status_badge(status):
    label = Status(status).label if status in Status.values else status
    css = STATUS_COLORS.get(status, "status-new")
    return format_html('<span class="status-badge {}">{}</span>', css, label)


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.filter
def split_lines(value):
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


@register.filter
def percent_of(value, total):
    try:
        return round(float(value) * 100 / float(total)) if float(total) else 0
    except (TypeError, ValueError):
        return 0
