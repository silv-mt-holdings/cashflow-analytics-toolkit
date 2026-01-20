"""
Bank Cash Flow Analyzer

Comprehensive cash flow analysis from bank statements:
- Trailing averages (3/6/12 month)
- Deposit categorization
- Monthly trends and volatility
- Average daily balance
- Negative day analysis
- Red flag detection

Author: IntensiveCapFi / Silv MT Holdings
Version: 2.0 (MCA-Risk-Model)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional

# Import shared models
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.analytics import MonthlyData, CashFlowSummary, BalanceMetrics


class BankCashFlowAnalyzer:
    """
    Comprehensive bank cash flow analyzer.

    Features:
    - Monthly aggregation
    - Trailing averages (3/6/12 month)
    - Trend analysis
    - Deposit categorization
    - NSF/overdraft detection
    - Balance tracking
    - Red flag generation
    """

    def __init__(self):
        """Initialize analyzer"""
        self.transactions = []
        self.monthly_data: Dict[str, MonthlyData] = {}
        self.daily_balances = []
        self.analysis = {}

    def load_transactions(self, transactions: List) -> 'BankCashFlowAnalyzer':
        """
        Load transaction data (from bank_parser output or manual).

        Args:
            transactions: List of Transaction objects or dicts

        Returns:
            Self for chaining
        """
        self.transactions = transactions
        self._process_transactions()
        return self

    def add_monthly_summary(self, month: int, year: int,
                           beginning_balance: float, ending_balance: float,
                           total_deposits: float, total_withdrawals: float,
                           deposit_count: int = 0) -> 'BankCashFlowAnalyzer':
        """
        Add monthly summary data manually.

        Args:
            month: Month (1-12)
            year: Year
            beginning_balance: Starting balance
            ending_balance: Ending balance
            total_deposits: Total deposits
            total_withdrawals: Total withdrawals
            deposit_count: Number of deposits

        Returns:
            Self for chaining
        """
        key = f"{year}-{month:02d}"
        self.monthly_data[key] = MonthlyData(
            period=key,
            year=year,
            month=month,
            beginning_balance=beginning_balance,
            ending_balance=ending_balance,
            total_deposits=total_deposits,
            total_withdrawals=total_withdrawals,
            deposit_count=deposit_count,
            net_cash_flow=total_deposits - total_withdrawals,
            average_balance=(beginning_balance + ending_balance) / 2
        )
        return self

    def _process_transactions(self):
        """Process transactions into monthly buckets"""
        monthly = defaultdict(lambda: {
            'deposits': [],
            'withdrawals': [],
            'all_transactions': []
        })

        for txn in self.transactions:
            # Get date
            if hasattr(txn, 'date'):
                txn_date = txn.date
            elif isinstance(txn, dict):
                date_str = txn.get('date', '')
                txn_date = self._parse_date(date_str)
            else:
                continue

            if not txn_date:
                continue

            # Get amount
            if hasattr(txn, 'amount'):
                amount = txn.amount
            else:
                amount = txn.get('amount', 0)

            # Month key
            month_key = f"{txn_date.year}-{txn_date.month:02d}"

            monthly[month_key]['all_transactions'].append(txn)

            if amount > 0:
                monthly[month_key]['deposits'].append(abs(amount))
            else:
                monthly[month_key]['withdrawals'].append(abs(amount))

        # Aggregate monthly
        for month_key, data in monthly.items():
            year, month = month_key.split('-')
            self.monthly_data[month_key] = MonthlyData(
                period=month_key,
                year=int(year),
                month=int(month),
                total_deposits=sum(data['deposits']),
                total_withdrawals=sum(data['withdrawals']),
                deposit_count=len(data['deposits']),
                withdrawal_count=len(data['withdrawals']),
                net_cash_flow=sum(data['deposits']) - sum(data['withdrawals']),
                avg_deposit=np.mean(data['deposits']) if data['deposits'] else 0,
                max_deposit=max(data['deposits']) if data['deposits'] else 0,
                min_deposit=min(data['deposits']) if data['deposits'] else 0
            )

    def _parse_date(self, date_str: str):
        """Parse date string"""
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            try:
                return datetime.strptime(date_str, '%m/%d/%Y').date()
            except:
                return None

    def calculate_trailing_averages(self) -> Dict:
        """
        Calculate trailing averages (3/6/12 month).

        Returns:
            Dict with trailing average data
        """
        if not self.monthly_data:
            return {}

        # Sort months
        sorted_months = sorted(self.monthly_data.keys(), reverse=True)

        # Calculate averages
        deposits_3mo = []
        deposits_6mo = []
        deposits_12mo = []

        for i, month_key in enumerate(sorted_months):
            month_data = self.monthly_data[month_key]

            if i < 3:
                deposits_3mo.append(month_data.total_deposits)
            if i < 6:
                deposits_6mo.append(month_data.total_deposits)
            if i < 12:
                deposits_12mo.append(month_data.total_deposits)

        result = {
            'months_available': len(sorted_months),
            'trend': 'stable'
        }

        if deposits_3mo:
            avg_3mo = np.mean(deposits_3mo)
            result['avg_3_month_deposits'] = avg_3mo
            result['3_month'] = {'avg_deposits': avg_3mo, 'months': len(deposits_3mo)}

        if deposits_6mo:
            avg_6mo = np.mean(deposits_6mo)
            result['avg_6_month_deposits'] = avg_6mo
            result['6_month'] = {'avg_deposits': avg_6mo, 'months': len(deposits_6mo)}

        if deposits_12mo:
            avg_12mo = np.mean(deposits_12mo)
            result['avg_12_month_deposits'] = avg_12mo
            result['12_month'] = {'avg_deposits': avg_12mo, 'months': len(deposits_12mo)}
            result['annualized_deposits'] = avg_12mo * 12

        # Determine trend
        if len(deposits_3mo) >= 3:
            if deposits_3mo[0] > deposits_3mo[-1] * 1.1:
                result['trend'] = 'increasing'
            elif deposits_3mo[0] < deposits_3mo[-1] * 0.9:
                result['trend'] = 'decreasing'

        self.analysis['trailing_averages'] = result
        return result

    def calculate_monthly_trends(self) -> Dict:
        """
        Calculate month-over-month trends and volatility.

        Returns:
            Dict with trend data
        """
        if len(self.monthly_data) < 2:
            return {}

        sorted_months = sorted(self.monthly_data.keys())
        deposits = [self.monthly_data[m].total_deposits for m in sorted_months]

        # MoM changes
        mom_changes = []
        for i in range(1, len(deposits)):
            if deposits[i-1] > 0:
                change_pct = ((deposits[i] - deposits[i-1]) / deposits[i-1]) * 100
                mom_changes.append(change_pct)

        # Volatility (coefficient of variation)
        mean_deposits = np.mean(deposits)
        std_deposits = np.std(deposits)
        cv = (std_deposits / mean_deposits * 100) if mean_deposits > 0 else 0

        # Trend direction
        if mom_changes:
            avg_change = np.mean(mom_changes)
            if avg_change > 5:
                trend = 'increasing'
            elif avg_change < -5:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'stable'

        result = {
            'trend_direction': trend,
            'avg_mom_change': np.mean(mom_changes) if mom_changes else 0,
            'volatility_cv': cv,
            'high_volatility': cv > 30,
            'mom_changes': mom_changes
        }

        self.analysis['monthly_trends'] = result
        return result

    def categorize_deposits(self) -> Dict:
        """
        Categorize deposits by type (ACH, wire, cash, card).

        Returns:
            Dict with deposit categories
        """
        categories = {
            'ach': {'total': 0, 'count': 0, 'pct_of_total': 0},
            'wire': {'total': 0, 'count': 0, 'pct_of_total': 0},
            'cash': {'total': 0, 'count': 0, 'pct_of_total': 0},
            'card': {'total': 0, 'count': 0, 'pct_of_total': 0},
            'other': {'total': 0, 'count': 0, 'pct_of_total': 0},
            'total_categorized': 0
        }

        for txn in self.transactions:
            if hasattr(txn, 'amount'):
                amount = txn.amount
                desc = txn.description.upper() if hasattr(txn, 'description') else ''
            else:
                amount = txn.get('amount', 0)
                desc = str(txn.get('description', '')).upper()

            if amount <= 0:
                continue

            # Categorize
            if 'WIRE' in desc or 'ORIG:' in desc:
                cat = 'wire'
            elif 'ACH' in desc:
                cat = 'ach'
            elif 'CASH' in desc or 'ATM' in desc:
                cat = 'cash'
            elif 'CARD' in desc or 'MERCHANT' in desc:
                cat = 'card'
            else:
                cat = 'other'

            categories[cat]['total'] += amount
            categories[cat]['count'] += 1
            categories['total_categorized'] += amount

        # Calculate percentages
        total = categories['total_categorized']
        if total > 0:
            for cat in ['ach', 'wire', 'cash', 'card', 'other']:
                categories[cat]['pct_of_total'] = (categories[cat]['total'] / total) * 100

        self.analysis['deposit_categories'] = categories
        return categories

    def analyze_large_deposits(self) -> Dict:
        """
        Analyze large deposits (outliers).

        Returns:
            Dict with large deposit analysis
        """
        deposits = [t.amount if hasattr(t, 'amount') else t.get('amount', 0)
                   for t in self.transactions
                   if (hasattr(t, 'amount') and t.amount > 0) or
                      (isinstance(t, dict) and t.get('amount', 0) > 0)]

        if not deposits:
            return {}

        mean_deposit = np.mean(deposits)
        std_deposit = np.std(deposits)
        threshold = mean_deposit + (2 * std_deposit)  # 2 std devs

        large_deposits = [d for d in deposits if d > threshold]
        total_large = sum(large_deposits)
        total_deposits = sum(deposits)

        result = {
            'threshold': threshold,
            'count': len(large_deposits),
            'total': total_large,
            'pct_from_large': (total_large / total_deposits * 100) if total_deposits > 0 else 0,
            'largest': max(deposits) if deposits else 0,
            'mean': mean_deposit,
            'std': std_deposit
        }

        self.analysis['large_deposits'] = result
        return result

    def analyze_balance_trends(self) -> Dict:
        """
        Analyze balance trends over time.

        Returns:
            Dict with balance trend data
        """
        if not self.monthly_data:
            return {}

        sorted_months = sorted(self.monthly_data.keys())
        balances = []

        for month_key in sorted_months:
            month_data = self.monthly_data[month_key]
            if month_data.ending_balance > 0:
                balances.append(month_data.ending_balance)

        if not balances:
            return {}

        first_balance = balances[0]
        last_balance = balances[-1]
        balance_change = last_balance - first_balance
        balance_change_pct = (balance_change / first_balance * 100) if first_balance > 0 else 0

        # Trend
        if balance_change_pct > 10:
            trend = 'increasing'
        elif balance_change_pct < -10:
            trend = 'decreasing'
        else:
            trend = 'stable'

        result = {
            'average_balance': np.mean(balances),
            'min_balance': min(balances),
            'max_balance': max(balances),
            'balance_change': balance_change,
            'balance_change_pct': balance_change_pct,
            'balance_trend': trend
        }

        self.analysis['balance_trends'] = result
        return result

    def check_nsf_overdraft(self) -> Dict:
        """
        Check for NSF fees and overdrafts.

        Returns:
            Dict with NSF/overdraft data
        """
        nsf_keywords = ['NSF', 'INSUFFICIENT', 'OVERDRAFT', 'OD FEE', 'RETURNED ITEM']

        nsf_count = 0
        nsf_total = 0.0

        for txn in self.transactions:
            if hasattr(txn, 'description'):
                desc = txn.description.upper()
                amount = txn.amount
            else:
                desc = str(txn.get('description', '')).upper()
                amount = txn.get('amount', 0)

            for keyword in nsf_keywords:
                if keyword in desc:
                    nsf_count += 1
                    nsf_total += abs(amount)
                    break

        # Severity
        if nsf_count > 5:
            severity = 'HIGH'
        elif nsf_count > 0:
            severity = 'MODERATE'
        else:
            severity = 'NONE'

        result = {
            'nsf_count': nsf_count,
            'nsf_total_fees': nsf_total,
            'severity': severity
        }

        self.analysis['nsf_overdraft'] = result
        return result

    def calculate_average_daily_balance(self) -> Dict:
        """
        Calculate average daily balance.

        Returns:
            Dict with ADB data
        """
        if not self.monthly_data:
            return {}

        # Use monthly averages as proxy
        sorted_months = sorted(self.monthly_data.keys())
        monthly_avgs = []

        for month_key in sorted_months:
            month_data = self.monthly_data[month_key]
            if month_data.average_balance > 0:
                monthly_avgs.append(month_data.average_balance)

        if not monthly_avgs:
            return {}

        adb = np.mean(monthly_avgs)

        result = {
            'average_daily_balance': adb,
            'months_included': len(monthly_avgs)
        }

        self.analysis['average_daily_balance'] = result
        return result

    def generate_underwriting_summary(self) -> Dict:
        """
        Generate comprehensive underwriting summary with red flags.

        Returns:
            Dict with complete summary and flags
        """
        # Run all analyses
        self.calculate_trailing_averages()
        self.calculate_monthly_trends()
        self.categorize_deposits()
        self.analyze_large_deposits()
        self.analyze_balance_trends()
        self.check_nsf_overdraft()
        self.calculate_average_daily_balance()

        # Compile flags
        flags = []
        red_flags = []

        # NSF flags
        nsf = self.analysis.get('nsf_overdraft', {})
        if nsf.get('nsf_count', 0) > 5:
            red_flags.append(f"High NSF activity: {nsf['nsf_count']} items")
        elif nsf.get('nsf_count', 0) > 0:
            flags.append(f"NSF activity present: {nsf['nsf_count']} items")

        # Trend flags
        trends = self.analysis.get('monthly_trends', {})
        if trends.get('trend_direction') == 'decreasing':
            flags.append('Declining deposit trend')
        if trends.get('high_volatility'):
            flags.append(f"High deposit volatility (CV: {trends.get('volatility_cv', 0):.1f}%)")

        # Large deposit flags
        large = self.analysis.get('large_deposits', {})
        if large.get('pct_from_large', 0) > 30:
            flags.append(f"High concentration in large deposits ({large.get('pct_from_large', 0):.1f}%)")

        # Balance trend flags
        bal = self.analysis.get('balance_trends', {})
        if bal.get('balance_change_pct', 0) < -20:
            flags.append(f"Declining balance trend ({bal.get('balance_change_pct', 0):.1f}%)")

        summary = {
            'trailing_averages': self.analysis.get('trailing_averages', {}),
            'monthly_trends': self.analysis.get('monthly_trends', {}),
            'deposit_categories': self.analysis.get('deposit_categories', {}),
            'large_deposits': self.analysis.get('large_deposits', {}),
            'balance_trends': self.analysis.get('balance_trends', {}),
            'nsf_overdraft': self.analysis.get('nsf_overdraft', {}),
            'average_daily_balance': self.analysis.get('average_daily_balance', {}),
            'red_flags': red_flags,
            'warnings': flags,
            'flag_count': len(flags) + len(red_flags)
        }

        return summary

    def to_cash_flow_summary(self) -> CashFlowSummary:
        """
        Convert analysis to CashFlowSummary model.

        Returns:
            CashFlowSummary object
        """
        summary = self.generate_underwriting_summary()

        trailing = summary.get('trailing_averages', {})
        nsf = summary.get('nsf_overdraft', {})
        adb_data = summary.get('average_daily_balance', {})

        return CashFlowSummary(
            monthly_true_revenue=trailing.get('avg_3_month_deposits', 0),
            average_daily_balance=adb_data.get('average_daily_balance', 0),
            nsf_count=nsf.get('nsf_count', 0),
            trailing_3mo_avg=trailing.get('avg_3_month_deposits'),
            trailing_6mo_avg=trailing.get('avg_6_month_deposits'),
            trailing_12mo_avg=trailing.get('avg_12_month_deposits'),
            trend=trailing.get('trend', 'stable'),
            red_flags=summary.get('red_flags', []),
            warnings=summary.get('warnings', [])
        )


if __name__ == '__main__':
    print("\nBank Cash Flow Analyzer v2.0")
    print("Part of MCA-Risk-Model library\n")
    print("Usage:")
    print("  from analytics.cashflow_analyzer import BankCashFlowAnalyzer")
    print("  analyzer = BankCashFlowAnalyzer()")
    print("  analyzer.add_monthly_summary(month=12, year=2025, ...)")
    print("  summary = analyzer.generate_underwriting_summary()")
