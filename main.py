import time
from prioritization.utils.logger import get_logger
logger = get_logger("Main")
logger.info("Starting Prioritization Workflow")
start_time = time.time()

from prioritization.utils.TrackLitellm import SpendTracker
from prioritization.pipelines.supervisor import create_prioritization_pipeline

pipeline = create_prioritization_pipeline()
tracker = SpendTracker()
tracker.initiate()

TEST_DIRECTORY = "data/test02_ERA_2025_Calliditas/"
#MODEL = "gpt-4.1"
MODEL = "gemini/gemini-2.5-pro"
#MODEL = "claude-haiku-4-5"

result = pipeline.invoke({
    "directory": TEST_DIRECTORY,
    "model": MODEL,
    "iteration_count": 0,
    "validation_errors": []
})
end_time = time.time()
logger.info(f"Workflow finished in {end_time - start_time} seconds")
metrics = tracker.close()
logger.info(f"Amount Spent: {metrics['spent']} Total Spent: {metrics['total_spent']}")