import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from logging.handlers import RotatingFileHandler
from contextvars import ContextVar

# Define context variables for storing request-specific information
request_var = ContextVar("request", default=None)
trace_id_var = ContextVar("trace_id", default=None)
tenant_id_var = ContextVar("tenant_id", default=None)
user_id_var = ContextVar("user_id", default=None)
session_id_var = ContextVar("session_id", default=None)

# Check for concise logging mode from environment variables
CONCISE_LOGGING = os.environ.get("CONCISE_LOGGING", "false").lower() == "true"


class ContextLoggingFormatter(logging.Formatter):
    """Custom Formatter that formats logs as JSON or concise string, including context variables."""

    def format(self, record):
        # Retrieve context values
        request = request_var.get()
        trace_id = trace_id_var.get()
        tenant_id = tenant_id_var.get()
        user_id = user_id_var.get()
        session_id = session_id_var.get()

        # Compute timestamp in IST (UTC+5:30) to match cosmos project behavior
        ist_time = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        
        # Translate level name if needed
        level_str = record.levelname.lower()
        if level_str == "warning":
            level_str = "warn"

        msg = record.getMessage()

        # Concise logging format for development
        if CONCISE_LOGGING:
            parts = [
                ist_time.strftime("%Y-%m-%d %H:%M:%S"),
                level_str.upper(),
                msg
            ]
            if request:
                parts.append(f"{request.method} {request.url.path}")
            
            status_code = getattr(record, "status_code", None)
            if status_code is not None:
                parts.append(f"status={status_code}")
                
            return " | ".join(parts)

        # Standard JSON logging format for production
        log_data = {
            "level": level_str,
            "ts": ist_time.isoformat(),
            "msg": msg,
            "platform": "agentic-template"
        }

        # Inject context variables
        if trace_id:
            log_data["traceId"] = trace_id
        if tenant_id:
            log_data["tenantId"] = tenant_id
        if user_id:
            log_data["userId"] = user_id
        if session_id:
            log_data["sessionId"] = session_id

        if request:
            log_data["method"] = request.method
            log_data["path"] = request.url.path
            if request.headers.get("host"):
                log_data["host"] = request.headers.get("host")
            if request.headers.get("x-caller"):
                log_data["caller"] = request.headers.get("x-caller")

        # Standard log record properties to exclude from extra payload
        standard_attrs = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msg', 'name', 'pathname', 'process', 'processName',
            'relativeCreated', 'stack_info', 'thread', 'threadName', 'taskName',
            'status_code', 'process_time', 'data'
        }

        # Gather custom extra fields
        for key, val in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                log_data[key] = val

        # Explicitly support standard cosmos fields attached to record
        for attr in ("process_time", "status_code", "data"):
            val = getattr(record, attr, None)
            if val is not None:
                log_data[attr] = val

        # Format exception if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class CustomLogger(logging.Logger):
    """Custom Logger class to support keyword logging parameters matching cosmos API."""

    def _log_with_extra(self, level_fn, msg, args, kwargs):
        extra = kwargs.pop("extra", {}) or {}
        
        # Extract cosmos-style keywords and add to extra dict
        for key in ["data", "process_time", "status_code", "tenant_id", "user_id", "session_id"]:
            if key in kwargs:
                extra[key] = kwargs.pop(key)
                
        kwargs["extra"] = extra
        level_fn(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log_with_extra(super().info, msg, args, kwargs)

    def error(self, msg, *args, **kwargs):
        self._log_with_extra(super().error, msg, args, kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log_with_extra(super().warning, msg, args, kwargs)

    def exception(self, msg, *args, **kwargs):
        self._log_with_extra(super().exception, msg, args, kwargs)


# Register CustomLogger as default logger class
logging.setLoggerClass(CustomLogger)


def setup_logging():
    """Initializes logging configurations for standard output and rotated file logs."""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Define console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ContextLoggingFormatter())

    # Define rotating file handler (max 20MB, 3 backup files)
    file_handler = RotatingFileHandler(
        "logs/logs.log", maxBytes=20 * 1024 * 1024, backupCount=3
    )
    file_handler.setFormatter(ContextLoggingFormatter())

    # Get root logger and configure
    root_logger = logging.getLogger()
    
    # Remove existing handlers to prevent duplication
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Force uvicorn and fastapi logs to propagate to root so they get our custom formatting
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        l = logging.getLogger(logger_name)
        l.handlers = []
        l.propagate = True


# Initialize logger configuration
setup_logging()

# Export a default logger instance
logger = logging.getLogger("custom_logger")