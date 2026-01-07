import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from prioritization.utils.logger import get_logger
from prioritization.utils.state import PrioritizationState
from prioritization.components.rule_analysis import RuleAnalysisNodes
from prioritization.components.rule_parsing import RuleParsingNodes

logger = get_logger("main_pipeline")

def pipeline_graph():
    """
    A LangGraph pipeline for rule prioritization is a state graph that combines:

    1. Rule Analysis (with Human-in-the-Loop)
    2. Rule Parsing (from optimized or original rules)
    """
    
    logger.info("Initializing Pipeline Graph")
    
    analysis_nodes = RuleAnalysisNodes()
    parsing_nodes = RuleParsingNodes()
    
    workflow = StateGraph(PrioritizationState)
    
    # --- ANALYSIS NODES ---
    workflow.add_node("analysis_load_data", analysis_nodes.load_data)
    workflow.add_node("analysis_analyze", analysis_nodes.analyze_rules)
    workflow.add_node("analysis_human_review", analysis_nodes.human_gatekeeper)
    workflow.add_node("analysis_apply_optimizations", analysis_nodes.apply_optimizations)
    workflow.add_node("analysis_skip_optimizations", analysis_nodes.skip_optimizations)
    workflow.add_node("analysis_save_report", analysis_nodes.save_to_excel)
    
    # --- PARSING NODES ---
    workflow.add_node("parsing_parse", parsing_nodes.parse_rules)
    workflow.add_node("parsing_validate", parsing_nodes.validate_rules)
    workflow.add_node("parsing_save_output", parsing_nodes.save_output)
    
    # --- DEFINE EDGES & ROUTING ---
    workflow.add_edge(START, "analysis_load_data")
    workflow.add_edge("analysis_load_data", "analysis_analyze")
    workflow.add_edge("analysis_analyze", "analysis_human_review")
    
    # Analysis Decision Router
    def analysis_decision_router(state: PrioritizationState) -> str:
        if state.get("step_status") == "failed":
            logger.error("🛑 Phase failure detected in Analysis. Terminating.")
            return END
            
        decision = state.get("review_decision")
        if decision == "approve":
            return "analysis_apply_optimizations"
        elif decision == "edit":
            return "analysis_load_data"  # Re-read rules.csv after manual edit
        elif decision == "reject":
            return "analysis_analyze"   # Re-run LLM analysis with feedback
        elif decision == "quit":
            return "analysis_save_report" # Save report then end
        elif decision == "skip":
            return "analysis_skip_optimizations"
            
        return "analysis_save_report"
    
    workflow.add_conditional_edges("analysis_human_review", analysis_decision_router, {
        "analysis_load_data": "analysis_load_data",
        "analysis_analyze": "analysis_analyze",
        "analysis_apply_optimizations": "analysis_apply_optimizations",
        "analysis_skip_optimizations": "analysis_skip_optimizations",
        "analysis_save_report": "analysis_save_report",
        END: END
    })
    
    # Transitions to Parsing after Analysis completes its cycle
    workflow.add_edge("analysis_apply_optimizations", "analysis_save_report")
    workflow.add_edge("analysis_skip_optimizations", "analysis_save_report")
    
    # After Analysis report is saved, we move to Parsing (unless it was a "quit" decision)
    def after_analysis_router(state: PrioritizationState) -> str:
        if state.get("review_decision") == "quit":
            logger.info("👋 User requested termination. Skipping parsing.")
            return END
        return "parsing_parse"
        
    workflow.add_conditional_edges("analysis_save_report", after_analysis_router, {
        "parsing_parse": "parsing_parse",
        END: END
    })
    
    # Parsing Flow
    workflow.add_edge("parsing_parse", "parsing_validate")
    
    def parsing_router(state: PrioritizationState) -> str:
        if state.get("step_status") == "failed":
            logger.error("🛑 Phase failure detected in Parsing.")
            return END
        # Internal rule_parsing loop for validation errors (limited iterations)
        if state.get("validation_errors") and state.get("iteration_count", 0) < 3:
            logger.info(f"🔄 Validation failed. Retrying parsing (Attempt {state.get('iteration_count', 0) + 1}/3)")
            return "parsing_parse"
        return "parsing_save_output"
        
    workflow.add_conditional_edges("parsing_validate", parsing_router, {
        "parsing_parse": "parsing_parse",
        "parsing_save_output": "parsing_save_output",
        END: END
    })
    
    workflow.add_edge("parsing_save_output", END)
    
    logger.info("✨ Pipeline graph successfully compiled and ready for execution.")
    return workflow.compile(checkpointer=MemorySaver())
