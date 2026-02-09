# openghg_inlet_search

A small utility library for formatting and searching metadata records, with a focus on inlet height values used in atmospheric observation stations.

This library provides:
- **`clean_string`**: normalizes metadata strings (lowercases, removes whitespace and non-alphanumeric characters except underscores and hyphens).
- **`format_inlet`**: formats inlet/height values to a consistent standard (e.g., `"10"` -> `"10m"`, `"10.111"` -> `"10.1m"`).
- **`MetaStore`**: a simple in-memory metadata store backed by TinyDB, supporting insert and search operations.
- **`search`**: a search function that normalizes search terms and queries the metastore.

## Installation

```bash
pip install -e .
```

## Running Tests

```bash
pytest tests/ -v
```
