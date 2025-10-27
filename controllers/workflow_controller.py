from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from agents.orchestrator import WorkflowOrchestrator
from agents.workflows.index import WorkflowMessage
from concurrent.futures import ThreadPoolExecutor
import asyncio
from functools import partial


class WorkflowRequest(BaseModel):
    content: str
    type: str
    role: str


workflow_router = APIRouter(prefix="/workflows", tags=["workflows"])

orchestrator = WorkflowOrchestrator()
executor = ThreadPoolExecutor(max_workers=4)


@workflow_router.post("/{workflow_name}")
async def start_workflow(workflow_name: str, request_data: WorkflowRequest) -> Dict[str, Any]:
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
        
        # Start workflow using executor to avoid blocking
        loop = asyncio.get_event_loop()
        start_func = partial(orchestrator.start, workflow_name, message)
        result = await loop.run_in_executor(executor, start_func)
        
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
async def continue_workflow(workflow_name: str, thread_id: str, request_data: WorkflowRequest) -> Dict[str, Any]:
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
        
        # Continue workflow using executor to avoid blocking
        loop = asyncio.get_event_loop()
        chat_func = partial(orchestrator.chat, workflow_name, thread_id, message)
        result = await loop.run_in_executor(executor, chat_func)
        
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
async def get_workflow_state(workflow_name: str, thread_id: str) -> Dict[str, Any]:
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
        
        # Get workflow state using executor to avoid blocking
        loop = asyncio.get_event_loop()
        get_state_func = partial(orchestrator.get_state, workflow_name, thread_id)
        result = await loop.run_in_executor(executor, get_state_func)
        
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
async def get_available_workflows() -> Dict[str, Any]:
    """Get list of available workflows
    
    Returns:
        JSON response with list of available workflow names
    """
    try:
        # Get available workflows using executor to avoid blocking
        loop = asyncio.get_event_loop()
        get_workflows_func = partial(orchestrator.get_available_workflows)
        workflows = await loop.run_in_executor(executor, get_workflows_func)
        
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