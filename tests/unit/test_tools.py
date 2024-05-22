from pprint import pprint

from bht.catalog_tools import (
    catfile_to_rows,
    rows_to_catstring,
    row_to_dict,
    hpevent_keys_ordered,
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
        dict = row_to_dict(_row[:7])
        assert set(dict.keys()).issubset(hpevent_keys_ordered[:7])
        dict = row_to_dict(_row[:10])
        assert set(dict.keys()).issubset(hpevent_keys_ordered[:10])

    def test_rows_to_catstring(self, cat_for_test):
        hp_events = catfile_to_rows(cat_for_test)
        cat_str = rows_to_catstring(
            hp_events,
            "test_rows_to_catstring",
            ["doi", "sats", "insts", "regs", "start_time", "stop_time"],
        )
        print(cat_str)
        assert len(cat_str) == 7039

    def test_catfile_to_rows(self, cat_for_test):
        hp_events = catfile_to_rows(cat_for_test)
        assert len(hp_events) == 46

    def test_event_as_dict(self, cat_for_test):
        hp_events = catfile_to_rows(cat_for_test)
        first_event = hp_events[0]
        awaited_keys = [
            "doi",
            "instrument",
            "mission",
            "region",
            "start_date",
            "stop_date",
        ]

        assert set(first_event).issubset(awaited_keys)
