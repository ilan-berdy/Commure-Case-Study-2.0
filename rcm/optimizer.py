"""
Optimization module for RCM staffing levels using linear programming.
"""

from typing import Dict, List
import pulp
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
        
        self.model = None
        self.results = []
        self.cohorts = {
            'submission': {},  # Track submission analyst cohorts by month
            'denial': {}       # Track denial analyst cohorts by month
        }
    
    def _get_active_accounts(self, month: int) -> int:
        """Get number of active accounts for a given month."""
        if month == 0:
            return 0
        return sum(cfg.ACCOUNTS_PER_MONTH.get(m, 0) for m in range(1, month + 1))
    
    def _calculate_effective_capacity(self, month: int, process_type: str) -> float:
        """Calculate effective capacity based on cohort productivity."""
        total_capacity = 0
        base_throughput = cfg.PRODUCTIVITY_RAMP_UP[process_type]['base_throughput']
        productivity = cfg.PRODUCTIVITY_RAMP_UP[process_type]['productivity']
        
        # For each cohort that exists in this month
        for cohort_month, count in self.cohorts[process_type].items():
            if cohort_month <= month:  # Only count cohorts that have been hired
                # Calculate months since hire
                months_since_hire = month - cohort_month
                # Get productivity based on months since hire
                if months_since_hire >= 2:
                    # Third month or later: 100% productivity
                    cohort_productivity = productivity[2]
                else:
                    # First or second month: use corresponding productivity
                    cohort_productivity = productivity[months_since_hire]
                # Add to total capacity
                total_capacity += count * cohort_productivity * base_throughput
        
        return total_capacity

    def _calculate_total_active_analysts(self, month: int, process_type: str) -> int:
        """Calculate total active analysts for a given month and process type."""
        return sum(count for cohort_month, count in self.cohorts[process_type].items() 
                  if cohort_month <= month)

    def _calculate_net_new_hires(self, month: int, daily_workload: float, process_type: str) -> int:
        """Calculate net new hires needed to cover capacity gap."""
        # Get monthly workload
        monthly_workload = daily_workload * cfg.TIME_CONSTANTS['days_per_month']
        
        # Calculate current effective capacity
        current_capacity = self._calculate_effective_capacity(month, process_type)
        monthly_capacity = current_capacity * cfg.TIME_CONSTANTS['days_per_month']
        
        # Calculate capacity gap
        capacity_gap = max(0, monthly_workload - monthly_capacity)
        
        if capacity_gap <= 0:
            return 0
        
        # Calculate net new hires needed
        new_cohort_productivity = cfg.PRODUCTIVITY_RAMP_UP[process_type]['productivity'][0]  # 80% for new hires
        base_throughput = cfg.PRODUCTIVITY_RAMP_UP[process_type]['base_throughput']
        monthly_throughput = base_throughput * cfg.TIME_CONSTANTS['days_per_month']
        
        net_new_hires = ceil(capacity_gap / (new_cohort_productivity * monthly_throughput))
        return net_new_hires

    def _optimize_staffing(self, month: int, active_accounts: int) -> Dict:
        """Optimize staffing levels for a given month."""
        # Calculate daily workload
        monthly_claims = active_accounts * cfg.CLAIMS_PARAMS['claims_per_account']
        daily_claims = monthly_claims / cfg.TIME_CONSTANTS['days_per_month']
        daily_denials = daily_claims * cfg.CLAIMS_PARAMS['denial_rate']
        
        # Create optimization model
        self.model = pulp.LpProblem(f"RCM_Staffing_Month_{month}", pulp.LpMinimize)
        
        # Calculate net new hires needed
        new_submission_analysts = self._calculate_net_new_hires(month, daily_claims, 'submission')
        new_denial_analysts = self._calculate_net_new_hires(month, daily_denials, 'denial')
        
        # Decision variables for new hires
        new_submission_var = pulp.LpVariable('new_submission_analysts', lowBound=0, cat='Integer')
        new_denial_var = pulp.LpVariable('new_denial_analysts', lowBound=0, cat='Integer')
        managers = pulp.LpVariable('managers', lowBound=0, cat='Integer')
        
        # Calculate total analysts (existing + new hires)
        total_submission_analysts = self._calculate_total_active_analysts(month, 'submission') + new_submission_var
        total_denial_analysts = self._calculate_total_active_analysts(month, 'denial') + new_denial_var
        
        # Objective: Minimize total cost
        total_cost = (
            total_submission_analysts * cfg.LABOR_COSTS['base_analyst'] * cfg.TIME_CONSTANTS['hours_per_day'] * cfg.TIME_CONSTANTS['days_per_month'] +
            total_denial_analysts * cfg.LABOR_COSTS['base_analyst'] * cfg.TIME_CONSTANTS['hours_per_day'] * cfg.TIME_CONSTANTS['days_per_month'] +
            managers * cfg.LABOR_COSTS['manager'] * cfg.TIME_CONSTANTS['hours_per_day'] * cfg.TIME_CONSTANTS['days_per_month'] +
            (total_submission_analysts + total_denial_analysts) * cfg.OVERHEAD_COSTS['per_analyst'] +
            managers * cfg.OVERHEAD_COSTS['per_manager'] +
            cfg.OVERHEAD_COSTS['fixed_monthly']
        )
        self.model += total_cost
        
        # For Month 0, we're just training for Month 1
        if month == 0:
            next_month_accounts = self._get_active_accounts(1)
            next_month_claims = next_month_accounts * cfg.CLAIMS_PARAMS['claims_per_account']
            next_month_daily_claims = next_month_claims / cfg.TIME_CONSTANTS['days_per_month']
            next_month_daily_denials = next_month_daily_claims * cfg.CLAIMS_PARAMS['denial_rate']
            
            # Set new hires to calculated values
            self.model += new_submission_var == new_submission_analysts
            self.model += new_denial_var == new_denial_analysts
        else:
            # Set new hires to calculated values
            self.model += new_submission_var == new_submission_analysts
            self.model += new_denial_var == new_denial_analysts
        
        # Manager ratio constraint
        self.model += managers >= (total_submission_analysts + total_denial_analysts) / cfg.STAFF_RATIOS['analysts_per_manager'], "Manager_Ratio"
        
        # Solve the model
        self.model.solve(pulp.PULP_CBC_CMD(msg=False))
        
        # Update cohorts for this month
        if month == 0:
            self.cohorts['submission'][0] = int(new_submission_var.value())
            self.cohorts['denial'][0] = int(new_denial_var.value())
        else:
            # Only track new hires for this month
            if int(new_submission_var.value()) > 0:
                self.cohorts['submission'][month] = int(new_submission_var.value())
            if int(new_denial_var.value()) > 0:
                self.cohorts['denial'][month] = int(new_denial_var.value())
        
        # Calculate financial metrics
        labor_cost = (
            total_submission_analysts.value() * cfg.LABOR_COSTS['base_analyst'] * cfg.TIME_CONSTANTS['hours_per_day'] * cfg.TIME_CONSTANTS['days_per_month'] +
            total_denial_analysts.value() * cfg.LABOR_COSTS['base_analyst'] * cfg.TIME_CONSTANTS['hours_per_day'] * cfg.TIME_CONSTANTS['days_per_month'] +
            managers.value() * cfg.LABOR_COSTS['manager'] * cfg.TIME_CONSTANTS['hours_per_day'] * cfg.TIME_CONSTANTS['days_per_month']
        )
        
        overhead_cost = (
            (total_submission_analysts.value() + total_denial_analysts.value()) * cfg.OVERHEAD_COSTS['per_analyst'] +
            managers.value() * cfg.OVERHEAD_COSTS['per_manager'] +
            cfg.OVERHEAD_COSTS['fixed_monthly']
        )
        
        total_cost = labor_cost + overhead_cost
        revenue = monthly_claims * cfg.CLAIMS_PARAMS['average_claim_value'] * cfg.CLAIMS_PARAMS['revenue_percentage']
        gross_margin = (revenue - total_cost) / revenue if revenue > 0 else 0
        
        return {
            'month': month,
            'active_accounts': active_accounts,
            'submission_analysts': int(total_submission_analysts.value()),
            'denial_analysts': int(total_denial_analysts.value()),
            'managers': int(managers.value()),
            'labor_cost': labor_cost,
            'overhead_cost': overhead_cost,
            'total_cost': total_cost,
            'revenue': revenue,
            'gross_margin': gross_margin,
            'cohorts': self.cohorts.copy()  # Include cohort information in results
        }
    
    def optimize(self) -> List[Dict]:
        """Run optimization for all months."""
        results = []
        
        # Month 0: Calculate and train staff needed for month 1
        month_1_staff = self._optimize_staffing(
            0,
            self.monthly_metrics[1]['accounts']
        )
        results.append({
            'month': 0,
            'active_accounts': 0,
            'submission_analysts': month_1_staff['submission_analysts'],
            'denial_analysts': month_1_staff['denial_analysts'],
            'managers': month_1_staff['managers'],
            'labor_cost': month_1_staff['labor_cost'],
            'overhead_cost': month_1_staff['overhead_cost'],
            'total_cost': month_1_staff['total_cost'],
            'revenue': 0,
            'margin': 0,
            'cohorts': month_1_staff['cohorts']
        })
        
        # Months 1-3: Optimize staffing based on workload
        for month in range(1, 4):
            metrics = self.monthly_metrics[month]
            staff = self._optimize_staffing(
                month,
                metrics['accounts']
            )
            
            results.append({
                'month': month,
                'active_accounts': metrics['accounts'],
                'submission_analysts': staff['submission_analysts'],
                'denial_analysts': staff['denial_analysts'],
                'managers': staff['managers'],
                'labor_cost': staff['labor_cost'],
                'overhead_cost': staff['overhead_cost'],
                'total_cost': staff['total_cost'],
                'revenue': staff['revenue'],
                'margin': staff['gross_margin'],
                'cohorts': staff['cohorts']
            })
        
        return results

