"""DuckDB database operations"""

import duckdb
from pathlib import Path

from .xbrl_parser import Financials
from .ratios import FinancialRatios


class CreditRiskDB:
    def __init__(self, db_path: str = "data/credit_risk.duckdb"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(db_path)
        self._init_tables()
    
    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                cik VARCHAR PRIMARY KEY,
                name VARCHAR,
                sic VARCHAR,
                sic_description VARCHAR
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS filings (
                cik VARCHAR,
                company VARCHAR,
                accession VARCHAR,
                filing_date DATE,
                fiscal_year_end DATE,
                xbrl_path VARCHAR,
                xbrl_size INTEGER,
                PRIMARY KEY (cik, accession)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS financials (
                cik VARCHAR,
                company VARCHAR,
                period_end DATE,
                revenue BIGINT,
                cost_of_revenue BIGINT,
                gross_profit BIGINT,
                operating_income BIGINT,
                net_income BIGINT,
                total_assets BIGINT,
                current_assets BIGINT,
                total_liabilities BIGINT,
                current_liabilities BIGINT,
                shareholders_equity BIGINT,
                cash BIGINT,
                long_term_debt BIGINT,
                operating_cash_flow BIGINT,
                PRIMARY KEY (cik, period_end)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ratios (
                cik VARCHAR,
                company VARCHAR,
                period_end DATE,
                current_ratio DOUBLE,
                debt_to_equity DOUBLE,
                debt_to_assets DOUBLE,
                gross_margin DOUBLE,
                operating_margin DOUBLE,
                net_margin DOUBLE,
                roe DOUBLE,
                roa DOUBLE,
                ocf_to_debt DOUBLE,
                PRIMARY KEY (cik, period_end)
            )
        """)
    
    def upsert_company(self, cik: str, name: str, sic: str | None = None, sic_desc: str | None = None):
        self.conn.execute(
            "INSERT OR REPLACE INTO companies VALUES (?, ?, ?, ?)",
            [cik, name, sic, sic_desc]
        )
    
    def upsert_filing(self, cik: str, accession: str, filing_date: str, 
                      fiscal_year_end: str | None = None, xbrl_path: str | None = None,
                      company: str | None = None, xbrl_size: int | None = None):
        # Get company name if not provided
        if company is None:
            result = self.conn.execute(f"SELECT name FROM companies WHERE cik = '{cik}'").fetchall()
            company = result[0][0] if result else None
        
        self.conn.execute(
            "INSERT OR REPLACE INTO filings VALUES (?, ?, ?, ?, ?, ?, ?)",
            [cik, company, accession, filing_date, fiscal_year_end, xbrl_path, xbrl_size]
        )
    
    def upsert_financials(self, cik: str, f: Financials, company: str | None = None):
        # Get company name if not provided
        if company is None:
            result = self.conn.execute(f"SELECT name FROM companies WHERE cik = '{cik}'").fetchall()
            company = result[0][0] if result else None
        
        self.conn.execute("""
            INSERT OR REPLACE INTO financials VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            cik, company, f.period_end, f.revenue, f.cost_of_revenue, f.gross_profit,
            f.operating_income, f.net_income, f.total_assets, f.current_assets,
            f.total_liabilities, f.current_liabilities, f.shareholders_equity,
            f.cash, f.long_term_debt, f.operating_cash_flow
        ])
    
    def upsert_ratios(self, cik: str, r: FinancialRatios, company: str | None = None):
        # Get company name if not provided
        if company is None:
            result = self.conn.execute(f"SELECT name FROM companies WHERE cik = '{cik}'").fetchall()
            company = result[0][0] if result else None
        
        self.conn.execute("""
            INSERT OR REPLACE INTO ratios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            cik, company, r.period_end, r.current_ratio, r.debt_to_equity, r.debt_to_assets,
            r.gross_margin, r.operating_margin, r.net_margin, r.roe, r.roa, r.ocf_to_debt
        ])
    
    def get_all_ratios(self, min_date: str | None = None) -> list[dict]:
        query = """
            SELECT c.name as company, r.* 
            FROM ratios r
            JOIN companies c ON r.cik = c.cik
        """
        if min_date:
            query += f" WHERE r.period_end >= '{min_date}'"
        query += " ORDER BY r.period_end DESC"
        return self.conn.execute(query).fetchdf().to_dict('records')
    
    def query(self, sql: str):
        return self.conn.execute(sql).fetchdf()
    
    def close(self):
        self.conn.close()