from fractions import Fraction

from src.gold import leg_gold_cost


def test_material_and_divine_gold_are_exact():
    config = {"divine": 800, "chaos": 160, "exalted": 120, "materials": {"mat": {"gold_cost": 7}}}

    assert leg_gold_cost(Fraction(3, 1), "mat", config) == 21
    assert leg_gold_cost(Fraction(2, 1), "divine", config) == 1600
