from __future__ import annotations

import os
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import yaml

from .api_discovery import write_contract
from .models import ScanError, ScanResult, StaleSnapshotError
from .normalize import build_edges, ensure_fresh, epoch_to_datetimes, snapshot_age_minutes
from .reporting import WARNING, write_reports
from .scout_client import ScoutClient, resolve_league
from .strategy import evaluate_candidates
from .unmapped import collect_unmapped, write_unmapped_report


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ScanError(f"YAML 必須是 mapping: {path}", phase="config")
    return data


def load_previous_status() -> dict:
    path = os.getenv("PREVIOUS_MARKET_STATUS")
    if not path:
        return {}
    status_path = Path(path)
    if not status_path.exists():
        return {}
    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def stale_context(current_epoch: int | None, previous_status: dict) -> tuple[tuple[str, ...], bool]:
    current = str(current_epoch) if current_epoch is not None else None
    if current is None:
        return (), False
    previous_was_stale = previous_status.get("status") == "stale"
    prior_epochs = previous_status.get("stale_epoch_history")
    if not isinstance(prior_epochs, list):
        prior_epochs = []
    if previous_was_stale and not prior_epochs:
        previous_epoch = previous_status.get("snapshot_epoch")
        if previous_epoch is not None:
            prior_epochs.append(str(previous_epoch))
    history = [str(epoch) for epoch in prior_epochs if epoch is not None]
    history.append(current)
    recent = tuple(history[-3:])
    return recent, previous_was_stale and len(recent) >= 2


def run(root: Path = ROOT) -> int:
    generated_at = datetime.now(tz=UTC)
    config_dir = root / "config"
    reports_dir = root / "reports"
    raw_dir = reports_dir / "raw"
    strategy_config = load_yaml(config_dir / "strategy.yml")
    portfolio_config = load_yaml(config_dir / "portfolio.yml")
    routing_config = load_yaml(config_dir / "routing.yml")
    market_reference = load_yaml(config_dir / "market-reference.yml")
    names = load_yaml(config_dir / "names.zh-Hant.yml")
    previous_status = load_previous_status()
    realm = str(strategy_config["realm"])
    configured_league = str(strategy_config["league"])
    client = ScoutClient(
        user_agent=os.getenv("POE2_SCOUT_USER_AGENT", "POE2CurrencyFlip/0.1 (contact: your-email@example.com)"),
        raw_dir=raw_dir,
    )
    try:
        spec = client.openapi()
        write_contract(spec, root / "docs" / "api-contract.md")
        leagues = client.leagues(realm)
        league = resolve_league(configured_league, leagues)
        snapshot = client.exchange_snapshot(realm, league)
        pairs = client.snapshot_pairs(realm, league)
        write_unmapped_report(
            collect_unmapped(pairs, names, market_reference),
            reports_dir / "unmapped-currencies.md",
        )
        utc_time, local_time = epoch_to_datetimes(snapshot.Epoch, strategy_config["display_timezone"])
        raw_saved = raw_dir.exists() and any(raw_dir.glob("*.json"))
        try:
            age = ensure_fresh(snapshot.Epoch, generated_at, int(strategy_config["max_snapshot_age_minutes"]))
        except StaleSnapshotError as exc:
            stale_epochs, source_delay_alert = stale_context(snapshot.Epoch, previous_status)
            result = ScanResult(
                realm=realm,
                league=league,
                epoch=snapshot.Epoch,
                generated_at=generated_at,
                snapshot_utc=utc_time,
                snapshot_local=local_time,
                age_minutes=exc.age_minutes,
                candidates=(),
                excluded_count=0,
                warnings=(WARNING,),
                status="數據過期 / 本次未計算套利",
                max_snapshot_age_minutes=exc.max_snapshot_age_minutes,
                raw_saved=raw_saved,
                stale_epoch_history=stale_epochs,
                source_delay_alert=source_delay_alert,
            )
            write_reports(result, names, reports_dir)
            return 0
        edges = []
        for pair in pairs:
            edges.extend(
                build_edges(
                    pair,
                    snapshot.Epoch,
                    market_reference,
                    Decimal(str(strategy_config.get("slippage_buffer_percent", 0))),
                )
            )
        candidates, excluded_count, age, utc_time, local_time = evaluate_candidates(
            edges=edges,
            epoch=snapshot.Epoch,
            now=generated_at,
            strategy_config=strategy_config,
            portfolio_config=portfolio_config,
            routing_config=routing_config,
            gold_config=market_reference,
            names=names,
        )
        result = ScanResult(
            realm=realm,
            league=league,
            epoch=snapshot.Epoch,
            generated_at=generated_at,
            snapshot_utc=utc_time,
            snapshot_local=local_time,
            age_minutes=age,
            candidates=tuple(candidates),
            excluded_count=excluded_count,
            warnings=(WARNING,),
            status="ok",
            max_snapshot_age_minutes=int(strategy_config["max_snapshot_age_minutes"]),
            raw_saved=raw_saved,
            stale_epoch_history=(),
            source_delay_alert=False,
        )
        write_reports(result, names, reports_dir)
        return 0
    except ScanError as exc:
        snapshot_utc = None
        snapshot_local = None
        age = None
        epoch = None
        try:
            if "snapshot" in locals():
                epoch = snapshot.Epoch
                snapshot_utc, snapshot_local = epoch_to_datetimes(epoch, strategy_config["display_timezone"])
                age = snapshot_age_minutes(epoch, generated_at)
        except Exception as diagnostic_error:
            print(f"diagnostic context unavailable: {diagnostic_error}")
        result = ScanResult(
            realm=realm,
            league=configured_league,
            epoch=epoch,
            generated_at=generated_at,
            snapshot_utc=snapshot_utc,
            snapshot_local=snapshot_local,
            age_minutes=age,
            candidates=(),
            excluded_count=0,
            warnings=(WARNING,),
            errors=(f"階段={exc.phase}; {exc}",),
            status="error",
            max_snapshot_age_minutes=int(strategy_config["max_snapshot_age_minutes"]) if "strategy_config" in locals() else None,
            raw_saved=raw_dir.exists() and any(raw_dir.glob("*.json")),
            stale_epoch_history=(),
            source_delay_alert=False,
        )
        write_reports(result, names, reports_dir)
        print(f"scan failed: phase={exc.phase}; {exc}")
        return 2
    finally:
        client.close()


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
