"""
Main entry point for running the RCM Capacity Planning Model.
"""

from rcm.model import RCMModel
from rcm.optimizer import RCMOptimizer, print_optimization_results

def main():
    """Run the RCM model and display results."""
    # Create model instance
    model = RCMModel()
    
    # Generate and display base model report
    print("\n=== Base Model Results ===")
    model.print_detailed_report()
    
    # Run optimization
    print("\n" + "="*50 + "\n")
    print("=== Running Staffing Optimization ===")
    optimizer = RCMOptimizer()
    results = optimizer.optimize()
    print_optimization_results(results)
    
    # Save results to CSV
    df = model.generate_report()
    df.to_csv('results/rcm_model_results.csv', index=False)
    print("\nResults saved to results/rcm_model_results.csv") 