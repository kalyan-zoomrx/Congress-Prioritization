import time
from langgraph.types import Command
from prioritization.utils.logger import get_logger
from prioritization.pipelines.main_pipeline import unified_prioritization_workflow

logger = get_logger("Supervisor")

def run_prioritization_pipeline(directory, model):
    """
    Orchestrates the unified prioritization workflow:
    1. Analysis (Iterative + HITL)
    2. Parsing (Automated transition)
    """
    logger.info("Starting Unified Prioritization Pipeline")
    pipeline = unified_prioritization_workflow()
    config = {"configurable": {"thread_id": "unified_session_" + str(int(time.time()))}}
    
    initial_input = {
        "directory": directory,
        "model": model,
        "analysis_iteration_count": 0,
        "review_history": [],
        "user_feedback": ""
    }

    current_input = initial_input

    while True:
        # Run the pipeline (will pause if there's an interrupt)
        result = pipeline.invoke(current_input, config=config)
        state_snapshot = pipeline.get_state(config)
        
        # Check if the pipeline has finished
        if not state_snapshot.next:
            print("\n✅ Unified Pipeline Complete!")
            if result.get("output_file"):
                print(f"📄 Final Parsed Rules Saved: {result['output_file']}")
            if result.get("report_path"):
                print(f"📊 Final Analysis Report: {result['report_path']}")
            return result

        # Check for Human-in-the-Loop interrupt
        current_node = state_snapshot.next[0]
        
        if current_node == "analysis_human_review":
            # Display analysis report for user review
            report = state_snapshot.values.get("analysis_report")
            if report:
                if "error" in report:
                    print(f"\n❌ AI Analysis Error: {report['error']}")
                    break
                    
                print("\n--- Rule Analysis Report ---")
                print("="*60)
                print(f"\n📋 Issues Found: {len(report.get('issues', []))}")
                for i, issue in enumerate(report.get('issues', []), 1):
                    severity = issue.get('severity', 'N/A').upper()
                    print(f" {i}. [{severity}] {issue.get('issue', 'N/A')}")
                
                print(f"\n✨ Optimizations Suggested: {len(report.get('optimizations', []))}")
                for i, opt in enumerate(report.get('optimizations', []), 1):
                    level = opt.get('priority_level', 'N/A')
                    print(f" {i}. [{level}] {opt.get('suggested_text', '')[:100]}...")
                
            print("\nDecision Options:")
            print(" [a] Approve - Apply optimizations and Proceed to Parsing")
            print(" [e] Edit    - Provide path to manually edited CSV (Re-load & Re-analyze)")
            print(" [r] Reject  - Provide feedback and Re-analyze")
            print(" [s] Skip    - Proceed to Parsing with original rules")
            print(" [q] Quit    - Save report and exit")
            
            choice = input("\nSelect an option [a/e/r/s/q]: ").lower().strip()

            if choice == 'a':
                decision = {"decisions": [{"type": "approve"}]}
            elif choice == 's':
                decision = {"decisions": [{"type": "skip"}]}
            elif choice == 'r':
                feedback = input("Feedback for AI: ")
                decision = {"decisions": [{"type": "reject", "message": feedback}]}
            elif choice == 'e':
                file_path = input("Path to edited CSV: ").strip().replace('"', '').replace("'", "")
                decision = {"decisions": [{"type": "edit", "edited_action": {"name": "analyze_rules", "args": {"edited_rules_path": file_path}}}]}
            elif choice == 'q':
                decision = {"decisions": [{"type": "quit"}]}
            else:
                print("Invalid choice. Please try again.")
                current_input = None # Stay in the same state
                continue

            current_input = Command(resume=decision)
        
        else:
            # If it pauses at any other node (unexpected), just resume
            logger.warning(f"Pipeline paused at unexpected node: {current_node}. Resuming...")
            current_input = None
