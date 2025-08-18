import time
from datetime import datetime, timezone

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

# Store application start time
start_time = time.time()


def convert_seconds_to_hms(seconds):
    """Convert seconds to hours, minutes, seconds format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours}h {minutes}m {seconds}s"


@app.get("/health")
def health_check():
    uptime_seconds = time.time() - start_time
    health_check_response = {
        "status": "UP",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": convert_seconds_to_hms(uptime_seconds),
    }
    return health_check_response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)