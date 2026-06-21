from datetime import UTC, datetime
from decimal import Decimal

from src.models import ScanResult
from src.reporting import render_markdown


def test_no_candidates_report_does_not_fake_profit():
    result = ScanResult("pc", "Mirage", 1, datetime.now(UTC), datetime.now(UTC), datetime.now(UTC), Decimal("1"), (), 3, ())

    markdown = render_markdown(result, {"divine": "神聖石"})

    assert "本小時沒有符合條件的歷史候選" in markdown
    assert "淨利潤" not in markdown
