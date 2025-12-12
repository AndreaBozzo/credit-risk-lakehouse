"""Tests for XBRL parser"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from credit_risk.xbrl_parser import XBRLParser, Financials
from credit_risk.ratios import calculate_ratios, safe_divide


class TestSafeDivide:
    def test_normal(self):
        assert safe_divide(100, 50) == 2.0
    
    def test_zero_denominator(self):
        assert safe_divide(100, 0) is None
    
    def test_none_numerator(self):
        assert safe_divide(None, 50) is None
    
    def test_none_denominator(self):
        assert safe_divide(100, None) is None


class TestFinancials:
    def test_field_count(self):
        f = Financials(period_end="2024-12-31", revenue=1000, net_income=100)
        assert f.field_count() == 2
    
    def test_field_count_empty(self):
        f = Financials(period_end="2024-12-31")
        assert f.field_count() == 0


class TestRatios:
    def test_calculate_ratios(self):
        f = Financials(
            period_end="2024-12-31",
            revenue=1000,
            net_income=100,
            total_assets=500,
            shareholders_equity=200,
            current_assets=150,
            current_liabilities=100,
            total_liabilities=300,
        )
        r = calculate_ratios(f)
        
        assert r.net_margin == 0.1
        assert r.roe == 0.5
        assert r.roa == 0.2
        assert r.current_ratio == 1.5
        assert r.debt_to_equity == 1.5


class TestXBRLParser:
    @pytest.fixture
    def sample_xbrl(self):
        """Load a test XBRL file if it exists"""
        test_file = Path("data/raw/xbrl/0000320193_2025-10-31.xml")  # Apple
        if test_file.exists():
            return test_file.read_text()
        pytest.skip("No test XBRL file available")
    
    def test_parse_apple(self, sample_xbrl):
        parser = XBRLParser(sample_xbrl)
        results = parser.parse()
        
        assert len(results) >= 1
        
        # Verify latest period
        latest = results[0]
        assert latest.revenue is not None
        assert latest.revenue > 0
        assert latest.net_income is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])