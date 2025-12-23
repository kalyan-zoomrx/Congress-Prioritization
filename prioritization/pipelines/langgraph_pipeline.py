from langgraph.graph import StateGraph, END
from prioritization.utils.state import PrioritizationState
from prioritization.components.prioritization_nodes import PrioritizationNodes

def create_prioritization_pipeline():
    nodes = PrioritizationNodes()
    workflow = StateGraph(PrioritizationState)

    workflow.add_node("load_data", nodes.load_data)
    workflow.add_node("parse_rules", nodes.parse_rules)
    workflow.add_node("validate", nodes.validate_rules)
    workflow.add_node("save_output", nodes.save_output)

    workflow.set_entry_point("load_data")
    workflow.add_edge("load_data", "parse_rules")
    workflow.add_edge("parse_rules", "validate")

    def router(state: PrioritizationState):
        if state["validation_errors"] and state["iteration_count"] < 3:
            return "parse_rules"
        return "save_output"

    workflow.add_conditional_edges("validate", router)
    workflow.add_edge("save_output", END)
    
    return workflow.compile()
