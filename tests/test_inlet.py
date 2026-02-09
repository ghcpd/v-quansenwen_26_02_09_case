"""Tests for format_inlet utility."""

import pytest
from openghg_inlet_search._inlet import format_inlet


class TestFormatInlet:
    def test_number_only(self):
        assert format_inlet("10") == "10m"

    def test_with_unit(self):
        assert format_inlet("10m") == "10m"

    def test_with_magl(self):
        assert format_inlet("10magl") == "10m"

    def test_decimal_value(self):
        assert format_inlet("10.111") == "10.1m"

    def test_decimal_with_unit(self):
        assert format_inlet("13.9m") == "13.9m"

    def test_special_keyword(self):
        assert format_inlet("multiple") == "multiple"

    def test_none(self):
        assert format_inlet(None) is None

    def test_with_key_name_inlet(self):
        assert format_inlet("10m", key_name="inlet") == "10m"

    def test_with_key_name_magl(self):
        assert format_inlet("10m", key_name="inlet_magl") == "10"

    def test_with_key_name_masl(self):
        assert format_inlet("10m", key_name="station_height_masl") == "10"

    def test_list_input(self):
        result = format_inlet(["10", "100"])
        assert result == ["10m", "100m"]

    def test_list_with_decimal(self):
        result = format_inlet(["13.9m", "5m"])
        assert result == ["13.9m", "5m"]
