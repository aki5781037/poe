from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from fractions import Fraction

from .gold import fraction_to_decimal, leg_gold_cost
from .models import Candidate, CandidateStatus, LegResult, ScanError, TradeEdge
from .normalize import ensure_fresh, epoch_to_datetimes


def apply_edge(edge: TradeEdge, pay_quantity: Fraction, gold_config: dict) -> LegResult:
    receive_quantity = pay_quantity * edge.receive_amount / edge.pay_amount
    gold_cost = leg_gold_cost(receive_quantity, edge.receive_currency, gold_config)
    return LegResult(edge=edge, pay_quantity=pay_quantity, receive_quantity=receive_quantity, gold_cost=gold_cost)


def build_graph(edges: list[TradeEdge]) -> dict[str, list[TradeEdge]]:
    graph: dict[str, list[TradeEdge]] = defaultdict(list)
    for edge in edges:
        graph[edge.payment_currency].append(edge)
    return graph


def direct_edge(graph: dict[str, list[TradeEdge]], start: str, target: str) -> TradeEdge | None:
    return next((edge for edge in graph.get(start, []) if edge.receive_currency == target), None)


def find_two_leg_paths(graph: dict[str, list[TradeEdge]], start: str, target: str) -> list[tuple[TradeEdge, TradeEdge]]:
    paths: list[tuple[TradeEdge, TradeEdge]] = []
    for first in graph.get(start, []):
        if first.receive_currency in {start, target}:
            continue
        for second in graph.get(first.receive_currency, []):
            if second.receive_currency == target and second.payment_currency != start:
                paths.append((first, second))
    return paths


def evaluate_candidates(
    *,
    edges: list[TradeEdge],
    epoch: int,
    now: datetime,
    strategy_config: dict,
    portfolio_config: dict,
    routing_config: dict,
    gold_config: dict,
    names: dict,
) -> tuple[list[Candidate], int, Decimal, datetime, datetime]:
    age = ensure_fresh(epoch, now, int(strategy_config["max_snapshot_age_minutes"]))
    utc_time, local_time = epoch_to_datetimes(epoch, strategy_config["display_timezone"])
    target = routing_config["target_currency"]
    graph = build_graph(edges)
    candidates: list[Candidate] = []
    excluded_count = 0
    balances = portfolio_config.get("balances", {})
    eligible = routing_config.get("eligible_start_currencies", [])

    for start in eligible:
        balance = Decimal(str(balances.get(start, 0)))
        benchmark = direct_edge(graph, start, target)
        if benchmark is None:
            excluded_count += 1
            continue
        for first, second in find_two_leg_paths(graph, start, target):
            if len({start, first.receive_currency, target}) != 3:
                excluded_count += 1
                continue
            route = (start, first.receive_currency, target)
            if any(part not in names for part in route):
                excluded_count += 1
                continue
            if first.historical_volume <= 0 or second.historical_volume <= 0:
                excluded_count += 1
                continue

            start_input = _position_input(balance, Decimal(str(strategy_config["test_cap_percent"])))
            if start_input <= 0:
                start_input = Fraction(1, 1)
            first_leg = apply_edge(first, start_input, gold_config)
            second_leg = apply_edge(second, first_leg.receive_quantity, gold_config)
            benchmark_leg = apply_edge(benchmark, start_input, gold_config)
            final_target = second_leg.receive_quantity
            direct_target = benchmark_leg.receive_quantity
            profit = final_target - direct_target
            if direct_target <= 0:
                excluded_count += 1
                continue
            profit_percent = fraction_to_decimal(profit / direct_target)
            total_gold = first_leg.gold_cost + second_leg.gold_cost
            if profit <= 0 or profit_percent < Decimal(str(strategy_config["min_historical_profit_percent"])):
                excluded_count += 1
                continue
            gold_per_profit = total_gold / fraction_to_decimal(profit)
            profit_per_100k = fraction_to_decimal(profit) / (total_gold / Decimal("100000")) if total_gold > 0 else None
            risk_tags = ["歷史候選", "需要遊戲內驗證", "訂單比例未知"]
            has_budget = balance > 0 and total_gold <= Decimal(str(portfolio_config["gold_balance"]))
            executable = False
            status = CandidateStatus.NEEDS_IN_GAME_VERIFICATION if has_budget else CandidateStatus.WATCH
            if not has_budget:
                risk_tags.append("缺少起始通貨")
            if gold_per_profit > Decimal(str(strategy_config["max_gold_per_divine"])):
                status = CandidateStatus.EXCLUDED
                risk_tags.append("金幣效率不達標")
            candidates.append(
                Candidate(
                    status=status,
                    start_currency=start,
                    target_currency=target,
                    route=route,
                    start_balance=balance,
                    start_input=start_input,
                    final_target_amount=final_target,
                    direct_target_amount=direct_target,
                    profit_target_equivalent=profit,
                    profit_percent=profit_percent,
                    total_gold=total_gold,
                    gold_per_divine_profit=gold_per_profit,
                    divine_profit_per_100k_gold=profit_per_100k,
                    epoch=epoch,
                    utc_time=utc_time,
                    local_time=local_time,
                    age_minutes=age,
                    legs=(first_leg, second_leg),
                    risk_tags=tuple(risk_tags),
                    executable=executable,
                )
            )
    return candidates, excluded_count, age, utc_time, local_time


def _position_input(balance: Decimal, percent: Decimal) -> Fraction:
    return Fraction(str(balance * percent)).limit_denominator(1000000)


def _watch_candidate(
    start: str,
    target: str,
    route: tuple[str, ...],
    balance: Decimal,
    epoch: int,
    utc_time: datetime,
    local_time: datetime,
    age: Decimal,
    risks: tuple[str, ...],
) -> Candidate:
    return Candidate(
        status=CandidateStatus.WATCH,
        start_currency=start,
        target_currency=target,
        route=route,
        start_balance=balance,
        start_input=Fraction(0),
        final_target_amount=Fraction(0),
        direct_target_amount=Fraction(0),
        profit_target_equivalent=Fraction(0),
        profit_percent=Decimal("0"),
        total_gold=Decimal("0"),
        gold_per_divine_profit=None,
        divine_profit_per_100k_gold=None,
        epoch=epoch,
        utc_time=utc_time,
        local_time=local_time,
        age_minutes=age,
        legs=(),
        risk_tags=("觀察候選",) + risks,
        executable=False,
    )
