from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import yaml

from .api_discovery import write_contract
from .models import ScanError, ScanResult
from .normalize import build_edges, epoch_to_datetimes, snapshot_age_minutes
from .reporting import WARNING, write_reports
from .scout_client import ScoutClient, resolve_league
from .strategy import evaluate_candidates


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ScanError(f"YAML 必須是 mapping: {path}", phase="config")
    return data


def run(root: Path = ROOT) -> int:
    generated_at = datetime.now(tz=UTC)
    config_dir = root / "config"
    reports_dir = root / "reports"
    raw_dir = reports_dir / "raw"
    strategy_config = load_yaml(config_dir / "strategy.yml")
    portfolio_config = load_yaml(config_dir / "portfolio.yml")
    routing_config = load_yaml(config_dir / "routing.yml")
    gold_config = load_yaml(config_dir / "gold.yml")
    names = load_yaml(config_dir / "names.zh-Hant.yml")
    realm = str(strategy_config["realm"])
    configured_league = str(strategy_config["league"])
    client = ScoutClient(
        user_agent=os.getenv("POE2_SCOUT_USER_AGENT", "POE2CurrencyFlip/0.1 (contact: user-configured-email)"),
        raw_dir=raw_dir,
    )
    try:
        spec = client.openapi()
        write_contract(spec, root / "docs" / "api-contract.md")
        leagues = client.leagues(realm)
        league = resolve_league(configured_league, leagues)
        snapshot = client.exchange_snapshot(realm, league)
        pairs = client.snapshot_pairs(realm, league)
        edges = []
        for pair in pairs:
            try:
                edges.extend(build_edges(pair, snapshot.Epoch, gold_config))
            except ScanError:
                continue
        candidates, excluded_count, age, utc_time, local_time = evaluate_candidates(
            edges=edges,
            epoch=snapshot.Epoch,
            now=generated_at,
            strategy_config=strategy_config,
            portfolio_config=portfolio_config,
            routing_config=routing_config,
            gold_config=gold_config,
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
