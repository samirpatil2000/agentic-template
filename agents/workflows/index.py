import os
from abc import ABC, abstractmethod
from typing import TypedDict, Any, Dict, Optional
from dataclasses import dataclass

from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.graph import MermaidDrawMethod
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage
from psycopg import Connection
from psycopg.rows import dict_row

from agents.postgres import get_connection_pool
from agents.resilient_postgres_saver import ResilientPostgresSaver
from dotenv import load_dotenv

load_dotenv()


def create_checkpointer():
    """Create checkpointer based on DATABASE_TYPE environment variable"""
    database_type = os.getenv("DATABASE_TYPE", "inmemory").lower()
    if database_type != "postgres":
        return MemorySaver()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Warning: DATABASE_URL not set, falling back to MemorySaver")
        return MemorySaver()

    try:
        conn_pool = get_connection_pool(database_url)
        checkpointer = ResilientPostgresSaver(conn=conn_pool)
        checkpointer.setup()
        print("ResilientPostgresSaver initialized successfully")
        return checkpointer
    except Exception as e:
        print(f"Warning: Failed to create ResilientPostgresSaver ({e}), falling back to MemorySaver")
        return MemorySaver()


class BaseWorkflowState(TypedDict):
    """Base state structure for all workflows"""
    messages: list[BaseMessage]
    user_input: Optional[Dict[str, Any]]
    current_step: str
    thread_id: Optional[str]
    workflow_data: Optional[Dict[str, Any]]


@dataclass
class WorkflowMessage:
    """Structured message for workflow communication"""
    content: str
    type: str
    role: str


class BaseWorkflowInterface(ABC):
    """Abstract base class for all workflows"""
    
    def __init__(self):
        self.initial_message = None
        self.checkpointer = create_checkpointer()
        self.graph: Optional[StateGraph] = None
        self.workflow_instance = None
    
    @abstractmethod
    def init(self) -> None:
        """Initialize the workflow graph and compile it"""
        pass
    
    @abstractmethod
    def _initialize_graph(self) -> None:
        """Build the workflow graph structure"""
        pass
    
    def save_state(self, thread_id: str, state: BaseWorkflowState) -> None:
        """Save workflow state using checkpointer"""
        # State is automatically saved by langgraph checkpointer
        pass

    def _save_workflow_diagram(self, file_path: str):
        try:
            self.mermaidimg = self.workflow_instance.get_graph().draw_mermaid_png(
                draw_method=MermaidDrawMethod.API,
            )
            folder_name = os.path.basename(file_path)
            output_file_path = os.path.join(file_path, f"{folder_name}-workflow-diagram.png")
            with open(output_file_path, "wb") as f:
                f.write(self.mermaidimg)
        except Exception:
            pass
    
    def resume_workflow(self, thread_id: str, message: WorkflowMessage) -> Dict[str, Any]:
        """Resume workflow from saved state with new input"""
        if not self.workflow_instance:
            raise ValueError("Workflow not initialized")

        config: RunnableConfig = RunnableConfig(
            configurable={
                "thread_id": thread_id,
            },
        )

        # Get the current interrupted state
        curr_state = self.workflow_instance.get_state(config)
        
        if not curr_state:
            raise ValueError(f"No workflow state found for thread_id: {thread_id}")

        # If workflow is already completed (no next steps), return current state
        if not curr_state.next:
            return self._serialize_result(curr_state.values)

        # Prepare the state for resumption with existing values
        values = curr_state.values.copy() if curr_state.values else {}
        values["is_processing"] = True

        # Initialize messages list if it doesn't exist
        if "messages" not in values:
            values["messages"] = []

        # Add new message to existing messages if provided
        if message:
            user_message = BaseMessage(
                content=message.content,
                type=message.type,
                role=message.role
            )
            values["messages"].append(user_message)

        # Update the state with the appended messages
        self.workflow_instance.update_state(config=config, values=values)
        
        # Continue workflow execution
        result = self.workflow_instance.invoke(None, config=config)
        
        return self._serialize_result(result)
    
    def start_workflow(self, message: WorkflowMessage, thread_id: str) -> Dict[str, Any]:
        """Start a new workflow instance"""
        if not self.workflow_instance:
            raise ValueError("Workflow not initialized")

        config: RunnableConfig = RunnableConfig(
            configurable={
                "thread_id": thread_id,
            },
        )

        # Initialize state with empty messages array
        initial_state = {
            "messages": [],
            "user_input": {"content": message.content, "type": message.type, "role": message.role},
            "current_step": "start",
            "thread_id": thread_id,
            "session_id": thread_id,
            "workflow_data": {},
            "is_processing": True,
        }

        # Add initial message if provided
        if message:
            initial_message = BaseMessage(
                content=message.content,
                type=message.type,
                role=message.role,
            )
            initial_state["messages"].append(initial_message)
        
        result = self.workflow_instance.invoke(initial_state, config=config)
        return self._serialize_result(result)
    
    def get_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow state"""
        if not self.workflow_instance:
            return None
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            state = self.workflow_instance.get_state(config)
            if state and state.values:
                return self._serialize_result(state.values)
            return None
        except Exception:
            return None
    
    def chat_update(self, thread_id: str, message: WorkflowMessage) -> Dict[str, Any]:
        """Handle chat updates in workflow"""
        return self.resume_workflow(thread_id, message)

    def _serialize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert workflow result to JSON-serializable format"""
        if not isinstance(result, dict):
            return {"raw_result": str(result)}
        
        serialized = {}
        for key, value in result.items():
            if key == "messages":
                # Convert BaseMessage objects to dictionaries
                serialized[key] = []
                if isinstance(value, list):
                    for msg in value:
                        if hasattr(msg, 'content') and hasattr(msg, 'type'):
                            serialized[key].append({
                                "content": msg.content,
                                "type": msg.type,
                                "role": getattr(msg, 'role', 'unknown')
                            })
                        else:
                            serialized[key].append(str(msg))
                else:
                    serialized[key] = str(value)
            elif isinstance(value, (str, int, float, bool, type(None))):
                serialized[key] = value
            elif isinstance(value, dict):
                serialized[key] = self._serialize_result(value)
            elif isinstance(value, list):
                serialized[key] = [self._serialize_result(item) if isinstance(item, dict) else str(item) for item in value]
            else:
                serialized[key] = str(value)
        
        return serialized