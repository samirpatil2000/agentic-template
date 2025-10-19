from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from agents.orchestrator import WorkflowOrchestrator
from agents.workflows.index import WorkflowMessage


class WorkflowRequest(BaseModel):
    content: str
    type: str
    role: str


workflow_router = APIRouter(prefix="/workflows", tags=["workflows"])

orchestrator = WorkflowOrchestrator()


@workflow_router.post("/{workflow_name}")
def start_workflow(workflow_name: str, request_data: WorkflowRequest) -> Dict[str, Any]:
    """Start a new workflow instance
    
    Args:
        workflow_name: Name of the workflow to start
        request_data: Workflow request data containing content, type, and role
        
    Returns:
        JSON response with workflow state and thread_id
    """
    try:
        message = WorkflowMessage(
            content=request_data.content,
            type=request_data.type,
            role=request_data.role
        )
        
        # Start workflow
        result = orchestrator.start(workflow_name, message)
        
        # Return appropriate status code based on result
        if result['status'] == 'started':
            return result
        else:
            raise HTTPException(status_code=500, detail=result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                'status': 'error',
                'message': str(e),
                'error': 'Invalid workflow name'
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': 'Internal server error',
                'error': str(e)
            }
        )


@workflow_router.post("/{workflow_name}/{thread_id}")
def continue_workflow(workflow_name: str, thread_id: str, request_data: WorkflowRequest) -> Dict[str, Any]:
    """Continue an existing workflow instance with new input
    
    Args:
        workflow_name: Name of the workflow
        thread_id: Thread ID of the workflow instance
        request_data: Workflow request data containing content, type, and role
        
    Returns:
        JSON response with updated workflow state
    """
    try:
        # Validate thread_id
        if not thread_id or not thread_id.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    'status': 'error',
                    'message': 'Invalid thread_id',
                    'error': 'Thread ID cannot be empty'
                }
            )
        
        # Create workflow message
        message = WorkflowMessage(
            content=request_data.content,
            type=request_data.type,
            role=request_data.role
        )
        
        # Continue workflow
        result = orchestrator.chat(workflow_name, thread_id, message)
        
        # Return appropriate response based on result
        if result['status'] == 'continued':
            return result
        elif result['status'] == 'error' and 'not found' in result.get('error', '').lower():
            raise HTTPException(status_code=404, detail=result)
        else:
            raise HTTPException(status_code=500, detail=result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                'status': 'error',
                'message': str(e),
                'error': 'Invalid workflow name or thread_id'
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': 'Internal server error',
                'error': str(e)
            }
        )


@workflow_router.get("/{workflow_name}/{thread_id}")
def get_workflow_state(workflow_name: str, thread_id: str) -> Dict[str, Any]:
    """Get current state of a workflow instance
    
    Args:
        workflow_name: Name of the workflow
        thread_id: Thread ID of the workflow instance
        
    Returns:
        JSON response with current workflow state
    """
    try:
        # Validate thread_id
        if not thread_id or not thread_id.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    'status': 'error',
                    'message': 'Invalid thread_id',
                    'error': 'Thread ID cannot be empty'
                }
            )
        
        # Get workflow state
        result = orchestrator.get_state(workflow_name, thread_id)
        
        # Return appropriate response based on result
        if result['status'] == 'found':
            return result
        elif result['status'] == 'not_found':
            raise HTTPException(status_code=404, detail=result)
        else:
            raise HTTPException(status_code=500, detail=result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                'status': 'error',
                'message': str(e),
                'error': 'Invalid workflow name'
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': 'Internal server error',
                'error': str(e)
            }
        )


@workflow_router.get("/available")
def get_available_workflows() -> Dict[str, Any]:
    """Get list of available workflows
    
    Returns:
        JSON response with list of available workflow names
    """
    try:
        workflows = orchestrator.get_available_workflows()
        
        return {
            'status': 'success',
            'workflows': workflows,
            'message': f'Found {len(workflows)} available workflows'
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': 'Failed to retrieve available workflows',
                'error': str(e)
            }
        )