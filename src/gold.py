from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

from .models import ScanError


def fraction_to_decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def gold_cost_for(api_id: str, gold_config: dict) -> Decimal:
    if api_id in gold_config:
        return Decimal(str(gold_config[api_id]))
    material = gold_config.get("materials", {}).get(api_id)
    if isinstance(material, dict) and "gold_cost" in material:
        return Decimal(str(material["gold_cost"]))
    raise ScanError(f"未知金幣成本: {api_id}", phase="gold")


def leg_gold_cost(received_amount: Fraction, receive_currency: str, gold_config: dict) -> Decimal:
    return fraction_to_decimal(received_amount) * gold_cost_for(receive_currency, gold_config)
