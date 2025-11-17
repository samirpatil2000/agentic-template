# FastAPI + LangGraph Workflow Orchestration Template

A starter template for building AI-driven workflow orchestration systems using FastAPI and LangGraph. This project provides a modular foundation with state management, persistence, and REST APIs so you can quickly prototype and extend your own workflows.

## Features

- FastAPI-based REST API endpoints for workflow management
- LangGraph integration for AI workflow orchestration
- Modular, extensible workflow architecture
- Built-in state management and checkpointing
- PostgreSQL-backed workflow persistence
- Support for workflow interrupts and continuations
- Non-blocking concurrent workflow execution using ThreadPoolExecutor
- LLM response validation and retry utilities with LiteLLM integration

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
- Update values in `.env` to match your local setup (database URL, host, port, etc.).

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
- Using environment variables (defined in `.env`):
```bash
uvicorn app:app --reload --port $PORT --host $HOST
```

# 🧩 API Endpoints

#### `GET /`
**Description:**  
Retrieve API information and a list of available endpoints.

**Response Example:**
```json
{
  "version": "1.0",
  "endpoints": [
    "/workflows/{workflow_name}",
    "/workflows/{workflow_name}/{thread_id}"
  ]
}
```

---

#### `POST /workflows/{workflow_name}`
**Description:**  
Start a new workflow.

**Request Body:**
```json
{
  "content": "{\"company_url\": \"https://www.github.com/\"}",
  "type": "text",
  "role": "user"
}
```

**Response Example:**
```json
{
  "thread_id": "abc123",
  "status": "started",
  "workflow_name": "example_workflow"
}
```

---

#### `POST /workflows/{workflow_name}/{thread_id}`
**Description:**  
Continue an existing workflow.

**Request Body:**
```json
{
  "content": "{\"company_url\": \"https://www.github.com/\"}",
  "type": "text",
  "role": "user"
}
```

**Response Example:**
```json
{
  "thread_id": "abc123",
  "status": "in_progress",
  "message": "Workflow updated successfully"
}
```

---

#### `GET /workflows/{workflow_name}/{thread_id}`
**Description:**  
Retrieve the current state of a workflow thread.

**Response Example:**
```json
{
  "thread_id": "abc123",
  "workflow_name": "example_workflow",
  "status": "completed",
  "result": {
    "summary": "Workflow execution finished successfully"
  }
}
```

## Roadmap

Planned features and improvements:

- [ ] Add logging and log rotation in file
- [ ] Add authentication
- [ ] Add Prometheus metrics
- [ ] Add tool calling example
- [ ] Langfuse middlewares for LLM observability
- [ ] Add rate limiting
- [ ] Replace sample agent with production-ready agent/chatbot (e.g., email agent)

## Notes

- This repository is a template intended for customization. Replace example workflows, models, and configuration with your own domain logic.
- Consider adding authentication, rate limiting, and observability for production deployments.
