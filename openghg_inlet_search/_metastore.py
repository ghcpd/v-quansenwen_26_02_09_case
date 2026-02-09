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
        """Convert all keys to lowercase and normalize values."""
        formatted = {}
        for k, v in metadata.items():
            k_lower = k.lower()
            if "inlet" in k_lower or "height" in k_lower:
                v = format_inlet(v, key_name=k)
            else:
                v = clean_string(v)
            formatted[k_lower] = v
        return formatted

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
