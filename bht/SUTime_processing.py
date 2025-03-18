import os
import re
import json
from datetime import date, datetime, timedelta

import requests
import dateutil.parser as parser

from bht.bht_logging import init_logger
from bht.sutime_tools import nearest_year, shortdate_rewriting_step
from tools import RawDumper

_logger = init_logger()

raw_dumper = RawDumper("sutime")


def SUTime_treatement(current_OCR_folder, sutime=None):
    _logger.info("SUTime_treatement -> res_sutime.json")
    file = open(current_OCR_folder + "/" + "out_filtered_text.txt", "r")
    input_content = file.read()

    if sutime is None:
        response = requests.post("http://localhost:8000/parse", json={"text": input_content})
        sutime_structs_list = response.json()
    else:
        sutime_structs_list = sutime.parse(input_content)  # Analysis of the whole text by SUTime
    raw_dumper.dump_to_raw(sutime_structs_list, "Raw sutime output", current_OCR_folder)

    raw_dumper.dump_to_raw(sutime_structs_list, "Filtering sutime by values", current_OCR_folder)

    res_file = open(current_OCR_folder + "/" + "res_sutime.json", "w")
    res_file.write(
        json.dumps(sutime_structs_list, sort_keys=True, indent=4)
    )  # write the result in a file

    file.close()
    res_file.close()


def get_struct_date(_s):
    """From a DATE , TIME or DURATION struct, get the date"""
    if _s["type"] == "DATE":
        return parser.parse(_s["value"])
    elif _s["type"] == "DURATION":
        begin_date = parser.parse(_s["value"]["begin"])
        end_date = parser.parse(_s["value"]["end"])
        # return end date of duration
        if not date_is_today(end_date):
            return end_date
        # or the beginning date
        elif not date_is_today(begin_date):
            return begin_date
        # or nothing if both are today
        else:
            return None


def set_duration_day(duration, day, keys=("begin", "end")):
    """
    Given a duration struct, replace the keys values with day as argument
    """
    for _k in keys:
        k_date = parser.parse(duration["value"][_k])
        k_date = k_date.replace(year=day.year, month=day.month, day=day.day)
        duration["value"][_k] = k_date.isoformat()


def durations_to_prevdate(json_list):
    """
    Browse all durations in a list and set the 'begin' and 'end' dates to the previous date in the list
    """
    for i, _s in enumerate(json_list):
        if "type" not in _s.keys() or _s["type"] != "DURATION":
            continue
        value = _s["value"]
        begin_date = parser.parse(value["begin"])
        end_date = parser.parse(value["end"])
        # either only end_date is set, so set begin to be the same
        if date_is_today(begin_date) and not date_is_today(end_date):
            set_duration_day(_s, end_date, keys=("begin",))
        # or only begin is set, so set end to be the same
        elif not date_is_today(begin_date) and date_is_today(end_date):
            set_duration_day(_s, begin_date, keys=("end",))
        # or both are not set, so
        elif date_is_today(begin_date) and date_is_today(end_date):
            # get the previous date in list
            prev_date = previous_date(json_list, i)
            # and set both begin and end to that found date
            if prev_date is not None:
                set_duration_day(_s, prev_date)

    return json_list


def date_is_today(_date):
    if type(_date) is str:
        _date = parser.parse(_date)
    _date = _date.replace(hour=0, minute=0, second=0, microsecond=0)
    _today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return (_date - _today) == timedelta(minutes=0)


def previous_date(JSON_list, index):
    """ """
    # reverse search from index upwards
    start_idx = index - 1
    first_list_idx = -1
    back_step = -1
    for i in range(start_idx, first_list_idx, back_step):
        _s = JSON_list[i]
        if "type" not in _s.keys():
            continue
        if _s["type"] == "DATE":
            prev_date = parser.parse(_s["value"])
            if not date_is_today(prev_date):
                return prev_date
        elif _s["type"] == "DURATION":
            begin_date = parser.parse(_s["value"]["begin"])
            end_date = parser.parse(_s["value"]["end"])
            if not date_is_today(begin_date):
                return begin_date
            elif not date_is_today(end_date):
                return end_date
        else:
            continue
    return None


