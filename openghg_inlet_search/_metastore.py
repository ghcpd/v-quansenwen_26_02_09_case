"""Simple in-memory metadata store backed by TinyDB."""

from contextlib import contextmanager
from collections.abc import Generator
from typing import Any, Dict, List, Optional

import tinydb
from tinydb.storages import MemoryStorage
from openghg_inlet_search._inlet import format_inlet

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
        """Convert all keys to lowercase and normalize values appropriately.
        
        For inlet-like keys (inlet, height, or keys ending in _magl/_masl),
        applies format_inlet() to preserve decimals and ensure consistency.
        For other values, applies clean_string() for normalization.
        """
        from openghg_inlet_search._strings import clean_string
        
        formatted = {}
        for k, v in metadata.items():
            lower_k = k.lower()
            # Check if this is an inlet-like key
            if lower_k in ("inlet", "height") or lower_k.endswith("_magl") or lower_k.endswith("_masl"):
                # Format inlet-like values using format_inlet
                if isinstance(v, (list, tuple)):
                    formatted[lower_k] = [format_inlet(item, key_name=lower_k) if item is not None else None for item in v]
                else:
                    formatted[lower_k] = format_inlet(v, key_name=lower_k) if v is not None else None
            else:
                # For other values, apply clean_string for normalization
                if isinstance(v, (list, tuple)):
                    formatted[lower_k] = [clean_string(item) if item is not None else None for item in v]
                else:
                    formatted[lower_k] = clean_string(v) if v is not None else None
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
