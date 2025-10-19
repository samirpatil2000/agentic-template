import json
import os
from typing import Dict, Any
from langchain_core.messages import BaseMessage


class MockLLM:
    """Mock LLM for testing when OpenAI API key is not available"""
    
    def invoke(self, messages):
        # Create a mock response based on the last message
        last_message = messages[-1] if messages else None
        if last_message and hasattr(last_message, 'content'):
            content = f"Mock LLM response to: {last_message.content}"
        else:
            content = "Mock LLM response - no input provided"
        
        class MockResponse:
            def __init__(self, content):
                self.content = content
                self.usage = {'total_tokens': 50}
        
        return MockResponse(content)


class SampleWorkflowNodes:
    """Defines logic for each node in the sample workflow"""
    
    def __init__(self):
        # Initialize LLM - use OpenAI if API key available, otherwise use mock
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    openai_api_key=api_key
                )
            else:
                print("Warning: OPENAI_API_KEY not found, using mock LLM for testing")
                self.llm = MockLLM()
        except ImportError:
            print("Warning: langchain_openai not available, using mock LLM")
            self.llm = MockLLM()

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
            type="update_strategies_node_response",
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
            response = self.llm.invoke(messages)

            final_message = BaseMessage(
                role="ai",
                type="next_node_response",
                content=json.dumps({"final_response": response.content}),
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