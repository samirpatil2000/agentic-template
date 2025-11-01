import os
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from agents.workflows.index import BaseWorkflowInterface, BaseWorkflowState
from agents.workflows.sample.nodes import SampleWorkflowNodes


class WorkflowState(BaseWorkflowState):
    """Extended state for Sample Workflow"""
    org_context: Dict[str, Any] = {}
    pass

class SampleWorkflow(BaseWorkflowInterface):
    """Sample workflow implementation demonstrating basic workflow pattern"""
    
    def __init__(self):
        super().__init__()
        self.sample_workflow_nodes = None
        self.graph = None
        self.workflow_instance = None
    
    def init(self) -> None:
        """Initialize the sample workflow
        
        Sets up workflow nodes, creates the state graph, initializes the graph structure,
        and compiles the workflow instance with checkpointer and interrupts.
        """
        # Initialize workflow nodes
        self.sample_workflow_nodes = SampleWorkflowNodes()
        
        # Create state graph
        self.graph = StateGraph(WorkflowState)
        
        # Initialize graph structure
        self._initialize_graph()
        
        # Compile workflow with checkpointer and interrupts
        self.workflow_instance = self.graph.compile(
            checkpointer=self.checkpointer,
            interrupt_after=[],
            interrupt_before=["next_node"]
        )

        self._save_workflow_diagram(os.path.dirname(__file__))

    
    def _initialize_graph(self) -> None:
        """Build the workflow graph structure
        
        Adds nodes for processing input and LLM interaction, sets entry point,
        and defines the flow between nodes ending at END.
        """
        # Add workflow nodes
        self.graph.add_node("fetch_context_and_questions", self.sample_workflow_nodes.fetch_context_and_questions_node)
        self.graph.add_node("next_node", self.sample_workflow_nodes.next_node)
        
        # Set an entry point
        self.graph.set_entry_point("fetch_context_and_questions")
        
        self.graph.add_edge("fetch_context_and_questions", "next_node")
        self.graph.add_edge("next_node", END)