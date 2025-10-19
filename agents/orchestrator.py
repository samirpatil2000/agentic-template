from typing import Dict, Any, Optional
import uuid
from agents.workflows.index import BaseWorkflowInterface, WorkflowMessage
from agents.workflows.sample.index import SampleWorkflow


class WorkflowOrchestrator:
    """Manages the lifecycle of workflows"""
    
    def __init__(self):
        self.workflows: Dict[str, BaseWorkflowInterface] = {}
        self._register_workflows()
    
    def _register_workflows(self) -> None:
        """Register available workflows"""
        # Initialize and register a sample workflow
        sample_workflow = SampleWorkflow()
        sample_workflow.init()
        self.workflows['sample'] = sample_workflow
    
    def start(self, workflow_name: str, message: WorkflowMessage) -> Dict[str, Any]:
        """Start a new workflow instance
        
        Args:
            workflow_name: Name of the workflow to start
            message: Initial message to process
            
        Returns:
            Dict containing workflow state and thread_id
            
        Raises:
            ValueError: If workflow name is invalid
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = self.workflows[workflow_name]
        thread_id = str(uuid.uuid4())
        
        try:
            result = workflow.start_workflow(message, thread_id)
            
            return {
                'status': 'started',
                'thread_id': thread_id,
                'workflow_name': workflow_name,
                'state': result,
                'message': 'Workflow started successfully'
            }
        except Exception as e:
            return {
                'status': 'error',
                'thread_id': thread_id,
                'workflow_name': workflow_name,
                'error': str(e),
                'message': 'Failed to start workflow'
            }
    
    def chat(self, workflow_name: str, thread_id: str, message: WorkflowMessage) -> Dict[str, Any]:
        """Continue workflow conversation with new input
        
        Args:
            workflow_name: Name of the workflow
            thread_id: Thread ID of the workflow instance
            message: New message to process
            
        Returns:
            Dict containing updated workflow state
            
        Raises:
            ValueError: If workflow name is invalid or thread_id not found
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = self.workflows[workflow_name]
        
        try:
            result = workflow.chat_update(thread_id, message)
            
            return {
                'status': 'continued',
                'thread_id': thread_id,
                'workflow_name': workflow_name,
                'state': result,
                'message': 'Workflow updated successfully'
            }
        except Exception as e:
            print(f"Error in chat: {e}")
            return {
                'status': 'error',
                'thread_id': thread_id,
                'workflow_name': workflow_name,
                'error': str(e),
                'message': 'Failed to continue workflow'
            }
    
    def get_state(self, workflow_name: str, thread_id: str) -> Dict[str, Any]:
        """Get current state of a workflow instance
        
        Args:
            workflow_name: Name of the workflow
            thread_id: Thread ID of the workflow instance
            
        Returns:
            Dict containing current workflow state
            
        Raises:
            ValueError: If workflow name is invalid
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = self.workflows[workflow_name]
        
        try:
            state = workflow.get_state(thread_id)
            
            if state is None:
                return {
                    'status': 'not_found',
                    'thread_id': thread_id,
                    'workflow_name': workflow_name,
                    'message': 'Workflow state not found'
                }
            
            return {
                'status': 'found',
                'thread_id': thread_id,
                'workflow_name': workflow_name,
                'state': state,
                'message': 'State retrieved successfully'
            }
        except Exception as e:
            return {
                'status': 'error',
                'thread_id': thread_id,
                'workflow_name': workflow_name,
                'error': str(e),
                'message': 'Failed to retrieve state'
            }
    
    def resume_workflow(self, workflow_name: str, thread_id: str, message: WorkflowMessage) -> Dict[str, Any]:
        """Resume a workflow from its saved state
        
        Args:
            workflow_name: Name of the workflow
            thread_id: Thread ID of the workflow instance
            message: Message to resume with
            
        Returns:
            Dict containing updated workflow state
            
        Raises:
            ValueError: If workflow name is invalid
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = self.workflows[workflow_name]
        
        try:
            result = workflow.resume_workflow(thread_id, message)
            
            return {
                'status': 'resumed',
                'thread_id': thread_id,
                'workflow_name': workflow_name,
                'state': result,
                'message': 'Workflow resumed successfully'
            }
        except Exception as e:
            return {
                'status': 'error',
                'thread_id': thread_id,
                'workflow_name': workflow_name,
                'error': str(e),
                'message': 'Failed to resume workflow'
            }

    def get_available_workflows(self) -> list[str]:
        """Get list of available workflow names"""
        return list(self.workflows.keys())