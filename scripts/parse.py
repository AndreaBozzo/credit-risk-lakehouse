#!/usr/bin/env python
"""CLI per parsing XBRL e calcolo ratios"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from credit_risk.xbrl_parser import XBRLParser
from credit_risk.ratios import calculate_ratios
from credit_risk.db import CreditRiskDB


def main():
    parser = argparse.ArgumentParser(description="Parse XBRL filings and calculate ratios")
    parser.add_argument("--db", type=str, default="data/credit_risk.duckdb", help="Database path")
    parser.add_argument("--file", type=str, help="Single XBRL file to parse")
    parser.add_argument("--all", action="store_true", help="Parse all files in database")
    args = parser.parse_args()
    
    if not args.file and not args.all:
        parser.error("Specify --file or --all")
    
    db = CreditRiskDB(args.db)
    
    if args.file:
        files = [(None, None, args.file)]
    else:
        files = db.query("SELECT cik, accession, xbrl_path FROM filings WHERE xbrl_path IS NOT NULL").values.tolist()
    
    total_periods = 0
    
    for cik, accession, xbrl_path in files:
        if not Path(xbrl_path).exists():
            print(f"⚠ File not found: {xbrl_path}")
            continue
        
        # Get company name
        if cik:
            result = db.query(f"SELECT name FROM companies WHERE cik = '{cik}'")
            company = result.values[0][0] if len(result) > 0 else "Unknown"
        else:
            company = Path(xbrl_path).stem
            cik = "manual"
        
        print(f"Parsing {company}...", end=" ", flush=True)
        
        try:
            with open(xbrl_path) as f:
                content = f.read()
            
            parser = XBRLParser(content)
            financials_list = parser.parse()
            
            for fin in financials_list:
                db.upsert_financials(cik, fin, company)
                ratios = calculate_ratios(fin)
                db.upsert_ratios(cik, ratios, company)
            
            print(f"✓ {len(financials_list)} periodi")
            total_periods += len(financials_list)
            
        except Exception as e:
            print(f"❌ {e}")
    
    db.close()
    print(f"\n✓ {total_periods} periodi totali elaborati")


if __name__ == "__main__":
    main()