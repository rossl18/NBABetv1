"""
Script to regenerate all dashboard data with the new model improvements.
This ensures all predictions use the enhanced features, time weighting, and optimized hyperparameters.
"""
import sys
import os
from datetime import date, timedelta

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

def regenerate_all_data():
    """
    Regenerate all dashboard data with new model improvements:
    1. Generate new betting dataset with improved models
    2. Update historical probabilities if needed
    3. Track outcomes and generate performance metrics
    4. Export to dashboard JSON files
    """
    print("=" * 70)
    print("REGENERATING ALL DASHBOARD DATA WITH NEW MODEL IMPROVEMENTS")
    print("=" * 70)
    print("\nThis will:")
    print("  1. Generate new betting predictions with enhanced features")
    print("  2. Use time-based weighting and optimized hyperparameters")
    print("  3. Track outcomes for past games")
    print("  4. Export updated data to dashboard")
    print("\n" + "=" * 70 + "\n")
    
    try:
        # Step 1: Generate new betting dataset with improved models
        print("[Step 1/4] Generating new betting dataset with improved models...")
        print("  - Using enhanced feature engineering")
        print("  - Time-based sample weighting")
        print("  - Optimized hyperparameters")
        print("  - Feature selection")
        print("  - Market-adjusted EV calculation\n")
        
        from export_to_json import export_for_dashboard
        df = export_for_dashboard()
        
        if df is not None and len(df) > 0:
            print(f"\n✓ Generated {len(df)} props with new model improvements")
        else:
            print("\n⚠ No props generated (may be no games today)")
        
        print("\n" + "=" * 70)
        print("✅ DATA REGENERATION COMPLETE")
        print("=" * 70)
        print("\nAll dashboard data has been updated with:")
        print("  ✓ Enhanced feature engineering (line context, trends, momentum)")
        print("  ✓ Time-based weighting (recent games weighted more)")
        print("  ✓ Optimized hyperparameters (200 trees, better regularization)")
        print("  ✓ Feature selection (removes noise)")
        print("  ✓ Market-adjusted EV (accounts for market efficiency)")
        print("\nDashboard files updated:")
        print("  - dashboard/public/data/latest-bets.json")
        print("  - dashboard/public/data/performance.json")
        print("\nNext steps:")
        print("  1. Run 'npm run build' in dashboard/ to rebuild the frontend")
        print("  2. Commit and push changes to GitHub")
        print("  3. Dashboard will automatically update on GitHub Pages")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error during regeneration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    regenerate_all_data()
