"""Search function for querying metadata records."""

from typing import Any, Dict, List, Optional

from openghg_inlet_search._strings import clean_string
from openghg_inlet_search._inlet import format_inlet
from openghg_inlet_search._metastore import MetaStore


class SearchResults:
    """Container for search results from the metadata store."""

    def __init__(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.metadata = metadata or {}

    def __bool__(self) -> bool:
        return bool(self.metadata)

    def __repr__(self) -> str:
        n = len(self.metadata)
        return f"SearchResults(n_results={n})"


def _is_inlet_key(key: str) -> bool:
    """Determine whether a search key refers to an inlet/height value."""
    if not isinstance(key, str):
        return False
    key = key.lower()
    return "inlet" in key or "height" in key


def _format_search_value(key: str, value: Any) -> Any:
    """Format a search value, applying inlet formatting when appropriate.

    Non-inlet values are cleaned using :func:`clean_string` to ensure
    consistent comparison. Inlet/height-like values are passed through
    :func:`format_inlet`, with the key name provided to ensure proper unit
    handling. The output is lowercased for consistency.
    """
    if value is None:
        return None

    if _is_inlet_key(key):
        try:
            formatted = format_inlet(value, key_name=key.lower())
        except Exception:
            # Fallback: if formatting fails, treat as string
            formatted = value
        if isinstance(formatted, str):
            formatted = formatted.lower().replace(" ", "")
        return formatted
    else:
        # Use existing clean_string behaviour for all other values
        return clean_string(value)


def _base_search(metastore: MetaStore, **kwargs: Any) -> SearchResults:
    """Search for data records. Any keyword arguments may be passed to the
    function and these keywords will be used to search metadata.

    Though any types can be passed as keyword arguments, these will be interpreted in the following ways:
     - None - argument will be ignored.
     - list/tuple - an OR search will be created for the argument and each of the values.
     - dict - an OR search will be created for the key, value pairs.
       - Note: in this case the name of argument itself will be ignored.
     - str/other - argument used directly.

    All input search values are formatted appropriately.

    Args:
        metastore: MetaStore instance to search.
        kwargs: search terms as key-value pairs.
    Returns:
        SearchResults: SearchResults object
    """
    import itertools

    # Select and format the search terms
    # - ignore any kwargs which are None
    # - apply formatting / cleaning to search terms directly or within data structures
    search_kwargs: Dict[str, Any] = {}
    for k, v in kwargs.items():
        if isinstance(v, (list, tuple)):
            formatted_list = [
                _format_search_value(k, value) for value in v if value is not None
            ]
            v = formatted_list if formatted_list else None
        elif isinstance(v, dict):
            formatted_dict = {
                key: _format_search_value(key if isinstance(key, str) else k, value)
                for key, value in v.items()
                if value is not None
            }
            v = formatted_dict if formatted_dict else None
        else:
            v = _format_search_value(k, v)

        if v is not None:
            search_kwargs[k] = v

    # Here we process the kwargs, allowing us to create the correct combinations of search queries.
    multiple_options: List = []
    single_options: Dict[str, Any] = {}
    for k, v in search_kwargs.items():
        if isinstance(v, (list, tuple)):
            expand_key_values = [(k, value) for value in v]
            multiple_options.append(expand_key_values)
        elif isinstance(v, dict):
            expand_key_values = list(v.items())
            multiple_options.append(expand_key_values)
        else:
            single_options[k] = v

    expanded_search: List[Dict[str, Any]] = []
    if multiple_options:
        for kv_pair in itertools.product(*multiple_options):
            d = dict(kv_pair)
            if single_options:
                d.update(single_options)
            expanded_search.append(d)
    else:
        expanded_search.append(single_options)

    metastore_records: List[Dict[str, Any]] = []
    for v in expanded_search:
        res = metastore.search(v)
        if res:
            metastore_records.extend(res)

    # Deduplicate by uuid
    seen_uuids = set()
    unique_records = []
    for record in metastore_records:
        uid = record.get("uuid")
        if uid and uid not in seen_uuids:
            seen_uuids.add(uid)
            unique_records.append(record)
        elif uid is None:
            unique_records.append(record)

    metadata = {r.get("uuid", str(i)): r for i, r in enumerate(unique_records)}

    return SearchResults(metadata=metadata)


def search(metastore: MetaStore, **kwargs: Any) -> SearchResults:
    """Search for data records.

    Any keyword arguments may be passed to the function and these
    keywords will be used to search the metadata associated with
    each record.

    Args:
        metastore: MetaStore instance to search.
        kwargs: search terms as key-value pairs.
    Returns:
        SearchResults: SearchResults object
    """
    return _base_search(metastore, **kwargs)
