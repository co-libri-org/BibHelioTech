#
# Unit Tests for the sutime parser file
#
import copy
import datetime
import dateutil.parser as parser

from bht.SUTime_processing import (
    durations_to_prevdate,
    set_duration_day,
    previous_date,
    date_is_today,
    get_struct_date,
)


class TestSutimeProcessing:

    def test_durations_to_prevdate(self, json_step_4):
        json_step_5 = durations_to_prevdate(json_step_4)
        durations_5 = [
            _s for _s in json_step_5 if "type" in _s.keys() and _s["type"] == "DURATION"
        ]
        assert get_struct_date(durations_5[0]).isoformat() == "2020-12-27T12:40:59"

    def test_durations_to_prevdate_2(self, json_step_4_2):
        json_step_5 = durations_to_prevdate(json_step_4_2)
        durations_5 = [
            _s for _s in json_step_5 if "type" in _s.keys() and _s["type"] == "DURATION"
        ]
        assert get_struct_date(durations_5[0]).isoformat() == "2019-12-26T00:00:00"

    def test_set_duration_day_one_limit(self):
        duration = {
            "end": 26018,
            "start": 26010,
            "text": "11:31:10",
            "timex-value": "T11:31:10",
            "type": "DURATION",
            "value": {"begin": "2023-03-03T11:31:00", "end": "T11:32:00"},
        }
        set_duration_day(duration, parser.parse("2023-03-04"), keys=("end",))
        assert duration["value"] == {
            "begin": "2023-03-03T11:31:00",
            "end": "2024-06-20T11:32:00",
        }

    def test_set_duration_day(self):
        duration = {
            "end": 26018,
            "start": 26010,
            "text": "11:31:10",
            "timex-value": "T11:31:10",
            "type": "DURATION",
            "value": {"begin": "T11:31:00", "end": "T11:32:00"},
        }
        assert date_is_today(duration["value"]["begin"])
        assert date_is_today(duration["value"]["end"])
        set_duration_day(duration, datetime.datetime(2023, 9, 9))
        assert duration["value"] == {
            "begin": "2024-06-20T11:31:00",
            "end": "2024-06-20T11:32:00",
        }

    def test_previous_date_from_first(self, json_step_4_2):
        prev_date = previous_date(json_step_4_2, 0)
        assert prev_date is None

    def test_previous_date(self, json_step_4):
        prev_date = previous_date(json_step_4, 10)
        assert prev_date == parser.parse("2020-12-27")

    def test_date_is_today(self):
        assert not date_is_today(datetime.datetime(2024, 9, 9))
        assert date_is_today(datetime.datetime.now())

    def test_date_is_today_str(self):
        assert not date_is_today("2023-03-06")
        assert date_is_today(datetime.datetime.now().isoformat())
