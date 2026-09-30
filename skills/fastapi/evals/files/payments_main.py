"""payments-api entrypoint.

requirements.txt pins fastapi[standard]==0.142.1 and opentelemetry-instrumentation-fastapi.

Environment from the Helm chart:
    production:
        OTEL_SERVICE_NAME=payments-api
        OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability:4318
    staging:
        OTEL_SERVICE_NAME=payments-api
        OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.staging:4317
        OTEL_EXPORTER_OTLP_PROTOCOL=grpc
"""

import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel

if os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL") == "grpc":
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
else:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

tracer = trace.get_tracer("payments")


def tag_tenant(span, scope):
    # Every request span must carry the tenant so dashboards can split by customer.
    for name, value in scope.get("headers", []):
        if name == b"x-tenant-id":
            span.set_attribute("tenant.id", value.decode())


@asynccontextmanager
async def lifespan(app: FastAPI):
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(
        app,
        server_request_hook=tag_tenant,
        excluded_urls="healthz",
    )
    yield
    provider.shutdown()


app = FastAPI(lifespan=lifespan)


class Charge(BaseModel):
    card_number: str
    amount_cents: int


def tenant(x_tenant_id: Annotated[str, Header()]) -> str:
    return x_tenant_id


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/charges")
def create_charge(charge: Charge, tenant_id: Annotated[str, Depends(tenant)]):
    with tracer.start_as_current_span("charge_card"):
        if charge.amount_cents <= 0:
            raise ValueError(f"refusing charge for card {charge.card_number}")
        return {"tenant": tenant_id, "status": "accepted"}
