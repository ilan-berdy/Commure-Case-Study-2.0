"""
Optimization module for RCM staffing levels using linear programming.
"""

from typing import Dict, List
import pulp as pl
import numpy as np
from math import ceil
from . import config as cfg
from . import calculations as calc

class RCMOptimizer:
    """
    Optimizes RCM staffing levels using linear programming to meet SLA and margin targets.
    """
    
    def __init__(self):
        """Initialize the optimizer."""
        self.time_constants = calc.calculate_time_constants()
        self.months = list(range(4))  # 0-3 months
        
        # Pre-calculate monthly volumes
        self.monthly_metrics = []
        for month in self.months:
            accounts = self._get_active_accounts(month)
            claims = calc.calculate_claims_metrics(accounts)
            revenue = calc.calculate_revenue(claims, month)
            
            self.monthly_metrics.append({
                'accounts': accounts,
                'claims': claims,
                'revenue': revenue
            })
    
    def _get_active_accounts(self, month: int) -> int:
        """Get number of active accounts for a given month."""
        if month == 0:
            return 0
        return sum(cfg.ACCOUNTS_PER_MONTH.get(m, 0) for m in range(1, month + 1))
    
    def _optimize_staffing(self, monthly_claims: float) -> Dict[str, int]:
        """Optimize staffing levels using throughput-based calculations."""
        # Calculate daily volumes
        daily_claims = monthly_claims / self.time_constants['days_per_month']
        daily_denials = daily_claims * cfg.CLAIMS_PARAMS['denial_rate']
        daily_denials_rework = daily_denials * cfg.CLAIMS_PARAMS['recovery_rate']
        
        # Calculate required analysts based on throughput
        submission_analysts = ceil(daily_claims / cfg.PROCESS_PARAMS['throughput_submission'])
        denial_analysts = ceil(daily_denials_rework / cfg.PROCESS_PARAMS['throughput_denial'])
        
        # Calculate required managers
        total_analysts = submission_analysts + denial_analysts
        manager_count = ceil(total_analysts / cfg.STAFF_RATIOS['analysts_per_manager'])
        
        # Calculate financials
        total_revenue = monthly_claims * cfg.CLAIMS_PARAMS['average_claim_value'] * cfg.CLAIMS_PARAMS['revenue_percentage']
        total_labor_cost = (
            (submission_analysts + denial_analysts) * cfg.LABOR_COSTS['base_analyst'] *
            self.time_constants['hours_per_day'] * self.time_constants['days_per_month'] +
            manager_count * cfg.LABOR_COSTS['manager'] * self.time_constants['hours_per_day'] * self.time_constants['days_per_month']
        )
        total_costs = (
            total_labor_cost +
            (submission_analysts + denial_analysts) * cfg.OVERHEAD_COSTS['per_analyst'] +
            manager_count * cfg.OVERHEAD_COSTS['per_manager'] +
            cfg.OVERHEAD_COSTS['fixed_monthly']
        )
        
        # Verify margin constraint
        margin = (total_revenue - total_costs) / total_revenue
        if margin < cfg.FINANCIAL_TARGETS['target_gross_margin']:
            # If margin is too low, increase staff to meet the target
            while margin < cfg.FINANCIAL_TARGETS['target_gross_margin']:
                submission_analysts += 1
                denial_analysts += 1
                total_analysts = submission_analysts + denial_analysts
                manager_count = ceil(total_analysts / cfg.STAFF_RATIOS['analysts_per_manager'])
                
                total_labor_cost = (
                    (submission_analysts + denial_analysts) * cfg.LABOR_COSTS['base_analyst'] *
                    self.time_constants['hours_per_day'] * self.time_constants['days_per_month'] +
                    manager_count * cfg.LABOR_COSTS['manager'] * self.time_constants['hours_per_day'] * self.time_constants['days_per_month']
                )
                total_costs = (
                    total_labor_cost +
                    (submission_analysts + denial_analysts) * cfg.OVERHEAD_COSTS['per_analyst'] +
                    manager_count * cfg.OVERHEAD_COSTS['per_manager'] +
                    cfg.OVERHEAD_COSTS['fixed_monthly']
                )
                margin = (total_revenue - total_costs) / total_revenue
        
        return {
            'submission_analysts': submission_analysts,
            'denial_analysts': denial_analysts,
            'managers': manager_count,
            'labor_cost': total_labor_cost,
            'overhead_cost': (
                (submission_analysts + denial_analysts) * cfg.OVERHEAD_COSTS['per_analyst'] +
                manager_count * cfg.OVERHEAD_COSTS['per_manager'] +
                cfg.OVERHEAD_COSTS['fixed_monthly']
            ),
            'revenue': total_revenue,
            'margin': margin
        }
    
    def optimize(self) -> List[Dict]:
        """
        Find optimal staffing levels for all months.
        Returns a list of monthly staffing and financial metrics.
        """
        results = []
        
        # Month 0: Calculate and train staff needed for month 1
        month_1_staff = self._optimize_staffing(
            self.monthly_metrics[1]['claims']['monthly_claims']
        )
        
        # Month 0 results (training)
        results.append({
            'month': 0,
            'active_accounts': 0,
            'submission_analysts': 0,
            'denial_analysts': 0,
            'training_analysts': month_1_staff['submission_analysts'] + month_1_staff['denial_analysts'],
            'managers': month_1_staff['managers'],
            'labor_cost': month_1_staff['labor_cost'],
            'overhead_cost': month_1_staff['overhead_cost'],
            'total_cost': month_1_staff['labor_cost'] + month_1_staff['overhead_cost'],
            'revenue': 0,
            'margin': 0
        })
        
        # Months 1-3: Calculate working staff needed
        for month in range(1, 4):
            metrics = self.monthly_metrics[month]
            staff = self._optimize_staffing(metrics['claims']['monthly_claims'])
            
            results.append({
                'month': month,
                'active_accounts': metrics['accounts'],
                'submission_analysts': staff['submission_analysts'],
                'denial_analysts': staff['denial_analysts'],
                'managers': staff['managers'],
                'labor_cost': staff['labor_cost'],
                'overhead_cost': staff['overhead_cost'],
                'total_cost': staff['labor_cost'] + staff['overhead_cost'],
                'revenue': staff['revenue'],
                'margin': staff['margin']
            })
        
        return results

