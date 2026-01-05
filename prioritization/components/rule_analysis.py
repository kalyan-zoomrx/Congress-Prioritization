import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from langgraph.types import interrupt
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from prioritization.utils.logger import get_logger
from prioritization.utils.state import RuleAnalysisState
from prioritization.utils.litellm import call_llm_with_user_prompt

logger = get_logger("RuleAnalysisNodes")


class RuleAnalysisNodes:
    def __init__(self):
        pass

    # --------------------------------------------------------------------------------------
    # Load Data (Rules.csv (Mandatory), client_keywords.csv (Optional))
    # --------------------------------------------------------------------------------------

    def load_data(self, state: RuleAnalysisState) -> RuleAnalysisState:
        """Loads data specifically for analysis."""

        logger.info("Loading Data for Rule Analysis")
        directory = state["directory"]
        
        with open(os.path.join(directory, "rules.csv"), "r", encoding="utf-8") as f:
            state["rules_raw"] = f.read()
        
        if os.path.exists(os.path.join(directory, "client_keywords.csv")):
            with open(os.path.join(directory, "client_keywords.csv"), "r", encoding="utf-8") as f:
                state["keywords_raw"] = f.read()
                logger.info("Rules & Client Keywords loaded successfully")
        else:
            logger.info("Rules loaded successfully, Client Keywords not found")
            
        return state


    # --------------------------------------------------------------------------------------
    # Analyze Rules (Issues & Optimizations)
    # --------------------------------------------------------------------------------------

    def analyze_rules(self, state: RuleAnalysisState) -> RuleAnalysisState:
        """Calls LLM via litellm.completion to find issues and optimizations."""

        logger.info("Analyzing Rules")
        
        try:
            response = call_llm_with_user_prompt(
                prompt_name="rule_analysis_prompt",
                format_params={
                    "rules": state["rules_raw"],
                    "client_keywords": state["keywords_raw"],
                    "user_feedback": state.get("user_feedback", "")
                },
                model_name=state["model"],
                json_output=True
            )

            content = response.content.replace("```json", "").replace("```", "").strip()
            state["analysis_report"] = json.loads(content)
            
            if not state.get("review_history"):
                state["review_history"] = []
            
            if state.get("user_feedback"):
                state["review_history"].append({
                    "iteration": state.get("iteration_count", 0),
                    "feedback": state["user_feedback"]
                })
                
            logger.info("Analysis complete.")

        except Exception as e:

            state["analysis_report"] = {"error": str(e)}
            logger.info(content)
            logger.error(f"Analysis failed: {e}")

        state["iteration_count"] = state.get("iteration_count", 0) + 1
        return state

    # --------------------------------------------------------------------------------------
    # Human Gatekeeper (Review & Feedback)
    # --------------------------------------------------------------------------------------

    def human_gatekeeper(self, state: RuleAnalysisState) -> RuleAnalysisState:
        """Interrupts the flow for user review using LangGraph interrupt()."""

        logger.info("Human Review Node - Interrupting for review...")
        
        interrupt_payload = {
            "action_requests": [
                {
                    "name": "analyze_rules",
                    "arguments": {"report": state["analysis_report"]},
                    "description": "Rule analysis results pending review\n\nAnalysis Report Ready"
                }
            ],
            "review_configs": [
                {
                    "action_name": "analyze_rules",
                    "allowed_decisions": ["approve", "edit", "reject", "quit"]
                }
            ]
        }
        
        # This will pause the execution and wait for a command resume
        response = interrupt(interrupt_payload)
        
        decisions = response.get("decisions", [])
        if decisions:
            decision = decisions[0]
            state["review_decision"] = decision.get("type")
            
            if decision["type"] == "reject":
                state["user_feedback"] = decision.get("message", "")
            elif decision["type"] == "edit":
                # User provided a path to manually edited rules
                edited_action = decision.get("edited_action", {})
                file_path = edited_action.get("args", {}).get("edited_rules_path")
                
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            state["rules_raw"] = f.read()
                        state["user_feedback"] = f"User manually edited rules file: {file_path}"
                        logger.info(f"Loaded manually edited rules from {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to read edited rules file: {e}")
                        state["user_feedback"] = f"Error reading edited rules file: {str(e)}"
                else:
                    feedback = edited_action.get("args", {}).get("edited_rules", "")
                    state["user_feedback"] = feedback
                    logger.warning("No valid file path provided for 'edit', using feedback text instead.")

        return state

    # --------------------------------------------------------------------------------------
    # Save to CSV
    # --------------------------------------------------------------------------------------

    def save_to_excel(self, state: RuleAnalysisState) -> RuleAnalysisState:
        """Saves the analysis report to an Excel file with separate sheets for optimizations and issues."""

        logger.info("Saving analysis report")
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            report_dir = os.path.join(state["directory"], "analysis_reports")
            os.makedirs(report_dir, exist_ok=True)
            
            report_path = os.path.join(report_dir, f"rule_analysis_{timestamp}.xlsx")
            
            analysis_report = state["analysis_report"]
            
            # Prepare Optimizations sheet
            optimizations_rows = []
            for opt in analysis_report.get("optimizations", []):
                optimizations_rows.append({
                    "Priority Level": opt.get("priority_level", "N/A"),
                    "Original Text": opt.get("original_text", ""),
                    "Suggested Text": opt.get("suggested_text", ""),
                    "Rationale": opt.get("rationale", "")
                })
            
            # Prepare Issues sheet
            issues_rows = []
            for issue in analysis_report.get("issues", []):
                issues_rows.append({
                    "Priority Levels": ", ".join(issue.get("priority_levels", [])),
                    "Severity": issue.get("severity", "N/A"),
                    "Issue Description": issue.get("issue", ""),
                    "Impact": issue.get("impact", "")
                })
            
            # Add review history to Issues sheet if exists
            if state.get("review_history"):
                issues_rows.append({
                    "Priority Levels": "",
                    "Severity": "",
                    "Issue Description": "--- Review History ---",
                    "Impact": ""
                })
                for review in state.get("review_history", []):
                    issues_rows.append({
                        "Priority Levels": "",
                        "Severity": "",
                        "Issue Description": f"Iteration {review['iteration']}: {review['feedback']}",
                        "Impact": ""
                    })
            
            # Create Excel writer
            with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
                # Write Optimizations sheet
                df_optimizations = pd.DataFrame(optimizations_rows)
                df_optimizations.to_excel(writer, sheet_name='Optimizations', index=False)
                
                # Write Issues sheet
                df_issues = pd.DataFrame(issues_rows)
                df_issues.to_excel(writer, sheet_name='Issues', index=False)
                
                # Auto-adjust column widths
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 100)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            state["report_path"] = report_path
            logger.info(f"Report saved to: {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            state["report_path"] = f"Error: {str(e)}"
        
        return state


# ------------------------------------------------------------------------------------------
# Pipeline Creation
# ------------------------------------------------------------------------------------------

def rule_analysis_workflow():
    """Creates the LangGraph workflow with HITL using pure LiteLLM."""
    
    logger.info("Creating Refinement Pipeline")
    nodes = RuleAnalysisNodes()
    
    workflow = StateGraph(RuleAnalysisState)
    
    # Add nodes
    workflow.add_node("load_data", nodes.load_data)
    workflow.add_node("analyze", nodes.analyze_rules)
    workflow.add_node("human_review", nodes.human_gatekeeper)
    workflow.add_node("save_report", nodes.save_to_excel)
    
    # Define edges
    workflow.set_entry_point("load_data")
    workflow.add_edge("load_data", "analyze")
    workflow.add_edge("analyze", "human_review")
    
    # Conditional routing based on decision
    def decision_router(state: RuleAnalysisState) -> str:
        decision = state.get("review_decision")
        if decision == "approve":
            return "save_report"
        elif decision == "edit":
            return "analyze"  # Re-analyze with edited rules
        elif decision == "reject":
            return "analyze"  # Loop back for re-analysis
        elif decision == "quit":
            return "save_report" # Save report before quiting
        return "save_report"
    
    workflow.add_conditional_edges("human_review", decision_router, {
        "analyze": "analyze",
        "save_report": "save_report"
    })
    
    workflow.add_edge("save_report", END)
    logger.info("Refinement Pipeline Created")
    
    # Compile with checkpointer
    return workflow.compile(checkpointer=MemorySaver())
