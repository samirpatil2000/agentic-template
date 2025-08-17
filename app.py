from flask import Flask
from controllers.workflow_controller import workflow_bp

app = Flask(__name__)

# Register workflow blueprint
app.register_blueprint(workflow_bp)


@app.route('/')
def hello_world():
    return {
        'message': 'Flask Workflow Orchestration System',
        'version': '1.0.0',
        'endpoints': {
            'start_workflow': 'POST /workflow/{workflow_name}',
            'continue_workflow': 'POST /workflow/{workflow_name}/{thread_id}',
            'get_state': 'GET /workflow/{workflow_name}/{thread_id}/state',
            'available_workflows': 'GET /workflow/available'
        }
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)