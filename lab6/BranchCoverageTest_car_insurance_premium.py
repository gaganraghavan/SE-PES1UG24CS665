import pytest

from car_insurance_premium import annual_premium, no_claim_bonus, claim_payout


def test_annual_premium():
    with pytest.raises(ValueError, match="unknown car type"):
        annual_premium("truck", 30, 0, False)

    with pytest.raises(ValueError, match="driver too young"):
        annual_premium("sedan", 17, 0, False)

    assert annual_premium("sedan", 20, 0, True) == 12300
    assert annual_premium("hatchback", 30, 1, False) == 8000
    assert annual_premium("suv", 60, 3, False) == 34000


def test_no_claim_bonus():
    with pytest.raises(ValueError, match="invalid years"):
        no_claim_bonus(-1)

    assert no_claim_bonus(0) == 0
    assert no_claim_bonus(1) == 20
    assert no_claim_bonus(3) == 35
    assert no_claim_bonus(5) == 50


def test_claim_payout():
    with pytest.raises(ValueError, match="invalid amount"):
        claim_payout(-1, 100, 10, False)

    with pytest.raises(ValueError, match="invalid amount"):
        claim_payout(50, 100, -1, False)

    assert claim_payout(20, 100, 10, True) == 100
    assert claim_payout(10, 100, 10, False) == 0
    assert claim_payout(70, 100, 10, False) == 60
    assert claim_payout(200, 100, 10, False) == 100

def test_annual_premium_boundary_cases():
    assert annual_premium("sedan", 25, 2, False) == 12000
    assert annual_premium("hatchback", 59, 1, True) == 7500
    assert annual_premium("suv", 24, 2, True) == 18500


def test_no_claim_bonus_boundary_cases():
    assert no_claim_bonus(2) == 20
    assert no_claim_bonus(4) == 35


def test_claim_payout_boundary_cases():
    assert claim_payout(11, 100, 10, False) == 1
    assert claim_payout(10, 100, 11, False) == 0
    assert claim_payout(150, 100, 50, False) == 100