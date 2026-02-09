"""Tests for clean_string utility."""

import pytest
from openghg_inlet_search._strings import clean_string, is_number


class TestCleanString:
    def test_clean_string_basic(self):
        assert clean_string("Hello World") == "helloworld"

    def test_clean_string_none(self):
        assert clean_string(None) is None

    def test_clean_string_preserves_underscores(self):
        assert clean_string("hello_world") == "hello_world"

    def test_clean_string_removes_dots(self):
        # clean_string removes non-alphanumeric characters (except underscore and hyphen)
        assert clean_string("13.9m") == "139m"

    def test_clean_string_number(self):
        assert clean_string("42") == "42"


class TestIsNumber:
    def test_is_number_int_string(self):
        assert is_number("42") is True

    def test_is_number_float_string(self):
        assert is_number("3.14") is True

    def test_is_number_not_number(self):
        assert is_number("hello") is False

    def test_is_number_bool(self):
        assert is_number(True) is False
