"""Simple in-memory metadata store backed by TinyDB."""

from contextlib import contextmanager
from collections.abc import Generator
from typing import Any, Dict, List, Optional

import tinydb
from tinydb.storages import MemoryStorage

from openghg_inlet_search._inlet import format_inlet
from openghg_inlet_search._strings import clean_string

MetaData = Dict[str, Any]
QueryResults = List[Dict[str, Any]]


class MetaStore:
    """MetaStore using a TinyDB database backend.

    Stores metadata records and allows searching by key-value pairs.
    """

    def __init__(self, database: tinydb.TinyDB) -> None:
        """Create MetaStore object.

        Args:
            database: a TinyDB database.
        """
        self._db = database

    def _format_metadata(self, metadata: MetaData) -> MetaData:
        """Convert all keys to lowercase."""
        return {k.lower(): v for k, v in metadata.items()}

    def _normalize_inlet_values(self, metadata: MetaData) -> MetaData:
        """Apply inlet/height formatting to relevant metadata values.

        This ensures consistency for storing values such as inlet or height,
        normalizing numeric and unit representations. It also cleans other
        string values to make searches case-insensitive and whitespace/punctuation
        agnostic.
        """
        normalized: MetaData = {}
        for key, value in metadata.items():
            # Only process if value is not None
            if value is None:
                normalized[key] = value
                continue

            lowkey = key.lower()
            if "inlet" in lowkey or "height" in lowkey:
                # Handle list/tuple inputs for inlet-like values
                if isinstance(value, (list, tuple)):
                    normalized[key] = [format_inlet(v, key_name=lowkey) for v in value]
                elif isinstance(value, dict):
                    normalized[key] = {k: format_inlet(v, key_name=k.lower()) for k, v in value.items()}
                else:
                    normalized[key] = format_inlet(value, key_name=lowkey)
            else:
                # Clean other values to ensure consistent comparison
                if isinstance(value, (list, tuple)):
                    normalized[key] = [clean_string(v) for v in value]
                elif isinstance(value, dict):
                    normalized[key] = {k: clean_string(v) for k, v in value.items()}
                else:
                    normalized[key] = clean_string(value)
        return normalized

    def search(self, search_terms: Optional[MetaData] = None) -> QueryResults:
        """Search metastore using a dictionary of search terms.

        Args:
            search_terms: dictionary of key-value pairs to search by.

        Returns:
            list of records matching the given search terms.
        """
        if not search_terms:
            search_terms = {}
        query = tinydb.Query().fragment(self._format_metadata(search_terms))
        return list(self._db.search(query))

    def insert(self, metadata: MetaData) -> None:
        """Add new metadata to the metastore.

        Args:
            metadata: metadata to add to the metastore.
        """
        # Normalize inlet/height-related values and clean other values before storing
        metadata = self._normalize_inlet_values(metadata)
        self._db.insert(self._format_metadata(metadata))


@contextmanager
def open_metastore(bucket: str) -> Generator[MetaStore, None, None]:
    """Context manager that opens or creates a MetaStore.

    Uses an in-memory TinyDB for simplicity.

    Args:
        bucket: identifier for the store (unused in memory mode, kept for API compatibility).

    Yields:
        MetaStore instance.
    """
    with tinydb.TinyDB(storage=MemoryStorage) as db:
        metastore = MetaStore(database=db)
        yield metastore
