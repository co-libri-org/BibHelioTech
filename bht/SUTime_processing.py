import os
import re
import json
from calendar import monthrange
from datetime import date, datetime, timedelta

import dateutil.parser as parser

from bht.bht_logging import init_logger
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
            ):  # remove times of types like PXS.XS,PTXS,PTXM,PTXH,PXD,PXW,PXY
                dicts.clear()
            elif re.search(
                "^([^0-9]*)$", str(dicts["text"])
            ):  # remove times that do not contains digit (like 'today', 'dusk', 'the night', etc...)
                dicts.clear()
            elif re.search(
                "-WE$", str(dicts["value"])
            ):  # remove times of type XXXX-WX-WE (weeks/week-end)
                dicts.clear()
            elif re.search(
                "-W", str(dicts["value"])
            ):  # remove times of type XXXX-WX-WE (weeks/week-end)
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
            elif re.search("^\+.*", str(dicts["value"])):  # remove +XXXX alone
                dicts.clear()
            elif re.search(
                str(str(date.today()).replace("-", "\-")), dicts["value"]
            ):  # remove date if it's today
                dicts["value"] = re.sub(
                    str(str(date.today()).replace("-", "\-")), "", dicts["value"]
                )
                dicts["timex-value"] = re.sub(
                    str(str(date.today()).replace("-", "\-")), "", dicts["timex-value"]
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
        # or the begin one
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


def nearest_date(JSON_list, compteur_dicts):
    compteur_avant = compteur_dicts - 1
    compteur_apres = compteur_dicts + 1
    avant = 0
    apres = 0
    # browse the elements contained before JSON_list[counter_dicts] in JSON_list
    while compteur_avant >= 0:
        if JSON_list[compteur_avant]["type"] == "DATE":
            if re.search(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)", JSON_list[compteur_avant]["value"]
            ):
                avant = JSON_list[compteur_avant]
                break
        elif JSON_list[compteur_avant]["type"] == "DURATION":
            if re.search(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)",
                JSON_list[compteur_avant]["value"]["begin"],
            ) and re.search(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)",
                JSON_list[compteur_avant]["value"]["end"],
            ):
                avant = JSON_list[compteur_avant]
                break
        compteur_avant -= 1

    # browse the elements contained after JSON_list[counter_dicts] in JSON_list
    while compteur_apres < len(JSON_list):
        if JSON_list[compteur_apres]["type"] == "DATE":
            if re.search(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)", JSON_list[compteur_apres]["value"]
            ):
                apres = JSON_list[compteur_apres]
                break
        elif JSON_list[compteur_apres]["type"] == "DURATION":
            if re.search(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)",
                JSON_list[compteur_apres]["value"]["begin"],
            ) and re.search(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)",
                JSON_list[compteur_apres]["value"]["end"],
            ):
                avant = JSON_list[compteur_apres]
                break
        compteur_apres += 1

    if avant == 0:  # case: no DATE or DURATION before
        nearest = JSON_list[compteur_apres]
    elif apres == 0:  # case: no DATE or DURATION after
        nearest = JSON_list[compteur_avant]
    elif abs(
        JSON_list[compteur_avant]["end"] - JSON_list[compteur_dicts]["start"]
    ) < abs(
        JSON_list[compteur_dicts]["end"] - JSON_list[compteur_apres]["start"]
    ):  # closer between before and after: it is before
        nearest = JSON_list[compteur_avant]
    else:  # closer between before and after: it is after
        nearest = JSON_list[compteur_apres]
    return nearest


