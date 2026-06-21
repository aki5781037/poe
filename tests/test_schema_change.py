import pytest
from pydantic import ValidationError

from src.models import SnapshotPair


def test_missing_snapshot_pair_field_fails_clearly():
    payload = {
        "CurrencyExchangeSnapshotPairId": 1,
        "CurrencyExchangeSnapshotId": 1,
        "Volume": "1",
        "BaseCurrencyApiId": "chaos",
        "BaseCurrencyText": "Chaos Orb",
    }

    with pytest.raises(ValidationError):
        SnapshotPair.model_validate(payload)
