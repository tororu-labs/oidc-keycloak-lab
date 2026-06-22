from __future__ import annotations

import logging
import os

logger = logging.getLogger("uvicorn.error")


def setup_telemetry(app) -> None:
    """OTEL_EXPORTER_OTLP_ENDPOINT が未設定なら何もしない（no-op）。"""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logger.info("stage=otel_setup skipped reason=OTEL_EXPORTER_OTLP_ENDPOINT_not_set")
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    service_name = os.getenv("OTEL_SERVICE_NAME", "demo-api")
    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    # OTEL_EXPORTER_OTLP_ENDPOINT を env var のまま読ませる。constructor に渡すと完全 URL 扱いになり /v1/traces が付かない。
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)

    logger.info("stage=otel_setup done service=%s endpoint=%s", service_name, endpoint)
