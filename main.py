from prioritization.utils.logger import get_logger
logger = get_logger(__name__)
logger.info("Starting Unified Congress Prioritization Pipeline")

from prioritization.pipelines.supervisor import run_prioritization_pipeline
from prioritization.utils.TrackLitellm import SpendTracker

TEST_DIRECTORY = "data/test03_NKF_2025_Ardelyx/"
MODEL = "gemini/gemini-2.5-pro"

tracker = SpendTracker()
tracker.initiate()
    
# Run the Unified Pipeline (Analysis -> HITL -> Parsing)
result = run_prioritization_pipeline(directory=TEST_DIRECTORY, model=MODEL)
    
if result:
    logger.info("Pipeline execution finished successfully.")
else:
    logger.warning("Pipeline execution did not complete.")

metrics = tracker.close()
logger.info(f"Session metrics - Amount Spent: {metrics['spent']} | Total Spend: {metrics['total_spent']}")
