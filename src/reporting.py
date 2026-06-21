from __future__ import annotations

import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from .gold import fraction_to_decimal
from .models import Candidate, ScanResult


WARNING = "本報告是 POE2 Scout 已完成小時的歷史聚合數據，不是遊戲內實時可用交易盤口。必須用遊戲內可用交易複核後才可下單。"


def fmt_fraction(value: Fraction) -> str:
    dec = fraction_to_decimal(value)
    return f"{dec:.6f}".rstrip("0").rstrip(".")


def fmt_decimal(value: Decimal | None) -> str:
    if value is None:
        return "未知"
    return f"{value:.6f}".rstrip("0").rstrip(".")


def render_markdown(result: ScanResult, names: dict[str, str]) -> str:
    lines = [
        "# POE2 通貨套利候選報告",
        "",
        f"- Realm: `{result.realm}`",
        f"- League: `{result.league}`",
        f"- 數據 epoch: `{result.epoch if result.epoch is not None else '未知'}`",
        f"- 數據時間 UTC: `{result.snapshot_utc.isoformat() if result.snapshot_utc else '未知'}`",
        f"- 數據時間 Asia/Shanghai: `{result.snapshot_local.isoformat() if result.snapshot_local else '未知'}`",
        f"- 報告生成時間: `{result.generated_at.isoformat()}`",
        f"- 數據延遲分鐘數: `{fmt_decimal(result.age_minutes)}`",
        "",
        f"> {WARNING}",
        "",
    ]
    if result.errors:
        lines.extend(["## 錯誤", ""])
        for error in result.errors:
            lines.append(f"- {error}")
        return "\n".join(lines) + "\n"

    review = [candidate for candidate in result.candidates if candidate.status.value == "需要遊戲內驗證"]
    watch = [candidate for candidate in result.candidates if candidate.status.value != "需要遊戲內驗證"]
    if not review and not watch:
        lines.append("本小時沒有符合條件的歷史候選。")
        return "\n".join(lines) + "\n"

    for title, items in (("需要遊戲內驗證", review), ("觀察候選", watch)):
        if not items:
            continue
        lines.extend([f"## {title}", ""])
        for candidate in items:
            lines.extend(_candidate_lines(candidate, names))
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def _candidate_lines(candidate: Candidate, names: dict[str, str]) -> list[str]:
    route = " → ".join(names[part] for part in candidate.route)
    lines = [
        f"### {route}",
        "",
        f"- 起始通貨: {names[candidate.start_currency]}",
        f"- 起始通貨餘額: {candidate.start_balance}",
        f"- 是否可立即下單: 否",
        f"- 數據 epoch: `{candidate.epoch}`",
        f"- UTC 時間: `{candidate.utc_time.isoformat()}`",
        f"- Asia/Shanghai 時間: `{candidate.local_time.isoformat()}`",
        f"- 數據延遲: {fmt_decimal(candidate.age_minutes)} 分鐘",
        f"- 起始通貨投入: {fmt_fraction(candidate.start_input)}",
        f"- 最終神聖石取得量: {fmt_fraction(candidate.final_target_amount)}",
        f"- 直接換神聖石基準量: {fmt_fraction(candidate.direct_target_amount)}",
        f"- 淨利潤（神聖石等值）: {fmt_fraction(candidate.profit_target_equivalent)}",
        f"- 利潤率: {fmt_decimal(candidate.profit_percent * Decimal('100'))}%",
        f"- 總金幣: {fmt_decimal(candidate.total_gold)}",
        f"- 每賺 1 枚神聖石消耗金幣: {fmt_decimal(candidate.gold_per_divine_profit)}",
        f"- 每 10 萬金幣可產生的神聖石等值利潤: {fmt_decimal(candidate.divine_profit_per_100k_gold)}",
        f"- 風險標籤: {' / '.join(candidate.risk_tags)}",
        "",
        "每一步：",
    ]
    for leg in candidate.legs:
        lines.append(
            "- "
            f"我擁有: {names[leg.edge.payment_currency]}；"
            f"我需要: {names[leg.edge.receive_currency]}；"
            f"支付數量: {fmt_fraction(leg.pay_quantity)}；"
            f"取得數量: {fmt_fraction(leg.receive_quantity)}；"
            f"保守比例: {fmt_decimal(leg.edge.conservative_rate)}；"
            f"金幣: {fmt_decimal(leg.gold_cost)}"
        )
    if candidate.legs:
        first, second = candidate.legs
        lines.extend(
            [
                "",
                "遊戲內複核指令：",
                f"1. 我需要：{names[first.edge.receive_currency]}；我擁有：{names[first.edge.payment_currency]}。驗證買入成本不得高於報告閾值。",
                f"2. 我需要：{names[second.edge.receive_currency]}；我擁有：{names[second.edge.payment_currency]}。驗證賣出收益不得低於報告閾值。",
            ]
        )
    return lines


def result_to_jsonable(result: ScanResult) -> dict:
    return {
        "realm": result.realm,
        "league": result.league,
        "epoch": result.epoch,
        "generated_at": result.generated_at.isoformat(),
        "snapshot_utc": result.snapshot_utc.isoformat() if result.snapshot_utc else None,
        "snapshot_local": result.snapshot_local.isoformat() if result.snapshot_local else None,
        "age_minutes": str(result.age_minutes) if result.age_minutes is not None else None,
        "warnings": list(result.warnings),
        "errors": list(result.errors),
        "excluded_count": result.excluded_count,
        "candidates": [
            {
                "status": candidate.status.value,
                "route": list(candidate.route),
                "start_currency": candidate.start_currency,
                "start_balance": str(candidate.start_balance),
                "executable": candidate.executable,
                "profit_target_equivalent": fmt_fraction(candidate.profit_target_equivalent),
                "profit_percent": str(candidate.profit_percent),
                "total_gold": str(candidate.total_gold),
                "risk_tags": list(candidate.risk_tags),
            }
            for candidate in result.candidates
        ],
    }


def write_reports(result: ScanResult, names: dict[str, str], reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "latest.md").write_text(render_markdown(result, names), encoding="utf-8")
    (reports_dir / "latest.json").write_text(
        json.dumps(result_to_jsonable(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
