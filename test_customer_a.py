"""
Test: Customer A — Product 0001, Winter, Volume 90, Non-EMEA
Customer is marked STRATEGIC + INDIVIDUAL with individual rate 1,000

DataFrame is set directly to avoid pandas reading '0001' as integer
when using load_csv (which calls pd.read_csv without dtype overrides).
"""

import pytest
import pandas as pd
from pricing_calculator import PricingCalculator


@pytest.fixture
def processed_calculator():
    """
    Calculator for Customer A with product 0001 at individual rate 1,000.
    DataFrame is injected directly so '0001' stays a string and the rate
    is respected without touching the shared class-level PRODUCT_RATES.
    """
    calc = PricingCalculator()
    # Register product 0001 on the instance dict so class dict is not mutated
    calc.PRODUCT_RATES = dict(PricingCalculator.PRODUCT_RATES)
    calc.PRODUCT_RATES['0001'] = {'individual': 1000.0, 'corporate': 900.0}

    # Inject pre-normalised DataFrame (mirrors what load_csv would produce)
    calc.df = pd.DataFrame([{
        'Customer': 'strategic',   # lowercase — Rule C checks 'strategic'
        'Product':  '0001',
        'Season':   'winter',
        'Volume':   90,
        'Region':   'NON-EMEA',    # uppercase — Rule E checks 'EMEA'
        'Status':   'individual',
    }])
    calc.process_calculations()
    return calc


# ---------------------------------------------------------------------------
# Core scenario tests
# ---------------------------------------------------------------------------

class TestCustomerAScenario:
    """Customer A: STRATEGIC + INDIVIDUAL, product 0001, winter, vol 90, Non-EMEA"""

    def test_total_receivable(self, processed_calculator):
        """vol 90 × rate 1,000 = 90,000 → 5% strategic discount → 85,500 (no region loading)"""
        result = processed_calculator.df.iloc[0]['Total receivables']
        expected = 85_500.0
        try:
            assert result == expected
            print(f"\nPASSED: Total receivables = {result}")
        except AssertionError:
            print(f"\nFAILED: Total receivables — expected {expected}, got {result}")
            raise


# ---------------------------------------------------------------------------
# Why each discount rule fires (or doesn't)
# ---------------------------------------------------------------------------

class TestDiscountRuleBreakdown:

    @pytest.fixture(autouse=True)
    def calc(self):
        c = PricingCalculator()
        c.PRODUCT_RATES = dict(PricingCalculator.PRODUCT_RATES)
        c.PRODUCT_RATES['0001'] = {'individual': 1000.0, 'corporate': 900.0}
        self._calc = c

    def test_no_season_discount_for_winter(self):
        """Rule A: only spring triggers 5%; winter = 0%"""
        result = self._calc.calculate_rule_a_discount('winter')
        try:
            assert result == 0.0
            print(f"\nPASSED: Rule A season discount (winter) = {result}")
        except AssertionError:
            print(f"\nFAILED: Rule A season discount — expected 0.0, got {result}")
            raise

    def test_no_volume_discount_below_100(self):
        """Rule B: volume 90 < 100 means 0% discount"""
        result = self._calc.calculate_rule_b_volume_discount(90)
        try:
            assert result == 0.0
            print(f"\nPASSED: Rule B volume discount (vol=90) = {result}")
        except AssertionError:
            print(f"\nFAILED: Rule B volume discount — expected 0.0, got {result}")
            raise

    def test_strategic_category_discount_is_5_percent(self):
        """Rule C: strategic customer earns 5% discount"""
        result = self._calc.calculate_rule_c_category_discount('strategic')
        try:
            assert result == 5.0
            print(f"\nPASSED: Rule C category discount (strategic) = {result}%")
        except AssertionError:
            print(f"\nFAILED: Rule C category discount — expected 5.0, got {result}")
            raise

    def test_individual_rate_used_not_corporate(self):
        """Rule D: status=individual → individual rate returned as base rate"""
        rate, individual_rate, corporate_rate = self._calc.get_product_rates('0001', 'individual')
        try:
            assert rate == 1000.0
            assert individual_rate == 1000.0
            assert corporate_rate == 0.0
            print(f"\nPASSED: Rule D rates — base={rate}, individual={individual_rate}, corporate={corporate_rate}")
        except AssertionError:
            print(f"\nFAILED: Rule D rates — got base={rate}, individual={individual_rate}, corporate={corporate_rate}")
            raise

    def test_non_emea_region_loading_is_zero(self):
        """Rule E: Non-EMEA means no regional surcharge"""
        result = self._calc.calculate_rule_e_region_loading('NON-EMEA', 85_500.0)
        try:
            assert result == 0.0
            print(f"\nPASSED: Rule E region loading (NON-EMEA) = {result}")
        except AssertionError:
            print(f"\nFAILED: Rule E region loading — expected 0.0, got {result}")
            raise


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
