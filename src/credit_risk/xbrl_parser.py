"""Parser XBRL per estrazione dati finanziari"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass


XBRLI = "http://www.xbrl.org/2003/instance"
XBRLDI = "http://xbrl.org/2006/xbrldi"

CONCEPT_MAPPING = {
    # Revenue variants
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "Revenues": "revenue",
    "SalesRevenueNet": "revenue",
    # Costs
    "CostOfGoodsAndServicesSold": "cost_of_revenue",
    "CostOfRevenue": "cost_of_revenue",
    # Profits
    "GrossProfit": "gross_profit",
    "OperatingIncomeLoss": "operating_income",
    "NetIncomeLoss": "net_income",
    # Assets
    "Assets": "total_assets",
    "AssetsCurrent": "current_assets",
    "CashAndCashEquivalentsAtCarryingValue": "cash",
    # Liabilities
    "Liabilities": "total_liabilities",
    "LiabilitiesCurrent": "current_liabilities",
    "LongTermDebt": "long_term_debt",
    "LongTermDebtNoncurrent": "long_term_debt",
    # Equity
    "StockholdersEquity": "shareholders_equity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": "shareholders_equity",
    # Cash flow
    "NetCashProvidedByUsedInOperatingActivities": "operating_cash_flow",
}


@dataclass
class Financials:
    period_end: str
    revenue: int | None = None
    cost_of_revenue: int | None = None
    gross_profit: int | None = None
    operating_income: int | None = None
    net_income: int | None = None
    total_assets: int | None = None
    current_assets: int | None = None
    total_liabilities: int | None = None
    current_liabilities: int | None = None
    shareholders_equity: int | None = None
    cash: int | None = None
    long_term_debt: int | None = None
    operating_cash_flow: int | None = None
    
    def field_count(self) -> int:
        return sum(1 for f in self.__dataclass_fields__ if f != "period_end" and getattr(self, f) is not None)


class XBRLParser:
    def __init__(self, xbrl_content: str):
        self.root = ET.fromstring(xbrl_content)
        self.contexts = self._parse_contexts()
    
    def _parse_contexts(self) -> dict:
        """Estrae context senza dimensioni"""
        contexts = {}
        for ctx in self.root.findall(f".//{{{XBRLI}}}context"):
            ctx_id = ctx.attrib.get("id")
            
            # Salta context con dimensioni
            if ctx.find(f".//{{{XBRLDI}}}explicitMember") is not None:
                continue
            
            period = ctx.find(f"{{{XBRLI}}}period")
            if period is None:
                continue
            
            instant = period.find(f"{{{XBRLI}}}instant")
            start = period.find(f"{{{XBRLI}}}startDate")
            end = period.find(f"{{{XBRLI}}}endDate")
            
            if instant is not None:
                contexts[ctx_id] = {"type": "instant", "date": instant.text}
            elif start is not None and end is not None:
                contexts[ctx_id] = {"type": "duration", "start": start.text, "end": end.text}
        
        return contexts
    
    def parse(self) -> list[Financials]:
        """Estrae tutti i periodi finanziari"""
        data_by_period: dict[str, dict] = {}
        
        for elem in self.root.iter():
            if "}" not in elem.tag:
                continue
            
            tag_name = elem.tag.split("}")[-1]
            if tag_name not in CONCEPT_MAPPING:
                continue
            
            ctx_id = elem.attrib.get("contextRef")
            if ctx_id not in self.contexts:
                continue
            
            value = elem.text
            if not value:
                continue
            
            try:
                numeric_value = int(float(value))
            except ValueError:
                continue
            
            concept = CONCEPT_MAPPING[tag_name]
            ctx_info = self.contexts[ctx_id]
            period_key = ctx_info["date"] if ctx_info["type"] == "instant" else ctx_info["end"]
            
            if period_key not in data_by_period:
                data_by_period[period_key] = {}
            
            if concept not in data_by_period[period_key]:
                data_by_period[period_key][concept] = numeric_value
        
        # Converti in Financials objects
        results = []
        for period, data in data_by_period.items():
            f = Financials(period_end=period, **data)
            if f.field_count() >= 3:  # Almeno 3 campi popolati
                results.append(f)
        
        return sorted(results, key=lambda x: x.period_end, reverse=True)