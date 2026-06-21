from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .models import SnapshotPair


@dataclass
class UnmappedItem:
    api_id: str
    text: str
    currency_item_id: int
    pair_ids: set[int] = field(default_factory=set)
    missing_zh_hant_name: bool = False
    missing_gold_cost: bool = False


def collect_unmapped(pairs: list[SnapshotPair], names: dict, market_reference: dict) -> dict[str, UnmappedItem]:
    items: dict[str, UnmappedItem] = {}
    for pair in pairs:
        for currency in (pair.CurrencyOne, pair.CurrencyTwo):
            entry = items.setdefault(
                currency.ApiId,
                UnmappedItem(
                    api_id=currency.ApiId,
                    text=currency.Text,
                    currency_item_id=currency.CurrencyItemId,
                ),
            )
            entry.pair_ids.add(pair.CurrencyExchangeSnapshotPairId)
            entry.missing_zh_hant_name = entry.missing_zh_hant_name or currency.ApiId not in names
            ref = market_reference.get(currency.ApiId)
            has_verified_gold = (
                isinstance(ref, dict)
                and ref.get("source_url")
                and ref.get("verified_at")
                and ref.get("gold_cost") is not None
            )
            entry.missing_gold_cost = entry.missing_gold_cost or not has_verified_gold
    return {
        api_id: item
        for api_id, item in items.items()
        if item.missing_zh_hant_name or item.missing_gold_cost
    }


def write_unmapped_report(unmapped: dict[str, UnmappedItem], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Unmapped Currencies",
        "",
        "此文件保留 POE2 Scout API 原始字段供维护配置使用；正式候选报告不得显示未映射英文物品名。",
        "",
    ]
    if not unmapped:
        lines.append("目前没有未映射项目。")
    for item in sorted(unmapped.values(), key=lambda value: value.api_id):
        missing = []
        if item.missing_zh_hant_name:
            missing.append("繁中名稱")
        if item.missing_gold_cost:
            missing.append("金幣成本")
        pair_ids = ", ".join(str(pair_id) for pair_id in sorted(item.pair_ids)[:50])
        lines.extend(
            [
                f"## {item.api_id}",
                "",
                f"- ApiId: `{item.api_id}`",
                f"- API 英文 Text: `{item.text}`",
                f"- CurrencyItemId: `{item.currency_item_id}`",
                f"- 出現過的交易對: `{pair_ids}`",
                f"- 缺少: {', '.join(missing)}",
                "",
            ]
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
