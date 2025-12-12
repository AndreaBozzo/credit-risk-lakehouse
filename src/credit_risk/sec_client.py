"""SEC EDGAR API client"""

import requests
import time
from dataclasses import dataclass


@dataclass
class Filing:
    cik: str
    company: str
    accession: str
    filing_date: str
    fiscal_year_end: str | None = None
    xbrl_content: str | None = None


class SECClient:
    BASE_URL = "https://data.sec.gov"
    ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
    
    def __init__(self, user_agent: str, rate_limit: float = 0.2):
        self.headers = {"User-Agent": user_agent}
        self.rate_limit = rate_limit
    
    def _get(self, url: str) -> requests.Response:
        time.sleep(self.rate_limit)
        return requests.get(url, headers=self.headers)
    
    def get_company_info(self, cik: str) -> dict | None:
        """Get company metadata and filing list"""
        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
        resp = self._get(url)
        return resp.json() if resp.status_code == 200 else None
    
    def get_latest_10k(self, cik: str) -> Filing | None:
        """Find the latest 10-K filing"""
        data = self.get_company_info(cik)
        if not data:
            return None
        
        filings = data["filings"]["recent"]
        for i, form in enumerate(filings["form"]):
            if form == "10-K":
                return Filing(
                    cik=cik,
                    company=data["name"],
                    accession=filings["accessionNumber"][i].replace("-", ""),
                    filing_date=filings["filingDate"][i],
                    fiscal_year_end=filings.get("reportDate", [None] * (i + 1))[i],
                )
        return None
    
    def download_xbrl(self, filing: Filing) -> str | None:
        """Download XBRL instance file"""
        cik_clean = filing.cik.lstrip("0")
        index_url = f"{self.ARCHIVES_URL}/{cik_clean}/{filing.accession}/index.json"
        
        resp = self._get(index_url)
        if resp.status_code != 200:
            return None
        
        for item in resp.json()["directory"]["item"]:
            if item["name"].endswith("_htm.xml"):
                xbrl_url = f"{self.ARCHIVES_URL}/{cik_clean}/{filing.accession}/{item['name']}"
                xbrl_resp = self._get(xbrl_url)
                if xbrl_resp.status_code == 200:
                    return xbrl_resp.text
        return None