import time
from prioritization.utils.logger import get_logger
logger = get_logger(__name__)

TEST_DIRECTORY = "data/test05_AACR_2025_GDH/"
MODEL = "gemini/gemini-2.5-pro"

start_time = time.time()
logger.info(f"🚀 Initializing Congress Prioritization Workflow | Source: {TEST_DIRECTORY} | Model: {MODEL}")

logger.info("Importing required modules")
from prioritization.pipelines.supervisor import run_prioritization_pipeline
from prioritization.utils.TrackLitellm import SpendTracker
logger.info("Required modules imported successfully")

tracker = SpendTracker()
tracker.initiate()

try:
    run_prioritization_pipeline(directory=TEST_DIRECTORY, model=MODEL)
except Exception as e:
    logger.error("Pipeline execution failed")

end_time = time.time()
metrics = tracker.close()
logger.info(f"Session metrics - Amount Spent: {metrics['spent']} | Total Spend: {metrics['total_spent']}")
logger.info(f"Total time taken: {end_time - start_time - 10} seconds")
