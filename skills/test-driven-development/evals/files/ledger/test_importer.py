import unittest
from unittest.mock import MagicMock

from importer import import_rows


class ImportRowsTest(unittest.TestCase):
    def test_commits_once_after_all_rows(self):
        conn = MagicMock()
        import_rows(conn, [{"id": "a", "amount_cents": 100}, {"id": "b", "amount_cents": 250}])
        self.assertEqual(conn.execute.call_count, 2)
        conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
