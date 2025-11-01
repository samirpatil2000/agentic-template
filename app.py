import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI
from controllers.workflow_controller import workflow_router

app = FastAPI(
    title="FastAPI Workflow Orchestration System",
    description="A workflow orchestration system built with FastAPI",
    version="1.0.0"
)

# Include workflow router
app.include_router(workflow_router)


@app.get("/")
def hello_world():
    return {
        'message': 'FastAPI Workflow Orchestration System',
        'version': '1.0.0',
        'endpoints': {
            'start_workflow': 'POST /workflows/{workflow_name}',
            'continue_workflow': 'POST /workflows/{workflow_name}/{thread_id}',
            'get_state': 'GET /workflows/{workflow_name}/{thread_id}/state',
            'available_workflows': 'GET /workflows/available'
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
    import uvicorn
    uvicorn.run("app:app", host='0.0.0.0', port=int(os.getenv("PORT")), reload=True)



# TODO
# - Add logging and log rotation in file
# - Add authentication
# - Add prometheus metrics
# - Add deployment dockers
# - Add tool calling example
# - Langfuse middlewares
# - Add rate limiting
# - Instead of sample agent add any simple agent / chatbot [ email agent ]
# - Add Exceptions handling