from opentelemetry import context, trace

from docchat_infra.observability import (
    current_trace_id,
    extract_trace_context,
    inject_trace_context,
    safe_span_attributes,
    setup_tracing,
)


def test_trace_id_propagates_to_worker_via_carrier() -> None:
    provider = setup_tracing("test")
    tracer = provider.get_tracer("t")
    with tracer.start_as_current_span("api"):
        api_trace = current_trace_id()
        carrier = inject_trace_context()
    assert api_trace and "traceparent" in carrier

    token = context.attach(extract_trace_context(carrier))
    try:
        with tracer.start_as_current_span("worker"):
            assert current_trace_id() == api_trace
    finally:
        context.detach(token)


def test_span_attributes_exclude_content() -> None:
    provider = setup_tracing("test")
    with provider.get_tracer("t").start_as_current_span("s") as span:
        safe_span_attributes(span, stage="embed", question="bí mật", snippet="x")
        attrs = dict(span.attributes or {})  # type: ignore[attr-defined]
    assert attrs == {"stage": "embed"}
    assert trace.get_current_span() is not None
