from prioritization.pipelines.supervisor import parsing_pipeline, analysis_pipeline
from prioritization.utils.TrackLitellm import SpendTracker
from prioritization.utils.logger import get_logger

logger = get_logger(__name__)

TEST_DIRECTORY = "data/test01_ASCO_2025_RevMed/"
#MODEL = "gpt-4.1"
#MODEL = "gemini/gemini-2.5-pro"
MODEL = "claude-haiku-4-5"

if __name__ == "__main__":
    logger.info("Starting Congress Prioritization Pipeline")
    tracker = SpendTracker()
    tracker.initiate()
    analysis_pipeline(directory=TEST_DIRECTORY, model=MODEL)
    #parsing_pipeline(directory=TEST_DIRECTORY, model=MODEL)
    metrics = tracker.close()
    logger.info(f"Session metrics - Amount Spent: {metrics['spent']} | Total Spend: {metrics['total_spent']}")
