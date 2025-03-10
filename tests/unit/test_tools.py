import os
from pprint import pprint

import pandas as pd

from bht.catalog_tools import (
    catfile_to_rows,
    rows_to_catstring,
    row_to_dict,
    hpevent_keys_ordered,
    dict_to_string,
    dict_to_dict,
    dicts_to_df, df_to_dicts,
)
from tools import StepLighter, JsonAnalyser
import json


class TestJsonAnalyser:
    def test_dump_sat_region(self, json_entities_16):
        json_analyser = JsonAnalyser(json_entities_16, 16, "entities")
        dumped = json_analyser.dump_sat_regions()
        assert "JSON Syntax Error" not in dumped
        assert len(dumped.split("\n")) == 41

    def test_dump_sat_region_2(self, json_entities_16_2):
        json_analyser = JsonAnalyser(json_entities_16_2, 16, "entities")
        dumped = json_analyser.dump_sat_regions()
        assert "JSON Syntax Error" in dumped
        assert len(dumped.split("\n")) == 15


class TestStepLighter:
    def test_analysed_sutime(self, ocr_dir_v4):
        """
        GIVEN a json struct
        WHEN analysed is run
        THEN check both length are equal
        """
        step_lighter = StepLighter(ocr_dir_v4, 0, "sutime")
        # From that the json analysis as txt table, only keep lines from json struct (not header)
        analysed_lines = step_lighter.analyse_json().split("\n")
        filtered_lines = []
        for _l in analysed_lines:
            _type = _l.split("|")[0].strip()
            if _type in ["DATE", "DURATION", "TIME"]:
                filtered_lines.append(_type)

        # Now, get the raw json struct
        json_struct = json.loads(step_lighter.json_string)

        #  Both lists lengths should be equal
        assert len(json_struct) == len(filtered_lines)

    def test_caption(self, ocr_dir_v4):
        """
        GIVEN an ocr dir
        WHEN StepLighter is instantiated
        THEN check caption is ok
        """
        step_lighter = StepLighter(ocr_dir_v4, 0, "entities")
        assert type(step_lighter.caption) is dict
        assert step_lighter.caption["step"] == "0"
        assert step_lighter.caption["pipeline_version"] == "4.0"
        assert step_lighter.caption["message"] == "0- Satellites Recognition"

    def test_initialize_txt(self, ocr_dir_v4):
        """
        GIVEN an ocr dir
        WHEN StepLighter is instantiated
        THEN check initialization runs ok
        """
        step_lighter = StepLighter(ocr_dir_v4, 0, "entities")
        assert os.path.isfile(step_lighter.txt_filepath)
        assert len(step_lighter.txt_content.split("\n")) == 170

    def test_initialize_json_path(self, ocr_dir_v4):
        """
        GIVEN an ocr dir
        WHEN StepLighter is instantiated
        THEN check json path is ok
        """
        step_lighter = StepLighter(ocr_dir_v4, 0, "entities")
        assert os.path.isfile(step_lighter.json_filepath)

    def test_initialize_json_params(self, ocr_dir_v4):
        """
        GIVEN an ocr dir
        WHEN StepLighter is instantiated
        THEN check json vars are ok
        """
        step_lighter = StepLighter(ocr_dir_v4, 0, "entities")
        assert type(step_lighter.caption) is dict
        assert type(step_lighter.json_struct) is list

    def test_all_steps(self, ocr_dir_v4):
        sutime_step_lighter = StepLighter(ocr_dir_v4, 0, "sutime")
        assert len(sutime_step_lighter.all_steps) == 12
        entities_step_lighter = StepLighter(ocr_dir_v4, 0, "entities")
        assert len(entities_step_lighter.all_steps) == 19

    def test_jinja_calls(self, ocr_dir_v4):
        """
        GIVEN a stepligther
        WHEN html methods called
        THEN check content is ok
        """
        step_lighter = StepLighter(ocr_dir_v4, 0, "entities")
        assert type(step_lighter.txt_enlighted) is str
        assert len(step_lighter.txt_enlighted) == 35732
        assert len(step_lighter.json_string.split("\n")) == 350
        assert len(step_lighter.json_analysed.split("\n")) == 63

    def test_entities_7(self, ocr_dir_v4):
        """
        GIVEN a on ocr dir v4
        WHEN stepligther is instanciated at step 7
        THEN check no Exception is raised
        """
        step_lighter = StepLighter(ocr_dir_v4, 7, "entities")


class TestBhtTools:
    def test_dicts_to_df(self, json_entities_18):
        _df = dicts_to_df(json_entities_18)
        assert isinstance(_df, pd.DataFrame)
        assert len(_df) == 13
        assert list(_df.columns) == ['D', 'DOI', 'R', 'SO', 'conf', 'inst', 'reg', 'sat', 'start_time', 'stop_time']

    def test_df_to_dicts(self, json_entities_18):
        _df = dicts_to_df(json_entities_18)
        _dicts = df_to_dicts(_df)
        assert isinstance(_dicts, list)
        assert len(_dicts) == 13
        _awaited_dict_keys = ['D', 'DOI', 'R', 'SO', 'conf', 'inst', 'reg', 'sat', 'start_time', 'stop_time']
        _returned_dict_keys = list(_dicts[0].keys())
        assert _awaited_dict_keys == _returned_dict_keys

    def test_row_to_dict(self, event_as_row):
        _dict = row_to_dict(event_as_row[:7])
        assert set(_dict.keys()).issubset(hpevent_keys_ordered[:7])
        _dict = row_to_dict(event_as_row[:10])
        assert set(_dict.keys()).issubset(hpevent_keys_ordered[:10])
        assert 'start_time' in _dict

    def test_row_to_dict_with_conf(self, event_as_row):
        _dict = row_to_dict(event_as_row)
        assert 'conf' in _dict
        pprint(_dict)

    def test_dict_to_string(self, small_event_dict, long_event_dict):
        small_string = dict_to_string(small_event_dict)
        long_string = dict_to_string(long_event_dict)
        # deal with empty strings
        small_string = small_string.replace(' " " ', ' "_" ' )
        long_string = long_string.replace(' " " ', ' "_" ' )
        assert len(small_string.split(" ")) == len(small_event_dict.keys())
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
        assert len(cat_rows) == 74

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
        assert len(_event_dict.keys()) == 5

    def test_catfile_to_rows_big(self, big_cat_for_test):
        _hp_events = catfile_to_rows(big_cat_for_test)
        assert len(_hp_events) == 32
        _event_dict = _hp_events[0]
        assert len(_event_dict.keys()) == 12

    def test_catfile_to_rows_allkeys(self, cat_for_test):
        _hp_events = catfile_to_rows(cat_for_test)
        _event_dict = _hp_events[0]
        assert len(_event_dict.keys()) == 12

    def test_event_as_dict(self, small_cat_for_test):
        hp_events = catfile_to_rows(small_cat_for_test)
        first_event = hp_events[0]
        assert set(first_event.keys()).issubset(hpevent_keys_ordered)
