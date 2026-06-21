from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScanError(RuntimeError):
    def __init__(self, message: str, *, phase: str = "unknown") -> None:
        super().__init__(message)
        self.phase = phase


class StaleSnapshotError(ScanError):
    def __init__(self, message: str, *, age_minutes: Decimal, max_snapshot_age_minutes: int) -> None:
        super().__init__(message, phase="staleness")
        self.age_minutes = age_minutes
        self.max_snapshot_age_minutes = max_snapshot_age_minutes


class CandidateStatus(StrEnum):
    NEEDS_IN_GAME_VERIFICATION = "需要遊戲內驗證"
    WATCH = "觀察候選"
    EXCLUDED = "排除候選"


class Direction(StrEnum):
    CURRENCY_ONE_TO_TWO = "currency_one_to_two"
    CURRENCY_TWO_TO_ONE = "currency_two_to_one"


class League(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Value: str
    ShortName: str
    IsCurrent: bool
    DivinePrice: float
    ChaosDivinePrice: float
    BaseCurrencyApiId: str
    BaseCurrencyText: str
    BaseCurrencyIconUrl: str | None
    ExaltedCurrencyText: str
    ExaltedCurrencyIconUrl: str | None
    DivineCurrencyText: str
    DivineCurrencyIconUrl: str | None
    ChaosCurrencyText: str
    ChaosCurrencyIconUrl: str | None
    DefaultCurrency: dict


class CurrencyItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    CurrencyItemId: int
    ItemId: int
    CurrencyCategoryId: int
    ApiId: str
    Text: str
    CategoryApiId: str
    IconUrl: str | None = None
    ItemMetadata: dict | None = None


class PairData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ValueTraded: Decimal
    RelativePrice: Decimal
    StockValue: Decimal
    VolumeTraded: int
    HighestStock: int

    @field_validator("ValueTraded", "RelativePrice", "StockValue", mode="before")
    @classmethod
    def decimal_from_api(cls, value: object) -> Decimal:
        return Decimal(str(value))


class SnapshotPair(BaseModel):
    model_config = ConfigDict(extra="forbid")

    CurrencyExchangeSnapshotPairId: int
    CurrencyExchangeSnapshotId: int
    Volume: Decimal
    BaseCurrencyApiId: str
    BaseCurrencyText: str
    CurrencyOne: CurrencyItem
    CurrencyTwo: CurrencyItem
    CurrencyOneData: PairData
    CurrencyTwoData: PairData

    @field_validator("Volume", mode="before")
    @classmethod
    def decimal_from_api(cls, value: object) -> Decimal:
        return Decimal(str(value))


class ExchangeSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Epoch: int
    Volume: Decimal
    MarketCap: Decimal
    BaseCurrencyApiId: str
    BaseCurrencyText: str

    @field_validator("Volume", "MarketCap", mode="before")
    @classmethod
    def decimal_from_api(cls, value: object) -> Decimal:
        return Decimal(str(value))


@dataclass(frozen=True)
class TradeEdge:
    payment_currency: str
    receive_currency: str
    pay_amount: Fraction
    receive_amount: Fraction
    ratio_direction: Direction
    epoch: int
    historical_volume: Decimal
    stock_value: Decimal
    implied_exchange_rate: Decimal
    gold_cost_per_received_unit: Decimal | None
    pair_id: int
    exact_integer_ratio: bool = False


@dataclass(frozen=True)
class LegResult:
    edge: TradeEdge
    pay_quantity: Fraction
    receive_quantity: Fraction
    gold_cost: Decimal


@dataclass(frozen=True)
class Candidate:
    status: CandidateStatus
    start_currency: str
    target_currency: str
    route: tuple[str, ...]
    start_balance: Decimal
    start_input: Fraction
    final_target_amount: Fraction
    direct_target_amount: Fraction
    profit_target_equivalent: Fraction
    profit_percent: Decimal
    total_gold: Decimal
    gold_per_divine_profit: Decimal | None
    divine_profit_per_100k_gold: Decimal | None
    epoch: int
    utc_time: datetime
    local_time: datetime
    age_minutes: Decimal
    legs: tuple[LegResult, ...]
    risk_tags: tuple[str, ...] = field(default_factory=tuple)
    executable: bool = False


@dataclass(frozen=True)
class ScanResult:
    realm: str
    league: str
    epoch: int | None
    generated_at: datetime
    snapshot_utc: datetime | None
    snapshot_local: datetime | None
    age_minutes: Decimal | None
    candidates: tuple[Candidate, ...]
    excluded_count: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...] = ()
    status: str = "ok"
    max_snapshot_age_minutes: int | None = None
    raw_saved: bool = False
    stale_epoch_history: tuple[str, ...] = ()
    source_delay_alert: bool = False
