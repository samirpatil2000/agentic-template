# FastAPI Workflow Orchestration System

A powerful workflow orchestration system built with FastAPI and LangGraph, designed to manage and execute AI-driven workflows with ease.

## Features

- FastAPI-based REST API endpoints for workflow management
- LangGraph integration for AI workflow orchestration
- Modular workflow system with extensible architecture
- Built-in state management and checkpointing
- PostgreSQL-based workflow persistence
- Support for workflow interrupts and continuations

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic-template
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

## Usage

1. Start the server:
   - Default port (8000):
   ```bash
   uvicorn app:app --reload
   ```
   - Custom port:
   ```bash
   uvicorn app:app --reload --port 8080
   ```
   - Using environment variables (defined in .env):
   ```bash
   uvicorn app:app --reload --port $PORT --host $HOST
   ```

2. Access the API at `http://localhost:<port>`

## API Endpoints

- `GET /` - API information and available endpoints
- `POST /workflows/{workflow_name}` - Start a new workflow
- `POST /workflows/{workflow_name}/{thread_id}` - Continue an existing workflow
- `GET /workflows/{workflow_name}/{thread_id}` - Get workflow state
- `GET /workflows/available` - List available workflows

## Project Structure

```
├── app.py                 # FastAPI application entry point
├── requirements.txt       # Project dependencies
├── agents/               
│   ├── orchestrator.py    # Workflow orchestration logic
│   └── workflows/         # Workflow implementations
│       ├── index.py      # Base workflow interfaces
│       └── sample/       # Sample workflow implementation
├── controllers/          
│   └── workflow_controller.py  # API route handlers
```

## Example cURL Commands

### Start a new workflow
```bash
curl --location 'http://localhost:8080/workflows/sample' \
--header 'Content-Type: application/json' \
--data '{"content": "{\"company_url\":\"niti.ai\"}", "type": "text", "role": "user"}'
```

### Continue an existing workflow
```bash
curl --location 'http://localhost:8080/workflows/sample/3a622774-128f-4f32-aa55-15f62d9a0c56' \
--header 'Content-Type: application/json' \
--data '{"content": "{\"userResponse\":[{\"question\":\"\",\"answer\":\"\"}]}", "type": "text", "role": "user"}'
```

### Get workflow state
```bash
curl --location 'http://localhost:8080/workflows/sample/3a622774-128f-4f32-aa55-15f62d9a0c56' \
```




## Creating New Workflows

1. Create a new directory under `agents/workflows/`
2. Implement workflow nodes in a `nodes.py` file
3. Create an `index.py` file extending `BaseWorkflowInterface`
4. Define your workflow graph structure

## Dependencies

- FastAPI (≥0.104.0)
- LangGraph (≥0.2.0)
- LangChain Core & OpenAI
- Python-dotenv
- PostgreSQL

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license information here]
