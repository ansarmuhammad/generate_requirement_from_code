"""
Test: Customer D — Product 0003, Spring, Volume 90, EMEA
Customer is marked NON-STRATEGIC + INDIVIDUAL with individual rate 1,000

DataFrame is set directly to avoid pandas reading '0003' as integer
when using load_csv (which calls pd.read_csv without dtype overrides).
"""

import pytest
import pandas as pd
from pricing_calculator import PricingCalculator


@pytest.fixture
def processed_calculator():
    """
    Calculator for Customer D with product 0003 at individual rate 1,000.
    DataFrame is injected directly so '0003' stays a string and the rate
    is respected without touching the shared class-level PRODUCT_RATES.
    """
    calc = PricingCalculator()
    # Register product 0003 on the instance dict so class dict is not mutated
    calc.PRODUCT_RATES = dict(PricingCalculator.PRODUCT_RATES)
    calc.PRODUCT_RATES['0003'] = {'individual': 1000.0, 'corporate': 900.0}

    # Inject pre-normalised DataFrame (mirrors what load_csv would produce)
    calc.df = pd.DataFrame([{
        'Customer': 'non-strategic',  # lowercase — Rule C checks 'strategic' (no match)
        'Product':  '0003',
        'Season':   'spring',
        'Volume':   90,
        'Region':   'EMEA',           # uppercase — Rule E checks 'EMEA' (match → 10% loading)
        'Status':   'individual',
    }])
    calc.process_calculations()
    return calc


# ---------------------------------------------------------------------------
# Core scenario tests
# ---------------------------------------------------------------------------

class TestCustomerDScenario:
    """Customer D: NON-STRATEGIC + INDIVIDUAL, product 0003, spring, vol 90, EMEA"""

    def test_receivable_before_discount(self, processed_calculator):
        """vol 90 × rate 1,000 = 90,000 (before any discount)"""
        result = processed_calculator.df.iloc[0]['Receivable before discount']
        expected = 90_000.0
        try:
            assert result == expected
            print(f"\nPASSED: Receivable before discount = {result}")
        except AssertionError:
            print(f"\nFAILED: Receivable before discount — expected {expected}, got {result}")
            raise

    def test_discount_amount(self, processed_calculator):
        """5% spring discount on 90,000 = 4,500 (no volume or category discount)"""
        result = processed_calculator.df.iloc[0]['Total discounts']
        expected = 4_500.0
        try:
            assert result == expected
            print(f"\nPASSED: Discount amount = {result}")
        except AssertionError:
            print(f"\nFAILED: Discount amount — expected {expected}, got {result}")
            raise

    def test_receivable_after_discount(self, processed_calculator):
        """90,000 − 4,500 spring discount = 85,500"""
        result = processed_calculator.df.iloc[0]['Receivable after discount']
        expected = 85_500.0
        try:
            assert result == expected
            print(f"\nPASSED: Receivable after discount = {result}")
        except AssertionError:
            print(f"\nFAILED: Receivable after discount — expected {expected}, got {result}")
            raise

    def test_total_receivable(self, processed_calculator):
        """85,500 + 10% EMEA loading (8,550) = 94,050"""
        result = processed_calculator.df.iloc[0]['Total receivables']
        expected = 94_050.0
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
        c.PRODUCT_RATES['0003'] = {'individual': 1000.0, 'corporate': 900.0}
        self._calc = c

    def test_spring_season_discount_is_5_percent(self):
        """Rule A: spring triggers 5% discount"""
        result = self._calc.calculate_rule_a_discount('spring')
        try:
            assert result == 5.0
            print(f"\nPASSED: Rule A season discount (spring) = {result}%")
        except AssertionError:
            print(f"\nFAILED: Rule A season discount — expected 5.0, got {result}")
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

    def test_non_strategic_category_discount_is_zero(self):
        """Rule C: non-strategic customer earns 0% discount"""
        result = self._calc.calculate_rule_c_category_discount('non-strategic')
        try:
            assert result == 0.0
            print(f"\nPASSED: Rule C category discount (non-strategic) = {result}%")
        except AssertionError:
            print(f"\nFAILED: Rule C category discount — expected 0.0, got {result}")
            raise

    def test_individual_rate_used_not_corporate(self):
        """Rule D: status=individual → individual rate returned as base rate"""
        rate, individual_rate, corporate_rate = self._calc.get_product_rates('0003', 'individual')
        try:
            assert rate == 1000.0
            assert individual_rate == 1000.0
            assert corporate_rate == 0.0
            print(f"\nPASSED: Rule D rates — base={rate}, individual={individual_rate}, corporate={corporate_rate}")
        except AssertionError:
            print(f"\nFAILED: Rule D rates — got base={rate}, individual={individual_rate}, corporate={corporate_rate}")
            raise

    def test_emea_region_loading_is_ten_percent(self):
        """Rule E: EMEA adds 10% on receivable after discount (85,500 × 10% = 8,550)"""
        result = self._calc.calculate_rule_e_region_loading('EMEA', 85_500.0)
        try:
            assert result == 8_550.0
            print(f"\nPASSED: Rule E region loading (EMEA, base=85,500) = {result}")
        except AssertionError:
            print(f"\nFAILED: Rule E region loading — expected 8,550.0, got {result}")
            raise


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
