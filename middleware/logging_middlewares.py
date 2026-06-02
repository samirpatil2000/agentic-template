import json
import uuid
from time import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from tools.logger_config import (
    logger,
    request_var,
    trace_id_var,
    tenant_id_var,
    user_id_var,
    session_id_var,
)


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts or generates a Trace ID to correlation logs across services."""

    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response


class AddRequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware that binds request-level attributes to thread/async ContextVars."""

    async def dispatch(self, request: Request, call_next):
        # Retrieve trace, tenant, user, and session IDs from request state or headers
        trace_id = getattr(request.state, "trace_id", None) or request.headers.get("x-trace-id")
        tenant_id = getattr(request.state, "tenant_id", None) or request.headers.get("x-tenant-id")
        user_id = getattr(request.state, "user_id", None) or request.headers.get("x-user-id")
        session_id = getattr(request.state, "session_id", None) or request.headers.get("x-session-id")

        # Set the context variables for the current task/thread
        token_req = request_var.set(request)
        token_trace = trace_id_var.set(trace_id)
        token_tenant = tenant_id_var.set(tenant_id)
        token_user = user_id_var.set(user_id)
        token_session = session_id_var.set(session_id)

        try:
            response = await call_next(request)
        finally:
            # Reset context variables to clean up context memory
            request_var.reset(token_req)
            trace_id_var.reset(token_trace)
            tenant_id_var.reset(token_tenant)
            user_id_var.reset(token_user)
            session_id_var.reset(token_session)

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs HTTP request execution times, response statuses, and errors."""

    async def dispatch(self, request: Request, call_next):
        start_time = time()
        body = None

        # Bypass performance logging for health/metrics endpoints to keep logs clean
        if request.url.path in {"/health", "/_Health", "/metrics"}:
            return await call_next(request)

        tenant_id = getattr(request.state, "tenant_id", None) or request.headers.get("x-tenant-id", "unknown")
        user_id = getattr(request.state, "user_id", None) or request.headers.get("x-user-id", "unknown")

        # Safely extract the request body for tracing mutations
        if request.method in {"POST", "PUT", "PATCH"}:
            try:
                # To prevent consumption of the request stream, we could read it if needed.
                # However, Starlette's request.body() can block or consume stream,
                # so we can parse it dynamically or skip body logs to avoid stream issues.
                # In cosmos, they did: body = await request.body() and parsed it.
                # Note: Reading request.body() in a middleware can block route parameters,
                # but cosmos uses it. Let's keep it safe by wrapping it.
                body_bytes = await request.body()
                if body_bytes:
                    body = json.dumps(json.loads(body_bytes.decode("utf-8")))
            except Exception:
                body = None

        try:
            response = await call_next(request)
            process_time = round((time() - start_time) * 1000, 2)

            log_msg = f"Request completed for {request.url.path} with status code {response.status_code} in {process_time} ms"
            if request.url.query:
                log_msg = f"Request completed for {request.url.path}?{request.url.query} with status code {response.status_code} in {process_time} ms"

            logger.info(
                log_msg,
                process_time=process_time,
                status_code=response.status_code,
                tenant_id=tenant_id,
                user_id=user_id,
            )
            return response

        except Exception as e:
            process_time = round((time() - start_time) * 1000, 2)
            logger.error(
                f"Error processing request for {request.url.path}: {str(e)}",
                data={
                    "body": body,
                    "error": str(e),
                    "process_time": process_time,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                },
            )
            raise
