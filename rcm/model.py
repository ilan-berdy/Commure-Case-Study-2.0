"""
RCM Capacity Planning Model.
"""

from typing import Dict, List
import pandas as pd
from . import calculations as calc
from . import config as cfg

class RCMModel:
    """RCM Capacity Planning Model."""
    
    def __init__(self):
        """Initialize the model."""
        self.time_constants = calc.calculate_time_constants()
    
    def calculate_monthly_metrics(self, month: int) -> Dict:
        """Calculate metrics for a given month."""
        # Get active accounts
        active_accounts = sum(cfg.ACCOUNTS_PER_MONTH.get(m, 0) for m in range(1, month + 1))
        
        # Calculate claims metrics
        claims_metrics = calc.calculate_claims_metrics(active_accounts)
        
        # Calculate revenue
        revenue = calc.calculate_revenue(claims_metrics, month)
        
        # Calculate staffing metrics
        staffing_metrics = calc.calculate_staffing_metrics(
            submission_analysts=1,  # Start with minimum
            denial_analysts=1,     # Start with minimum
            managers=1,            # Start with minimum
            monthly_claims=claims_metrics['monthly_claims']
        )
        
        # Calculate financial metrics
        financial_metrics = calc.calculate_financial_metrics(
            submission_analysts=1,  # Start with minimum
            denial_analysts=1,     # Start with minimum
            managers=1,            # Start with minimum
            monthly_claims=claims_metrics['monthly_claims']
        )
        
        return {
            'month': month,
            'active_accounts': active_accounts,
            'monthly_claims': claims_metrics['monthly_claims'],
            'monthly_claims_value': claims_metrics['monthly_claims_value'],
            'revenue': revenue,
            'submission_analysts': 1,  # Start with minimum
            'denial_analysts': 1,     # Start with minimum
            'managers': 1,            # Start with minimum
            'trainers': 1,           # Start with minimum
            'qa_staff': 1,           # Start with minimum
            'submission_utilization': staffing_metrics['submission_utilization'],
            'denial_utilization': staffing_metrics['denial_utilization'],
            'submission_sla_days': staffing_metrics['submission_sla_days'],
            'denial_sla_days': staffing_metrics['denial_sla_days'],
            'labor_cost': financial_metrics['labor_cost'],
            'overhead_cost': financial_metrics['overhead_cost'],
            'total_cost': financial_metrics['total_cost'],
            'gross_margin': financial_metrics['gross_margin']
        }
    
    def generate_report(self) -> pd.DataFrame:
        """Generate a detailed report of monthly metrics."""
        data = [self.calculate_monthly_metrics(month) for month in range(0, 4)]
        return pd.DataFrame(data)
    
    def print_detailed_report(self):
        """Print a detailed report of monthly metrics."""
        df = self.generate_report()
        
        print("\n=== RCM Capacity Planning Model Results ===\n")
        
        for month in range(4):
            print(f"\nMonth {month} Details:")
            print("="*50)
            
            print("\nAccount & Claims Metrics:")
            print(f"Active Accounts: {df['active_accounts'].iloc[month]:,}")
            print(f"Monthly Claims: {df['monthly_claims'].iloc[month]:,.1f}")
            print(f"Claims Value: ${df['monthly_claims_value'].iloc[month]:,.2f}")
            
            print("\nStaffing Levels:")
            print(f"Submission Analysts: {df['submission_analysts'].iloc[month]:,}")
            print(f"Denial Analysts: {df['denial_analysts'].iloc[month]:,}")
            print(f"Total Analysts: {df['submission_analysts'].iloc[month] + df['denial_analysts'].iloc[month]:,}")
            print(f"Managers: {df['managers'].iloc[month]:,}")
            print(f"Trainers: {df['trainers'].iloc[month]:,}")
            print(f"QA Staff: {df['qa_staff'].iloc[month]:,}")
            
            print("\nUtilization Metrics:")
            print(f"Submission Utilization: {df['submission_utilization'].iloc[month]*100:.1f}%")
            print(f"Denial Utilization: {df['denial_utilization'].iloc[month]*100:.1f}%")
            
            print("\nSLA Metrics:")
            print(f"Submission Days Needed: {df['submission_sla_days'].iloc[month]:.1f}")
            print(f"Denial Days Needed: {df['denial_sla_days'].iloc[month]:.1f}")
            print(f"Submission SLA Met: {'Yes' if df['submission_sla_days'].iloc[month] <= 5 else 'No'}")
            print(f"Denial SLA Met: {'Yes' if df['denial_sla_days'].iloc[month] <= 3 else 'No'}")
            
            print("\nFinancial Metrics:")
            print(f"Revenue: ${df['revenue'].iloc[month]:,.2f}")
            print(f"Labor Cost: ${df['labor_cost'].iloc[month]:,.2f}")
            print(f"Overhead Cost: ${df['overhead_cost'].iloc[month]:,.2f}")
            print(f"Total Cost: ${df['total_cost'].iloc[month]:,.2f}")
            print(f"Gross Margin: {df['gross_margin'].iloc[month]*100:.1f}%")
            
            print("\n" + "="*50)
        
        # Save results to CSV
        df.to_csv('results/rcm_model_results.csv', index=False)
        print("\nResults saved to results/rcm_model_results.csv")

if __name__ == "__main__":
    # Create model instance
    model = RCMModel()
    
    # Generate and display report
    model.print_detailed_report() 