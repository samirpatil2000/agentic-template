from flask import Blueprint, request, jsonify
from typing import Dict, Any
from agents.orchestrator import WorkflowOrchestrator
from agents.workflows.index import WorkflowMessage


workflow_bp = Blueprint('workflows', __name__, url_prefix='/workflows')

orchestrator = WorkflowOrchestrator()


@workflow_bp.route('/<workflow_name>', methods=['POST'])
def start_workflow(workflow_name: str) -> Dict[str, Any]:
    """Start a new workflow instance
    
    Args:
        workflow_name: Name of the workflow to start
        
    Returns:
        JSON response with workflow state and thread_id
    """
    try:
        # Validate request data
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Request must be JSON',
                'error': 'Invalid content type'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['content', 'type', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}',
                    'error': 'Validation error'
                }), 400
        
        message = WorkflowMessage(
            content=data['content'],
            type=data['type'],
            role=data['role']
        )
        
        # Start workflow
        result = orchestrator.start(workflow_name, message)
        
        # Return appropriate status code based on result
        status_code = 200 if result['status'] == 'started' else 500
        
        return jsonify(result), status_code
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error': 'Invalid workflow name'
        }), 404
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(e)
        }), 500


@workflow_bp.route('/<workflow_name>/<thread_id>', methods=['POST'])
def continue_workflow(workflow_name: str, thread_id: str) -> Dict[str, Any]:
    """Continue an existing workflow instance with new input
    
    Args:
        workflow_name: Name of the workflow
        thread_id: Thread ID of the workflow instance
        
    Returns:
        JSON response with updated workflow state
    """
    try:
        # Validate request data
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Request must be JSON',
                'error': 'Invalid content type'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['content', 'type', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}',
                    'error': 'Validation error'
                }), 400
        
        # Validate thread_id
        if not thread_id or not thread_id.strip():
            return jsonify({
                'status': 'error',
                'message': 'Invalid thread_id',
                'error': 'Thread ID cannot be empty'
            }), 400
        
        # Create workflow message
        message = WorkflowMessage(
            content=data['content'],
            type=data['type'],
            role=data['role']
        )
        
        # Continue workflow
        result = orchestrator.chat(workflow_name, thread_id, message)
        
        # Return appropriate status code based on result
        if result['status'] == 'continued':
            status_code = 200
        elif result['status'] == 'error' and 'not found' in result.get('error', '').lower():
            status_code = 404
        else:
            status_code = 500
        
        return jsonify(result), status_code
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error': 'Invalid workflow name or thread_id'
        }), 404
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(e)
        }), 500


@workflow_bp.route('/<workflow_name>/<thread_id>/state', methods=['GET'])
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
            return jsonify({
                'status': 'error',
                'message': 'Invalid thread_id',
                'error': 'Thread ID cannot be empty'
            }), 400
        
        # Get workflow state
        result = orchestrator.get_state(workflow_name, thread_id)
        
        # Return appropriate status code based on result
        if result['status'] == 'found':
            status_code = 200
        elif result['status'] == 'not_found':
            status_code = 404
        else:
            status_code = 500
        
        return jsonify(result), status_code
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error': 'Invalid workflow name'
        }), 404
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(e)
        }), 500


@workflow_bp.route('/available', methods=['GET'])
def get_available_workflows() -> Dict[str, Any]:
    """Get list of available workflows
    
    Returns:
        JSON response with list of available workflow names
    """
    try:
        workflows = orchestrator.get_available_workflows()
        
        return jsonify({
            'status': 'success',
            'workflows': workflows,
            'message': f'Found {len(workflows)} available workflows'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve available workflows',
            'error': str(e)
        }), 500


@workflow_bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'error': 'The requested resource does not exist'
    }), 404


@workflow_bp.errorhandler(405)
def method_not_allowed_error(error):
    """Handle 405 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Method not allowed',
        'error': 'The HTTP method is not allowed for this endpoint'
    }), 405


@workflow_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'error': 'An unexpected error occurred'
    }), 500