import os
import sys

# Ensure current dir is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset_ingestion import ingest_dataset
from monitoring_engine import run_continuous_monitoring

def seed_database(reset_db: bool = True):
    print("=== SEEDING SWASTHYASETU AI DATABASE FROM SYNTHETIC 1,000 PATIENT DATASET ===")
    ingest_summary = ingest_dataset(reset_db=reset_db)
    print(f"[OK] Ingestion Complete: {ingest_summary['total_imported']} records imported.")
    
    monitoring_summary = run_continuous_monitoring()
    print(f"[OK] Monitoring Initialized: {monitoring_summary['new_alerts_created']} alerts, {monitoring_summary['tasks_generated']} tasks.")
    print("=== DATABASE READY FOR LIVE PRODUCTION & EVALUATION DEMONSTRATION ===")

if __name__ == "__main__":
    seed_database(reset_db=True)