def nearest_year(JSON_list, compteur_dicts):
    if JSON_list[compteur_dicts]["type"] == "DURATION":
        if re.search(
            "((XXXX)-[0-9]{2}-[0-9]{2})", JSON_list[compteur_dicts]["value"]["begin"]
        ):
            nearest = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_dicts]["value"]["end"],
            )
            if nearest != None:
                return nearest.group(2)
        elif re.search(
            "((XXXX)-[0-9]{2}-[0-9]{2})", JSON_list[compteur_dicts]["value"]["end"]
        ):
            nearest = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_dicts]["value"]["begin"],
            )
            if nearest != None:
                return nearest.group(2)

    compteur_avant = compteur_dicts - 1
    compteur_apres = compteur_dicts + 1
    avant = 0
    apres = 0
    # browse the elements contained before JSON_list[counter_dicts] in JSON_list
    while compteur_avant >= 0:
        if JSON_list[compteur_avant]["type"] == "DATE":
            matcher = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_avant]["value"]
            )
            if matcher != None:
                avant = JSON_list[compteur_avant]
                break
        elif JSON_list[compteur_avant]["type"] == "DURATION":
            matcher_begin = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_avant]["value"]["begin"],
            )
            matcher_end = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_avant]["value"]["end"],
            )
            if matcher_begin != None or matcher_end != None:
                avant = JSON_list[compteur_avant]
                break
        elif JSON_list[compteur_avant]["type"] == "TIME":
            matcher = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_avant]["value"]
            )
            if matcher != None:
                avant = JSON_list[compteur_avant]
                break
        compteur_avant -= 1

    # browse the elements contained after JSON_list[counter_dicts] in JSON_list
    while compteur_apres < len(JSON_list):
        if JSON_list[compteur_apres]["type"] == "DATE":
            matcher = re.match(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_apres]["value"]
            )
            if matcher != None:
                apres = JSON_list[compteur_apres]
                break
        elif JSON_list[compteur_apres]["type"] == "DURATION":
            matcher_begin = re.match(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_apres]["value"]["begin"],
            )
            matcher_end = re.match(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_apres]["value"]["end"],
            )
            if matcher_begin != None or matcher_end != None:
                apres = JSON_list[compteur_apres]
                break
        elif JSON_list[compteur_apres]["type"] == "TIME":
            matcher = re.match(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_apres]["value"]
            )
            if matcher != None:
                avant = JSON_list[compteur_apres]
                break
        compteur_apres += 1

    if avant == 0:  # case: no DATE or DURATION before
        if JSON_list[compteur_apres]["type"] == "DATE":
            nearest = re.match(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_apres]["value"]
            ).group(2)
        elif JSON_list[compteur_apres]["type"] == "TIME":
            nearest = re.match(
                "((^[0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_apres]["value"]
            ).group(2)
        elif JSON_list[compteur_apres]["type"] == "DURATION":
            if re.search(
                "((XXXX)-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_apres]["value"]["begin"],
            ):
                nearest = re.match(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_apres]["value"]["end"],
                )
                if nearest != None:
                    return nearest.group(2)
            elif re.search(
                "((XXXX)-[0-9]{2}-[0-9]{2})", JSON_list[compteur_apres]["value"]["end"]
            ):
                nearest = re.match(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_apres]["value"]["begin"],
                )
                if nearest != None:
                    return nearest.group(2)
            else:
                if re.search(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_apres]["value"]["begin"],
                ):
                    nearest = re.match(
                        "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                        JSON_list[compteur_apres]["value"]["begin"],
                    ).group(2)
                elif re.search(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_apres]["value"]["end"],
                ):
                    nearest = re.match(
                        "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                        JSON_list[compteur_apres]["value"]["end"],
                    ).group(2)
    elif apres == 0:  # case: no DATE or DURATION after
        if JSON_list[compteur_avant]["type"] == "DATE":
            nearest = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_avant]["value"]
            ).group(2)
        elif JSON_list[compteur_avant]["type"] == "TIME":
            nearest = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_avant]["value"]
            ).group(2)
        elif JSON_list[compteur_avant]["type"] == "DURATION":
            if re.search(
                "((XXXX)-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_avant]["value"]["begin"],
            ):
                nearest = re.match(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_avant]["value"]["end"],
                )
                if nearest != None:
                    return nearest.group(2)
            elif re.search(
                "((XXXX)-[0-9]{2}-[0-9]{2})", JSON_list[compteur_avant]["value"]["end"]
            ):
                nearest = re.match(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_avant]["value"]["begin"],
                )
                if nearest != None:
                    return nearest.group(2)
            else:
                if re.search(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_avant]["value"]["begin"],
                ):
                    nearest = re.match(
                        "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                        JSON_list[compteur_avant]["value"]["begin"],
                    ).group(2)
                elif re.search(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_avant]["value"]["end"],
                ):
                    nearest = re.match(
                        "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                        JSON_list[compteur_avant]["value"]["end"],
                    ).group(2)
    elif abs(
        JSON_list[compteur_avant]["end"] - JSON_list[compteur_dicts]["start"]
    ) < abs(
        JSON_list[compteur_dicts]["end"] - JSON_list[compteur_apres]["start"]
    ):  # plus proche entre avant et après: c'est avant
        if JSON_list[compteur_avant]["type"] == "DATE":
            nearest = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_avant]["value"]
            ).group(2)
        elif JSON_list[compteur_avant]["type"] == "TIME":
            nearest = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_avant]["value"]
            ).group(2)
        elif JSON_list[compteur_avant]["type"] == "DURATION":
            matcher_begin = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_avant]["value"]["begin"],
            )
            if matcher_begin != None:
                nearest = re.match(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_avant]["value"]["begin"],
                ).group(2)
            matcher_end = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_avant]["value"]["end"],
            )
            if matcher_end != None:
                nearest = re.match(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_avant]["value"]["end"],
                ).group(2)
    else:  # closer between before and after: it is after
        if JSON_list[compteur_apres]["type"] == "DATE":
            nearest = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_apres]["value"]
            ).group(2)
        elif JSON_list[compteur_apres]["type"] == "TIME":
            nearest = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})", JSON_list[compteur_apres]["value"]
            ).group(2)
        elif JSON_list[compteur_apres]["type"] == "DURATION":
            matcher_begin = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_apres]["value"]["begin"],
            )
            if matcher_begin != None:
                nearest = re.match(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_apres]["value"]["begin"],
                ).group(2)
            matcher_end = re.match(
                "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                JSON_list[compteur_apres]["value"]["end"],
            )
            if matcher_end != None:
                nearest = re.match(
                    "(([0-9]{4})-[0-9]{2}-[0-9]{2})",
                    JSON_list[compteur_apres]["value"]["end"],
                ).group(2)
    return nearest


