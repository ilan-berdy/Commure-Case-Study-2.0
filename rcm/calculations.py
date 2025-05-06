"""
Calculation utilities for RCM staffing optimization.
"""

from typing import Dict
import numpy as np
from . import config as cfg

def calculate_time_constants() -> Dict[str, float]:
    """Calculate time-related constants."""
    return {
        'hours_per_day': cfg.TIME_CONSTANTS['hours_per_day'],
        'minutes_per_hour': cfg.TIME_CONSTANTS['minutes_per_hour'],
        'days_per_month': cfg.TIME_CONSTANTS['days_per_month'],
        'target_utilization': cfg.TIME_CONSTANTS['target_utilization']
    }

def calculate_claims_metrics(accounts: int) -> Dict[str, float]:
    """Calculate claims metrics for a given number of accounts."""
    monthly_claims = accounts * cfg.CLAIMS_PARAMS['claims_per_account']
    monthly_claims_value = monthly_claims * cfg.CLAIMS_PARAMS['average_claim_value']
    
    return {
        'monthly_claims': monthly_claims,
        'monthly_claims_value': monthly_claims_value
    }

def calculate_revenue(claims: Dict[str, float], month: int) -> float:
    """Calculate revenue for a given month's claims."""
    return claims['monthly_claims_value'] * cfg.CLAIMS_PARAMS['revenue_percentage']

def calculate_staffing_metrics(
    submission_analysts: int,
    denial_analysts: int,
    managers: int,
    monthly_claims: float
) -> Dict[str, float]:
    """Calculate staffing metrics for given headcount."""
    # Calculate daily volumes
    daily_claims = monthly_claims / cfg.TIME_CONSTANTS['days_per_month']
    daily_denials = daily_claims * cfg.CLAIMS_PARAMS['denial_rate']
    daily_denials_rework = daily_denials * cfg.CLAIMS_PARAMS['recovery_rate']
    
    # Calculate available minutes
    submission_available = (
        submission_analysts *
        cfg.TIME_CONSTANTS['hours_per_day'] *
        cfg.TIME_CONSTANTS['minutes_per_hour'] *
        cfg.TIME_CONSTANTS['target_utilization'] *
        cfg.TIME_CONSTANTS['days_per_month']
    )
    
    denial_available = (
        denial_analysts *
        cfg.TIME_CONSTANTS['hours_per_day'] *
        cfg.TIME_CONSTANTS['minutes_per_hour'] *
        cfg.TIME_CONSTANTS['target_utilization'] *
        cfg.TIME_CONSTANTS['days_per_month']
    )
    
    # Calculate required minutes
    submission_minutes_per_day = daily_claims * cfg.PROCESS_PARAMS['avg_claim_time_min']
    denial_minutes_per_day = daily_denials_rework * cfg.PROCESS_PARAMS['avg_claim_time_min'] * cfg.PROCESS_PARAMS['denial_time_multiplier']
    
    # Calculate utilization
    submission_utilization = submission_minutes_per_day / submission_available
    denial_utilization = denial_minutes_per_day / denial_available
    
    # Calculate SLA compliance
    submission_sla_days = submission_minutes_per_day / (submission_available / cfg.TIME_CONSTANTS['days_per_month'])
    denial_sla_days = denial_minutes_per_day / (denial_available / cfg.TIME_CONSTANTS['days_per_month'])
    
    return {
        'submission_utilization': submission_utilization,
        'denial_utilization': denial_utilization,
        'submission_sla_days': submission_sla_days,
        'denial_sla_days': denial_sla_days
    }

def calculate_financial_metrics(
    submission_analysts: int,
    denial_analysts: int,
    managers: int,
    monthly_claims: float
) -> Dict[str, float]:
    """Calculate financial metrics for given headcount."""
    # Calculate revenue
    monthly_claims_value = monthly_claims * cfg.CLAIMS_PARAMS['average_claim_value']
    revenue = monthly_claims_value * cfg.CLAIMS_PARAMS['revenue_percentage']
    
    # Calculate labor costs
    analyst_labor_cost = (
        (submission_analysts + denial_analysts) *
        cfg.LABOR_COSTS['base_analyst'] *
        cfg.TIME_CONSTANTS['hours_per_day'] *
        cfg.TIME_CONSTANTS['days_per_month']
    )
    
    manager_labor_cost = (
        managers *
        cfg.LABOR_COSTS['manager'] *
        cfg.TIME_CONSTANTS['hours_per_day'] *
        cfg.TIME_CONSTANTS['days_per_month']
    )
    
    total_labor_cost = analyst_labor_cost + manager_labor_cost
    
    # Calculate overhead costs
    analyst_overhead = (submission_analysts + denial_analysts) * cfg.OVERHEAD_COSTS['per_analyst']
    manager_overhead = managers * cfg.OVERHEAD_COSTS['per_manager']
    total_overhead = analyst_overhead + manager_overhead + cfg.OVERHEAD_COSTS['fixed_monthly']
    
    # Calculate total costs and margin
    total_costs = total_labor_cost + total_overhead
    gross_margin = (revenue - total_costs) / revenue if revenue > 0 else 0
    
    return {
        'revenue': revenue,
        'labor_cost': total_labor_cost,
        'overhead_cost': total_overhead,
        'total_cost': total_costs,
        'gross_margin': gross_margin
    } 