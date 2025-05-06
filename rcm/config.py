"""
Configuration parameters for RCM staffing optimization.
"""

# Account growth parameters
ACCOUNTS_PER_MONTH = {
    1: 10,  # Month 1: 10 accounts
    2: 30,  # Month 2: +30 accounts (40 total)
    3: 60   # Month 3: +60 accounts (100 total)
}

# Claims parameters
CLAIMS_PARAMS = {
    'claims_per_account': 10000,  # 10,000 claims per account per month
    'average_claim_value': 200,   # $200 average claim value
    'revenue_percentage': 0.05,   # 5% of claim value
    'denial_rate': 0.15,         # 15% of claims are denied
    'recovery_rate': 0.60        # 60% of denied claims are recoverable
}

# Process parameters
PROCESS_PARAMS = {
    'avg_claim_time_min': 15,     # 15 minutes per clean claim
    'denial_time_multiplier': 2.0,  # Denied claims take 2x longer
    'submission_sla_days': 5,
    'denial_sla_days': 3,
    'throughput_submission': 100,  # claims per analyst per day
    'throughput_denial': 40       # denials per analyst per day
}

# Staffing ratios
STAFF_RATIOS = {
    'analysts_per_manager': 24,
    'analysts_per_trainer': 50,
    'analysts_per_qa': 40
}

# Labor costs (India-based)
LABOR_COSTS = {
    'base_analyst': 2.50,        # $2.50 per hour for all analysts
    'manager': 3.75,             # 50% higher than base rate
    'trainer': 2.50,             # Same as base rate
    'qa_staff': 2.50             # Same as base rate
}

# Overhead costs
OVERHEAD_COSTS = {
    'per_analyst': 50,           # $50 per analyst per month
    'per_manager': 100,          # $100 per manager per month
    'fixed_monthly': 10000       # $10,000 fixed monthly costs
}

# Financial targets
FINANCIAL_TARGETS = {
    'target_gross_margin': 0.60  # 60% target gross margin
}

# Time constants
TIME_CONSTANTS = {
    'hours_per_day': 8,
    'minutes_per_hour': 60,
    'days_per_month': 22,
    'target_utilization': 0.85   # 85% target utilization
}

# Process steps and time requirements
PROCESS_STEPS = {
    'submission': {
        'extract_encounters': {'min': 2, 'max': 5},    # 2-5 minutes per spec
        'submit_claims': {'min': 2, 'max': 5},         # 2-5 minutes per spec
        'reconcile': {'min': 2, 'max': 5},             # 2-5 minutes per spec
        'revenue_reporting': {'min': 2, 'max': 5}      # 2-5 minutes per spec
    },
    'denial': {
        'denial_analysis': {'min': 2, 'max': 5},       # 2-5 minutes per spec
        'resubmission': {'min': 2, 'max': 5}           # 2-5 minutes per spec
    }
}

# Denial parameters
DENIAL_PARAMS = {
    'types': {
        'coding': {'rate': 0.30, 'complexity': 1.2},
        'documentation': {'rate': 0.25, 'complexity': 1.5},
        'eligibility': {'rate': 0.20, 'complexity': 1.0},
        'medical_necessity': {'rate': 0.15, 'complexity': 2.0},
        'other': {'rate': 0.10, 'complexity': 1.3}
    }
}

# Time constants
TIME_CONSTANTS = {
    'days_per_month': 20,              # 20 working days per month
    'hours_per_day': 8,                # 8 working hours per day
    'minutes_per_hour': 60,            # 60 minutes per hour
    'target_utilization': 0.85,        # Back to 85% as it wasn't specified
    'buffer_factor': 1.15              # 15% buffer for contingencies
}

# SLA parameters
SLA_PARAMS = {
    'submission_days': 5,              # 5 days for submission
    'denial_days': 3,                  # 3 days for denial work
    'ar_resolution': 90                # 90 days for AR resolution
}

# Implementation metrics
IMPLEMENTATION_METRICS = {
    'onboarding_days_per_account': 5,  # 5 days to onboard each account
    'training_days_per_analyst': 20,   # 20 days of training per analyst
    'ramp_up_period': 60               # 60 days to reach full productivity
}

# Quality metrics
QUALITY_METRICS = {
    'target_error_rate': 0.02,         # 2% target error rate
    'target_efficiency': 0.95,         # 95% target efficiency
    'target_recovery_rate': 0.70       # 70% target recovery rate
} 