def print_optimization_results(results: List[Dict]):
    """Print optimization results in a readable format."""
    print("\n=== RCM Staffing Optimization Results ===\n")
    
    for month_results in results:
        print(f"\nMonth {month_results['month']}:")
        print(f"Active Accounts: {month_results['active_accounts']}")
        
        # Calculate workload metrics
        if month_results['month'] > 0:
            accounts = month_results['active_accounts']
            monthly_claims = accounts * cfg.CLAIMS_PARAMS['claims_per_account']
            daily_claims = monthly_claims / cfg.TIME_CONSTANTS['days_per_month']
            daily_denials = daily_claims * cfg.CLAIMS_PARAMS['denial_rate']
            daily_denials_rework = daily_denials * cfg.CLAIMS_PARAMS['recovery_rate']
            
            print("\nWorkload Analysis:")
            print(f"Monthly Claims: {monthly_claims:,.0f}")
            print(f"Daily Claims: {daily_claims:,.0f}")
            print(f"Daily Denials: {daily_denials:,.0f}")
            print(f"Daily Denials to Rework: {daily_denials_rework:,.0f}")
            
            print("\nThroughput Analysis:")
            print("Submission:")
            print(f"  Required Throughput: {daily_claims:,.0f} claims/day")
            print(f"  Analyst Throughput: {cfg.PROCESS_PARAMS['throughput_submission']} claims/day")
            print(f"  Analysts Needed: {month_results['submission_analysts']}")
            
            print("\nDenial:")
            print(f"  Required Throughput: {daily_denials_rework:,.0f} denials/day")
            print(f"  Analyst Throughput: {cfg.PROCESS_PARAMS['throughput_denial']} denials/day")
            print(f"  Analysts Needed: {month_results['denial_analysts']}")
        
        print("\nStaffing Levels:")
        if month_results['month'] == 0:
            print(f"Training Analysts: {month_results['training_analysts']}")
        else:
            print("Working Analysts:")
            print(f"  - Submission: {month_results['submission_analysts']}")
            print(f"  - Denial: {month_results['denial_analysts']}")
        
        print("\nSupport Staff:")
        print(f"  - Managers: {month_results['managers']}")
        
        print("\nFinancial Metrics:")
        print(f"Labor Cost: ${month_results['labor_cost']:,.2f}")
        print(f"Overhead Cost: ${month_results['overhead_cost']:,.2f}")
        print(f"Total Cost: ${month_results['total_cost']:,.2f}")
        print(f"Revenue: ${month_results['revenue']:,.2f}")
        print(f"Gross Margin: {month_results['margin']*100:.1f}%")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    # Create optimizer instance
    optimizer = RCMOptimizer()
    
    # Run optimization
    results = optimizer.optimize()
    
    # Print results
    print_optimization_results(results) 