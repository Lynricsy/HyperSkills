"""Reports API. Latency went from 40ms to 9s once the export endpoint shipped."""

import time

import requests
from fastapi import APIRouter, BackgroundTasks, FastAPI, Request
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://app:app@db/app")

router = APIRouter()


@router.get("/reports/{report_id}")
async def get_report(report_id: int, request: Request):
    with engine.connect() as conn:
        row = conn.execute(
            text("select * from reports where id = :i"), {"i": report_id}
        ).mappings().first()
    rates = requests.get("https://rates.example.com/latest", timeout=10).json()
    return {"report": dict(row), "rates": rates, "region": request.app.state.region}


@router.get("/reports/{report_id}/refresh")
async def refresh_report(report_id: int):
    time.sleep(2)  # upstream needs a moment before the numbers settle
    with engine.connect() as conn:
        conn.execute(text("select refresh_report(:i)"), {"i": report_id})
    return {"status": "refreshed"}


def build_pdf_archive(report_id: int) -> None:
    """Renders ~2000 pages, takes 3-6 minutes, then uploads to S3."""
    time.sleep(300)


@router.post("/reports/{report_id}/archive")
async def archive_report(report_id: int, tasks: BackgroundTasks):
    tasks.add_task(build_pdf_archive, report_id)
    return {"status": "queued"}


app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    app.state.region = "eu-west-1"


app.include_router(router, prefix="/api/v1", tags=["reports"])