def SUTime_transform(current_OCR_folder):
    _logger.info("SUTime_transform -> res_sutime2.json")
    orig_sutime_file = os.path.join(current_OCR_folder, "res_sutime.json")
    with open(orig_sutime_file, "r") as file:
        reading = file.read()
        JSON_list = eval(reading)

    # stockage dans la date d'aujourd'hui au format YYYY-MM-DD
    today = datetime.today().strftime("%Y-%m-%d")
    # stockage de l'année actuelle
    current_year = re.match("(((^[0-9]{4})|(XXXX))-[0-9]{2}-[0-9]{2}$)", today).group(2)

    for dicts in JSON_list:
        if dicts["type"] == "DATE":
            dicts["value"] = re.sub(rf"{current_year}", "XXXX", dicts["value"])
        elif dicts["type"] == "TIME":
            dicts["value"] = re.sub(rf"{current_year}", "XXXX", dicts["value"])
        elif dicts["type"] == "DURATION":
            if "begin" not in dicts["value"] or "end" not in dicts["value"]:
                dicts.clear()
            else:
                dicts["value"]["begin"] = re.sub(
                    rf"{current_year}", "XXXX", dicts["value"]["begin"]
                )
                dicts["value"]["end"] = re.sub(
                    rf"{current_year}", "XXXX", dicts["value"]["end"]
                )

    JSON_list = [i for i in JSON_list if i != {}]  # filtrage des dictionnaires vides

    raw_dumper.dump_to_raw(JSON_list, "Current Year to XXXX", current_OCR_folder)

    # resolution of all XXXX
    compteur_dicts = 0
    for dicts in JSON_list:
        if dicts["type"] == "DURATION":
            if "begin" in dicts["value"]:
                if re.search("XXXX", dicts["value"]["begin"]):
                    year = nearest_year(JSON_list, compteur_dicts)
                    JSON_list[compteur_dicts]["value"]["begin"] = re.sub(
                        r"XXXX", year, dicts["value"]["begin"]
                    )
            if "end" in dicts["value"]:
                if re.search("XXXX", dicts["value"]["end"]):
                    year = nearest_year(JSON_list, compteur_dicts)
                    JSON_list[compteur_dicts]["value"]["end"] = re.sub(
                        r"XXXX", year, dicts["value"]["end"]
                    )
        elif dicts["type"] == "DATE":
            if re.search("XXXX", dicts["value"]):
                year = nearest_year(JSON_list, compteur_dicts)
                JSON_list[compteur_dicts]["value"] = re.sub(
                    "XXXX", year, dicts["value"]
                )
        elif dicts["type"] == "TIME":
            if re.search("XXXX", dicts["value"]):
                year = nearest_year(JSON_list, compteur_dicts)
                JSON_list[compteur_dicts]["value"] = re.sub(
                    "XXXX", year, dicts["value"]
                )
        compteur_dicts += 1

    raw_dumper.dump_to_raw(
        JSON_list, "Resolution of XXXX to closest year in text", current_OCR_folder
    )

    for dicts in JSON_list:
        try:
            # Removal in the DURATIONS of the "+0000" added in the times, induced by the reading of "UTC" by SUTime
            if dicts["type"] == "DURATION":
                dicts["value"]["begin"] = re.sub("\+0000", "", dicts["value"]["begin"])
                dicts["value"]["end"] = re.sub("\+0000", "", dicts["value"]["end"])
            else:
                dicts["value"] = re.sub("\+0000", "", dicts["value"])
        except:
            continue

    for dicts in JSON_list:
        try:
            # TIMES
            if dicts["type"] == "TIME":
                # search for a time that is at least THH (with all possible variations of YYYY-MM-DDTHH:MM:SS.msmsmsms)
                test = re.match(
                    "((?:[0-9]{4})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)(T)([0-9]{2})((?:(\:))?)((?:[0-9]{2})?)((?:\:)?)((?:[0-9]{2})?)((?:\.)?)((?:[0-9]{1,4})?)",
                    dicts["value"],
                )
                if test != None:
                    begin = ""
                    end = ""

                    group_counter_max = len(test.groups())
                    while (
                        test.group(group_counter_max) == ""
                        or test.group(group_counter_max) == None
                    ):  # stop test at HH or MM or ...
                        group_counter_max -= 1

                    group_counter_min = group_counter_max
                    while (
                        test.group(group_counter_min) != ""
                    ):  # test start at YYYY or MM or ...
                        if group_counter_min == 0:
                            break
                        group_counter_min -= 1
                    group_counter_min += 1

                    if group_counter_max == 16:  # end of ms (milliseconds)
                        if group_counter_min == 1:  # beginning in the years
                            begin = "".join(
                                list(
                                    test.group(1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15)
                                )
                            ) + str("%03d" % (int(test.group(group_counter_max)) - 1))
                            end = "".join(
                                list(
                                    test.group(1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15)
                                )
                            ) + str("%03d" % (int(test.group(group_counter_max)) + 1))
                        elif group_counter_min == 4:  # beginning at months
                            begin = "".join(
                                list(test.group(4, 5, 7, 8, 9, 10, 12, 13, 14, 15))
                            ) + str("%03d" % (int(test.group(group_counter_max)) - 1))
                            end = "".join(
                                list(test.group(4, 5, 7, 8, 9, 10, 12, 13, 14, 15))
                            ) + str("%03d" % (int(test.group(group_counter_max)) + 1))
                        elif group_counter_min == 8:  # start at T (undated time)
                            begin = "".join(
                                list(test.group(8, 9, 10, 12, 13, 14, 15))
                            ) + str("%03d" % (int(test.group(group_counter_max)) - 1))
                            end = "".join(
                                list(test.group(8, 9, 10, 12, 13, 14, 15))
                            ) + str("%03d" % (int(test.group(group_counter_max)) + 1))
                    elif group_counter_max == 14:  # end to the seconds
                        if group_counter_min == 1:  # beginning in the years
                            begin = "".join(
                                list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14))
                            ) + str(".%03d" % (000))
                            end = "".join(
                                list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14))
                            ) + str(".%03d" % (999))
                        elif group_counter_min == 4:  # beginning at months
                            begin = "".join(
                                list(test.group(4, 5, 7, 8, 9, 10, 12, 13, 14))
                            ) + str(".%03d" % (000))
                            end = "".join(
                                list(test.group(4, 5, 7, 8, 9, 10, 12, 13, 14))
                            ) + str(".%03d" % (999))
                        elif group_counter_min == 8:  # start at T (undated time)
                            begin = "".join(
                                list(test.group(8, 9, 10, 12, 13, 14))
                            ) + str(".%03d" % (000))
                            end = "".join(list(test.group(8, 9, 10, 12, 13, 14))) + str(
                                ".%03d" % (999)
                            )
                    elif group_counter_max == 12:  # end to the minutes
                        if group_counter_min == 1:  # beginning in the years
                            begin = "".join(
                                list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12))
                            ) + str(":" + "%02d" % (0))
                            end = "".join(
                                list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12))
                            ) + str(":" + "%02d" % (59))
                        elif group_counter_min == 4:  # beginning at months
                            begin = "".join(
                                list(test.group(4, 5, 7, 8, 9, 10, 12))
                            ) + str(":" + "%02d" % (0))
                            end = "".join(
                                list(test.group(4, 5, 7, 8, 9, 10, 12))
                            ) + str(":" + "%02d" % (59))
                        elif group_counter_min == 8:  # start at T (undated time)
                            begin = "".join(list(test.group(8, 9, 10, 12))) + str(
                                ":" + "%02d" % (0)
                            )
                            end = "".join(list(test.group(8, 9, 10, 12))) + str(
                                ":" + "%02d" % (59)
                            )
                    elif group_counter_max == 9:  # end of the hours
                        if group_counter_min == 1:  # beginning in the years
                            begin = (
                                "".join(list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12)))
                                + str(":" + "%02d" % (0))
                                + str(":" + "%02d" % (0))
                            )
                            end = (
                                "".join(list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12)))
                                + str(":" + "%02d" % (59))
                                + str(":" + "%02d" % (59))
                            )
                        elif group_counter_min == 4:  # beginning at months
                            begin = (
                                "".join(list(test.group(4, 5, 7, 8, 9, 10, 12)))
                                + str(":" + "%02d" % (0))
                                + str(":" + "%02d" % (0))
                            )
                            end = "".join(
                                list(test.group(4, 5, 7, 8, 9, 10, 12))
                            ) + str(":" + "%02d" % (59))
                        elif group_counter_min == 8:  # start at T (undated time)
                            begin = (
                                "".join(list(test.group(8, 9, 10, 12)))
                                + str(":" + "%02d" % (0))
                                + str(":" + "%02d" % (0))
                            )
                            end = (
                                "".join(list(test.group(8, 9, 10, 12)))
                                + str(":" + "%02d" % (59))
                                + str(":" + "%02d" % (59))
                            )
                    dicts["type"] = "DURATION"  # TIME becomes a DURATIONS
                    dicts["value"] = {
                        "begin": begin,
                        "end": end,
                    }  # Adding the new value
        except:
            continue

    raw_dumper.dump_to_raw(
        JSON_list, "Change type TIME to DURATION", current_OCR_folder
    )

    # date correction when in short format (YYYY-MM (no DD))
    compteur_dicts = 0
    for dicts in JSON_list:
        if dicts["type"] == "DATE":
            matched = re.search("^([0-9]{4})-([0-9]{2})$", dicts["value"])
            if matched:
                year, month = matched.groups()
                year, month = int(year), int(month)
                first, last = monthrange(year, month)
                begin = datetime(year, month, 1)
                end = datetime(year, month, last)
                DATEFORMAT = "%Y-%m-%d %H:%M:%S.000"

                dicts["type"] = "DURATION"
                dicts["value"] = {
                    "begin": begin.strftime(DATEFORMAT),
                    "end": end.strftime(DATEFORMAT),
                }
        compteur_dicts += 1

    raw_dumper.dump_to_raw(
        JSON_list,
        "Date rewriting: short date to whole month DURATION",
        current_OCR_folder,
    )

    # compteur = 0
    # for dicts in JSON_list:
    #     # addition of the nearest date contained in a DATE or DURATION when faced with a DURATION in the format {begin: T<one time>, end: T<one time>} (no date)
    #     try:
    #         if (
    #             dicts["type"] == "DURATION"
    #             and "begin" in dicts["value"]
    #             and "end" in dicts["value"]
    #         ):
    #             if re.search("^T.*", dicts["value"]["begin"]) and re.search(
    #                 "^T.*", dicts["value"]["end"]
    #             ):
    #                 nearest = nearest_date(JSON_list, compteur)
    #                 if nearest["type"] == "DATE":
    #                     temp = {
    #                         "begin": nearest["value"] + dicts["value"]["begin"],
    #                         "end": nearest["value"] + dicts["value"]["end"],
    #                     }
    #                     dicts["value"] = temp
    #                 elif nearest["type"] == "DURATION":
    #                     temp = {
    #                         "begin": nearest["value"]["begin"]
    #                         + dicts["value"]["begin"],
    #                         "end": nearest["value"]["end"] + dicts["value"]["end"],
    #                     }
    #                     dicts["value"] = temp
    #             elif re.search("^T.*", dicts["value"]["begin"]) and re.search(
    #                 "(([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})).*",
    #                 dicts["value"]["end"],
    #             ):  # case date in one but not in the other
    #                 temp = {
    #                     "begin": re.match(
    #                         "(([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})).*",
    #                         dicts["value"]["end"],
    #                     ).group(1)
    #                     + dicts["value"]["begin"],
    #                     "end": dicts["value"]["end"],
    #                 }
    #                 dicts["value"] = temp
    #             elif re.search("^T.*", dicts["value"]["end"]) and re.search(
    #                 "(([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})).*",
    #                 dicts["value"]["begin"],
    #             ):  # case date in one but not in the other
    #                 temp = {
    #                     "begin": dicts["value"]["begin"],
    #                     "end": re.match(
    #                         "(([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})).*",
    #                         dicts["value"]["begin"],
    #                     ).group(1)
    #                     + dicts["value"]["end"],
    #                 }
    #                 dicts["value"] = temp
    #
    #     except:
    #         continue
    #     compteur += 1
    #
    # raw_dumper.dump_to_raw(JSON_list, "DURATION gets Nearest date", current_OCR_folder)
    JSON_list = durations_to_prevdate(JSON_list)
    raw_dumper.dump_to_raw(JSON_list, "DURATION gets Previous date", current_OCR_folder)

    # Change DATE to DURATION
    for elmnt in JSON_list:
        if elmnt["type"] == "DATE":
            date_string = elmnt["value"]
            try:
                begin_date = parser.parse(date_string)
            except parser.ParserError:
                continue
            end_date = begin_date + timedelta(days=1) - timedelta(seconds=1)
            elmnt["value"] = {
                "begin": begin_date.isoformat(),
                "end": end_date.isoformat(),
            }
            elmnt["type"] = "DURATION"
    raw_dumper.dump_to_raw(
        JSON_list, "Change type DATE to DURATION", current_OCR_folder
    )

    # CLEAR EMPTY
    # At the end of the treatment, deletion of all SUTime results which is not a DURATION
    for dicts in JSON_list:
        if dicts["type"] != "DURATION":
            dicts.clear()
        elif dicts["type"] == "DURATION":
            if re.search("[0-9]{2}-[0-9]{2}$", dicts["value"]["begin"]) and re.search(
                "[0-9]{2}-[0-9]{2}$", dicts["value"]["end"]
            ):
                dicts["value"]["begin"] += "T00:00:00.000"
                dicts["value"]["end"] += "T23:59:59.000"
    JSON_list = [i for i in JSON_list if i != {}]

    raw_dumper.dump_to_raw(
        JSON_list, "Remove all but DURATION , add midnight", current_OCR_folder
    )

    # harmonise the formats, bring them all down to the millisecond
    for dicts in JSON_list:
        begin = re.match(
            "((?:[0-9X]{4})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)(T)([0-9]{2})((?:(\:))?)((?:[0-9]{2})?)((?:\:)?)((?:[0-9]{2})?)((?:\.)?)((?:[0-9X]{1,4})?)",
            dicts["value"]["begin"],
        )
        end = re.match(
            "((?:[0-9X]{4})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)(T)([0-9]{2})((?:(\:))?)((?:[0-9]{2})?)((?:\:)?)((?:[0-9]{2})?)((?:\.)?)((?:[0-9X]{1,4})?)",
            dicts["value"]["end"],
        )

        try:
            if begin.group(14) == "":
                dicts["value"]["begin"] += ":00.000"
            elif begin.group(12) == "":
                dicts["value"]["begin"] += ":00:00.000"
            elif begin.group(16) == "":
                dicts["value"]["begin"] += ".000"

            if end.group(14) == "":
                dicts["value"]["end"] += ":59.000"
            elif end.group(12) == "":
                dicts["value"]["end"] += ":59:59.000"
            elif end.group(16) == "":
                dicts["value"]["end"] += ".000"
        except:
            continue

    raw_dumper.dump_to_raw(JSON_list, "Do some .000 magic ", current_OCR_folder)

    for dicts in JSON_list:
        if not re.search(
            "^([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})(T)([0-9]{2})(:)([0-9]{2})(:)([0-9]{2})(.)([0-9]{3})$",
            dicts["value"]["begin"],
        ) or not re.search(
            "^([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})(T)([0-9]{2})(:)([0-9]{2})(:)([0-9]{2})(.)([0-9]{3})$",
            dicts["value"]["end"],
        ):
            dicts.clear()
    JSON_list = [i for i in JSON_list if i != {}]

    raw_dumper.dump_to_raw(JSON_list, "Remove wrong date format ", current_OCR_folder)

    # CLEAR EMPTY
    for dicts in JSON_list:
        if dicts["type"] != "DURATION":
            dicts.clear()
    JSON_list = [i for i in JSON_list if i != {}]

    raw_dumper.dump_to_raw(JSON_list, "Remove not DURATION", current_OCR_folder)

    final_sutime_file = os.path.join(current_OCR_folder, "res_sutime_2.json")
    # save the transformed results in a separate file.
    # This is the file that will be read for later linking of intervals/sat/inst/etc.
    _logger.info(f"OPENING {final_sutime_file}")
    with open(final_sutime_file, "w") as final_json:
        final_json.write(json.dumps(JSON_list, sort_keys=True, indent=4))
        final_json.close()
