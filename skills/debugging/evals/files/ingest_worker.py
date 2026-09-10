"""Background ingest worker.

`IngestWorker.start()` returns immediately; `processed` fills up as records
land, and `finished` flips to True once the whole batch is done.
"""

import random
import threading
import time


class IngestWorker:
    def __init__(self):
        self.processed = []
        self.finished = False

    def start(self, records):
        threading.Thread(target=self._run, args=(records,), daemon=True).start()

    def _run(self, records):
        for record in records:
            # Stands in for per-record IO (a network write in the real worker),
            # which is why the per-record cost varies from run to run.
            time.sleep(random.uniform(0.001, 0.002))
            self.processed.append(record)
        self.finished = True
