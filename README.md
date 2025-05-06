# RCM Capacity Planning Model

A Python-based model for Revenue Cycle Management (RCM) capacity planning and optimization.

## Project Structure

```
.
├── rcm/                    # Core RCM module
│   ├── __init__.py        # Module initialization
│   ├── model.py           # Main RCM model class
│   ├── optimizer.py       # Staffing optimization logic
│   ├── calculations.py    # Core calculation functions
│   └── config.py          # Configuration parameters
├── results/               # Output files
│   └── rcm_model_results.csv
├── docs/                  # Documentation
│   └── caseStudy.txt
├── tests/                 # Unit tests
├── main.py               # Entry point
└── requirements.txt      # Python dependencies
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the model:
   ```bash
   python main.py
   ```

## Features

- Monthly capacity planning for RCM operations
- Staffing optimization with SLA constraints
- Financial modeling and margin analysis
- Progressive account onboarding simulation
- Training and ramp-up period modeling

## Configuration

Key parameters can be adjusted in `rcm/config.py`:
- Account onboarding schedule
- Revenue and cost parameters
- SLA requirements
- Staff ratios and costs
- Quality metrics

## Output

Results are saved to `results/rcm_model_results.csv` and include:
- Monthly staffing levels
- Financial metrics
- SLA compliance
- Utilization rates
- Quality metrics 