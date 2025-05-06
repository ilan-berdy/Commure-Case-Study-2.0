"""
Main script for RCM Capacity Planning Model.
"""

from rcm.model import RCMModel
from rcm.optimizer import RCMOptimizer, print_optimization_results

def main():
    """Run the RCM model and display results."""
    # Create model instance
    model = RCMModel()
    
    # Generate and display report
    model.print_detailed_report()
    
    # Run optimization
    print("\n" + "="*50 + "\n")
    optimizer = RCMOptimizer()
    results = optimizer.optimize()
    print_optimization_results(results)

if __name__ == "__main__":
    main() 