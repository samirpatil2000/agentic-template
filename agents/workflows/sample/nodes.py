import json
import os
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage


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
            Updated state with processed input
        """
        print("Processing input")
        user_input = state.get("user_input", {})
        
        # Extract content from user input
        content = user_input.get("content", "")
        input_type = user_input.get("type", "text")
        role = user_input.get("role", "user")
        
        # Parse content if it's JSON string
        try:
            if isinstance(content, str) and content.startswith("{"):
                parsed_content = json.loads(content)
                prompt = parsed_content.get("prompt", content)
            else:
                prompt = content
        except json.JSONDecodeError:
            prompt = content
        
        if not prompt or not prompt.strip():
            raise ValueError("Empty or invalid prompt provided")
        
        human_message = HumanMessage(content=prompt)
        
        # Update state
        updated_state = state.copy()
        updated_state["messages"] = state.get("messages", []) + [human_message]
        updated_state["current_step"] = "input_processed"
        updated_state["workflow_data"] = {
            **state.get("workflow_data", {}),
            "processed_prompt": prompt,
            "input_type": input_type,
            "role": role
        }
        
        return updated_state
    
    def llm_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Call LLM with processed input
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with LLM response
        """
        print("Calling LLM")
        messages = state.get("messages", [])

        print(f"Messages: {messages}")
        
        if not messages:
            raise ValueError("No messages found in state")
        
        try:
            # Call LLM
            response = self.llm.invoke(messages)
            
            # Create AI message
            ai_message = AIMessage(content=response.content)
            
            # Update state
            updated_state = state.copy()
            updated_state["messages"] = messages + [ai_message]
            updated_state["current_step"] = "llm_completed"
            updated_state["workflow_data"] = {
                **state.get("workflow_data", {}),
                "llm_response": response.content,
                "tokens_used": getattr(response, 'usage', {}).get('total_tokens', 0) if hasattr(response, 'usage') else 0
            }
            
            return updated_state
            
        except Exception as e:
            # Handle LLM errors
            error_message = f"LLM processing failed: {str(e)}"
            
            updated_state = state.copy()
            updated_state["current_step"] = "error"
            updated_state["workflow_data"] = {
                **state.get("workflow_data", {}),
                "error": error_message
            }
            
            raise ValueError(error_message)