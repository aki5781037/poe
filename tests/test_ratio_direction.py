from decimal import Decimal
from fractions import Fraction

from src.models import CurrencyItem, Direction, PairData, SnapshotPair
from src.normalize import build_edges


def _pair() -> SnapshotPair:
    return SnapshotPair(
        CurrencyExchangeSnapshotPairId=1,
        CurrencyExchangeSnapshotId=10,
        Volume="100",
        BaseCurrencyApiId="chaos",
        BaseCurrencyText="Chaos Orb",
        CurrencyOne=CurrencyItem(
            CurrencyItemId=101,
            ItemId=201,
            CurrencyCategoryId=1,
            ApiId="exalted",
            Text="Exalted Orb",
            CategoryApiId="currency",
        ),
        CurrencyTwo=CurrencyItem(
            CurrencyItemId=102,
            ItemId=202,
            CurrencyCategoryId=1,
            ApiId="divine",
            Text="Divine Orb",
            CategoryApiId="currency",
        ),
        CurrencyOneData=PairData(ValueTraded="50", RelativePrice="10", StockValue="10", VolumeTraded=5, HighestStock=20),
        CurrencyTwoData=PairData(ValueTraded="5", RelativePrice="1", StockValue="1", VolumeTraded=5, HighestStock=10),
    )


def test_reverse_pair_uses_api_side_labels_not_numeric_guessing():
    market_reference = {
        "exalted": {
            "gold_cost": 120,
            "source_url": "https://example.com",
            "verified_at": "2026-06-21",
        },
        "divine": {
            "gold_cost": 800,
            "source_url": "https://example.com",
            "verified_at": "2026-06-21",
        },
    }
    edges = build_edges(_pair(), 1000, market_reference)
    forward = next(edge for edge in edges if edge.payment_currency == "exalted")
    reverse = next(edge for edge in edges if edge.payment_currency == "divine")

    assert forward.receive_currency == "divine"
    assert forward.ratio_direction == Direction.CURRENCY_ONE_TO_TWO
    assert forward.receive_amount / forward.pay_amount == Fraction(10, 1)
    assert reverse.receive_currency == "exalted"
    assert reverse.ratio_direction == Direction.CURRENCY_TWO_TO_ONE
    assert reverse.receive_amount / reverse.pay_amount == Fraction(1, 10)
    assert (forward.receive_amount / forward.pay_amount) * (reverse.receive_amount / reverse.pay_amount) == 1
    assert forward.implied_exchange_rate == Decimal("10")
