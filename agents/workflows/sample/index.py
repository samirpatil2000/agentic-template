from typing import Dict, Any
from langgraph.graph import StateGraph, END
from agents.workflows.index import BaseWorkflowInterface, BaseWorkflowState
from agents.workflows.sample.nodes import SampleWorkflowNodes


class WorkflowState(BaseWorkflowState):
    """Extended state for Sample Workflow"""
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
            interrupt_before=["llm_node"]
        )
    
    def _initialize_graph(self) -> None:
        """Build the workflow graph structure
        
        Adds nodes for processing input and LLM interaction, sets entry point,
        and defines the flow between nodes ending at END.
        """
        # Add workflow nodes
        self.graph.add_node("process_input", self.sample_workflow_nodes.process_input)
        self.graph.add_node("llm_node", self.sample_workflow_nodes.llm_node)
        
        # Set entry point
        self.graph.set_entry_point("process_input")
        
        # Add edges to define workflow flow
        self.graph.add_edge("process_input", "llm_node")
        self.graph.add_edge("llm_node", END)