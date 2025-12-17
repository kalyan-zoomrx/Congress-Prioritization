from dotenv import load_dotenv
from prioritization.utils.logger import get_logger
from prioritization.pipelines.supervisor import initiate_supervisor
from prioritization.utils.TrackLitellm import SpendTracker

load_dotenv()
logger = get_logger("Main")
tracker = SpendTracker()
tracker.initiate()

TEST_DIRECTORY = "data/test06_ESMO_2025_JNJ_Lung/"
#MODEL = "gpt-4.1"
#MODEL = "gemini/gemini-2.5-pro"
MODEL = "claude-haiku-4-5"

try:
    logger.info("Initiating Supervisor")
    initiate_supervisor(TEST_DIRECTORY, MODEL)
    logger.info("Supervisor Completed Successfully")
    metrics = tracker.close()
    logger.info(f"Amount Spent: {metrics['spent']}")
except Exception as e:
    logger.error(e)
    metrics = tracker.close()
    logger.info(f"Amount Spent: {metrics['spent']}")