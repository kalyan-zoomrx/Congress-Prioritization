from prioritization.utils.logger import get_logger
logger = get_logger(__name__)

TEST_DIRECTORY = "data/test01_ASCO_2025_RevMed/"
MODEL = "gemini/gemini-2.5-pro"

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

metrics = tracker.close()
logger.info(f"Session metrics - Amount Spent: {metrics['spent']} | Total Spend: {metrics['total_spent']}")
