from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from django import template


register = template.Library()


def _to_decimal(value) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


@register.filter(name="vnd")
def vnd(value, suffix: str = "₫") -> str:
    """Format a numeric value as Vietnamese currency.

    Example: 12500000 -> "12.500.000 ₫"
    """

    dec = _to_decimal(value)
    if dec is None:
        return ""

    amount = int(dec.quantize(Decimal("1")))
    formatted = f"{amount:,}".replace(",", ".")
    suffix = (suffix or "").strip()
    return f"{formatted} {suffix}" if suffix else formatted
