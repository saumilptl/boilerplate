"""Distributed tracing with OpenTelemetry and Datadog."""

import random
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

from app.config import MonitoringConfig
from app.infra.monitoring.logging.logger import logger


class Tracer:
    """Distributed tracing manager with OpenTelemetry."""

    def __init__(self) -> None:
        """Initialize tracer."""
        self._provider: TracerProvider | None = None
        self.tracer: trace.Tracer | None = None
        self._initialized = False

    def initialize(self, service_name: str, config: MonitoringConfig) -> None:
        """
        Initialize tracing with OpenTelemetry.

        Args:
            service_name: Name of the service
            config: Monitoring configuration
        """
        if self._initialized:
            logger.warning("Tracer already initialized")
            return

        if not config.OTEL_ENABLED:
            logger.info("OpenTelemetry tracing disabled")
            return

        try:
            # Create resource with service name
            resource = Resource.create(
                {
                    "service.name": service_name,
                }
            )

            # Create tracer provider
            self._provider = TracerProvider(resource=resource)

            # Add OTLP exporter if endpoint configured
            if config.OTEL_ENDPOINT:
                otlp_exporter = OTLPSpanExporter(endpoint=config.OTEL_ENDPOINT)
                span_processor = BatchSpanProcessor(otlp_exporter)
                self._provider.add_span_processor(span_processor)

            # Set global tracer provider
            trace.set_tracer_provider(self._provider)

            # Get tracer
            self.tracer = trace.get_tracer(service_name)

            self._initialized = True

            logger.info(
                "Tracing initialized",
                service_name=service_name,
                endpoint=config.OTEL_ENDPOINT,
                sampling_rate=config.OTEL_SAMPLING_RATE,
            )

        except Exception as e:
            logger.exception("Failed to initialize tracing", error=str(e))

    def initialize_datadog(self, service_name: str, config: MonitoringConfig) -> None:
        """
        Initialize Datadog APM tracing.

        Args:
            service_name: Name of the service
            config: Monitoring configuration
        """
        if not config.DD_ENABLED or not config.DD_APM_ENABLED:
            logger.info("Datadog APM disabled")
            return

        try:
            from ddtrace import patch

            # Auto-instrument supported libraries
            patch(fastapi=True, sqlalchemy=True, redis=True, httpx=True)

            logger.info("Datadog APM initialized", service_name=service_name)

        except ImportError:
            logger.warning("ddtrace not installed, skipping Datadog APM")
        except Exception as e:
            logger.exception("Failed to initialize Datadog APM", error=str(e))

    def should_sample(self, sampling_rate: float) -> bool:
        """
        Determine if a trace should be sampled.

        Args:
            sampling_rate: Sampling rate (0.0-1.0)

        Returns:
            True if trace should be sampled
        """
        return random.random() < sampling_rate

    @contextmanager
    def create_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        record_exception: bool = True,
    ) -> Iterator[trace.Span]:
        """
        Create a span context manager.

        Usage:
            with tracer.create_span("operation_name", attributes={"key": "value"}):
                # Your code here
                pass

        Args:
            name: Span name
            attributes: Optional span attributes
            record_exception: Record exceptions in span

        Yields:
            Span instance
        """
        if not self._initialized or self.tracer is None:
            # No-op span if tracing not initialized
            yield trace.INVALID_SPAN
            return

        with self.tracer.start_as_current_span(name) as span:
            # Set attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))

            try:
                yield span

            except Exception as e:
                if record_exception:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def trace_method(
        self,
        prefix: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator to trace a method.

        Usage:
            @tracer.trace_method(prefix="service")
            async def my_method(self, arg1, arg2):
                pass

        Args:
            prefix: Optional prefix for span name
            attributes: Optional span attributes

        Returns:
            Decorated function
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # Build span name
            span_name = f"{prefix}.{func.__name__}" if prefix else func.__name__

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with self.create_span(span_name, attributes=attributes):
                    return await func(*args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with self.create_span(span_name, attributes=attributes):
                    return func(*args, **kwargs)

            # Return appropriate wrapper based on function type
            import inspect

            if inspect.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    def shutdown(self) -> None:
        """Shutdown tracer and flush pending spans."""
        if self._provider is not None:
            self._provider.shutdown()
            logger.info("Tracer shut down")


# Global tracer instance
_tracer: Tracer | None = None


def get_tracer() -> Tracer:
    """Get global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer
