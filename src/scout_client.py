from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
from pydantic import ValidationError

from .models import ExchangeSnapshot, League, ScanError, SnapshotPair


class ScoutClient:
    def __init__(
        self,
        base_url: str = "https://api.poe2scout.com",
        user_agent: str = "POE2CurrencyFlip/0.1 (contact: user-configured-email)",
        raw_dir: Path | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.raw_dir = raw_dir
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"User-Agent": user_agent, "Accept": "application/json"},
            timeout=30,
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def _get_json(self, path: str, *, phase: str) -> Any:
        response = self.client.get(path)
        content_type = response.headers.get("content-type", "")
        if response.status_code >= 400:
            raise ScanError(
                f"HTTP {response.status_code}; Content-Type={content_type}; path={path}; body={response.text[:300]}",
                phase=phase,
            )
        if "json" not in content_type.lower():
            raise ScanError(
                f"非 JSON 回應; HTTP {response.status_code}; Content-Type={content_type}; path={path}; body={response.text[:300]}",
                phase=phase,
            )
        data = response.json()
        if self.raw_dir:
            self.raw_dir.mkdir(parents=True, exist_ok=True)
            safe = path.strip("/").replace("/", "_").replace("?", "_") or "root"
            (self.raw_dir / f"{safe}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return data

    def openapi(self) -> dict[str, Any]:
        return self._get_json("/openapi.json", phase="api_discovery")

    def leagues(self, realm: str) -> list[League]:
        data = self._get_json(f"/{realm}/Leagues", phase="leagues")
        try:
            return [League.model_validate(item) for item in data]
        except ValidationError as exc:
            raise ScanError(f"Leagues schema 欄位缺失或變更: {exc}", phase="leagues") from exc

    def exchange_snapshot(self, realm: str, league: str) -> ExchangeSnapshot:
        data = self._get_json(f"/{realm}/Leagues/{league}/ExchangeSnapshot", phase="snapshot")
        try:
            return ExchangeSnapshot.model_validate(data)
        except ValidationError as exc:
            raise ScanError(f"ExchangeSnapshot schema 欄位缺失或變更: {exc}", phase="snapshot") from exc

    def snapshot_pairs(self, realm: str, league: str) -> list[SnapshotPair]:
        data = self._get_json(f"/{realm}/Leagues/{league}/SnapshotPairs", phase="snapshot_pairs")
        try:
            return [SnapshotPair.model_validate(item) for item in data]
        except ValidationError as exc:
            raise ScanError(f"SnapshotPairs schema 欄位缺失或變更: {exc}", phase="snapshot_pairs") from exc


def resolve_league(configured: str, leagues: list[League]) -> str:
    if configured != "auto":
        return configured
    current = [league for league in leagues if league.IsCurrent and "hardcore" not in league.Value.lower()]
    if not current:
        current = [league for league in leagues if league.IsCurrent]
    if not current:
        raise ScanError("找不到 IsCurrent=true 的 League", phase="leagues")
    return current[0].Value
