import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from langgraph.types import interrupt
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from prioritization.utils.logger import get_logger
from prioritization.utils.state import PrioritizationState
from prioritization.utils.litellm import call_llm_with_user_prompt


logger = get_logger("RuleAnalysisNodes")


class RuleAnalysisNodes:

    # --------------------------------------------------------------------------------------------------
    # Load Data (Rules.csv (Mandatory), client_keywords.csv (Optional), custom_synonyms.csv (Optional))
    # --------------------------------------------------------------------------------------------------

    def load_data(self, state: PrioritizationState) -> PrioritizationState:
        """Loads data specifically for analysis."""

        state["current_step"] = "rule_analysis - loading_data"
        state["step_status"] = "pending"

        logger.info("Loading Data for Rule Analysis")
        directory = state.get("directory")
        if not directory:
            state.update({"step_status": "failed", "step_error": "state missing required key: directory"})
            return state
        
        def read_file(filename: str, required: bool = False) -> str | None:
            path = os.path.join(directory, filename)

            if not os.path.exists(path):
                if required:
                    state.update({"step_status": "failed", "step_error": f"required `rules.csv` file not found: {path}"})
                    raise FileNotFoundError(f"required `rules.csv` file not found: {path}")
                logger.info("%s not found (optional)", filename)
                return None

            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if required and not content:
                state.update({"step_status": "failed", "step_error": f"required `rules.csv` file is empty: {path}"})
                raise ValueError(f"required `rules.csv` file is empty: {path}")

            logger.info("%s loaded successfully", filename)
            return content

        try:
            state["rules_raw"] = read_file("rules.csv", required=True)
            state["keywords_raw"] = read_file("client_keywords.csv", required=False)
            state["synonyms_raw"] = read_file("custom_synonyms.csv", required=False)
            logger.info("Data loaded successfully")
            state.update({"step_status": "success"})

        except (FileNotFoundError, ValueError, OSError) as e:
            logger.error("Failed to load data: %s", e)
            state.update({"step_status": "failed", "step_error": str(e)})

        finally:
            return state

    # --------------------------------------------------------------------------------------
    # Analyze Rules (Issues & Optimizations)
    # --------------------------------------------------------------------------------------

    def analyze_rules(self, state: PrioritizationState) -> PrioritizationState:
        """Calls LLM via litellm.completion to find issues and optimizations."""

        if state.get("step_status") == "failed":
            logger.warning("Skipping analysis due to previous failure.")
            return state
        
        logger.info("Analyzing Rules")
        state.update({"current_step": "rule_analysis - analyzing_rules", "step_status": "pending"})
        
        content = ""
        try:
            response = call_llm_with_user_prompt(
                prompt_name="rule_analysis_prompt",
                format_params={
                    "rules": state["rules_raw"],
                    "client_keywords": state.get("keywords_raw", ""),
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
                    "iteration": state.get("analysis_iteration_count", 0),
                    "feedback": state["user_feedback"]
                })
                
            logger.info("Analysis complete.")
            state["step_status"] = "success"

        except Exception as e:
            state["analysis_report"] = {"error": str(e)}
            logger.info(content)
            logger.error(f"Analysis failed: {e}")
            state.update({
                "step_status": "failed",
                "step_error": str(e)
            })
        
        finally:
            state["analysis_iteration_count"] = state.get("analysis_iteration_count", 0) + 1
            return state

        

    # --------------------------------------------------------------------------------------
    # Human Gatekeeper (Review & Feedback)
    # --------------------------------------------------------------------------------------

    def human_gatekeeper(self, state: PrioritizationState) -> PrioritizationState:
        """Interrupts the flow for user review using LangGraph interrupt()."""

        if state.get("step_status") == "failed":
            return state
        
        try:
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
                        "allowed_decisions": ["approve", "edit", "reject", "quit", "skip"]
                    }
                ]
            }
            
            response = interrupt(interrupt_payload)
            
            decisions = response.get("decisions", [])
            if decisions:
                decision = decisions[0]
                state["review_decision"] = decision.get("type")
                
                if decision["type"] == "reject":
                    state["user_feedback"] = decision.get("message", "")

                elif decision["type"] == "edit":
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

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            # Check if it's a LangGraph Interrupt (which should be allowed to propagate)
            if "Interrupt" in type(e).__name__:
                raise e
            logger.error(f"Human gatekeeper failed: {e}")
            state["step_status"] = "failed"
            state["step_error"] = str(e)
        
        return state

    # --------------------------------------------------------------------------------------
    # Apply Optimizations (If Approved)
    # --------------------------------------------------------------------------------------

    def apply_optimizations(self, state: PrioritizationState) -> PrioritizationState:
        """Applies suggested optimizations from the report to rules_raw if approved."""
        if state.get("step_status") == "failed" or state.get("review_decision") != "approve":
            return state

        logger.info("Applying AI Optimizations to rules_raw")
        report = state.get("analysis_report", {})
        optimizations = report.get("optimizations", [])
        
        rules_content = state.get("rules_raw", "")
        
        if optimizations:
            applied_count = 0
            # Sort optimizations by original text length descending to avoid partial matches
            sorted_opts = sorted(optimizations, key=lambda x: len(x.get("original_text", "")), reverse=True)
            
            for opt in sorted_opts:
                original = opt.get("original_text", "").strip()
                suggested = opt.get("suggested_text", "").strip()
                
                if original and suggested and original in rules_content:
                    rules_content = rules_content.replace(original, suggested)
                    applied_count += 1
            
            logger.info(f"Applied {applied_count} optimizations.")
        else:
            logger.info("No optimizations to apply.")
        
        state["transformed_rules"] = rules_content
        return state

    # --------------------------------------------------------------------------------------
    # Skip Optimizations (Carry forward original rules)
    # --------------------------------------------------------------------------------------

    def skip_optimizations(self, state: PrioritizationState) -> PrioritizationState:
        """Carries forward raw rules as transformed rules when analysis is skipped."""
        logger.info("Skipping optimizations - using raw rules as transformed rules")
        state["transformed_rules"] = state.get("rules_raw", "")
        return state

    # --------------------------------------------------------------------------------------
    # Save to CSV
    # --------------------------------------------------------------------------------------

    def save_to_excel(self, state: PrioritizationState) -> PrioritizationState:
        """Saves the analysis report to an Excel file with separate sheets for optimizations and issues."""

        if state.get("step_status") == "failed":
            return state
        
        logger.info("Saving analysis report")
        state.update({
            "current_sub_step": "Saving Analysis Report"
        })
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            report_dir = os.path.join(state["directory"], "analysis_reports")
            os.makedirs(report_dir, exist_ok=True)
            
            report_path = os.path.join(report_dir, f"rule_analysis_{timestamp}_{state['model'].split('/')[-1]}.xlsx")
            
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
            state["step_status"] = "success"
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            state["step_status"] = "error"
            state["step_error"] = str(e)
        
        finally:
            return state