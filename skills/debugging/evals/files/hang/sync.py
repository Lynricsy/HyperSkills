import sys
import threading
import time

stock_lock = threading.Lock()
ledger_lock = threading.Lock()


def reserve_stock(order_id):
    with stock_lock:
        time.sleep(0.01)  # read the warehouse row
        post_ledger_entry(order_id)


def post_ledger_entry(order_id):
    with ledger_lock:
        return order_id


def reconcile_ledger(batch_id):
    with ledger_lock:
        time.sleep(0.01)  # load the ledger batch
        adjust_stock(batch_id)


def adjust_stock(batch_id):
    with stock_lock:
        return batch_id


def heartbeat():
    while True:
        time.sleep(1)


def main(token):
    threading.Thread(target=heartbeat, name="heartbeat", daemon=True).start()
    writer = threading.Thread(target=reserve_stock, args=(1001,), name="stock-writer")
    reconciler = threading.Thread(target=reconcile_ledger, args=(77,), name="ledger-reconciler")
    writer.start()
    reconciler.start()
    writer.join()
    reconciler.join()


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--ledger-token") + 1])
