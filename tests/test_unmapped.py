from src.models import CurrencyItem, PairData, SnapshotPair
from src.unmapped import collect_unmapped


def test_collect_unmapped_keeps_raw_api_fields_for_maintenance():
    pair = SnapshotPair(
        CurrencyExchangeSnapshotPairId=123,
        CurrencyExchangeSnapshotId=10,
        Volume="100",
        BaseCurrencyApiId="chaos",
        BaseCurrencyText="Chaos Orb",
        CurrencyOne=CurrencyItem(
            CurrencyItemId=101,
            ItemId=201,
            CurrencyCategoryId=1,
            ApiId="unknown-material",
            Text="Unknown Material",
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

    unmapped = collect_unmapped(
        [pair],
        {"divine": "神聖石"},
        {"divine": {"gold_cost": 800, "source_url": "https://example.com", "verified_at": "2026-06-21"}},
    )

    assert "unknown-material" in unmapped
    assert unmapped["unknown-material"].text == "Unknown Material"
    assert unmapped["unknown-material"].currency_item_id == 101
    assert unmapped["unknown-material"].missing_zh_hant_name is True
    assert unmapped["unknown-material"].missing_gold_cost is True
