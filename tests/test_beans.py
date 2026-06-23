import argparse
import sqlite3
import sys
import types
import unittest
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")

from beans import (
    get_connection,
    handle_add,
    handle_delete,
    handle_list,
    handle_update,
    init_db,
)


def make_conn():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


def ns(**kwargs):
    return argparse.Namespace(**kwargs)


class TestInitDb(unittest.TestCase):
    def test_creates_beans_table(self):
        conn = make_conn()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='beans'"
        ).fetchall()
        self.assertEqual(len(tables), 1)

    def test_idempotent(self):
        conn = make_conn()
        init_db(conn)  # second call must not raise

    def test_correct_columns(self):
        conn = make_conn()
        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(beans)").fetchall()
        }
        self.assertIn("name", cols)
        self.assertIn("origin_country", cols)
        self.assertIn("roast_level", cols)
        self.assertIn("pounds_in_stock", cols)


class TestAdd(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()

    def test_happy_path_inserts_row(self):
        with patch("sys.stdout", new_callable=StringIO):
            handle_add(self.conn, ns(name="Kenya AA", origin_country="Kenya", roast_level="medium", pounds="2.5"))
        row = self.conn.execute("SELECT * FROM beans WHERE name='Kenya AA'").fetchone()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row[3], 2.5)

    def test_duplicate_name_errors(self):
        with patch("sys.stdout", new_callable=StringIO):
            handle_add(self.conn, ns(name="Kenya AA", origin_country="Kenya", roast_level="medium", pounds="2.5"))
        with patch("sys.stderr", new_callable=StringIO) as err:
            with self.assertRaises(SystemExit):
                handle_add(self.conn, ns(name="Kenya AA", origin_country="Kenya", roast_level="medium", pounds="1.0"))
        self.assertIn("already exists", err.getvalue())
        count = self.conn.execute("SELECT COUNT(*) FROM beans").fetchone()[0]
        self.assertEqual(count, 1)

    def test_zero_pounds_rejected(self):
        with patch("sys.stderr", new_callable=StringIO) as err:
            with self.assertRaises(SystemExit):
                handle_add(self.conn, ns(name="X", origin_country="Y", roast_level="Z", pounds="0"))
        self.assertIn("positive", err.getvalue())
        count = self.conn.execute("SELECT COUNT(*) FROM beans").fetchone()[0]
        self.assertEqual(count, 0)

    def test_negative_pounds_rejected(self):
        with patch("sys.stderr", new_callable=StringIO) as err:
            with self.assertRaises(SystemExit):
                handle_add(self.conn, ns(name="X", origin_country="Y", roast_level="Z", pounds="-1"))
        self.assertIn("positive", err.getvalue())

    def test_non_numeric_pounds_rejected(self):
        with patch("sys.stderr", new_callable=StringIO) as err:
            with self.assertRaises(SystemExit):
                handle_add(self.conn, ns(name="X", origin_country="Y", roast_level="Z", pounds="abc"))
        self.assertIn("number", err.getvalue())


class TestList(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()

    def test_empty_inventory_message(self):
        with patch("sys.stdout", new_callable=StringIO) as out:
            handle_list(self.conn, ns())
        self.assertIn("No beans in inventory.", out.getvalue())

    def test_shows_all_fields(self):
        with patch("sys.stdout", new_callable=StringIO):
            handle_add(self.conn, ns(name="Kenya AA", origin_country="Kenya", roast_level="medium", pounds="2.5"))
        with patch("sys.stdout", new_callable=StringIO) as out:
            handle_list(self.conn, ns())
        output = out.getvalue()
        self.assertIn("Kenya AA", output)
        self.assertIn("Kenya", output)
        self.assertIn("medium", output)
        self.assertIn("2.5", output)


class TestUpdate(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        with patch("sys.stdout", new_callable=StringIO):
            handle_add(self.conn, ns(name="Kenya AA", origin_country="Kenya", roast_level="medium", pounds="2.5"))

    def test_happy_path_sets_absolute_value(self):
        with patch("sys.stdout", new_callable=StringIO):
            handle_update(self.conn, ns(name="Kenya AA", pounds="4.0"))
        row = self.conn.execute("SELECT pounds_in_stock FROM beans WHERE name='Kenya AA'").fetchone()
        self.assertAlmostEqual(row[0], 4.0)

    def test_nonexistent_name_errors(self):
        with patch("sys.stderr", new_callable=StringIO) as err:
            with self.assertRaises(SystemExit):
                handle_update(self.conn, ns(name="Ghost", pounds="1.0"))
        self.assertIn("Ghost", err.getvalue())

    def test_zero_pounds_rejected(self):
        with patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit):
                handle_update(self.conn, ns(name="Kenya AA", pounds="0"))
        row = self.conn.execute("SELECT pounds_in_stock FROM beans WHERE name='Kenya AA'").fetchone()
        self.assertAlmostEqual(row[0], 2.5)

    def test_negative_pounds_rejected(self):
        with patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit):
                handle_update(self.conn, ns(name="Kenya AA", pounds="-3"))

    def test_non_numeric_pounds_rejected(self):
        with patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit):
                handle_update(self.conn, ns(name="Kenya AA", pounds="bad"))


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        with patch("sys.stdout", new_callable=StringIO):
            handle_add(self.conn, ns(name="Kenya AA", origin_country="Kenya", roast_level="medium", pounds="2.5"))

    def test_happy_path_removes_bean(self):
        with patch("sys.stdout", new_callable=StringIO):
            handle_delete(self.conn, ns(name="Kenya AA"))
        row = self.conn.execute("SELECT * FROM beans WHERE name='Kenya AA'").fetchone()
        self.assertIsNone(row)

    def test_nonexistent_name_errors(self):
        with patch("sys.stderr", new_callable=StringIO) as err:
            with self.assertRaises(SystemExit):
                handle_delete(self.conn, ns(name="Ghost"))
        self.assertIn("Ghost", err.getvalue())

    def test_delete_then_list_does_not_include_it(self):
        with patch("sys.stdout", new_callable=StringIO):
            handle_delete(self.conn, ns(name="Kenya AA"))
        with patch("sys.stdout", new_callable=StringIO) as out:
            handle_list(self.conn, ns())
        self.assertIn("No beans in inventory.", out.getvalue())


if __name__ == "__main__":
    unittest.main()
