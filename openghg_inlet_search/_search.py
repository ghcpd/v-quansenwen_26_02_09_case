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


def _is_inlet_like_key(key: str) -> bool:
    """Determine if a key should be formatted as an inlet/height value.
    
    Inlet-like keys include:
     - 'inlet' or 'height' directly
     - Keys ending with '_magl' or '_masl' (height-related keys)
    
    Args:
        key: The metadata key name to check
        
    Returns:
        bool: True if the key should be formatted as an inlet, False otherwise
    """
    if key in ("inlet", "height"):
        return True
    if key.endswith("_magl") or key.endswith("_masl"):
        return True
    return False


def _format_value(value: Any, key: Optional[str] = None) -> Any:
    """Format a single search value using appropriate normalization.
    
    For inlet-like keys, uses format_inlet() to preserve decimals.
    For other keys, uses clean_string() for general normalization.
    
    Args:
        value: The value to format
        key: The metadata key name (optional, used to determine formatting logic)
        
    Returns:
        The formatted value
    """
    if value is None:
        return None
    
    # Use format_inlet for inlet-like keys to preserve decimals
    if key and _is_inlet_like_key(key):
        return format_inlet(value, key_name=key)
    
    # Use clean_string for other keys
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

    All input search values are formatted. For inlet-like keys (inlet, height, 
    keys ending in _magl or _masl), format_inlet() is used to preserve decimals.
    For other keys, clean_string() is used for general normalization.

    Args:
        metastore: MetaStore instance to search.
        kwargs: search terms as key-value pairs.
    Returns:
        SearchResults: SearchResults object
    """
    import itertools

    # Select and format the search terms
    # - ignore any kwargs which are None
    # - format search terms using appropriate normalization (inlet or string)
    search_kwargs: Dict[str, Any] = {}
    for k, v in kwargs.items():
        if isinstance(v, (list, tuple)):
            # Format each item in the list/tuple
            v = [_format_value(value, key=k) for value in v if value is not None]
            if not v:  # Check empty list
                v = None
        elif isinstance(v, dict):
            # For dict values, format each value in the dict
            v = {key: _format_value(value, key=k) for key, value in v.items() if value is not None}
            if not v:  # Check empty dict
                v = None
        else:
            # Format the single value
            v = _format_value(v, key=k)

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
