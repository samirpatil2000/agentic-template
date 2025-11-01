import json
import os
from typing import Dict, Any
from langchain_core.messages import BaseMessage
import litellm

class SampleWorkflowNodes:
    """Defines logic for each node in the sample workflow"""
    
    def __init__(self):
        # Initialize LiteLLM with minimal configuration
        # Uses environment variables for API keys (OPENAI_API_KEY, GEMINI_API_KEY etc.)

        self.model = "gemini/gemini-1.5-pro"
        self.temperature = 0.7

    def process_input(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate user input

        Args:
            state: Current workflow state

        Returns:
            Partial state update with only changed fields
        """
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        user_input = json.loads(last_message.content) if last_message else {}

        # Create new message to append
        new_message = BaseMessage(
            role="ai",
            type="starter_node",
            content=json.dumps({"hello": "world"}),
        )
        
        # Get existing messages and append new one
        updated_messages = messages.copy()
        updated_messages.append(new_message)

        return {
            "current_step": "input_processed",
            "workflow_data": {
                **state.get("workflow_data", {}),
                "processed_prompt": user_input.get("prompt")
            },
            "messages": updated_messages
        }

    def next_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Call LLM with processed input

        Args:
            state: Current workflow state

        Returns:
            Partial state update with only changed fields
        """
        messages = state.get("messages", [])

        if not messages:
            raise ValueError("No messages found in state")

        try:
            # Convert LangChain messages to LiteLLM format
            litellm_messages = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    # Extract role from message or default to 'user'
                    role = getattr(msg, 'role', 'user')
                    litellm_messages.append({"role": role, "content": msg.content})
            
            response = litellm.completion(
                model=self.model,
                messages=litellm_messages,
                temperature=self.temperature
            )

            final_message = BaseMessage(
                role="ai",
                type="next_node_response",
                content=json.dumps({"final_response": response.choices[0].message.content}),
            )

            # Get existing messages and append new one
            updated_messages = messages.copy()
            updated_messages.append(final_message)

            return {
                "current_step": "llm_completed",
                "messages": updated_messages,
                "workflow_data": {
                    **state.get("workflow_data", {}),
                    "llm_response": response.content
                }
            }
            
        except Exception as e:
            # Handle LLM errors
            error_message = f"LLM processing failed: {str(e)}"
            
            return {
                "current_step": "error",
                "workflow_data": {
                    **state.get("workflow_data", {}),
                    "error": error_message
                }
            }