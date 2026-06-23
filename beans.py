import argparse
import math
import sqlite3
import sys

LOW_STOCK_THRESHOLD = 1.0


def get_connection(path):
    return sqlite3.connect(path)


def init_db(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS beans (
            name TEXT PRIMARY KEY,
            origin_country TEXT NOT NULL,
            roast_level TEXT NOT NULL,
            pounds_in_stock REAL NOT NULL
        )
        """
    )
    conn.commit()


def _parse_positive_float(value, field="pounds"):
    try:
        f = float(value)
    except ValueError:
        print(f"Error: {field} must be a number.", file=sys.stderr)
        sys.exit(1)
    if not math.isfinite(f):
        print(f"Error: {field} must be a finite number.", file=sys.stderr)
        sys.exit(1)
    if f <= 0:
        print(f"Error: {field} must be a positive number.", file=sys.stderr)
        sys.exit(1)
    return f


def handle_add(conn, args):
    pounds = _parse_positive_float(args.pounds)
    try:
        conn.execute(
            "INSERT INTO beans (name, origin_country, roast_level, pounds_in_stock) VALUES (?, ?, ?, ?)",
            (args.name, args.origin_country, args.roast_level, pounds),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Error: a bean named '{args.name}' already exists.", file=sys.stderr)
        sys.exit(1)
    print(f"Added '{args.name}'.")
    if pounds < LOW_STOCK_THRESHOLD:
        print(f"Warning: '{args.name}' is low on stock ({pounds} lbs).")


def handle_list(conn, args):
    rows = conn.execute(
        "SELECT name, origin_country, roast_level, pounds_in_stock FROM beans ORDER BY name"
    ).fetchall()
    if not rows:
        print("No beans in inventory.")
        return
    name_w = max(len("Name"), max(len(r[0]) for r in rows))
    origin_w = max(len("Origin"), max(len(r[1]) for r in rows))
    roast_w = max(len("Roast"), max(len(r[2]) for r in rows))
    header = f"{'Name':<{name_w}}  {'Origin':<{origin_w}}  {'Roast':<{roast_w}}  Lbs"
    print(header)
    print("-" * len(header))
    for name, origin, roast, pounds in rows:
        warning = "  LOW STOCK" if pounds < LOW_STOCK_THRESHOLD else ""
        print(f"{name:<{name_w}}  {origin:<{origin_w}}  {roast:<{roast_w}}  {pounds}{warning}")


def handle_update(conn, args):
    pounds = _parse_positive_float(args.pounds)
    cursor = conn.execute(
        "UPDATE beans SET pounds_in_stock = ? WHERE name = ?",
        (pounds, args.name),
    )
    conn.commit()
    if cursor.rowcount == 0:
        print(f"Error: no bean named '{args.name}' found.", file=sys.stderr)
        sys.exit(1)
    print(f"Updated '{args.name}' to {pounds} lbs.")
    if pounds < LOW_STOCK_THRESHOLD:
        print(f"Warning: '{args.name}' is low on stock ({pounds} lbs).")


def handle_delete(conn, args):
    cursor = conn.execute("DELETE FROM beans WHERE name = ?", (args.name,))
    conn.commit()
    if cursor.rowcount == 0:
        print(f"Error: no bean named '{args.name}' found.", file=sys.stderr)
        sys.exit(1)
    print(f"Deleted '{args.name}'.")


def build_parser():
    parser = argparse.ArgumentParser(description="Track your coffee bean inventory.")
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="Add a new bean.")
    add_p.add_argument("name")
    add_p.add_argument("origin_country")
    add_p.add_argument("roast_level")
    add_p.add_argument("pounds")

    sub.add_parser("list", help="List all beans.")

    update_p = sub.add_parser("update", help="Update pounds in stock for a bean.")
    update_p.add_argument("name")
    update_p.add_argument("pounds")

    delete_p = sub.add_parser("delete", help="Delete a bean by name.")
    delete_p.add_argument("name")

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    try:
        conn = get_connection("beans.db")
    except sqlite3.OperationalError as e:
        print(f"Error: could not open database: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        init_db(conn)
        dispatch = {
            "add": handle_add,
            "list": handle_list,
            "update": handle_update,
            "delete": handle_delete,
        }
        dispatch[args.command](conn, args)
    except sqlite3.DatabaseError as e:
        print(f"Error: database error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()
