import os
import time
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from controllers.workflow_controller import workflow_router
from agents.resilient_postgres_saver import ResilientPostgresSaver
from agents.postgres import get_connection_pool

# 1. Define the Cleanup Function
def cleanup_old_threads(checkpointer, retention_days=7):
    """Deletes threads that haven't been active for the retention period."""
    print(f"🧹 Running cleanup: Removing threads older than {retention_days} days...")
    
    # Calculate cutoff string in ISO format (matching the 'ts' format in JSON)
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()

    # Query: Find thread_ids where the LATEST checkpoint is older than the cutoff
    # We look inside the 'checkpoint' JSONB column for the 'ts' field
    query = """
        SELECT thread_id 
        FROM checkpoints 
        GROUP BY thread_id 
        HAVING MAX(checkpoint ->> 'ts') < %s
    """
    
    old_threads = []
    # Execute query using the connection pool
    with checkpointer.conn.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (cutoff_date,))
            old_threads = cur.fetchall()

    if not old_threads:
        print("✅ No old threads found to clean up.")
        return

    print(f"Found {len(old_threads)} threads to cleanup")

    # Safely delete each thread and its history using checkpointer's delete method
    for record in old_threads:
        print(f"Deleting thread: {record[0]}")
        thread_id = record[0]
        try:
            # Use the checkpointer's built-in delete functionality
            checkpointer.delete_thread(thread_id)
            print(f"Deleted expired thread: {thread_id}")
        except Exception as e:
            print(f"Failed to delete thread {thread_id}: {e}")


# 2. Integrate into FastAPI Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with database cleanup."""
    # --- Startup ---
    print("🚀 Application starting up...")
    
    # Get database URL and connection pool if using PostgreSQL
    database_type = os.getenv("DATABASE_TYPE", "inmemory").lower()
    checkpointer = None
    
    if database_type == "postgres":
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            try:
                # Create connection pool and checkpointer
                conn_pool = get_connection_pool(database_url)
                checkpointer = ResilientPostgresSaver(conn=conn_pool)
                checkpointer.setup()
                
                # Run cleanup on startup (in a thread to avoid blocking async context)
                import threading
                cleanup_thread = threading.Thread(
                    target=cleanup_old_threads, 
                    args=(checkpointer, 7),
                    daemon=True
                )
                cleanup_thread.start()
                
                # OPTIONAL: Schedule it to run periodically (e.g., every day)
                
            except Exception as e:
                print(f"Warning: Failed to initialize cleanup task: {e}")
    
    yield
    
    # --- Shutdown ---
    print("🛑 Application shutting down...")
    # Close connection pool if it was created
    if checkpointer and hasattr(checkpointer, 'conn'):
        try:
            checkpointer.conn.close()
        except Exception as e:
            print(f"Error closing connection pool: {e}")


app = FastAPI(
    title="FastAPI Workflow Orchestration System",
    description="A workflow orchestration system built with FastAPI",
    version="1.0.0",
    lifespan=lifespan
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