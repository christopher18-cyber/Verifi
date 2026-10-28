from langgraph.graph import StateGraph, END
from app.graph.state import ScamState
from app.graph.nodes.rules_node import run_rules_check
from app.graph.nodes.llm_node import run_llm_evaluation

# Initialize the graph workflow
workflow = StateGraph(ScamState)

# Add nodes
workflow.add_node("rules_node", run_rules_check)
workflow.add_node("llm_node", run_llm_evaluation)

# Set entry point and edges
workflow.set_entry_point("rules_node")
workflow.add_edge("rules_node", "llm_node")
workflow.add_edge("llm_node", END)

# Compile the graph
graph = workflow.compile()