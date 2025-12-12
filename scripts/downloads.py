#!/usr/bin/env python
"""CLI per download filing SEC"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from credit_risk.sec_client import SECClient
from credit_risk.db import CreditRiskDB


# Top 50 US companies by market cap
DEFAULT_CIKS = {
    "0000320193": "Apple",
    "0000789019": "Microsoft",
    "0001652044": "Alphabet",
    "0001018724": "Amazon",
    "0001045810": "Nvidia",
    "0001326801": "Meta",
    "0001318605": "Tesla",
    "0000078003": "Pfizer",
    "0000200406": "Johnson & Johnson",
    "0000051143": "IBM",
    "0000093410": "Chevron",
    "0000034088": "Exxon Mobil",
    "0000019617": "JPMorgan Chase",
    "0000070858": "Bank of America",
    "0000104169": "Walmart",
    "0000021344": "Coca-Cola",
    "0000080424": "Procter & Gamble",
    "0000858877": "Cisco",
    "0000012927": "Caterpillar",
    "0000050863": "Intel",
}


def main():
    parser = argparse.ArgumentParser(description="Download SEC 10-K filings")
    parser.add_argument("--cik", type=str, help="Single CIK to download")
    parser.add_argument("--all", action="store_true", help="Download all default companies")
    parser.add_argument("--db", type=str, default="data/credit_risk.duckdb", help="Database path")
    parser.add_argument("--output", type=str, default="data/raw/xbrl", help="XBRL output directory")
    parser.add_argument("--user-agent", type=str, default="CreditRiskLakehouse contact@example.com")
    args = parser.parse_args()
    
    if not args.cik and not args.all:
        parser.error("Specify --cik or --all")
    
    Path(args.output).mkdir(parents=True, exist_ok=True)
    
    client = SECClient(user_agent=args.user_agent)
    db = CreditRiskDB(args.db)
    
    ciks = {args.cik: "Unknown"} if args.cik else DEFAULT_CIKS
    
    success = 0
    for cik, expected_name in ciks.items():
        print(f"Downloading {expected_name}...", end=" ", flush=True)
        
        filing = client.get_latest_10k(cik)
        if not filing:
            print("No 10-K found")
            continue
        
        xbrl = client.download_xbrl(filing)
        if not xbrl:
            print("No XBRL")
            continue
        
        # Save file
        xbrl_path = f"{args.output}/{cik}_{filing.filing_date}.xml"
        with open(xbrl_path, "w") as f:
            f.write(xbrl)
        
        # Save to DB
        db.upsert_company(cik, filing.company)
        db.upsert_filing(cik, filing.accession, filing.filing_date, 
                        filing.fiscal_year_end, xbrl_path)
        
        print(f"✓ {filing.company} ({filing.filing_date})")
        success += 1
    
    db.close()
    print(f"\n✓ {success}/{len(ciks)} filing scaricati")


if __name__ == "__main__":
    main()