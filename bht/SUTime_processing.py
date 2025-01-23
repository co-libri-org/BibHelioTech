import os
import re
import json
from datetime import date, datetime, timedelta

import dateutil.parser as parser

from bht.bht_logging import init_logger
from bht.sutime_tools import nearest_year, shortdate_rewriting_step
from tools import RawDumper

_logger = init_logger()

raw_dumper = RawDumper("sutime")


def SUTime_treatement(current_OCR_folder, sutime):
    _logger.info("SUTime_treatement -> res_sutime.json")
    file = open(current_OCR_folder + "/" + "out_filtered_text.txt", "r")
    input_content = file.read()

    test_list = sutime.parse(input_content)  # Analysis of the whole text by SUTime
    raw_dumper.dump_to_raw(test_list, "Raw sutime output", current_OCR_folder)

    compteur = 0
    for dicts in test_list:
        try:
            # removal of useless values
            if re.search(
                    "PRESENT_REF", str(dicts["value"])
            ):  # remove times of type "..._REF"
                dicts.clear()
            elif re.search(
                    "FUTURE_REF", str(dicts["value"])
            ):  # remove times of type "..._REF"
                dicts.clear()
            elif re.search(
                    "PAST_REF", str(dicts["value"])
            ):  # remove times of type "..._REF"
                dicts.clear()
            elif re.search(
                    "P.*", str(dicts["value"])
            ):  # remove times of types like PXS.XS,PTXS,TOM,PTAH,PXD,PXW,PXY
                dicts.clear()
            elif re.search(
                    "^([^0-9]*)$", str(dicts["text"])
            ):  # remove times that do not contain digit (like 'today', 'dusk', 'the night', etc...)
                dicts.clear()
            elif re.search(
                    "-WE$", str(dicts["value"])
            ):  # remove times of type XXXX-WX-WE (weeks/weekend)
                dicts.clear()
            elif re.search(
                    "-W", str(dicts["value"])
            ):  # remove times of type XXXX-WX-WE (weeks/weekend)
                dicts.clear()
            elif re.search(
                    ".*Q.*", str(dicts["value"])
            ):  # remove times of type QX (Quarters)
                dicts.clear()
            elif re.search(
                    "MO$", str(dicts["value"])
            ):  # remove times of type MO (morning)
                dicts.clear()
            elif re.search(
                    "AF$", str(dicts["value"])
            ):  # remove times of type AF (afternoon)
                dicts.clear()
            elif re.search(
                    "EV$", str(dicts["value"])
            ):  # remove times of type EV (evening)
                dicts.clear()
            elif re.search(
                    "NI$", str(dicts["value"])
            ):  # remove times of type NI (night)
                dicts.clear()
            elif re.search(
                    "-FA$", str(dicts["value"])
            ):  # remove times of type FA (autumn)
                dicts.clear()
            elif re.search(
                    "-SU$", str(dicts["value"])
            ):  # remove times of type SU (summer)
                dicts.clear()
            elif re.search(
                    "-SP$", str(dicts["value"])
            ):  # remove times of type SP (spring)
                dicts.clear()
            elif re.search(
                    "-WI$", str(dicts["value"])
            ):  # remove times of type WI (winter)
                dicts.clear()
            elif re.search(
                    "^[0-9]{4}$", str(dicts["value"])
            ):  # remove years alone (value : "2004")
                dicts.clear()
            elif re.search(r"^\+.*", str(dicts["value"])):  # remove +XXXX alone
                dicts.clear()
            elif re.search(
                    str(str(date.today()).replace("-", "-")), dicts["value"]
            ):  # remove date if it's today
                dicts["value"] = re.sub(
                    str(str(date.today()).replace("-", "-")), "", dicts["value"]
                )
                dicts["timex-value"] = re.sub(
                    str(str(date.today()).replace("-", "-")), "", dicts["timex-value"]
                )
                if dicts["value"] == "":
                    dicts.clear()
        except:
            continue
        compteur += 1

    test_list = [i for i in test_list if i != {}]  # remove empty dictionaries

    raw_dumper.dump_to_raw(test_list, "Filtering sutime by values", current_OCR_folder)

    res_file = open(current_OCR_folder + "/" + "res_sutime.json", "w")
    res_file.write(
        json.dumps(test_list, sort_keys=True, indent=4)
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
        from pprint import pprint
        pprint(_s)
        begin_date = parser.parse(value["begin"])
        end_date = parser.parse(value["end"])
        to_print = f"{begin_date} -> {end_date}"
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
        return re.match("(((^[0-9]{4})|(XXXX))-[0-9]{2}-[0-9]{2}$)", today).group(2)

    def _filter_empty(self):
        self.json_list = [entry for entry in self.json_list if entry]

    def _replace_current_year(self):
        for entry in self.json_list:
            if entry["type"] in ["DATE", "TIME"]:
                entry["value"] = re.sub(rf"{self.current_year}", "XXXX", entry["value"])
            elif entry["type"] == "DURATION":
                if "begin" in entry["value"] and "end" in entry["value"]:
                    for key in ["begin", "end"]:
                        entry["value"][key] = re.sub(rf"{self.current_year}", "XXXX", entry["value"][key])
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

    def transform(self):
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
