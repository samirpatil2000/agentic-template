import os
from typing import Dict, Any
from langchain_core.messages import BaseMessage
import litellm

from agents.workflows.sample.prompts import get_system_prompt, get_company_summary_prompt
from tools.exceptions import Exceptions
from utils.json_parser import safe_json_parse, safe_json_dumps, validate_json_structure
from utils.llm_utils import validate_llm_response


class SampleWorkflowNodes:
    """Defines logic for each node in the sample workflow"""
    
    def __init__(self):
        # Initialize LiteLLM with minimal configuration
        # Uses environment variables for API keys (OPENAI_API_KEY, GEMINI_API_KEY etc.)
        self.model = "gemini/gemini-2.5-pro"
        self.temperature = 0.7

    def fetch_context_and_questions_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate user input

        Args:
            state: Current workflow state

        Returns:
            Partial state update with only changed fields
        """
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        # Safely parse and validate JSON from last message content
        user_input = {}
        if last_message and hasattr(last_message, 'content'):
            user_input = safe_json_parse(last_message.content)

        try:
            validated_input = validate_json_structure(
                user_input, 
                required_fields=["company_url"],
                optional_fields=["prompt"]
            )
            company_url = validated_input["company_url"]
        except Exception as e:
            raise ValueError(f"Invalid user input structure: {str(e)}")

        litellm_messages = [
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": get_company_summary_prompt(company_url)}
        ]

        try:
            response = litellm.completion(
                model=self.model,
                api_key=os.environ.get("GEMINI_API_KEY"),
                messages=litellm_messages,
                temperature=self.temperature
            )

            # Validate response using utility function
            response_content = validate_llm_response(response, require_content=True)
            response_content = safe_json_parse(response_content)
            new_message = BaseMessage(
                role="ai",
                type="fetch_context_and_questions_node",
                content=safe_json_dumps({"org_context": response_content}),
            )
        except Exception as e:
            print(f"Error calling LLM in fetch_context_and_questions_node: {e}")
            raise Exceptions.general_exception(500, f"Failed to process company context: {str(e)}")

        updated_messages = messages.copy()
        updated_messages.append(new_message)

        return {
            "current_step": "fetch_context_and_questions_node",
            "workflow_data": {
                **state.get("workflow_data", {}),
                "processed_prompt": user_input.get("prompt")
            },
            "org_context": response_content,
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

            print(f"Sending messages to LLM: {litellm_messages}")

            litellm_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"}
            ]

            response = litellm.completion(
                model=self.model,
                api_key=os.environ.get("GEMINI_API_KEY"),
                messages=litellm_messages,
                temperature=self.temperature
            )

            # Validate response using utility function
            response_content = validate_llm_response(response, require_content=True)

            final_message = BaseMessage(
                role="ai",
                type="next_node_response",
                content=safe_json_dumps({"final_response": response_content}),
            )

            # Get existing messages and append new one
            updated_messages = messages.copy()
            updated_messages.append(final_message)

            return {
                "current_step": "llm_completed",
                "messages": updated_messages,
                "workflow_data": {
                    **state.get("workflow_data", {}),
                    "llm_response": response.choices[0].message.content
                }
            }
            
        except Exception as e:
            print(f"Error in next_node: {e}")
            raise Exceptions.general_exception(500, str(e))