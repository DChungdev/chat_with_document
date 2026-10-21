"""OpenTelemetry tracing. Không gắn nội dung người dùng vào span (SAD 5.3)."""

from __future__ import annotations

from typing import Any

from opentelemetry import context, propagate, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

SAFE_SPAN_ATTRS: frozenset[str] = frozenset(
    {"route", "method", "status", "stage", "error_code", "job_id", "document_id", "attempt"}
)


def setup_tracing(service_name: str, otlp_endpoint: str | None = None) -> TracerProvider:
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    if otlp_endpoint:
        # Exporter là phụ thuộc tùy chọn: pip install ".[otlp]"
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore[import-not-found,unused-ignore]
            OTLPSpanExporter,
        )

        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    trace.set_tracer_provider(provider)
    return provider


def current_trace_id() -> str | None:
    ctx = trace.get_current_span().get_span_context()
    return f"{ctx.trace_id:032x}" if ctx.is_valid else None


def inject_trace_context() -> dict[str, str]:
    """Carrier (W3C traceparent) để lưu cùng job ingest và nối trace sang worker."""
    carrier: dict[str, str] = {}
    propagate.inject(carrier)
    return carrier


def extract_trace_context(carrier: dict[str, str] | None) -> context.Context:
    return propagate.extract(carrier or {})


def safe_span_attributes(span: trace.Span, **attrs: Any) -> None:
    for key, value in attrs.items():
        if key in SAFE_SPAN_ATTRS:
            span.set_attribute(key, value)
