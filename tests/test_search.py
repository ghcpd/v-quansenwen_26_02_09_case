"""Tests for search functionality."""

import pytest
import tinydb
from tinydb.storages import MemoryStorage

from openghg_inlet_search._metastore import MetaStore
from openghg_inlet_search._search import search, _base_search


def _make_metastore_with_records(records):
    """Helper: create an in-memory MetaStore pre-populated with records."""
    db = tinydb.TinyDB(storage=MemoryStorage)
    store = MetaStore(database=db)
    for rec in records:
        store.insert(rec)
    return store, db


class TestSearchBasic:
    """Tests for basic search behavior."""

    def test_search_no_results(self):
        store, db = _make_metastore_with_records([
            {"uuid": "abc1", "species": "co2", "site": "TAC"},
        ])
        result = search(store, species="ch4")
        assert not result

    def test_search_simple_match(self):
        store, db = _make_metastore_with_records([
            {"uuid": "abc1", "species": "co2", "site": "TAC"},
            {"uuid": "abc2", "species": "ch4", "site": "BSD"},
        ])
        result = search(store, species="ch4")
        assert result
        assert len(result.metadata) == 1

    def test_search_cleans_strings(self):
        store, db = _make_metastore_with_records([
            {"uuid": "abc1", "species": "co2", "site": "tac"},
        ])
        # Search with uppercase - clean_string should lowercase it
        result = search(store, species="CO2", site="TAC")
        assert result

    def test_search_ignores_none(self):
        store, db = _make_metastore_with_records([
            {"uuid": "abc1", "species": "co2"},
        ])
        result = search(store, species="co2", inlet=None)
        assert result


class TestSearchInlet:
    """Tests for searching with inlet values, including decimal inlets."""

    def test_search_integer_inlet(self):
        """Searching for an integer inlet should work."""
        store, db = _make_metastore_with_records([
            {"uuid": "abc1", "inlet": "100m", "species": "ch4", "data_type": "surface"},
        ])
        result = search(store, inlet="100m", data_type="surface")
        assert result
        assert len(result.metadata) == 1

    def test_search_for_float_inlet(self):
        """Searching for a decimal valued inlet should return matching records.

        This is the core scenario: a record stored with inlet="12.3m" should
        be findable when searching with inlet="12.3m".
        """
        store, db = _make_metastore_with_records([
            {"uuid": "abc123", "inlet": "12.3m", "data_type": "surface"},
        ])
        result = search(store, inlet="12.3m", data_type="surface")
        assert result
        assert len(result.metadata) == 1

    def test_search_for_float_inlet_without_unit(self):
        """Searching for a decimal inlet without unit suffix should also match."""
        store, db = _make_metastore_with_records([
            {"uuid": "def456", "inlet": "13.9m", "data_type": "surface"},
        ])
        result = search(store, inlet="13.9", data_type="surface")
        assert result

    def test_search_height_with_decimal(self):
        """Searching using the 'height' key with a decimal value should work."""
        store, db = _make_metastore_with_records([
            {"uuid": "ghi789", "height": "12.3m", "data_type": "footprints"},
        ])
        result = search(store, height="12.3m", data_type="footprints")
        assert result

    def test_search_inlet_height_magl(self):
        """Searching using 'inlet_height_magl' with a decimal value."""
        store, db = _make_metastore_with_records([
            {"uuid": "jkl012", "inlet_height_magl": "15.5", "data_type": "surface"},
        ])
        result = search(store, inlet_height_magl="15.5", data_type="surface")
        assert result

    def test_search_station_height_masl(self):
        """Searching using 'station_height_masl' with a decimal value."""
        store, db = _make_metastore_with_records([
            {"uuid": "mno345", "station_height_masl": "3580.5", "data_type": "surface"},
        ])
        result = search(store, station_height_masl="3580.5m", data_type="surface")
        assert result

    def test_search_multiple_inlets_finds_decimal(self):
        """When store has multiple records including decimal inlets,
        searching for a specific decimal inlet should return only that record.
        """
        store, db = _make_metastore_with_records([
            {"uuid": "r1", "inlet": "5m", "species": "ch4", "site": "jfj", "data_type": "surface"},
            {"uuid": "r2", "inlet": "13.9m", "species": "ch4", "site": "jfj", "data_type": "surface"},
            {"uuid": "r3", "inlet": "13.9m", "species": "co2", "site": "jfj", "data_type": "surface"},
        ])
        result = search(store, species="ch4", site="JFJ", inlet="13.9m", data_type="surface")
        assert result
        assert len(result.metadata) == 1
        record = list(result.metadata.values())[0]
        assert record["inlet"] == "13.9m"
        assert record["species"] == "ch4"
