from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction
from math import gcd
from zoneinfo import ZoneInfo

from .models import Direction, ScanError, SnapshotPair, TradeEdge
from .gold import gold_cost_for


def epoch_to_datetimes(epoch: int, timezone_name: str) -> tuple[datetime, datetime]:
    utc_dt = datetime.fromtimestamp(epoch, tz=UTC)
    return utc_dt, utc_dt.astimezone(ZoneInfo(timezone_name))


def snapshot_age_minutes(epoch: int, now: datetime) -> Decimal:
    utc_dt = datetime.fromtimestamp(epoch, tz=UTC)
    seconds = Decimal(str((now.astimezone(UTC) - utc_dt).total_seconds()))
    return seconds / Decimal("60")


def ensure_fresh(epoch: int, now: datetime, max_age_minutes: int) -> Decimal:
    age = snapshot_age_minutes(epoch, now)
    if age > Decimal(max_age_minutes):
        raise ScanError(
            f"快照過期: age_minutes={age:.2f}, max_snapshot_age_minutes={max_age_minutes}",
            phase="staleness",
        )
    return age


def decimal_to_fraction(value: Decimal, max_denominator: int = 1000000) -> Fraction:
    return Fraction(str(value)).limit_denominator(max_denominator)


def lcm(left: int, right: int) -> int:
    return abs(left * right) // gcd(left, right)


def minimum_cycle_input(edges: list[TradeEdge]) -> Fraction | None:
    if not edges or any(not edge.exact_integer_ratio for edge in edges):
        return None
    for start_units in range(1, 100000):
        quantity = Fraction(start_units, 1)
        valid = True
        for edge in edges:
            if quantity % edge.pay_amount != 0:
                valid = False
                break
            quantity = quantity * edge.receive_amount / edge.pay_amount
        if valid:
            return Fraction(start_units, 1)
    raise ScanError("無法在上限內找到最小完整整數循環", phase="integer_orders")


def build_edges(pair: SnapshotPair, epoch: int, gold_config: dict) -> list[TradeEdge]:
    one = pair.CurrencyOne.ApiId
    two = pair.CurrencyTwo.ApiId
    if pair.CurrencyOneData.RelativePrice <= 0 or pair.CurrencyTwoData.RelativePrice <= 0:
        raise ScanError(f"未知比例方向或非正相對價格: pair_id={pair.CurrencyExchangeSnapshotPairId}", phase="normalize")

    edges: list[TradeEdge] = []
    pairs = [
        (
            one,
            two,
            pair.CurrencyOneData,
            pair.CurrencyTwoData,
            Direction.CURRENCY_ONE_TO_TWO,
        ),
        (
            two,
            one,
            pair.CurrencyTwoData,
            pair.CurrencyOneData,
            Direction.CURRENCY_TWO_TO_ONE,
        ),
    ]
    for payment, receive, pay_data, receive_data, direction in pairs:
        gold_cost = gold_cost_for(receive, gold_config)
        pay_amount = decimal_to_fraction(pay_data.RelativePrice)
        receive_amount = decimal_to_fraction(receive_data.RelativePrice)
        edges.append(
            TradeEdge(
                payment_currency=payment,
                receive_currency=receive,
                pay_amount=pay_amount,
                receive_amount=receive_amount,
                ratio_direction=direction,
                epoch=epoch,
                historical_volume=receive_data.ValueTraded,
                stock_value=receive_data.StockValue,
                conservative_rate=receive_data.RelativePrice,
                gold_cost_per_received_unit=gold_cost,
                pair_id=pair.CurrencyExchangeSnapshotPairId,
                exact_integer_ratio=False,
            )
        )
    return edges
