from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

from .models import ScanError


def fraction_to_decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def gold_cost_for(api_id: str, gold_config: dict) -> Decimal | None:
    entry = gold_config.get(api_id)
    if not isinstance(entry, dict):
        return None
    if not entry.get("source_url") or not entry.get("verified_at"):
        return None
    if "gold_cost" not in entry or entry["gold_cost"] is None:
        return None
    return Decimal(str(entry["gold_cost"]))


def leg_gold_cost(received_amount: Fraction, receive_currency: str, gold_config: dict) -> Decimal:
    gold_cost = gold_cost_for(receive_currency, gold_config)
    if gold_cost is None:
        raise ScanError(f"未知金幣成本: {receive_currency}", phase="gold")
    return fraction_to_decimal(received_amount) * gold_cost
