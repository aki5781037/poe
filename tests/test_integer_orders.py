from fractions import Fraction

from src.models import Direction, TradeEdge
from src.normalize import minimum_cycle_input


def _edge(payment: str, receive: str, pay: int, got: int) -> TradeEdge:
    return TradeEdge(
        payment_currency=payment,
        receive_currency=receive,
        pay_amount=Fraction(pay, 1),
        receive_amount=Fraction(got, 1),
        ratio_direction=Direction.CURRENCY_ONE_TO_TWO,
        epoch=1,
        historical_volume=1,
        stock_value=1,
        implied_exchange_rate=1,
        gold_cost_per_received_unit=1,
        pair_id=1,
        exact_integer_ratio=True,
    )


def test_minimum_cycle_prevents_unsold_material_tail():
    first = _edge("exalted", "material", 2, 3)
    second = _edge("material", "divine", 5, 1)

    cycle = minimum_cycle_input([first, second])

    assert cycle == Fraction(10, 1)
    material = cycle * first.receive_amount / first.pay_amount
    assert material % second.pay_amount == 0


def test_unknown_exact_ratio_disables_direct_order_quantity():
    first = _edge("exalted", "material", 2, 3)
    second = _edge("material", "divine", 5, 1)
    second = TradeEdge(**{**second.__dict__, "exact_integer_ratio": False})

    assert minimum_cycle_input([first, second]) is None
