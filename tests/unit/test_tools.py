from pprint import pprint

import pytest

from bht.catalog_tools import (
    catfile_to_rows,
    rows_to_catstring,
    row_to_dict,
    hpevent_keys_ordered,
    dict_to_row,
    dict_to_dict,
)
from tools import StepLighter
import json


class TestStepLighter:
    def test_analyse_length(self, ocr_dir_sutime):
        """
        GIVEN a json struct
        WHEN analysed is run
        THEN check both length are equal
        """
        step_lighter = StepLighter(ocr_dir_sutime, 0, "sutime")
        # get  the whole output as a list
        analysed_lines = step_lighter.analyse_json().split("\n")
        # only keep lines from json struct
        filtered_lines = []
        for _l in analysed_lines:
            _type = _l.split("|")[0].strip()
            if _type in ["DATE", "DURATION", "TIME"]:
                filtered_lines.append(_type)
        json_struct = json.loads(step_lighter.dump_json())
        # Compare analysed list length with json structs number
        assert len(json_struct) == len(filtered_lines)


class TestBhtTools:
    def test_row_to_dict(self, event_as_row):
        _dict = row_to_dict(event_as_row[:7])
        assert set(_dict.keys()).issubset(hpevent_keys_ordered[:7])
        _dict = row_to_dict(event_as_row[:10])
        assert set(_dict.keys()).issubset(hpevent_keys_ordered[:10])

    def test_dict_to_row(self, small_event_dict, long_event_dict):
        small_row = dict_to_row(small_event_dict)
        assert len(small_row) == len(small_event_dict.keys())
        long_row = dict_to_row(long_event_dict)
        assert len(long_row) == len(long_event_dict.keys())

    def test_upper_dict_to_row(self, wrong_keys_dict):
        """
        GIVEN an event dict with upper case keys
        WHEN dict_to_row is called
        THEN check no exception were raised
        """
        try:
            _row_from_upper = dict_to_row(wrong_keys_dict)
        except KeyError:
            pytest.fail("Upper key should have been lowered")

    def test_dict_to_dict(self, wrong_keys_dict):
        """
        GIVEN an event dict with wrong keys
        WHEN dict_to_dict is applied
        THEN check new dict has correct keys
        @return:
        """
        _converted_dict = dict_to_dict(wrong_keys_dict)
        assert set(_converted_dict.keys()).issubset(hpevent_keys_ordered)
        assert True

    def test_rows_to_catstring(self, cat_for_test):
        hp_events = catfile_to_rows(cat_for_test)
        cat_str = rows_to_catstring(
            hp_events,
            "test_rows_to_catstring",
            ["doi", "sats", "insts", "regs", "start_time", "stop_time"],
        )
        # cat_rows=[_r for _r in cat_str.split('\n') if '#' not in _r]
        cat_rows = cat_str.split('\n')
        assert len(cat_rows) == 67

    def test_rows_to_catstring_allkeys(self, cat_for_test):
        import csv

        all_dicts = []
        with open(cat_for_test, newline="") as csvfile:
            reader = csv.reader(
                filter(lambda r: r[0] != "#", csvfile), delimiter=" ", quotechar='"'
            )
            for row in reader:
                all_dicts.append(row_to_dict(row))
        _cat_string = rows_to_catstring(all_dicts, "test")
        assert len(all_dicts[0]) == 12
        assert len(all_dicts) == 46

    def test_catfile_to_rows(self, small_cat_for_test):
        _hp_events = catfile_to_rows(small_cat_for_test)
        assert len(_hp_events) == 46
        _event_dict = _hp_events[0]
        assert len(_event_dict.keys()) == 6

    def test_catfile_to_rows_allkeys(self, cat_for_test):
        _hp_events = catfile_to_rows(cat_for_test)
        _event_dict = _hp_events[0]
        assert len(_event_dict.keys()) == 12

    def test_event_as_dict(self, small_cat_for_test):
        hp_events = catfile_to_rows(small_cat_for_test)
        first_event = hp_events[0]
        assert set(first_event.keys()).issubset(hpevent_keys_ordered)
