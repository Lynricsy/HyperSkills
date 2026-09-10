"""Small internal API. Nothing is broken here; this is the file new endpoints
go into."""

import os

from flask import Flask, jsonify

app = Flask(__name__)
BUILD_SHA = os.environ.get("BUILD_SHA", "dev")


@app.get("/v1/orders/<order_id>")
def get_order(order_id):
    return jsonify({"id": order_id, "status": "open"})


@app.get("/v1/orders")
def list_orders():
    return jsonify({"orders": []})
