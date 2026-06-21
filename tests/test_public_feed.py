from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction

from src.models import Candidate, CandidateStatus, Direction, LegResult, ScanResult, TradeEdge
from src.reporting import public_result_to_jsonable, render_public_markdown, status_jsonable


def _candidate() -> Candidate:
    edge = TradeEdge(
        "exalted",
        "mat",
        Fraction(1),
        Fraction(2),
        Direction.CURRENCY_ONE_TO_TWO,
        1,
        Decimal("1"),
        Decimal("1"),
        Decimal("2"),
        Decimal("10"),
        1,
    )
    edge2 = TradeEdge(
        "mat",
        "divine",
        Fraction(2),
        Fraction(1),
        Direction.CURRENCY_ONE_TO_TWO,
        1,
        Decimal("1"),
        Decimal("1"),
        Decimal("0.5"),
        Decimal("800"),
        2,
    )
    return Candidate(
        status=CandidateStatus.NEEDS_IN_GAME_VERIFICATION,
        start_currency="exalted",
        target_currency="divine",
        route=("exalted", "mat", "divine"),
        start_balance=Decimal("7500"),
        start_input=Fraction(150),
        final_target_amount=Fraction(75),
        direct_target_amount=Fraction(50),
        profit_target_equivalent=Fraction(25),
        profit_percent=Decimal("0.5"),
        total_gold=Decimal("61800"),
        gold_per_divine_profit=Decimal("2472"),
        divine_profit_per_100k_gold=Decimal("40.45"),
        epoch=1,
        utc_time=datetime(2026, 6, 21, tzinfo=UTC),
        local_time=datetime(2026, 6, 21, 8, tzinfo=UTC),
        age_minutes=Decimal("5"),
        legs=(LegResult(edge, Fraction(150), Fraction(300), Decimal("3000")), LegResult(edge2, Fraction(300), Fraction(150), Decimal("120000"))),
        risk_tags=("歷史候選", "需要遊戲內驗證"),
        executable=False,
    )


def test_public_feed_is_sanitized():
    names = {"exalted": "崇高石", "mat": "材料甲", "divine": "神聖石"}
    candidate = _candidate()
    result = ScanResult(
        "pc",
        "Mirage",
        1,
        datetime(2026, 6, 21, tzinfo=UTC),
        candidate.utc_time,
        candidate.local_time,
        Decimal("5"),
        (candidate,),
        0,
        (),
    )

    markdown = render_public_markdown(result, names)
    latest_json = public_result_to_jsonable(result, names)
    status_json = status_jsonable(result)

    assert "崇高石 → 材料甲 → 神聖石" in markdown
    assert "7500" not in markdown
    assert "起始通貨餘額" not in markdown
    assert "起始通貨投入" not in markdown
    assert "exalted" not in str(latest_json)
    assert "start_balance" not in str(latest_json)
    assert "start_input" not in str(latest_json)
    assert status_json["status"] == "fresh"
    assert status_json["candidate_count"] == 1
