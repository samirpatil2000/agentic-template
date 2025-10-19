from typing import Dict, Any, List
from langchain_core.messages import BaseMessage


def merge_partial_state_update(current_state: Dict[str, Any], partial_update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge partial state update into current state with special handling for messages.
    
    Args:
        current_state: The existing workflow state
        partial_update: Dictionary containing only the fields to update
        
    Returns:
        Merged state with partial updates applied
        
    Special behaviors:
    - messages: Appends new messages to existing message history
    - Other fields: Replaces existing values with new values
    - New fields: Adds them to the state
    - Immutable fields like thread_id are preserved from current_state
    """
    if not current_state:
        current_state = {}
    
    # Start with a copy of current state
    merged_state = current_state.copy()
    
    # Handle each field in the partial update
    for key, value in partial_update.items():
        if key == "messages" and isinstance(value, list):
            # Special handling for messages - append to existing messages
            existing_messages = merged_state.get("messages", [])
            
            # Ensure existing_messages is a list
            if not isinstance(existing_messages, list):
                existing_messages = []
            
            # Append new messages to existing ones
            merged_state["messages"] = existing_messages + value
            
        elif key == "workflow_data" and isinstance(value, dict):
            # Special handling for workflow_data - merge dictionaries
            existing_workflow_data = merged_state.get("workflow_data", {})
            if isinstance(existing_workflow_data, dict):
                merged_workflow_data = existing_workflow_data.copy()
                merged_workflow_data.update(value)
                merged_state["workflow_data"] = merged_workflow_data
            else:
                merged_state["workflow_data"] = value
                
        elif key in ["thread_id", "session_id"] and key in current_state:
            # Preserve immutable fields from current state if they exist
            # Don't override with partial update values
            continue
            
        else:
            # For all other fields, replace with new value
            merged_state[key] = value
    
    return merged_state


def create_message_from_dict(message_data: Dict[str, Any]) -> BaseMessage:
    """
    Create a BaseMessage object from dictionary data.
    
    Args:
        message_data: Dictionary with message content, type, and role
        
    Returns:
        BaseMessage object
    """
    return BaseMessage(
        content=message_data.get("content", ""),
        type=message_data.get("type", "message"),
        role=message_data.get("role", "user")
    )


def prepare_messages_for_update(messages: List[Any]) -> List[BaseMessage]:
    """
    Convert various message formats to BaseMessage objects.
    
    Args:
        messages: List of messages in various formats (dict, BaseMessage, etc.)
        
    Returns:
        List of BaseMessage objects
    """
    prepared_messages = []
    
    for msg in messages:
        if isinstance(msg, BaseMessage):
            prepared_messages.append(msg)
        elif isinstance(msg, dict):
            prepared_messages.append(create_message_from_dict(msg))
        else:
            # Try to convert other formats to string and create a basic message
            prepared_messages.append(BaseMessage(
                content=str(msg),
                type="message",
                role="unknown"
            ))
    
    return prepared_messages