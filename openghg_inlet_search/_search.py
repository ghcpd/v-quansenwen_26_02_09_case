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


def _base_search(metastore: MetaStore, **kwargs: Any) -> SearchResults:
    """Search for data records. Any keyword arguments may be passed to the
    function and these keywords will be used to search metadata.

    Though any types can be passed as keyword arguments, these will be interpreted in the following ways:
     - None - argument will be ignored.
     - list/tuple - an OR search will be created for the argument and each of the values.
     - dict - an OR search will be created for the key, value pairs.
       - Note: in this case the name of argument itself will be ignored.
     - str/other - argument used directly.

    All input search values are formatted (clean_string).

    Args:
        metastore: MetaStore instance to search.
        kwargs: search terms as key-value pairs.
    Returns:
        SearchResults: SearchResults object
    """
    import itertools

    # Select and format the search terms
    # - ignore any kwargs which are None
    # - clean search terms directly or within data structures
    search_kwargs: Dict[str, Any] = {}
    for k, v in kwargs.items():
        k_lower = k.lower()
        is_inlet_key = "inlet" in k_lower or "height" in k_lower
        if isinstance(v, (list, tuple)):
            if is_inlet_key:
                v = [format_inlet(value, key_name=k) for value in v if value is not None]
            else:
                v = [clean_string(value) for value in v if value is not None]
            if not v:  # Check empty list
                v = None
        elif isinstance(v, dict):
            if is_inlet_key:
                v = {key: format_inlet(value, key_name=k) for key, value in v.items() if value is not None}
            else:
                v = {key: clean_string(value) for key, value in v.items() if value is not None}
            if not v:  # Check empty dict
                v = None
        else:
            if is_inlet_key:
                v = format_inlet(v, key_name=k)
            else:
                v = clean_string(v)

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
