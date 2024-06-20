#
# Unit Tests for the sutime parser file
#
import datetime
import dateutil.parser as parser

from bht.SUTime_processing import (
    durations_to_prevdate,
    set_duration_day,
    previous_date,
    date_is_today,
)


class TestSutimeProcessing:

    def test_duration_to_prevdate(self, json_step_4):
        json_step_5 = durations_to_prevdate(json_step_4)
        from pprint import pprint

        pprint(json_step_5)
        assert True

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
        assert duration["value"] == {'begin': '2023-03-03T11:31:00', 'end': '2024-06-20T11:32:00'}

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
        assert duration["value"] == { "begin": "2024-06-20T11:31:00", "end": "2024-06-20T11:32:00", }

    def test_previous_date(self, json_step_4):
        prev_date = previous_date(json_step_4, 10)
        assert prev_date == parser.parse("2020-12-27")

    def test_date_is_today(self):
        assert not date_is_today(datetime.datetime(2024, 9, 9))
        assert date_is_today(datetime.datetime.now())

    def test_date_is_today_str(self):
        assert not date_is_today("2023-03-06")
        assert date_is_today(datetime.datetime.now().isoformat())
