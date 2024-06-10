import os

import pytest

from bht.catalog_tools import (
    catfile_to_rows,
    rows_to_catstring,
    row_to_dict,
    hpevent_keys_ordered,
    dict_to_string,
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

    def test_caption(self, ocr_dir_v4):
        """
        GIVEN an ocr dir
        WHEN StepLigther is instantiated
        THEN check caption is ok
        """
        step_lighter = StepLighter(ocr_dir_v4, 0, "entities")
        assert type(step_lighter.caption) is dict
        assert step_lighter.caption["step"] == "0"
        assert step_lighter.caption["pipeline_version"] == "4.0"
        assert step_lighter.caption["message"] == "0- Satellites Recognition"

    def test_initialize(self, ocr_dir_v4):
        """
        GIVEN an ocr dir
        WHEN StepLigther is instantiated
        THEN check initialization runs ok
        """

        step_lighter = StepLighter(ocr_dir_v4, 0, "entities")
        step_lighter.initialize()
        assert os.path.isfile(step_lighter._txt_filepath)
        assert len(step_lighter._txt_raw.split("\n")) == 170


class TestBhtTools:
    def test_row_to_dict(self, event_as_row):
        _dict = row_to_dict(event_as_row[:7])
        assert set(_dict.keys()).issubset(hpevent_keys_ordered[:7])
        _dict = row_to_dict(event_as_row[:10])
        assert set(_dict.keys()).issubset(hpevent_keys_ordered[:10])

    def test_dict_to_string(self, small_event_dict, long_event_dict):
        small_string = dict_to_string(small_event_dict)
        assert len(small_string.split(" ")) == len(small_event_dict.keys())
        long_string = dict_to_string(long_event_dict)
        assert len(long_string.split(" ")) == len(long_event_dict.keys())

    def test_dict_to_dict(self, wrong_keys_dict):
        """
        GIVEN an event dict with wrong keys
        WHEN dict_to_dict is applied
        THEN check new dict has correct keys
        @return:
        """
        _converted_dict = dict_to_dict(wrong_keys_dict)
        assert set(_converted_dict.keys()).issubset(hpevent_keys_ordered)

    def test_rows_to_catstring(self, cat_for_test):
        hp_events = catfile_to_rows(cat_for_test)
        cat_str = rows_to_catstring(
            hp_events,
            "test_rows_to_catstring",
            ["doi", "sats", "insts", "regs", "start_time", "stop_time"],
        )
        # cat_rows=[_r for _r in cat_str.split('\n') if '#' not in _r]
        cat_rows = cat_str.split("\n")
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
