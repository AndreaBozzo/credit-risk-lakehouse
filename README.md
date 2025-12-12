# Credit Risk Lakehouse

Pipeline for credit risk analysis based on SEC EDGAR public financial data.

## Features

- Automatic 10-K filing download from SEC EDGAR
- XBRL parsing with normalized financial data extraction
- Ratio calculations: current ratio, D/E, ROE, ROA, operating margins
- Local storage in DuckDB (zero infrastructure)
- Ready for scaling on Databricks/Spark

## Quick Start
```bash
# Setup
git clone https://github.com/youruser/credit-risk-lakehouse.git
cd credit-risk-lakehouse
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Download filing (single company)
python scripts/downloads.py --cik 0000320193  # Apple

# Download top 20 US companies
python scripts/downloads.py --all

# Parse and calculate ratios
python scripts/parse.py --all

# Query data
python -c "
import duckdb
conn = duckdb.connect('data/credit_risk.duckdb')
print(conn.execute('''
    SELECT c.name, r.period_end, 
           ROUND(r.roe * 100, 1) as roe_pct,
           ROUND(r.debt_to_equity, 2) as d_e
    FROM ratios r
    JOIN companies c ON r.cik = c.cik
    WHERE r.period_end >= '2024-01-01'
    ORDER BY r.roe DESC
''').fetchdf())
"
```

## Project Structure
```
credit-risk-lakehouse/
├── src/credit_risk/
│   ├── sec_client.py     # SEC EDGAR API client
│   ├── xbrl_parser.py    # XBRL parser
│   ├── ratios.py         # Ratio calculations
│   └── db.py             # DuckDB operations
├── scripts/
│   ├── downloads.py      # Download CLI
│   └── parse.py          # Parsing CLI
├── notebooks/
│   └── 01_exploratory_analysis.ipynb  # Exploratory analysis
├── data/
│   ├── raw/xbrl/         # Raw XBRL filings
│   └── credit_risk.duckdb
└── tests/
```

## Exploratory Analysis

The notebook `notebooks/01_exploratory_analysis.ipynb` contains a complete dataset analysis with:

- **Overview**: 20+ US companies, ~60 financial periods
- **Ratio distributions**: histograms of all financial ratios
- **ROE Ranking**: company ranking by Return on Equity
- **Correlations**: correlation matrix between ratios
- **Leverage vs Profitability**: D/E vs ROE scatter plot
- **Time trends**: average evolution over time
- **Anomalies**: outlier identification (low liquidity, high leverage)
- **Risk Score**: synthetic risk profile 0-100

### Sample Output

#### ROE Ranking by Company
![ROE Ranking](notebooks/fig_roe_ranking.png)

#### Correlation Matrix Between Ratios
![Correlation Matrix](notebooks/fig_correlation.png)

#### Credit Risk Score
![Risk Score](notebooks/fig_risk_score.png)

## Calculated Ratios

| Ratio | Formula | Purpose |
|-------|---------|---------|
| Current Ratio | Current Assets / Current Liabilities | Liquidity |
| Debt to Equity | Total Liabilities / Shareholders Equity | Leverage |
| Debt to Assets | Total Liabilities / Total Assets | Leverage |
| Gross Margin | Gross Profit / Revenue | Profitability |
| Operating Margin | Operating Income / Revenue | Profitability |
| Net Margin | Net Income / Revenue | Profitability |
| ROE | Net Income / Shareholders Equity | Return |
| ROA | Net Income / Total Assets | Efficiency |
| OCF to Debt | Operating Cash Flow / Total Liabilities | Solvency |

## Roadmap

- [ ] Altman Z-Score
- [ ] Piotroski F-Score  
- [ ] Time-series features (CAGR, volatility)
- [ ] ML model for default prediction
- [ ] Export as Databricks Solution Accelerator

## License

MIT