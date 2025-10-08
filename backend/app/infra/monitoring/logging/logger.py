"""Custom logger with OpenTelemetry trace context and Datadog integration."""

import json
import logging
import logging.config
import os
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import structlog
import yaml

from app.config import Environment, MonitoringConfig

# Create a global logger instance
logger: logging.Logger = structlog.get_logger("app")


class OpenTelemetryLogProcessor:
    """Add OpenTelemetry trace context to log entries."""

    def __call__(
        self, _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        """Process log events to add OpenTelemetry trace context."""
        try:
            from ddtrace import tracer

            span = tracer.current_span()
            if span:
                # Format trace_id to match Datadog's expected format
                trace_id = str((1 << 64) - 1 & span.trace_id)
                span_id = str(span.span_id)
                event_dict["dd.trace_id"] = trace_id
                event_dict["dd.span_id"] = span_id
        except ImportError:
            pass  # Datadog tracing not installed

        return event_dict


class PrettyJSONRenderer:
    """Render logs as pretty-printed JSON."""

    def __call__(self, *, _: str, event_dict: dict) -> str:
        """Pretty print the JSON in development environment."""
        return json.dumps(event_dict, indent=2, sort_keys=True)


def get_logging_config(
    default_log_level: str,
    app_log_level: str,
    service_name: str = "app",
) -> dict[str, Any]:
    """
    Load logging configuration from YAML file.

    Args:
        default_log_level: Default log level for all loggers
        app_log_level: Log level for application logger
        service_name: Service name for log file

    Returns:
        Logging configuration dictionary
    """
    config_file = Path(__file__).parent / "logging_config.yaml"
    with open(config_file, encoding="utf-8") as file:
        config_data = yaml.safe_load(file)

    log_filename = f"/var/log/app/{service_name}.log"
    config_data["handlers"]["file"]["filename"] = log_filename

    # Update log levels from environment variables or config
    app_log_level_str = app_log_level.upper()
    print(f"Setting app log level to {app_log_level_str}")
    config_data["loggers"]["app"]["level"] = app_log_level_str

    # We use app log level for these assuming it'll likely be the lowest
    config_data["handlers"]["console"]["level"] = app_log_level_str
    config_data["handlers"]["file"]["level"] = app_log_level_str

    # Default log level is used for all other loggers
    default_log_level_str = default_log_level.upper()
    print(f"Setting default log level to {default_log_level_str}")
    config_data["root"]["level"] = default_log_level_str
    return config_data  # type: ignore[no-any-return]


def _ensure_log_directory(log_dir: str) -> bool:
    """
    Ensure log directory exists. Returns True if successful, False otherwise.

    Args:
        log_dir: Directory path for log files

    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        os.makedirs(log_dir, exist_ok=True)
    except (PermissionError, OSError):
        # Expected in CI/test environments
        return False
    else:
        return True


def _disable_file_handler(config_data: dict) -> None:
    """
    Remove file handler from logging configuration when file logging is not available.

    Args:
        config_data: Logging configuration dictionary to modify
    """
    # Remove from handlers section
    config_data.get("handlers", {}).pop("file", None)

    # Remove from all loggers that reference it
    for logger_config in config_data.get("loggers", {}).values():
        if "file" in logger_config.get("handlers", []):
            logger_config["handlers"].remove("file")

    # Remove from root logger
    root_handlers = config_data.get("root", {}).get("handlers", [])
    if "file" in root_handlers:
        root_handlers.remove("file")


def initialize_logging(
    service_name: str,
    config: MonitoringConfig,
    environment: Environment,
) -> None:
    """
    Initialize structured logging with custom configuration.

    Args:
        service_name: Service name for logging
        config: Monitoring configuration
        environment: Current environment
    """
    config_data = get_logging_config(
        default_log_level=config.LOG_LEVEL,
        app_log_level=config.LOG_LEVEL,
        service_name=service_name,
    )

    # Check if we can enable file logging
    log_dir = "/var/log/app"
    if not _ensure_log_directory(log_dir):
        _disable_file_handler(config_data)
        # Only warn in non-test environments
        if environment not in (Environment.DEVELOPMENT,):
            import warnings

            warnings.warn(f"File logging disabled: cannot write to {log_dir}", RuntimeWarning, stacklevel=2)

    logging.config.dictConfig(config_data)

    # Auto-detect: colored logs in dev, JSON in prod
    use_json_logs = config.LOG_JSON

    processors = [
        OpenTelemetryLogProcessor(),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ExtraAdder(),
        lambda _, __, event_dict: {**event_dict, "service": service_name},
        # Add 'status' field for Datadog log severity detection
        # Datadog uses 'status' as a reserved attribute for log levels
        lambda _, __, event_dict: {**event_dict, "status": event_dict.get("level", "info")},
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.EventRenamer("message"),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    # Use colored console output in development, JSON in production
    if use_json_logs:
        # For JSON logs (production/Datadog), use dict_tracebacks to keep exceptions structured
        processors.append(structlog.processors.dict_tracebacks)
        processors.append(structlog.processors.JSONRenderer(sort_keys=True))
    else:
        # For console logs (development), use format_exc_info for readable output
        processors.append(structlog.processors.format_exc_info)
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Structlog logger supports extra kwargs, but mypy doesn't recognize this
    logger.debug(  # type: ignore[call-arg]
        "Logging initialized",
        log_level=config.LOG_LEVEL,
        use_json_logs=use_json_logs,
        service=service_name,
    )


def get_logger(name: str = "app") -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ or "app")

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)