def print_optimization_results(results: List[Dict]):
    """Print optimization results in a readable format."""
    print("\nRCM Staffing Optimization Results")
    print("=" * 50)
    
    for result in results:
        month = result['month']
        print(f"\nMonth {month}:")
        print(f"Active Accounts: {result['active_accounts']}")
        
        # Print cohort information
        print("\nCohort Analysis:")
        print("Submission Analysts by Cohort:")
        for cohort_month, count in result['cohorts']['submission'].items():
            if month == 0:
                # Month 0 is training, show initial productivity
                print(f"  Month {cohort_month} cohort: {count} analysts (in training)")
                print(f"    Effective daily capacity: 0 claims (training period)")
            else:
                months_since_hire = month - cohort_month
                if months_since_hire >= 0:  # Only show productivity for hired cohorts
                    if months_since_hire >= 2:
                        productivity = cfg.PRODUCTIVITY_RAMP_UP['submission']['productivity'][2]
                    else:
                        productivity = cfg.PRODUCTIVITY_RAMP_UP['submission']['productivity'][months_since_hire]
                    effective_capacity = count * productivity * cfg.PRODUCTIVITY_RAMP_UP['submission']['base_throughput']
                    print(f"  Month {cohort_month} cohort: {count} analysts ({productivity*100:.0f}% productive)")
                    print(f"    Effective daily capacity: {effective_capacity:.1f} claims")
        
        print("\nDenial Analysts by Cohort:")
        for cohort_month, count in result['cohorts']['denial'].items():
            if month == 0:
                # Month 0 is training, show initial productivity
                print(f"  Month {cohort_month} cohort: {count} analysts (in training)")
                print(f"    Effective daily capacity: 0 denials (training period)")
            else:
                months_since_hire = month - cohort_month
                if months_since_hire >= 0:  # Only show productivity for hired cohorts
                    if months_since_hire >= 2:
                        productivity = cfg.PRODUCTIVITY_RAMP_UP['denial']['productivity'][2]
                    else:
                        productivity = cfg.PRODUCTIVITY_RAMP_UP['denial']['productivity'][months_since_hire]
                    effective_capacity = count * productivity * cfg.PRODUCTIVITY_RAMP_UP['denial']['base_throughput']
                    print(f"  Month {cohort_month} cohort: {count} analysts ({productivity*100:.0f}% productive)")
                    print(f"    Effective daily capacity: {effective_capacity:.1f} denials")
        
        print("\nStaffing Levels:")
        print(f"Total Submission Analysts: {result['submission_analysts']}")
        print(f"Total Denial Analysts: {result['denial_analysts']}")
        print(f"Managers: {result['managers']}")
        
        print("\nFinancial Metrics:")
        print(f"Labor Cost: ${result['labor_cost']:,.2f}")
        print(f"Overhead Cost: ${result['overhead_cost']:,.2f}")
        print(f"Total Cost: ${result['total_cost']:,.2f}")
        print(f"Revenue: ${result['revenue']:,.2f}")
        print(f"Gross Margin: {result['margin']*100:.1f}%")
        print("-" * 50)

if __name__ == "__main__":
    # Create optimizer instance
    optimizer = RCMOptimizer()
    
    # Run optimization
    results = optimizer.optimize()
    
    # Print results
    print_optimization_results(results) 