from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction

from src.models import Candidate, CandidateStatus, Direction, LegResult, ScanResult, TradeEdge
from src.reporting import render_markdown


def test_formal_markdown_uses_mapped_traditional_chinese_names():
    names = {"exalted": "崇高石", "mat": "材料甲", "divine": "神聖石"}
    edge = TradeEdge("exalted", "mat", Fraction(1), Fraction(2), Direction.CURRENCY_ONE_TO_TWO, 1, Decimal("1"), Decimal("1"), Decimal("2"), Decimal("10"), 1)
    edge2 = TradeEdge("mat", "divine", Fraction(2), Fraction(1), Direction.CURRENCY_ONE_TO_TWO, 1, Decimal("1"), Decimal("1"), Decimal("0.5"), Decimal("800"), 2)
    candidate = Candidate(
        status=CandidateStatus.NEEDS_IN_GAME_VERIFICATION,
        start_currency="exalted",
        target_currency="divine",
        route=("exalted", "mat", "divine"),
        start_balance=Decimal("100"),
        start_input=Fraction(1),
        final_target_amount=Fraction(1),
        direct_target_amount=Fraction(1, 2),
        profit_target_equivalent=Fraction(1, 2),
        profit_percent=Decimal("1"),
        total_gold=Decimal("820"),
        gold_per_divine_profit=Decimal("1640"),
        divine_profit_per_100k_gold=Decimal("60"),
        epoch=1,
        utc_time=datetime(2026, 6, 21, tzinfo=UTC),
        local_time=datetime(2026, 6, 21, 8, tzinfo=UTC),
        age_minutes=Decimal("5"),
        legs=(LegResult(edge, Fraction(1), Fraction(2), Decimal("20")), LegResult(edge2, Fraction(2), Fraction(1), Decimal("800"))),
        risk_tags=("歷史候選",),
        executable=True,
    )
    result = ScanResult("pc", "Mirage", 1, datetime(2026, 6, 21, tzinfo=UTC), candidate.utc_time, candidate.local_time, Decimal("5"), (candidate,), 0, ())

    markdown = render_markdown(result, names)

    assert "崇高石 → 材料甲 → 神聖石" in markdown
    assert "exalted" not in markdown
    assert "divine" not in markdown
    assert "mat" not in markdown
