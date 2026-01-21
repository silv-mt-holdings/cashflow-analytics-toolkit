# Cash Flow Analytics Toolkit - AI Coding Guidelines

## Project Overview

**cashflow-analytics-toolkit** is a pure functional library for calculating financial metrics from classified transactions.

**Core Purpose**: Calculate trailing averages, trends, volatility, NSF counts, and balance metrics.

**Architecture Pattern**: **Functional Core** (Pure Functions, No I/O)

---

## Functional Core Principles

### ✅ What This Toolkit SHOULD Do
- Accept transaction lists as input
- Calculate financial metrics (averages, trends, volatility)
- Return structured analytics results
- Provide deterministic calculations

### ❌ What This Toolkit MUST NOT Do
- File I/O operations
- Database connections
- HTTP requests
- State mutations

---

## Architecture

```
cashflow-analytics-toolkit/
├── analytics/
│   ├── cashflow_analyzer.py    # Main analytics engine
│   ├── nsf_analyzer.py          # NSF/overdraft detection
│   └── balance_tracker.py       # Balance calculations
├── models/
│   └── analytics.py             # CashFlowSummary, MetricResult
└── tests/
    └── test_analytics.py
```

---

## Core Metrics

```python
@dataclass(frozen=True)
class CashFlowSummary:
    monthly_true_revenue: Decimal          # 30-day average
    avg_3_month_deposits: Decimal          # 90-day average
    avg_6_month_deposits: Decimal          # 180-day average
    deposit_variance: float                # Coefficient of variation
    trend: str                             # "increasing", "stable", "declining"
    nsf_count_90d: int                     # NSF count (90 days)
    negative_days_90d: int                 # Days with negative balance
    average_daily_balance: Decimal         # ADB
```

---

## Key Functional Patterns

### Trailing Average Calculation

```python
def calculate_trailing_average(
    transactions: List[Transaction],
    days: int = 30
) -> Decimal:
    """
    Calculate trailing average revenue.

    Args:
        transactions: List of classified transactions
        days: Number of days to average (30, 90, 180)

    Returns:
        Average daily revenue for period
    """
    cutoff_date = date.today() - timedelta(days=days)
    revenue_txns = [
        t for t in transactions
        if t.type == TransactionType.TRUE_REVENUE
        and t.date >= cutoff_date
    ]

    total = sum(t.amount for t in revenue_txns)
    return total / days
```

---

## Testing

```python
def test_calculate_variance():
    deposits = [Decimal("10000"), Decimal("12000"), Decimal("9500")]
    variance = calculate_deposit_variance(deposits)
    assert 0.10 < variance < 0.20  # ~15% CV expected

def test_nsf_detection():
    balances = [
        ("2024-01-01", Decimal("-50.00")),
        ("2024-01-02", Decimal("-10.00")),
        ("2024-01-03", Decimal("500.00"))
    ]
    nsf_count = count_nsf_events(balances)
    assert nsf_count == 2
```

---

## Integration with Risk-Model-01

```python
# Risk-Model-01/api.py
from analytics.cashflow_analyzer import CashFlowAnalyzer

analyzer = CashFlowAnalyzer()
cash_flow = analyzer.analyze(classified_transactions)
```

---

## Version

**v1.0** - Functional Core Extraction (January 2026)

**Author**: IntensiveCapFi / Silv MT Holdings
