from dateutil import parser
from typing import List, Dict, Optional
from datetime import datetime, date
import re


def dt2date(_dt):
    _r_date = date(_dt.year, _dt.month, _dt.day)
    return _r_date


# TODO: mix with SUTime_processing.py::get_struct_date()
def date_from_struct(_sutime_struct):
    """Extract a date from any SUTIME structure
    May be a DATE or a DURATION;
    We don't parse TIME as it doesn't handle dates

    @return python date or None
    """

    _dt_date = None
    _dt_begin = None
    _dt_end = None
    _res_date = None

    _dt_today = dt2date(datetime.today())

    try:
        # parse any date string in struct to datetime
        if _sutime_struct["type"] == "DATE":
            _dt = parser.parse(_sutime_struct["value"])
            _dt_date = dt2date(_dt)
        elif _sutime_struct["type"] == "DURATION":
            _dt = parser.parse(_sutime_struct["value"]["begin"])
            _dt_begin = dt2date(_dt)
            _dt = parser.parse(_sutime_struct["value"]["end"])
            _dt_end = dt2date(_dt)
        else:
            raise Exception("NOOOO")
    except:
        return None

    # now, get better guess if not today
    if _dt_date is not None and _dt_date != _dt_today:
        _res_date = _dt_date
    elif _dt_begin is not None and _dt_begin != _dt_today:
        _res_date = _dt_begin
    elif _dt_end is not None and _dt_end != _dt_today:
        _res_date = _dt_end
    else:
        print("NONE OF ALL")

    return _res_date


def nearest_date(json_list: List[Dict], current_index: int) -> Optional[Dict]:
    """
    Find the nearest date or duration entry relative to a given position in a JSON list.

    Args:
        json_list: List of dictionaries containing date and duration information
        current_index: Index of the current position to find nearest date from

    Returns:
        Dictionary containing the nearest date/duration entry or None if no valid dates found
    """

    def is_valid_date_format(date_str: str) -> bool:
        """Check if a string matches YYYY-MM-DD format."""
        return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", date_str))

    def is_valid_date_entry(entry: Dict) -> bool:
        """Validate if an entry contains properly formatted date information."""
        if entry["type"] == "DATE":
            return is_valid_date_format(entry["value"])
        elif entry["type"] == "DURATION":
            return is_valid_date_format(
                entry["value"]["begin"]
            ) and is_valid_date_format(entry["value"]["end"])
        return False

    def find_nearest_valid_date(
        start_idx: int, step: int, limit: int
    ) -> Optional[Dict]:
        """Find the nearest valid date entry in a given direction."""
        idx = start_idx
        while 0 <= idx < limit:
            if is_valid_date_entry(json_list[idx]):
                return json_list[idx]
            idx += step
        return None

    # Find nearest valid dates before and after current position
    before = find_nearest_valid_date(current_index - 1, -1, len(json_list))
    after = find_nearest_valid_date(current_index + 1, 1, len(json_list))

    # Handle cases where one or both directions have no valid dates
    if not before:
        return after
    if not after:
        return before

    # Calculate distances to determine the nearest date
    current_entry = json_list[current_index]
    distance_to_before = abs(before["end"] - current_entry["start"])
    distance_to_after = abs(current_entry["end"] - after["start"])

    return before if distance_to_before < distance_to_after else after


# Constants
DATE_PATTERN = r"([0-9]{4})-[0-9]{2}(-[0-9]{2})?"
UNKNOWN_YEAR_PATTERN = r"XXXX-[0-9]{2}(-[0-9]{2})?"


class DateProcessor:
    @staticmethod
    def extract_year(date_string: str) -> Optional[str]:
        """Extracts the year from a date string in YYYY-MM-DD format."""
        match = re.search(f"({DATE_PATTERN})", date_string)
        return match.group(1)[:4] if match else None

    @staticmethod
    def has_unknown_year(date_string: str) -> bool:
        """Checks if the date contains XXXX as year."""
        return bool(re.search(UNKNOWN_YEAR_PATTERN, date_string))


class DateItem:
    def __init__(self, data: Dict):
        self.type = data["type"]
        self.data = data
        self.value = data["value"]

    def get_year(self) -> Optional[str]:
        """Extracts the year based on the item type."""
        if self.type in ["DATE", "TIME"]:
            return DateProcessor.extract_year(self.value)

        if self.type == "DURATION":
            # Case where one of the dates has an unknown year (XXXX)
            if DateProcessor.has_unknown_year(self.value["begin"]):
                return DateProcessor.extract_year(self.value["end"])
            if DateProcessor.has_unknown_year(self.value["end"]):
                return DateProcessor.extract_year(self.value["begin"])

            # If both dates have years, take the first one
            return DateProcessor.extract_year(
                self.value["begin"]
            ) or DateProcessor.extract_year(self.value["end"])

        return None


def nearest_year(items: List[Dict], current_index: int) -> str:
    """
    Finds the nearest year in a list of date/duration items.

    Args:
        items: List of dictionaries containing date information
        current_index: Current index in the list

    Returns:
        str: The nearest year found or current year if none found
    """
    current_item = DateItem(items[current_index])

    # First check the current item if it's a DURATION type
    if current_item.type == "DURATION":
        year = current_item.get_year()
        if year:
            return year

    # Look for items before and after
    before = None
    after = None

    # Search backwards
    for i in range(current_index - 1, -1, -1):
        item = DateItem(items[i])
        if year := item.get_year():
            before = (item, i)
            break

    # Search forwards
    for i in range(current_index + 1, len(items)):
        item = DateItem(items[i])
        if year := item.get_year():
            after = (item, i)
            break

    # Case where no dates are found
    if not before and not after:
        return datetime.now().strftime("%Y")

    # Case where only one direction has a date
    if not before:
        return after[0].get_year()
    if not after:
        return before[0].get_year()

    # Compare distances to find the closest
    dist_before = abs(items[before[1]]["end"] - items[current_index]["start"])
    dist_after = abs(items[current_index]["end"] - items[after[1]]["start"])

    return before[0].get_year() if dist_before < dist_after else after[0].get_year()


def jsonfile_to_struct(json_file):
    import json

    with open(json_file) as _fd:
        json_struct = json.load(_fd)
    return json_struct


def try_nearest_year():
    sutime_1_file = "/home/richard/01DEV/bht2/DATA/web-upload/8DD74E2D8726EB88DC6EC10F22790CBF852567EE/res_sutime.json"
    sutime_1_structs = jsonfile_to_struct(sutime_1_file)
    return nearest_year(sutime_1_structs, 4)


def try_date_from_struct():
    filename = "/home/richard/01DEV/bht2/DATA/web-upload/F0F66AF64F9A96EB6B8E36BD19F269229B48E29F/raw4_sutime.json"
    json_struct = jsonfile_to_struct(filename)

    print(json_struct.pop())
    for _st in json_struct:
        _date = date_from_struct(_st)
        if _date is None:
            _date = "None"
        else:
            _date = _date.strftime("%Y-%m-%d")
        return f"{_st['type']:9} {_date.__repr__():<15} {_st['value'].__repr__():<65} {_st['text']}"


if __name__ == "__main__":
    # TODO : move that to test case
    import sys
    from pprint import pprint

    choice = 1

    if choice == 0:
        print(try_nearest_year())
    elif choice == 1:
        print(try_date_from_struct())

#
