from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import ScanError


REQUIRED_PATHS = [
    "/{Realm}/Leagues",
    "/{Realm}/Leagues/{LeagueName}/ExchangeSnapshot",
    "/{Realm}/Leagues/{LeagueName}/SnapshotPairs",
    "/{Realm}/Leagues/{LeagueName}/ReferenceCurrencies",
    "/{Realm}/Leagues/{LeagueName}/Currencies/Pairs/{CurrencyOneItemId}/{CurrencyTwoItemId}/History",
]

REQUIRED_SCHEMAS = [
    "GetExchangeSnapshotResponse",
    "GetSnapshotPairsResponse",
    "_CurrencyItem",
    "_PairData",
    "poe2scout__api__routes__leagues__get__GetResponse",
]


def validate_contract(spec: dict[str, Any]) -> None:
    paths = spec.get("paths", {})
    schemas = spec.get("components", {}).get("schemas", {})
    missing_paths = [path for path in REQUIRED_PATHS if path not in paths]
    missing_schemas = [schema for schema in REQUIRED_SCHEMAS if schema not in schemas]
    if missing_paths or missing_schemas:
        raise ScanError(
            f"OpenAPI schema 變更: missing_paths={missing_paths}; missing_schemas={missing_schemas}",
            phase="api_discovery",
        )


def render_contract(spec: dict[str, Any]) -> str:
    validate_contract(spec)
    schemas = spec["components"]["schemas"]
    pair = schemas["GetSnapshotPairsResponse"]["properties"]
    pair_data = schemas["_PairData"]["properties"]
    currency_item = schemas["_CurrencyItem"]["properties"]
    lines = [
        "# POE2 Scout API Contract",
        "",
        "Base URL: `https://api.poe2scout.com`",
        "",
        "Discovery source: `GET /openapi.json` returned OpenAPI JSON. `/swagger` also points to `/api/openapi.json`.",
        "",
        "## 實際使用的端點",
    ]
    for path in REQUIRED_PATHS:
        lines.append(f"- `GET {path}`")
    lines.extend(
        [
            "",
            "## 參數",
            "- `Realm`: path string, configured by `config/strategy.yml` (`pc` by default).",
            "- `LeagueName`: path string. `league: auto` resolves from `GET /{Realm}/Leagues` where `IsCurrent=true`, preferring non-hardcore.",
            "- `CurrencyOneItemId` / `CurrencyTwoItemId`: path integers from `CurrencyOne.CurrencyItemId` and `CurrencyTwo.CurrencyItemId` in `SnapshotPairs`.",
            "- `Limit`: required integer for pair history. The scanner v1 does not depend on history for executable quantities.",
            "- `EndEpoch`: optional integer for pair history.",
            "",
            "## SnapshotPairs 響應字段",
        ]
    )
    for name in pair:
        lines.append(f"- `{name}`")
    lines.extend(["", "## Currency item 字段"])
    for name in currency_item:
        lines.append(f"- `{name}`")
    lines.extend(["", "## Pair data 字段"])
    for name in pair_data:
        lines.append(f"- `{name}`")
    lines.extend(
        [
            "",
            "## 貨幣對比例方向",
            "- `CurrencyOneData` and `CurrencyTwoData` are bound to the named sides returned by the API.",
            "- The code creates two directed edges per pair: `CurrencyOne -> CurrencyTwo` and `CurrencyTwo -> CurrencyOne`.",
            "- Direction is never inferred from numeric magnitude. It is recorded as `currency_one_to_two` or `currency_two_to_one` from the API side labels.",
            "- POE2 Scout snapshot data is historical aggregate data. It does not provide a live order book or a guaranteed directly executable integer order.",
            "",
            "## Realm、League、Currency Item ID 取得方法",
            "- Realm: configured value, default `pc`.",
            "- League: `GET /{Realm}/Leagues`; `auto` selects current non-hardcore league.",
            "- Currency Item ID: `CurrencyOne.CurrencyItemId` / `CurrencyTwo.CurrencyItemId` from `GET /{Realm}/Leagues/{LeagueName}/SnapshotPairs`.",
            "",
            "## 保守限制",
            "- Field loss, non-JSON responses, unknown direction, unknown gold cost, unmapped Traditional Chinese name, or stale snapshots stop or exclude calculations.",
            "- Reports must say historical candidate and in-game verification threshold only, not realtime executable order.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_contract(spec: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_contract(spec), encoding="utf-8")
