"""Calcolo indici finanziari"""

from dataclasses import dataclass
from .xbrl_parser import Financials


@dataclass
class FinancialRatios:
    period_end: str
    current_ratio: float | None = None
    debt_to_equity: float | None = None
    debt_to_assets: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    roe: float | None = None
    roa: float | None = None
    ocf_to_debt: float | None = None


def safe_divide(numerator: int | None, denominator: int | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def calculate_ratios(f: Financials) -> FinancialRatios:
    """Calcola tutti gli indici da un Financials"""
    return FinancialRatios(
        period_end=f.period_end,
        current_ratio=safe_divide(f.current_assets, f.current_liabilities),
        debt_to_equity=safe_divide(f.total_liabilities, f.shareholders_equity),
        debt_to_assets=safe_divide(f.total_liabilities, f.total_assets),
        gross_margin=safe_divide(f.gross_profit, f.revenue),
        operating_margin=safe_divide(f.operating_income, f.revenue),
        net_margin=safe_divide(f.net_income, f.revenue),
        roe=safe_divide(f.net_income, f.shareholders_equity),
        roa=safe_divide(f.net_income, f.total_assets),
        ocf_to_debt=safe_divide(f.operating_cash_flow, f.total_liabilities),
    )