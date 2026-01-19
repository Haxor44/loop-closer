import time
import subprocess
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

PIPELINE_SCRIPT = "execution/run_user_pipeline.py"
INTERVAL_SECONDS = 3600  # Run every hour

def run_pipeline():
    logging.info("Starting scheduled pipeline run...")
    try:
        # Run the pipeline script
        result = subprocess.run(
            [sys.executable, PIPELINE_SCRIPT],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Pipeline run completed successfully.")
            logging.info(result.stdout)
        else:
            logging.error(f"Pipeline run failed with return code {result.returncode}")
            logging.error(result.stderr)
            
    except Exception as e:
        logging.error(f"Error running pipeline: {str(e)}")

def main():
    logging.info(f"Scheduler started. Running pipeline every {INTERVAL_SECONDS} seconds.")
    
    # Run immediately on start
    run_pipeline()
    
    while True:
        try:
            time.sleep(INTERVAL_SECONDS)
            run_pipeline()
        except KeyboardInterrupt:
            logging.info("Scheduler stopped by user.")
            break
        except Exception as e:
            logging.error(f"Scheduler crashed: {str(e)}")
            time.sleep(60) # Wait a bit before retrying

if __name__ == "__main__":
    main()
