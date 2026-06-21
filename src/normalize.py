from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction
from math import gcd
from zoneinfo import ZoneInfo

from .gold import gold_cost_for
from .models import Direction, ScanError, SnapshotPair, StaleSnapshotError, TradeEdge


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
        raise StaleSnapshotError(
            f"快照過期: age_minutes={age:.2f}, max_snapshot_age_minutes={max_age_minutes}",
            age_minutes=age,
            max_snapshot_age_minutes=max_age_minutes,
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


def build_edges(pair: SnapshotPair, epoch: int, market_reference: dict, slippage_buffer_percent: Decimal = Decimal("0")) -> list[TradeEdge]:
    one = pair.CurrencyOne.ApiId
    two = pair.CurrencyTwo.ApiId
    if pair.CurrencyOneData.RelativePrice <= 0 or pair.CurrencyTwoData.RelativePrice <= 0:
        return []

    edges: list[TradeEdge] = []
    buffer_multiplier = Decimal("1") - (slippage_buffer_percent / Decimal("100"))
    if buffer_multiplier <= 0:
        raise ScanError("slippage_buffer_percent 必須小於 100", phase="config")
    pairs = [
        (
            one,
            two,
            pair.CurrencyTwoData.RelativePrice,
            pair.CurrencyOneData.RelativePrice,
            pair.CurrencyTwoData,
            Direction.CURRENCY_ONE_TO_TWO,
        ),
        (
            two,
            one,
            pair.CurrencyOneData.RelativePrice,
            pair.CurrencyTwoData.RelativePrice,
            pair.CurrencyOneData,
            Direction.CURRENCY_TWO_TO_ONE,
        ),
    ]
    for payment, receive, pay_price, receive_price, receive_data, direction in pairs:
        gold_cost = gold_cost_for(receive, market_reference)
        pay_amount = decimal_to_fraction(pay_price)
        receive_amount = decimal_to_fraction(receive_price * buffer_multiplier)
        implied_rate = (receive_price * buffer_multiplier) / pay_price
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
                implied_exchange_rate=implied_rate,
                gold_cost_per_received_unit=gold_cost,
                pair_id=pair.CurrencyExchangeSnapshotPairId,
                exact_integer_ratio=False,
            )
        )
    return edges