class SUTimeTransformer:
    TIME_FORMAT_REGEX = r"((?:[0-9]{4})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)(T)([0-9]{2})((?:(\:))?)((?:[0-9]{2})?)((?:\:)?)((?:[0-9]{2})?)((?:\.)?)((?:[0-9]{1,4})?)"
    FINAL_DATE_FORMAT = r"^([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})(T)([0-9]{2})(:)([0-9]{2})(:)([0-9]{2})(.)([0-9]{3})$"

    def __init__(self, ocr_folder):
        self.ocr_folder = ocr_folder
        self.json_list = self._load_json()
        self.current_year = self._get_current_year()

    def _load_json(self):
        filepath = os.path.join(self.ocr_folder, "res_sutime.json")
        with open(filepath, "r") as f:
            return eval(f.read())

    def _get_current_year(self):
        today = datetime.today().strftime("%Y-%m-%d")
        current_year_str = re.match("(((^[0-9]{4})|(XXXX))-[0-9]{2}-[0-9]{2}$)", today).group(2)
        return int(current_year_str)

    def _filter_empty(self):
        self.json_list = [entry for entry in self.json_list if entry]


    def _clear_if_match(self, dicts, pattern, key="value"):
        """Utility function to clear dictionary if a regex pattern matches.

        Handles both string values and dictionary values with 'begin' and 'end' keys.
        """
        value = dicts.get(key, "")

        if isinstance(value, str):
            # If the value is a string, apply the regex pattern directly
            if re.search(pattern, value):
                dicts.clear()

        elif isinstance(value, dict):
            # If the value is a dictionary with 'begin' and 'end', apply the regex to both
            begin_match = re.search(pattern, value.get("begin", ""))
            end_match = re.search(pattern, value.get("end", ""))

            if begin_match or end_match:
                dicts.clear()

    def _remove_today_date(self):
        """Special case: Remove today's date from all dictionaries in json_list."""
        today_str = str(date.today())
        for dicts in self.json_list:
            if today_str in str(dicts.get("value", "")):
                dicts["value"] = re.sub(today_str, "", dicts["value"])
                dicts["timex-value"] = re.sub(today_str, "", dicts.get("timex-value", ""))
                if not dicts["value"]:
                    dicts.clear()

        # Remove empty dictionaries
        self.json_list = [i for i in self.json_list if i]

    def _remove_unparsable_patterns(self):
        patterns = [
            ("PRESENT_REF|FUTURE_REF|PAST_REF", "value"),
            ("P.*", "value"),
            ("^([^0-9]*)$", "text"),
            ("-WE$", "value"),
            ("-W", "value"),
            (".*Q.*", "value"),
            ("TXX$|FA$|MO$|AF$|EV$|NI$", "value"),
            ("-FA$|-SU$|-SP$|-WI$", "value"),
            ("^[0-9]{4}$", "value"),
            (r"^-?[0-9][0-9X][0-9X]X$", "value"), # "-04XX|186X|188X|18XX|190X|192X|195X|196X|19XX ... "
            (r"^\\+.*", "value"),
        ]

        for dicts in self.json_list:
            try:
                for pattern, key in patterns:
                    self._clear_if_match(dicts, pattern, key)
            except Exception as e:
                print(f"Error processing dict: {e}")

        # Remove empty dictionaries
        self.json_list = [i for i in self.json_list if i]

    def _replace_current_year(self):
        r_pattern = rf"{self.current_year}|{self.current_year-1}"
        for entry in self.json_list:
            if entry["type"] in ["DATE", "TIME"]:
                entry["value"] = re.sub(r_pattern, "XXXX", entry["value"])
            elif entry["type"] == "DURATION":
                if "begin" in entry["value"] and "end" in entry["value"]:
                    for key in ["begin", "end"]:
                        entry["value"][key] = re.sub(r_pattern, "XXXX", entry["value"][key])
                else:
                    entry.clear()
        self._filter_empty()

    def _resolve_xxxx_years(self):
        for i, entry in enumerate(self.json_list):
            if entry["type"] == "DURATION":
                for key in ["begin", "end"]:
                    if key in entry["value"] and re.search("XXXX", entry["value"][key]):
                        year = nearest_year(self.json_list, i)
                        entry["value"][key] = re.sub("XXXX", year, entry["value"][key])
            elif entry["type"] in ["DATE", "TIME"]:
                if re.search("XXXX", entry["value"]):
                    year = nearest_year(self.json_list, i)
                    entry["value"] = re.sub("XXXX", year, entry["value"])

    def _remove_utc(self):
        for entry in self.json_list:
            try:
                if entry["type"] == "DURATION":
                    entry["value"]["begin"] = re.sub(r"\+0000", "", entry["value"]["begin"])
                    entry["value"]["end"] = re.sub(r"\+0000", "", entry["value"]["end"])
                else:
                    entry["value"] = re.sub(r"\+0000", "", entry["value"])
            except:
                continue

    def _calculate_time_bounds(self, match):
        groups = match.groups()
        max_group = len(groups)

        while max_group > 0 and (not groups[max_group - 1] or groups[max_group - 1] == ""):
            max_group -= 1

        min_group = max_group
        while min_group > 0 and groups[min_group - 1]:
            min_group -= 1
        min_group += 1

        try:
            begin, end = "", ""
            if max_group == 16:  # Milliseconds
                group_nums = (1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15)
                base = "".join(match.group(*group_nums))
                begin = f"{base}{int(match.group(max_group)) - 1:03d}"
                end = f"{base}{int(match.group(max_group)) + 1:03d}"

            elif max_group == 14:  # Seconds
                base = "".join(match.group(1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14))
                begin = f"{base}.000"
                end = f"{base}.999"

            elif max_group == 12:  # Minutes
                base = "".join(match.group(1, 2, 4, 5, 7, 8, 9, 10, 12))
                begin = f"{base}:00"
                end = f"{base}:59"

            elif max_group == 9:  # Hours
                base = "".join(match.group(1, 2, 4, 5, 7, 8, 9))
                begin = f"{base}:00:00"
                end = f"{base}:59:59"

            return begin, end

        except:
            return None, None

    def _convert_time_to_duration(self):
        for entry in self.json_list:
            if entry["type"] != "TIME":
                continue

            match = re.match(self.TIME_FORMAT_REGEX, entry["value"])
            if not match:
                continue

            begin, end = self._calculate_time_bounds(match)
            if begin and end:
                entry["type"] = "DURATION"
                entry["value"] = {"begin": begin, "end": end}

    def _convert_dates_to_duration(self):
        for entry in self.json_list:
            if entry["type"] != "DATE":
                continue

            try:
                begin_date = parser.parse(entry["value"])
                end_date = begin_date + timedelta(days=1) - timedelta(seconds=1)
                entry["value"] = {
                    "begin": begin_date.isoformat(),
                    "end": end_date.isoformat()
                }
                entry["type"] = "DURATION"
            except parser.ParserError:
                continue

    def _standardize_formats(self):
        for entry in self.json_list:
            if entry["type"] != "DURATION":
                entry.clear()
                continue

            if any(re.search("[0-9]{2}-[0-9]{2}$", entry["value"][k]) for k in ["begin", "end"]):
                entry["value"]["begin"] += "T00:00:00.000"
                entry["value"]["end"] += "T23:59:59.000"

            self._normalize_timestamps(entry)

        self._filter_empty()
        self._validate_final_format()

    def _normalize_timestamps(self, entry):
        for key in ["begin", "end"]:
            match = re.match(self.TIME_FORMAT_REGEX, entry["value"][key])
            if not match:
                continue

            if not match.group(14):
                suffix = ":00.000" if key == "begin" else ":59.000"
                entry["value"][key] += suffix
            elif not match.group(12):
                suffix = ":00:00.000" if key == "begin" else ":59:59.000"
                entry["value"][key] += suffix
            elif not match.group(16):
                entry["value"][key] += ".000"

    def _validate_final_format(self):
        for entry in self.json_list:
            if not all(re.search(self.FINAL_DATE_FORMAT, entry["value"][k]) for k in ["begin", "end"]):
                entry.clear()
        self._filter_empty()

    def _normalize_24h_time(self):
        for entry in self.json_list:
            if entry["type"] == "DURATION":
                for key in ["begin", "end"]:
                    entry["value"][key] = re.sub(r'T24:00', 'T23:59', entry["value"][key])
                    entry["value"][key] = re.sub(r'(0\d)(\d{2})', r'\1:\2', entry["value"][key])


    def transform(self):
        self._remove_unparsable_patterns()
        raw_dumper.dump_to_raw(self.json_list, "First Filter: Remove Unreadable Patterns",
                               self.ocr_folder, start_step=2)

        self._remove_today_date()
        raw_dumper.dump_to_raw(self.json_list, "Remove date today", self.ocr_folder)

        self._replace_current_year()
        raw_dumper.dump_to_raw(self.json_list, "Current Year to XXXX", self.ocr_folder)

        self._resolve_xxxx_years()
        raw_dumper.dump_to_raw(self.json_list, "Resolution of XXXX to closest year in text", self.ocr_folder)

        self._remove_utc()
        raw_dumper.dump_to_raw(self.json_list, "Remove UTC +0000", self.ocr_folder)

        self._convert_time_to_duration()
        raw_dumper.dump_to_raw(self.json_list, "Change type TIME to DURATION", self.ocr_folder)

        shortdate_rewriting_step(self.json_list)
        raw_dumper.dump_to_raw(self.json_list, "Date rewriting: short date to whole month DURATION", self.ocr_folder)

        self._normalize_24h_time()
        raw_dumper.dump_to_raw(self.json_list, "Normalize 24:00 to 23:59", self.ocr_folder)

        self.json_list = durations_to_prevdate(self.json_list)
        raw_dumper.dump_to_raw(self.json_list, "DURATION gets Previous date", self.ocr_folder)

        self._convert_dates_to_duration()
        raw_dumper.dump_to_raw(self.json_list, "Change type DATE to DURATION", self.ocr_folder)

        self._standardize_formats()
        raw_dumper.dump_to_raw(self.json_list, "Standardize formats (DURATIONS, .000, wrong date) ", self.ocr_folder)
        # raw_dumper.dump_to_raw(self.json_list, "Remove all but DURATION, add midnight", self.ocr_folder)
        # raw_dumper.dump_to_raw(self.json_list, "Do some .000 magic", self.ocr_folder)
        # raw_dumper.dump_to_raw(self.json_list, "Remove wrong date format", self.ocr_folder)
        # raw_dumper.dump_to_raw(self.json_list, "Remove not DURATION", self.ocr_folder)

        output_file = os.path.join(self.ocr_folder, "res_sutime_2.json")
        with open(output_file, "w") as f:
            json.dump(self.json_list, f, sort_keys=True, indent=4)


def SUTime_transform(current_OCR_folder):
    transformer = SUTimeTransformer(current_OCR_folder)
    transformer.transform()
