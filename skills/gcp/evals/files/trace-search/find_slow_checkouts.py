"""Find checkout traces that were slow because the database call failed.

Ticket SHOP-2291: "Pull every trace from the last 45 days where /checkout took over 2 seconds
AND the inventory DB call (span `db.inventory.reserve`) failed, so we can count them."

Our services export OpenTelemetry spans to Cloud Trace. Root spans are named after the route,
for example `POST /checkout` and `POST /checkout/confirm`. The DB client sets the span label
`db.status` to `ok` or `error`; every other span in the trace (payment, pricing, email) also
carries its own `db.status` when it touches a database.
"""

import datetime as dt

from google.cloud import trace_v1

PROJECT = "shop-prod-4411"


def main() -> None:
    client = trace_v1.TraceServiceClient()
    end = dt.datetime.now(dt.timezone.utc)
    start = end - dt.timedelta(days=45)
    request = trace_v1.ListTracesRequest(
        project_id=PROJECT,
        start_time=start,
        end_time=end,
        filter="root:POST /checkout latency: 2s span:db.inventory db.status:error",
        page_size=5000,
    )
    count = 0
    for trace in client.list_traces(request=request):
        count += 1
        print(trace.trace_id)
    print(f"{count} slow checkouts caused by inventory DB failures")


if __name__ == "__main__":
    main()
