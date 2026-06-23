---
title: "feat: Add coffee bean inventory CLI"
type: feat
date: 2026-06-22
origin: docs/brainstorms/2026-06-22-coffee-bean-inventory-requirements.md
---

# feat: Add coffee bean inventory CLI

## Summary

A Python script (`beans.py`) that manages a local coffee bean inventory via subcommands. Running `python beans.py <subcommand>` handles add, list, update-stock, and delete operations, persisting records to a local SQLite file (`beans.db`) created in the working directory on first run.

---

## Requirements

**Data model**

- R1. Each bean record stores: name, origin country, roast level, and pounds in stock.

**Add**

- R2. The user can add a new bean by providing name, origin country, roast level, and pounds in stock.
- R3. Pounds in stock must be a positive number; the app rejects non-numeric or zero/negative values with an error message.

**List**

- R4. The user can list all beans with all four fields displayed in a readable format.
- R5. When the inventory is empty, the app displays a message instead of blank output.

**Update stock**

- R6. The user can update the pounds-in-stock for a named bean to an absolute new value.
- R7. If the named bean does not exist, the app reports an error.

**Delete**

- R8. The user can delete a bean by name.
- R9. If the named bean does not exist, the app reports an error.

---

## Key Technical Decisions

- **Single-file implementation:** All logic lives in `beans.py`, invoked with `python beans.py <subcommand>`. No dependencies beyond the Python standard library.
- **`sqlite3` for persistence:** Standard library module; no server or install required. Database file is `beans.db` created in the current working directory on first run.
- **`argparse` subcommand routing:** Each operation maps to a subparser (`add`, `list`, `update`, `delete`). Semantic validation (positive float) happens in handlers after argparse delivers the raw string.
- **Name as primary key:** Bean names must be unique. Duplicate add attempts are rejected at the DB constraint level and surfaced as a user-readable error.
- **`update` sets absolute value:** The `update` subcommand replaces current stock with the user-supplied value. Simpler and unambiguous for inventory tracking.
- **Pounds stored as REAL:** Supports fractional values (e.g., 1.5 lbs).

---

## Implementation Units

### U1. Database setup and project scaffold

- **Goal:** Create `beans.py` with a DB connection helper and table initialization that runs on every invocation.
- **Requirements:** R1
- **Dependencies:** none
- **Files:**
  - `beans.py`
  - `tests/test_beans.py`
- **Approach:** `get_connection(path)` opens the SQLite file at `path` and returns a `sqlite3.Connection`. `init_db(conn)` runs `CREATE TABLE IF NOT EXISTS beans` with columns `name TEXT PRIMARY KEY`, `origin_country TEXT NOT NULL`, `roast_level TEXT NOT NULL`, `pounds_in_stock REAL NOT NULL`. Both are called at startup before subcommand dispatch.
- **Test scenarios:**
  - Running `init_db` on a fresh in-memory connection creates the `beans` table with the correct columns.
  - Calling `init_db` twice on the same connection does not raise an error.
  - A connection opened at a nonexistent path creates the file.

---

### U2. `add` and `list` subcommands

- **Goal:** Implement `add` and `list` commands with argument wiring, validation, and output formatting.
- **Requirements:** R2, R3, R4, R5
- **Dependencies:** U1
- **Files:**
  - `beans.py`
  - `tests/test_beans.py`
- **Approach:** `add` handler parses pounds as a float and rejects values ≤ 0 or non-numeric before touching the DB. Uses `INSERT INTO beans` and catches `sqlite3.IntegrityError` to report a duplicate-name error. `list` handler runs `SELECT * FROM beans ORDER BY name` and formats rows as aligned columns (name, origin, roast, lbs); prints `"No beans in inventory."` when the result is empty. Argparse scaffold: top-level parser with `add_subparsers(dest='command', required=True)`; `add` subparser takes four positional args; `list` subparser takes none.
- **Patterns to follow:** `argparse.ArgumentParser`, `add_subparsers`
- **Test scenarios:**
  - Happy path: adding a bean with valid args inserts a row and prints a success message.
  - Happy path: listing one bean shows all four fields in the output.
  - Duplicate name: adding a bean whose name already exists prints an error and does not insert a second row.
  - Empty list: listing when no beans exist prints `"No beans in inventory."` rather than blank output.
  - Invalid pounds — zero: `add` rejects with an error message, no row inserted.
  - Invalid pounds — negative: `add` rejects with an error message, no row inserted.
  - Invalid pounds — non-numeric string: `add` rejects with an error message, no row inserted.
- **Verification:** `python beans.py add "Kenya AA" Kenya medium 2.5` succeeds; `python beans.py list` shows the row; a second `add "Kenya AA"` prints an error without inserting a duplicate.

---

### U3. `update` and `delete` subcommands + main entry point

- **Goal:** Implement `update` and `delete` commands and wire the complete `__main__` block.
- **Requirements:** R6, R7, R8, R9
- **Dependencies:** U1, U2
- **Files:**
  - `beans.py`
  - `tests/test_beans.py`
- **Approach:** `update` handler applies the same positive-float validation as `add`, runs `UPDATE beans SET pounds_in_stock=? WHERE name=?`, and checks `cursor.rowcount == 0` to detect a missing bean. `delete` handler runs `DELETE FROM beans WHERE name=?` and checks `cursor.rowcount` the same way. The `if __name__ == '__main__':` block opens the connection, calls `init_db`, parses args, dispatches to the matching handler, and closes the connection.
- **Test scenarios:**
  - Happy path: `update` on an existing bean sets pounds to the new absolute value.
  - Happy path: `delete` removes an existing bean; a subsequent `list` does not include it.
  - `update` on a nonexistent name prints an error and changes no rows.
  - `delete` on a nonexistent name prints an error and changes no rows.
  - `update` with invalid pounds (zero, negative, non-numeric) prints an error and changes no rows.
- **Verification:** A full round-trip — `add → list → update → list → delete → list` — reflects each operation correctly with no errors on any step.

---

## Scope Boundaries

- Editing fields other than pounds-in-stock — deferred (see origin).
- Sorting, filtering, or searching the list — deferred.
- Price, cost, or supplier tracking — deferred.
- Low-stock alerts or notifications — deferred.
- Web interface, cloud sync, or multi-user access — outside scope.

---

## Documentation / Operational Notes

- Invocation: `python beans.py <subcommand> [args]`
- Database location: `beans.db` is created in the directory where the script is run. Always run from the same directory to access the same inventory.
- To start fresh: delete `beans.db`.
- No `pip install` required — Python 3.x standard library only.
