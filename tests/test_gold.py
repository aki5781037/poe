from fractions import Fraction

from src.gold import leg_gold_cost


def test_material_and_divine_gold_are_exact():
    config = {
        "divine": {"gold_cost": 800, "source_url": "https://example.com", "verified_at": "2026-06-21"},
        "mat": {"gold_cost": 7, "source_url": "https://example.com", "verified_at": "2026-06-21"},
    }

    assert leg_gold_cost(Fraction(3, 1), "mat", config) == 21
    assert leg_gold_cost(Fraction(2, 1), "divine", config) == 1600
