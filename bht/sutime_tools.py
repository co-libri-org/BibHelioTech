from dateutil import parser
from datetime import datetime, date


def dt2date(_dt):
    _date =date(_dt.year, _dt.month, _dt.day)
    return _date


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
    except :
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


if __name__ == "__main__":
    # TODO : move that to test case
    import json
    filename = '/home/richard/01DEV/bht2/DATA/web-upload/F0F66AF64F9A96EB6B8E36BD19F269229B48E29F/raw4_sutime.json'
    with open(filename) as _fd:
        json_structs = json.load(_fd)

    print(json_structs.pop())
    for _st in json_structs:
        _date = date_from_struct(_st)
        if _date is None:
            _date = "None"
        else:
            _date = _date.strftime("%Y-%m-%d")

        # print(f"<{type(_date.__repr__())}>")
        print(f"{_st['type']:9} {_date.__repr__():<15} {_st['value'].__repr__():<65} {_st['text']}")

