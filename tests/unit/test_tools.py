from pprint import pprint

from bht.catalog_tools import (
    catfile_to_rows,
    rows_to_catstring,
    row_to_dict,
    hpevent_keys_ordered,
    dict_to_row,
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
    def test_row_to_dict(self):
        _row = [
            "2006-08-15T00:00:00.000",
            "2006-08-15T00:00:59.999",
            "https://doi.org/10.5194/angeo-28-233-2010",
            "STEREO",
            "",
            "Heliosphere.Remote1AU",
            7591,
            1,
            15,
            46,
            23,
            0.048298021250874845,
        ]
        _dict = row_to_dict(_row[:7])
        pprint(_dict)
        assert set(_dict.keys()).issubset(hpevent_keys_ordered[:7])
        _dict = row_to_dict(_row[:10])
        pprint(_dict)
        assert set(_dict.keys()).issubset(hpevent_keys_ordered[:10])

    def test_dict_to_row(self):
        _small_dict = {
            "d": 7591,
            "doi": "https://doi.org/10.5194/angeo-28-233-2010",
            "insts": "",
            "regs": "Heliosphere.Remote1AU",
            "sats": "STEREO",
            "start_time": "2006-08-15T00:00:00.000",
            "stop_time": "2006-08-15T00:00:59.999",
        }
        _long_dict = {
            "d": 7591,
            "doi": "https://doi.org/10.5194/angeo-28-233-2010",
            "insts": "",
            "occur_sat": 46,
            "r": 1,
            "regs": "Heliosphere.Remote1AU",
            "sats": "STEREO",
            "so": 15,
            "start_time": "2006-08-15T00:00:00.000",
            "stop_time": "2006-08-15T00:00:59.999",
        }
        small_row = dict_to_row(_small_dict)
        assert len(small_row) == len(_small_dict.keys())
        long_row = dict_to_row(_long_dict)
        assert len(long_row) == len(_long_dict.keys())

    def test_rows_to_catstring(self, cat_for_test):
        hp_events = catfile_to_rows(cat_for_test)
        cat_str = rows_to_catstring(
            hp_events,
            "test_rows_to_catstring",
            ["doi", "sats", "insts", "regs", "start_time", "stop_time"],
        )
        assert len(cat_str) == 7051

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
        awaited_keys = [
            "doi",
            "insts",
            "sats",
            "regs",
            "start_time",
            "stop_time",
        ]
        assert set(first_event.keys()).issubset(awaited_keys)
