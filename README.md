# FastAPI + LangGraph Workflow Orchestration Template

A starter template for building AI-driven workflow orchestration systems using FastAPI and LangGraph. This project provides a modular foundation with state management, persistence, and REST APIs so you can quickly prototype and extend your own workflows.

## Features

- FastAPI-based REST API endpoints for workflow management
- LangGraph integration for AI workflow orchestration
- Modular, extensible workflow architecture
- Built-in state management and checkpointing
- PostgreSQL-backed workflow persistence
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

2. Access the API at:
```
http://localhost:<port>
```

## API Endpoints

- `GET /` — API information and available endpoints
- `POST /workflows/{workflow_name}` — Start a new workflow
- `POST /workflows/{workflow_name}/{thread_id}` — Continue an existing workflow
- `GET /workflows/{workflow_name}/{thread_id}` — Get workflow state

## Notes

- This repository is a template intended for customization. Replace example workflows, models, and configuration with your own domain logic.
- Consider adding authentication, rate limiting, and observability for production deployments.
