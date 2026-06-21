from datetime import UTC, datetime
from decimal import Decimal

from src.models import ScanResult
from src.reporting import render_markdown
from src.main import stale_context


def test_stale_snapshot_report_is_readable_status_without_profit():
    result = ScanResult(
        "pc",
        "Mirage",
        1782021600,
        datetime(2026, 6, 21, 8, 49, tzinfo=UTC),
        datetime(2026, 6, 21, 6, 0, tzinfo=UTC),
        datetime(2026, 6, 21, 14, 0, tzinfo=UTC),
        Decimal("169.29"),
        (),
        0,
        (),
        status="數據過期 / 本次未計算套利",
        max_snapshot_age_minutes=70,
        raw_saved=True,
    )

    markdown = render_markdown(result, {"divine": "神聖石"})

    assert "數據過期 / 本次未計算套利" in markdown
    assert "本次不計算策略、不生成候選、不計算利潤" in markdown
    assert "淨利潤" not in markdown


def test_consecutive_stale_keeps_recent_three_epoch_observations():
    previous_status = {
        "status": "stale",
        "snapshot_epoch": "100",
        "stale_epoch_history": ["90", "100"],
    }

    history, alert = stale_context(100, previous_status)

    assert history == ("90", "100", "100")
    assert alert is True
