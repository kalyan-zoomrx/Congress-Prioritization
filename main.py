import os
import time
from prioritization.utils.logger import get_logger
logger = get_logger("Main")

TEST_DIRECTORY = "data/test02_ERA_2025_Calliditas/"
#MODEL = "gpt-4.1"
MODEL = "gemini/gemini-2.5-pro"
#MODEL = "claude-haiku-4-5"

def main(directory, model):
    logger.info("Starting Prioritization Workflow")
    start_time = time.time()

    # Heavy Imports
    logger.info("Importing Heavy Dependencies")
    from prioritization.utils.TrackLitellm import SpendTracker
    from prioritization.pipelines.supervisor import create_prioritization_pipeline
    logger.info("Heavy Dependencies Imported Successfully")
    
    logger.info("Creating Prioritization Pipeline")
    pipeline = create_prioritization_pipeline()
    logger.info("Prioritization Pipeline Created Successfully")
    
    logger.info("Initializing Spend Tracker")
    tracker = SpendTracker()
    tracker.initiate()
    logger.info("Spend Tracker Initialized Successfully")

    logger.info(f"Starting Workflow | Directory: {TEST_DIRECTORY} | Model: {MODEL}")

    try:
        result = pipeline.invoke({
            "directory": TEST_DIRECTORY,
            "model": MODEL,
            "iteration_count": 0,
            "validation_errors": [],
            "user_instructions": ""
        })
        end_time = time.time()
        logger.info(f"Workflow finished successfully in {end_time - start_time:.2f} seconds")
    
    except Exception as e:
        logger.error(f"Critical error during workflow: {str(e)}", exc_info=True)
    
    finally:
        metrics = tracker.close()
        logger.info(f"Session metrics - Amount Spent: {metrics['spent']} | Total Spend: {metrics['total_spent']}")

if __name__ == "__main__":
    main(directory=TEST_DIRECTORY, model=MODEL)