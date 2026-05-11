"""
Test: Customer B — Product 0002, Winter, Volume 900, Non-EMEA
Customer is marked STRATEGIC + INDIVIDUAL with individual rate 1,000

Volume 900 falls in the 5% volume-discount band (≥100 < 1000).
All discounts applied on the original receivable before discount:
  1. Season (winter): 0%  → 0
  2. Volume (900):    5%  → 900,000 × 5% = 45,000
  3. Category:        5%  → 900,000 × 5% = 45,000
  Total discounts: 90,000  |  Receivable after discount: 810,000

DataFrame is injected directly so '0002' stays a string.
"""

import pytest
import pandas as pd
from pricing_calculator import PricingCalculator


@pytest.fixture
def processed_calculator():
    """
    Calculator for Customer B with product 0002 at individual rate 1,000.
    DataFrame is injected directly so '0002' stays a string and the rate
    is respected without touching the shared class-level PRODUCT_RATES.
    """
    calc = PricingCalculator()
    calc.PRODUCT_RATES = dict(PricingCalculator.PRODUCT_RATES)
    calc.PRODUCT_RATES['0002'] = {'individual': 1000.0, 'corporate': 900.0}

    calc.df = pd.DataFrame([{
        'Customer': 'strategic',
        'Product':  '0002',
        'Season':   'winter',
        'Volume':   900,
        'Region':   'NON-EMEA',
        'Status':   'individual',
    }])
    calc.process_calculations()
    return calc


# ---------------------------------------------------------------------------
# Core scenario test
# ---------------------------------------------------------------------------

class TestCustomerBScenario:
    """Customer B: STRATEGIC + INDIVIDUAL, product 0002, winter, vol 900, Non-EMEA"""

    def test_total_receivable(self, processed_calculator):
        """vol 900 × rate 1,000 = 900,000 → 5% vol + 5% strategic on original → 810,000"""
        result = processed_calculator.df.iloc[0]['Total receivables']
        expected = 810_000.0
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
        c.PRODUCT_RATES['0002'] = {'individual': 1000.0, 'corporate': 900.0}
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

    def test_volume_discount_5_percent_for_900(self):
        """Rule B: volume 900 is ≥100 and <1000 → 5% discount"""
        result = self._calc.calculate_rule_b_volume_discount(900)
        try:
            assert result == 5.0
            print(f"\nPASSED: Rule B volume discount (vol=900) = {result}%")
        except AssertionError:
            print(f"\nFAILED: Rule B volume discount — expected 5.0, got {result}")
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
        """Rule D: status=individual → individual rate 1,000 returned as base rate"""
        rate, individual_rate, corporate_rate = self._calc.get_product_rates('0002', 'individual')
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
        result = self._calc.calculate_rule_e_region_loading('NON-EMEA', 810_000.0)
        try:
            assert result == 0.0
            print(f"\nPASSED: Rule E region loading (NON-EMEA) = {result}")
        except AssertionError:
            print(f"\nFAILED: Rule E region loading — expected 0.0, got {result}")
            raise


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
