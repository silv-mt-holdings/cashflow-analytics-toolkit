# cashflow-analytics-toolkit

Cash flow analytics toolkit - Analyzes trends, volatility, NSF, ADB, and banking behavior metrics.

## Features

- Trailing averages (3/6/12 month rolling)
- Deposit trend analysis (increasing/stable/declining)
- Volatility metrics (coefficient of variation)
- NSF/overdraft detection
- Negative day analysis
- Average daily balance calculation
- Cash flow margin (CFCR) calculation
- Red flag generation

## Installation

```bash
pip install git+https://github.com/silv-mt-holdings/cashflow-analytics-toolkit.git
```

## Quick Start

```python
from analytics.cashflow_analyzer import BankCashFlowAnalyzer

analyzer = BankCashFlowAnalyzer()
analyzer.load_transactions(classified_transactions)
summary = analyzer.analyze()

print(f"Monthly Revenue: ${summary.monthly_true_revenue:,.2f}")
print(f"3-Month Avg: ${summary.avg_3_month_deposits:,.2f}")
print(f"Trend: {summary.trend_direction}")
print(f"Volatility: {summary.volatility_cv:.2%}")
```

## Dependencies

- transaction-classifier-toolkit
- pandas>=1.5.0
- numpy>=1.24.0
