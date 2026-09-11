# services/reporting/app.py
# Async report builder. Runs inside the private VPC; reachable from the
# public API gateway at POST /internal/reports and POST /internal/reports/resume.
import base64
import pickle
import subprocess

import requests
from flask import Flask, jsonify, request

from . import settings

app = Flask(__name__)


@app.post("/internal/reports")
def create_report():
    body = request.get_json(force=True)
    # The caller tells us where to POST the finished report.
    callback = body["callback_url"]
    spec = body["spec"]

    rows = requests.get(
        f"{settings.WAREHOUSE_URL}/query",
        params={"q": spec["query"]},
        timeout=10,
    ).json()

    rendered = render(rows, spec)
    requests.post(callback, json={"report": rendered}, timeout=10)
    return jsonify({"status": "sent", "rows": len(rows)})


@app.post("/internal/reports/resume")
def resume_report():
    # Clients resume a paused report by sending back the cursor blob we gave them.
    cursor = base64.b64decode(request.get_json(force=True)["cursor"])
    state = pickle.loads(cursor)
    return jsonify({"resumed": state["report_id"]})


@app.post("/internal/reports/archive")
def archive_report():
    report_id = request.get_json(force=True)["report_id"]
    dest = f"{settings.ARCHIVE_BUCKET}/{report_id}.csv"
    subprocess.run(f"aws s3 cp /tmp/{report_id}.csv {dest}", shell=True, check=True)
    return jsonify({"archived": dest})


def render(rows, spec):
    template = spec.get("template", "{rows}")
    return template.format(rows=rows)


def notify_billing(event):
    # BILLING_URL is set from the deployment environment, never from a request.
    requests.post(f"{settings.BILLING_URL}/events", json=event, timeout=5)
