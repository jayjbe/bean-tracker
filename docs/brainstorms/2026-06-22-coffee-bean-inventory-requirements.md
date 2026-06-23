---
date: 2026-06-22
topic: coffee-bean-inventory
---

## Summary

A Python CLI app for managing a local coffee bean inventory. Users run subcommands to add beans, list inventory, update stock amounts, and delete bean records. Data persists in a local SQLite database across sessions.

---

## Key Decisions

- **SQLite via Python standard library:** No external database or server required. The database file lives locally and persists between runs without any setup beyond installing Python.
- **Subcommand interface:** Each operation maps to a discrete CLI subcommand, making the app scriptable and each operation self-contained.

---

## Requirements

**Data model**

- R1. Each bean record stores: name, origin country, roast level, and pounds in stock.

**Add**

- R2. The user can add a new bean by providing all four fields.
- R3. Pounds in stock must be a positive number; the app rejects non-numeric or zero/negative input with an error message.

**List**

- R4. The user can list all beans with all fields displayed in a readable format.
- R5. When the inventory is empty, the app displays a message instead of blank output.

**Update stock**

- R6. The user can update the pounds-in-stock for a named bean.
- R7. If the named bean does not exist, the app reports an error.

**Delete**

- R8. The user can delete a bean by name.
- R9. If the named bean does not exist, the app reports an error.

---

## Scope Boundaries

- Editing fields other than stock amount — deferred; R6 covers the most common update.
- Sorting, searching, or filtering the list — deferred.
- Price, cost, or supplier tracking — deferred.
- Low-stock alerts or notifications — deferred.
- Web interface, cloud sync, or multi-user access — outside scope.

---

## Outstanding Questions

**Deferred to Planning**

- Update behavior: whether the `update` subcommand sets stock to an absolute value, adjusts by a delta, or supports both. Planning can decide based on ergonomics.
