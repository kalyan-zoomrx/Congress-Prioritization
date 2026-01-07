import time
from langgraph.types import Command
from prioritization.utils.logger import get_logger
from prioritization.pipelines.main_pipeline import pipeline_graph

logger = get_logger("Supervisor")

def run_prioritization_pipeline(directory, model):
    """
    A function to run the prioritization pipeline
    
    Args:
        directory (str): The directory containing the input files
        model (str): The model to use for analysis
    """

    thread_id = f"session_{int(time.time())}"
    logger.info(f"Initializing Session: {thread_id}")

    pipeline = pipeline_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_input = {
        "directory": directory,
        "model": model,
        "analysis_iteration_count": 0,
        "review_history": [],
        "user_feedback": ""
    }

    current_input = initial_input

    while True:
        result = pipeline.invoke(current_input, config=config)
        state_snapshot = pipeline.get_state(config)
        
        if not state_snapshot.next:
            logger.info("Prioritization Pipeline Completed Successfully")

            if result.get("output_file"):
                print("Parsed Rules are saved at: ", result['output_file'])
                logger.info(f"Final Parsed Rules Saved: {result['output_file']}")
            
            if result.get("report_path"):
                print("Analysis Report is saved at: ", result['report_path'])
                logger.info(f"Final Analysis Report: {result['report_path']}")
            
            return result

        # Check for Human-in-the-Loop interrupt
        current_node = state_snapshot.next[0]
        
        if current_node == "analysis_human_review":
            # Display analysis report for user review
            report = state_snapshot.values.get("analysis_report")
            if report:
                if "error" in report:
                    logger.error(f"AI Analysis Error: {report['error']}")
                    break
                
                print("\n" + "="*60)
                print("📋 RULE ANALYSIS REPORT SUMMARY")
                print("="*60)

                issues = report.get('issues', [])
                print(f"\n🔍 Issues Found: {len(issues)}")
                for i, issue in enumerate(issues, 1):
                    severity = issue.get('severity', 'N/A').upper()
                    print(f" {i}. [{severity}] {issue.get('issue', 'N/A')}")
                
                optimizations = report.get('optimizations', [])
                print(f"\n✨ Optimizations Suggested: {len(optimizations)}")
                for i, opt in enumerate(optimizations, 1):
                    level = opt.get('priority_level', 'N/A')
                    print(f" {i}. [{level}] {opt.get('suggested_text', '')}")
            
            print("\n" + "-"*30)
            print("DECISION REQUIRED:")
            print(" [a] Approve         - Apply optimizations and Proceed to Parsing")
            print(" [e] Edit            - Provide path to manually edited CSV")
            print(" [r] Reject          - Provide feedback and Re-analyze")
            print(" [s] Skip            - Proceed to Parsing with original rules")
            print(" [q] Save & Exit     - Save report and exit")
            
            choice = input("\nSelect an option [a/e/r/s/q]: ").lower().strip()

            if choice == 'a':
                decision = {"decisions": [{"type": "approve"}]}
                logger.info("User Approved the Optimizations")

            elif choice == 's':
                decision = {"decisions": [{"type": "skip"}]}
                logger.info("User Skipped the Optimizations")

            elif choice == 'r':
                feedback = input("Feedback for AI optimization: ").strip().replace('"', '').replace("'", "")
                decision = {"decisions": [{"type": "reject", "message": feedback}]}
                logger.info("User Rejected the Optimizations")

            elif choice == 'e':
                file_path = input("Path to edited CSV: ").strip().replace('"', '').replace("'", "")
                decision = {"decisions": [{"type": "edit", "edited_action": {"name": "analyze_rules", "args": {"edited_rules_path": file_path}}}]}
                logger.info("User Edited the Optimizations")

            elif choice == 'q':
                decision = {"decisions": [{"type": "quit"}]}
                logger.info("User Quit the Optimizations")

            else:
                logger.warning(f"Invalid input received: '{choice}'. Retrying decision node.")
                print("Invalid choice. Please try again.")
                current_input = None # Stay in the same state
                continue

            current_input = Command(resume=decision)
        
        else:
            # If it pauses at any other node (unexpected), just resume
            logger.warning(f"Pipeline paused at unexpected node: {current_node}. Resuming...")
            current_input = None