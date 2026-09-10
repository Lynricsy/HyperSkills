import time
import unittest

from ingest_worker import IngestWorker


class IngestTest(unittest.TestCase):
    def test_worker_processes_every_record(self):
        worker = IngestWorker()
        worker.start(["a", "b", "c"])
        time.sleep(0.005)
        self.assertEqual(worker.processed, ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
