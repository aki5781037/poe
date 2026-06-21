from datetime import UTC, datetime, timedelta

import pytest

from src.models import ScanError
from src.normalize import ensure_fresh


def test_snapshot_older_than_70_minutes_is_rejected():
    now = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
    old_epoch = int((now - timedelta(minutes=71)).timestamp())

    with pytest.raises(ScanError, match="快照過期"):
        ensure_fresh(old_epoch, now, 70)
