# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Inventory

### Bean
A named coffee variety record in the inventory. Each Bean has four fields: a unique name, an origin country, a roast level, and a current stock amount in pounds. Name is the primary key — duplicate names are rejected.

A Bean enters a Low Stock state when its pounds in stock falls below the configured threshold. This state is surfaced as a warning on add and update operations, and as an inline marker in the list output.
