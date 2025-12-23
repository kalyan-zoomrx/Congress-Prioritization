from dotenv import load_dotenv
from prioritization.utils.logger import get_logger
from prioritization.pipelines.supervisor import initiate_supervisor
from prioritization.utils.TrackLitellm import SpendTracker

load_dotenv()
logger = get_logger("Main")
tracker = SpendTracker()
tracker.initiate()

TEST_DIRECTORY = "data/test02_ERA_2025_Calliditas/"
#MODEL = "gpt-4.1"
#MODEL = "gemini/gemini-2.5-pro"
MODEL = "claude-haiku-4-5"

try:
    logger.info("Initiating Supervisor")
    initiate_supervisor(TEST_DIRECTORY, MODEL)
    logger.info("Supervisor Completed Successfully")
    metrics = tracker.close()
    logger.info(f"Amount Spent: {metrics['spent']} Total Spent: {metrics['total_spent']}")

except Exception as e:
    logger.error(e)
    logger.error("Supervisor Failed")
    metrics = tracker.close()
    logger.info(f"ERROR - Amount Spent: {metrics['spent']} Total Spent: {metrics['total_spent']}")