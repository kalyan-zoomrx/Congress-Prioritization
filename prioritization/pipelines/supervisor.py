import time
from langgraph.types import Command
from prioritization.utils.logger import get_logger
from prioritization.components.rule_analysis import rule_analysis_workflow

logger = get_logger("Supervisor")

def analysis_pipeline(directory, model):
    logger.info("Starting Analysis Pipeline Workflow")
    pipeline = rule_analysis_workflow()
    config = {"configurable": {"thread_id": "Session1"}}
    initial_input = {
        "directory": directory,
        "model": model,
        "iteration_count": 0,
        "review_history": []
    }

    current_input = initial_input

    while True:
        # Run/Continue pipeline
        result = pipeline.invoke(current_input, config=config)
        
        # Check current state for interruptions
        state_snapshot = pipeline.get_state(config)
        
        # If no more nodes to run, we are finished
        if not state_snapshot.next:
            print("\n✅ Refinement Complete!")
            if result.get("report_path"):
                print(f"📊 Analysis Report Saved to: {result['report_path']}")
            break

        # Display analysis results if available
        report = state_snapshot.values.get("analysis_report")
        if report:
            if "error" in report:
                print(f"\n❌ AI Analysis Error: {report['error']}")
                break
                
            print("\n" + "="*60)
            print("AI ANALYSIS REPORT READY")
            print("="*60)
            
            print(f"\n📋 Issues Found: {len(report.get('issues', []))}")
            for i, issue in enumerate(report.get('issues', []), 1):
                severity = issue.get('severity', 'N/A').upper()
                print(f" {i}. [{severity}] {issue.get('issue', 'N/A')}")
            
            print(f"\n✨ Optimizations Suggested: {len(report.get('optimizations', []))}")
            for i, opt in enumerate(report.get('optimizations', []), 1):
                level = opt.get('priority_level', 'N/A')
                print(f" {i}. [{level}] {opt.get('suggested_text', '')[:100]}...")

        # Get user decision
        print("\n" + "-"*60)
        print("Decision Options:")
        print(" [a] Approve - Save report and finish")
        print(" [e] Edit    - Provide feedback/edits and re-analyze")
        print(" [r] Reject  - Provide reason and re-analyze")
        print(" [q] Quit    - Exit refinement session")
        
        choice = input("\nSelect an option [a/e/r/q]: ").lower().strip()

        if choice == 'q':
            print("Exiting refinement session...")
            break
            
        # Build decision command
        if choice == 'a':
            decision = {"decisions": [{"type": "approve"}]}
        elif choice == 'r':
            feedback = input("Why is this rejected? Feedback for LLM: ")
            decision = {"decisions": [{"type": "reject", "message": feedback}]}
        elif choice == 'e':
            feedback = input("Enter your edits or feedback for improvement: ")
            decision = {
                "decisions": [{
                    "type": "edit",
                    "edited_action": {
                        "name": "analyze_rules",
                        "args": {"edited_rules": feedback}
                    }
                }]
            }
        else:
            print("Invalid choice. Please try again.")
            current_input = None # Stay in current state
            continue

        # Resume the pipeline with the user's decision
        current_input = Command(resume=decision)



def parsing_pipeline(directory, model):
    logger.info("Starting Parsing Pipeline Workflow")
    start_time = time.time()

    # Heavy Imports & Initializations
    # -----------------------------------------------------------------------------------
    logger.info("Importing Heavy Dependencies")
    from prioritization.utils.TrackLitellm import SpendTracker
    from prioritization.components.rule_parsing import rule_parsing_workflow
    logger.info("Heavy Dependencies Imported Successfully")
    
    logger.info("Initializing Supervisor Pipeline")
    pipeline = rule_parsing_workflow()
    tracker = SpendTracker()
    tracker.initiate()
    logger.info("Supervisor Pipeline Initialized Successfully")

    # Supervisor Workflow
    # -----------------------------------------------------------------------------------
    logger.info(f"Starting Supervisor Workflow | Directory: {directory} | Model: {model}")

    try:
        result = pipeline.invoke({
            "directory": directory,
            "model": model,
            "iteration_count": 0,
            "validation_errors": [],
            "user_instructions": ""
        })
        end_time = time.time()
        logger.info(f"Supervisor Workflow finished successfully in {end_time - start_time:.2f} seconds")
        
        if result.get("output_file"):
            logger.info(f"Final output saved to: {result['output_file']}")
    
    except Exception as e:
        logger.error(f"Critical error during prioritization workflow: {str(e)}", exc_info=True)
    
    finally:
        metrics = tracker.close()
        logger.info(f"Session metrics - Amount Spent: {metrics['spent']} | Total Spend: {metrics['total_spent']}")