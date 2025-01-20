import string
import collections
import copy
from datetime import *
from pprint import pprint
from typing import Dict, List, Tuple

from bht_config import yml_settings
from bht.DOI_finder import *
from bht.bht_logging import init_logger
from bht.catalog_tools import rows_to_catstring, dicts_to_df, df_to_dicts
from bht.databank_reader import DataBank, DataBankSheet
from bht.errors import BhtPipelineError
from bht.published_date_finder import *
from tools import RawDumper, structs_from_list

v = sys.version
token = "IXMbiJNANWTlkMSb4ea7Y5qJIGCFqki6IJPZjc1m"  # API Key

dump_step = 0

raw_dumper = RawDumper("entities")

punctuation_with_slash = string.punctuation.replace("/", "")


def show_final(fal):
    """Final_Amda_List structure displayer for debugging"""
    from pprint import pprint

    if len(fal) > 0:
        opening = ">" * 50
        ending = "<" * 50
        msg = f"{opening} {len(fal)} {ending}"
    else:
        msg = "0" * 100
    print("-" * len(msg))
    print(msg)
    print("-" * len(msg))
    pprint(fal)


def keys_exists(element, *keys):
    """
    Check if *keys (nested) exists in `element` (dict).
    """
    if not isinstance(element, dict):
        raise AttributeError("keys_exists() expects dict as first argument.")
    if len(keys) == 0:
        raise AttributeError("keys_exists() expects at least two arguments, one given.")

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True


# =====================================================================================================================
def load_dataframes():
    _dbk = DataBank()

    df_Satellites = _dbk.get_sheet_as_df(dbk_sheet=DataBankSheet.SATS)
    SAT_dict = {}
    for compteur_ligne in range(len(df_Satellites)):
        SAT_dict[str(df_Satellites.iloc[compteur_ligne, 0])] = []
        for compteur_colonne in range(len(df_Satellites.iloc[compteur_ligne])):
            if str(df_Satellites.iloc[compteur_ligne, compteur_colonne]) != "nan":
                SAT_dict[str(df_Satellites.iloc[compteur_ligne, 0])].append(
                    str(df_Satellites.iloc[compteur_ligne, compteur_colonne])
                )

    df_Instruments = _dbk.get_sheet_as_df(dbk_sheet=DataBankSheet.INSTR)
    INST_dict = {}
    for compteur_ligne in range(len(df_Instruments)):
        INST_dict[str(df_Instruments.iloc[compteur_ligne, 0])] = []
        for compteur_colonne in range(1, len(df_Instruments.iloc[compteur_ligne])):
            if str(df_Instruments.iloc[compteur_ligne, compteur_colonne]) != "nan":
                if re.search(
                    "^\{", df_Instruments.iloc[compteur_ligne, compteur_colonne]
                ):
                    INST_dict[str(df_Instruments.iloc[compteur_ligne, 0])].append(
                        eval(df_Instruments.iloc[compteur_ligne, compteur_colonne])
                    )
                else:
                    INST_dict[str(df_Instruments.iloc[compteur_ligne, 0])].append(
                        str(df_Instruments.iloc[compteur_ligne, compteur_colonne])
                    )

    df_Regions_general = _dbk.get_sheet_as_df(dbk_sheet=DataBankSheet.REG_GEN)
    REG_general_list = []
    for compteur_ligne in range(len(df_Regions_general)):
        REG_general_list.append(str(df_Regions_general.iloc[compteur_ligne, 0]))

    df_Regions = _dbk.get_sheet_as_df(dbk_sheet=DataBankSheet.REG_TREE)
    REG_dict = {}
    for compteur_ligne in range(len(df_Regions)):
        REG_dict[str(df_Regions.iloc[compteur_ligne, 0])] = {}
        for compteur_colonne in range(1, len(df_Regions.iloc[compteur_ligne])):
            if str(df_Regions.iloc[compteur_ligne, compteur_colonne]) != "nan":
                REG_dict[str(df_Regions.iloc[compteur_ligne, 0])].update(
                    eval(str(df_Regions.iloc[compteur_ligne, compteur_colonne]))
                )

    df_AMDA_SPASE = _dbk.get_sheet_as_df(dbk_sheet=DataBankSheet.SATS_REG)
    AMDA_dict = {}
    for compteur_ligne in range(len(df_AMDA_SPASE)):
        for compteur_colonne in range(1, len(df_AMDA_SPASE.iloc[compteur_ligne])):
            AMDA_dict[str(df_AMDA_SPASE.iloc[compteur_ligne, 0])] = eval(
                df_AMDA_SPASE.iloc[compteur_ligne, compteur_colonne]
            )

    df_operating_spans = _dbk.get_sheet_as_df(dbk_sheet=DataBankSheet.TIME_SPAN)
    SPAN_dict = {}
    for compteur_ligne in range(len(df_operating_spans)):
        SPAN_dict[str(df_operating_spans.iloc[compteur_ligne, 0])] = []
        for compteur_colonne in range(1, len(df_operating_spans.iloc[compteur_ligne])):
            SPAN_dict[str(df_operating_spans.iloc[compteur_ligne, 0])].append(
                str(df_operating_spans.iloc[compteur_ligne, compteur_colonne])
            )

    # For all operating spans, if no start or end date, default to T-Sputnik for the start, or today for the end.
    for elements, val in SPAN_dict.items():
        if val[0] == "nan":
            val[0] = "1957-10-04"  # T-Spoutnik
        if val[1] == "nan":
            val[1] = str(datetime.date(datetime.now()))

    returned_dict = {
        DataBankSheet.SATS: SAT_dict,
        DataBankSheet.INSTR: INST_dict,
        DataBankSheet.REG_GEN: REG_general_list,
        DataBankSheet.REG_TREE: REG_dict,
        DataBankSheet.SATS_REG: AMDA_dict,
        DataBankSheet.TIME_SPAN: SPAN_dict,
    }
    return returned_dict


def operating_span_checker(sat, durations, SAT_dict, SPAN_dict, published_date):
    # Checks that an interval linked to a satellite is included in the operating span of that satellite.
    try:
        # retrieves the primary (first) name of a satellite.
        sat_name = sat["text"]
        for syns in SAT_dict.values():
            if sat_name in syns:
                sat_name = syns[0]

        # cutting YYYY,MM,DD in the spans
        SPAN_start_year, SPAN_start_month, SPAN_start_day = (
            int(
                re.search(
                    "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", SPAN_dict[sat_name][0]
                ).group(2)
            ),
            int(
                re.search(
                    "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", SPAN_dict[sat_name][0]
                ).group(3)
            ),
            int(
                re.search(
                    "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", SPAN_dict[sat_name][0]
                ).group(4)
            ),
        )
        if published_date != None:
            SPAN_stop_year, SPAN_stop_month, SPAN_stop_day = (
                int(
                    re.search(
                        "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", published_date
                    ).group(2)
                ),
                int(
                    re.search(
                        "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", published_date
                    ).group(3)
                ),
                int(
                    re.search(
                        "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", published_date
                    ).group(4)
                ),
            )
        else:
            SPAN_stop_year, SPAN_stop_month, SPAN_stop_day = (
                int(
                    re.search(
                        "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", SPAN_dict[sat_name][1]
                    ).group(2)
                ),
                int(
                    re.search(
                        "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", SPAN_dict[sat_name][1]
                    ).group(3)
                ),
                int(
                    re.search(
                        "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", SPAN_dict[sat_name][1]
                    ).group(4)
                ),
            )

        # cutting YYYY,MM,DD into durations
        begin_year, begin_month, begin_day = (
            int(
                re.search(
                    "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", durations["value"]["begin"]
                ).group(2)
            ),
            int(
                re.search(
                    "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", durations["value"]["begin"]
                ).group(3)
            ),
            int(
                re.search(
                    "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", durations["value"]["begin"]
                ).group(4)
            ),
        )
        end_year, end_month, end_day = (
            int(
                re.search(
                    "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", durations["value"]["end"]
                ).group(2)
            ),
            int(
                re.search(
                    "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", durations["value"]["end"]
                ).group(3)
            ),
            int(
                re.search(
                    "(([0-9]{4})-([0-9]{2})-([0-9]{2}))", durations["value"]["end"]
                ).group(4)
            ),
        )

        # check: duration included in operating span
        if (
            datetime(begin_year, begin_month, begin_day)
            >= datetime(SPAN_start_year, SPAN_start_month, SPAN_start_day)
        ) and (
            datetime(end_year, end_month, end_day)
            <= datetime(SPAN_stop_year, SPAN_stop_month, SPAN_stop_day)
        ):
            return True
        else:
            return False
    except:
        return 1


# =================================================


def get_sat_syn(sat_name: str, _data_frames: dict):
    """
    From string, look for main mission synonymous

    @param sat_name:  sat name to search for
    @param _data_frames:  give access to sat_dict and amda_dict
    @return: main synonymous
    """
    sat_dict = _data_frames[DataBankSheet.SATS]
    amda_dict = _data_frames[DataBankSheet.SATS_REG]


    result = None

    # join both dict keys in one list, and see if the searched name is in
    main_names = list(sat_dict.keys()) + list(amda_dict.keys())
    if sat_name in main_names:
        result = sat_name

    # Now look for main synonymous in the sat_dict
    for main_syn, syns_list in sat_dict.items():
        if sat_name in syns_list:
            result = main_syn

    return result


def sat_recognition(content_as_str, sats_dict):
    """
    1st Entities Finder step:

    Find satellites and their synonyms in the Article's content

    @param content_as_str:  article's content as string
    @param sats_dict:  dict of satellites synonymous
    @return: dict of satellites found in the article
    """
    # Build a flatten list of all missions and their synonyms
    all_missions_names = []
    for _s in sats_dict.values():
        all_missions_names.extend(_s)
    # Detect mission names in text, and build a list of structs
    sat_dict_list = []
    for mission_name in all_missions_names:

        test = re.finditer("[;( \n]" + mission_name + "[’`';)., ]", content_as_str)
        for matches in test:
            _text = re.sub("[(\n.,);’`']", "", matches.group()).strip()
            sat_dict_list += [
                {
                    "start": matches.start(),
                    "end": matches.end(),
                    "text": _text,
                    "type": "sat",
                }
            ]


    if len(sat_dict_list) == 0:
        return sat_dict_list

    # Sort by text indexes
    sat_dict_list.sort(
        key=lambda matched_dict: (matched_dict["start"], matched_dict["end"])
    )

    # Remove duplicated start_indexes by keeping the longest found string
    # ( the latest, as it was sorted before)
    #
    # For example, when the text contains "Pioneer Venus Orbiter", pipeline will detect
    #
    #   {'start': 335, 'end': 344, 'text': 'Pioneer', 'type': 'sat'}
    #   {'start': 335, 'end': 350, 'text': 'Pioneer Venus', 'type': 'sat'}
    #   {'start': 335, 'end': 358, 'text': 'Pioneer Venus Orbiter', 'type': 'sat'}
    #
    # we want to keep the longest string, "Pioneer Venus Orbiter"
    _r_dict_list = []
    prev_dict = sat_dict_list.pop(0)
    for sat_dict in sat_dict_list:
        if sat_dict["start"] != prev_dict["start"]:
            _r_dict_list.append(prev_dict)
        prev_dict = sat_dict
    # add latest occurrence
    _r_dict_list.append(prev_dict)

    return _r_dict_list


# SAT recognition
def inst_recognition(content_as_str, inst_dict):
    """
    2nd Entities Finder step:

    Find instruments in the Article's content

    @param content_as_str:  article's content as string
    @param inst_dict: dict of instruments
    @return: dict of instruments found in the article
    """

    # Grab a flattened list of instruments structures from Entities_DataBank.xls file
    instruments_list = []
    for inst_list in inst_dict.values():
        instruments_list += inst_list

    pattern_string = " {searched_string}(\.|,| |;)"

    # INST recognition
    inst_dict_list = []
    for inst in instruments_list:
        if isinstance(inst, str):
            searched_pattern = pattern_string.format(searched_string=inst)
            test = re.finditer(searched_pattern, content_as_str)
            inst_dict_list += [
                {
                    "start": matches.start(),
                    "end": matches.end(),
                    "text": matches.group()
                    .strip()
                    .translate(str.maketrans("", "", punctuation_with_slash)),
                }
                for matches in test
            ]
        elif isinstance(inst, dict):
            for key, value in inst.items():
                searched_pattern = pattern_string.format(searched_string=key)
                test = re.finditer(searched_pattern, content_as_str)
                inst_dict_list += [
                    {
                        "start": matches.start(),
                        "end": matches.end(),
                        "text": matches.group()
                        .strip()
                        .translate(str.maketrans("", "", punctuation_with_slash)),
                    }
                    for matches in test
                ]
                if isinstance(value, str):
                    searched_pattern = pattern_string.format(searched_string=value)
                    test_2 = re.finditer(searched_pattern, content_as_str)
                    for matches in test_2:
                        inst_dict_list += [
                            {
                                "start": matches.start(),
                                "end": matches.end(),
                                "text": key,
                            }
                        ]
                elif isinstance(value, list):
                    for syns in value:
                        searched_pattern = pattern_string.format(searched_string=syns)
                        test_2 = re.finditer(searched_pattern, content_as_str)
                        for matches in test_2:
                            inst_dict_list += [
                                {
                                    "start": matches.start(),
                                    "end": matches.end(),
                                    "text": key,
                                }
                            ]
    # Sort by start
    inst_dict_list.sort(key=lambda matched_dict: matched_dict["start"])

    # Add 'type = instr'
    inst_dict_list = list(map(lambda _d: _d | {"type": "instr"}, inst_dict_list))

    # Remove overlapping
    res_inst_list = []
    for i, _d in enumerate(inst_dict_list):
        if i == 0:
            res_inst_list.append(_d)
            continue
        # keep only if current start after previous stop
        _p = inst_dict_list[i - 1]
        if _d["start"] > _p["end"]:
            res_inst_list.append(_d)

    return res_inst_list


def clean_sats_inside_insts(sats_list, insts_list):
    """
    3rd Entities Finder step:

    Remove from list any satellites which time span is included in any instrument's time span.

    @param sats_list:  the satellites time span list
    @param insts_list:  the instruments time span list
    @return:  the cleaned satellites list
    """
    # remove satellites matches included in spans of instrument matches
    temp = []
    for sat_1 in sats_list:
        for inst_2 in insts_list:
            if sat_1 != {}:
                if (inst_2["start"] - 1 <= sat_1["start"]) and (
                    inst_2["end"] + 1 >= sat_1["end"]
                ):  # is include
                    print(f"Removing {sat_1['text']}")
                    sat_1.clear()
                    # break
        temp.append(sat_1)
    res_sats = [i for i in temp if i != {}]
    return res_sats


def make_final_links(sats: list, insts: list, content: str):
    """
    4th Entities Finder step:

    Build a list of couples containing
        - the cleaned sats
        - a list of instruments with middle of content as end/start


    @param sats: cleaned sats list
    @param insts: uniq sorted list of found instruments
    @param content:  articles content as string
    @return: the list of final links
    """
    _final_links = []
    for _s in sats:
        _final_links.append(
            [
                _s,
                {
                    "end": (len(content) / 2) + 1,
                    "start": (len(content) / 2),
                    "text": insts,
                },
            ]
        )
    return _final_links


def update_final_instruments(_final_links, data_frames):
    """
    5th Entities Finder step:

    For each found satellite check the instruments that belong to them respectively.

    @param _final_links:
    @param data_frames:
    @return:
    """
    _fl = copy.deepcopy(_final_links)
    insts_dict = data_frames[DataBankSheet.INSTR]
    for elements in _fl:
        temp = []
        try:
            for inst in elements[1]["text"]:
                INST_temp = []
                for elems in insts_dict[elements[0]["text"]]:
                    if isinstance(elems, str):
                        INST_temp.append(elems)
                    elif isinstance(elems, dict):
                        for key in elems.keys():
                            INST_temp.append(key)
                if inst in INST_temp:
                    temp.append(inst)
        except Exception as e:
            elements[1]["text"] = []
        elements[1]["text"] = temp
    return _fl


def update_final_synonyms(_final_links, _data_frames):
    """
    6th Entities Finder step:

    Change the names of all found satellites by their main name
    (AMDA name when existing OR first name in sat_dict)

    @param _data_frames:  give access to sat_dict and amda_dict
    @param _final_links:  list to deal with
    @return: changed final_links list
    """
    _fl = copy.deepcopy(_final_links)
    for _link in _fl:
        sat_name = _link[0]["text"]
        sat_syn = get_sat_syn(sat_name, _data_frames)
        _link[0]["text"] = sat_syn

    return _fl


def add_sat_occurrence(_final_links, _sutime_json):
    """
    7th Entities Finder step:

    Count number of times each satellite appears.
    Add this value to the final_links list.

    @param _final_links: final_links orig list
    @param _sutime_json: the json to concatenate
    @return: final_links enhanced, temp strange concatenation for later use
    """
    _fl_to_return = copy.deepcopy(_final_links)

    # satellite occurrence counting and integrations
    list_occur = dict(
        collections.Counter([dicts[0]["text"] for dicts in _fl_to_return])
    )
    for elems in _fl_to_return:
        elems[0]["SO"] = list_occur[elems[0]["text"]]

    _temp = [elem[0] for elem in _fl_to_return]
    _temp += _sutime_json
    _temp = sorted(_temp, key=lambda d: d["start"])

    return _temp, _fl_to_return


def in_time_span(mission_name, start_stop, dataframes):
    from dateutil import parser

    # may raise KeyError
    mission_start, mission_stop = [
        parser.parse(d) for d in dataframes["time_span"][mission_name]
    ]

    event_start, event_stop = parser.parse(start_stop[0]), parser.parse(start_stop[1])
    if (
        mission_start <= event_start <= mission_stop
        or mission_start <= event_stop <= mission_stop
    ):
        return True
    else:
        return False


def get_prev_mission(_final_links, start_stop, data_frames):
    prev_mission = None
    _r = 0
    for _fl in _final_links[::-1]:
        if _fl[0]["type"] == "sat":
            _r = _r + 1
            mission_name = _fl[0]["text"]
            if in_time_span(mission_name, start_stop, data_frames):
                prev_mission = copy.deepcopy(_fl)
                prev_mission[0]["R"] = _r
                break
    return prev_mission


def duration_to_mission(_temp, _final_links, data_frames):
    """
    From a given duration, find the closest previous mission with proper time_span

    FIXME:  _temps structs and _final_links structs have same  memory address
            Thus, modifying the first one, changes the other.
    """
    _res_links = []

    # Merge DURATIONS  from _temp and 'sats' from _final_links
    # sort by 'start' field
    #
    # _final_links is of the form
    # [ [{sat}, {instr}], [{s},{i}], .... [{s},{i}]]
    #
    # it ends with durations inserted among [sat,instr] list
    # [ [{sat}, {instr}], [{s},{i}], [{duration}], [{s},{i}] ...., [{duration}], ..., [{s},{i}]]
    #

    # 1- extract a list of duration as list of 1 element lists
    _durations = [[_t] for _t in _temp if _t["type"] == "DURATION"]
    # 2- add to final links list
    _final_links.extend(_durations)
    # 3- sort by char 'start' field
    _final_links = sorted(_final_links, key=lambda d: d[0]["start"])

    # Go to first DURATION,
    # get the previous mission,
    # build a [{sat}, {instr}, {duration}]
    # add to the result list
    for i, _fl in enumerate(_final_links):
        _fl0 = _fl[0]  # either 'duration' or 'sat'
        if _fl0["type"] != "DURATION":
            continue
        duration_start_stop = [_fl0["value"]["begin"], _fl0["value"]["end"]]
        _mission = get_prev_mission(_final_links[:i], duration_start_stop, data_frames)
        if _mission is None:
            continue
        _mission.append(_fl0)
        # now compute D
        _satellite = _mission[0]
        _duration = _mission[2]  # which is in fact _fl0
        _d = abs(_satellite["start"] - _duration["start"])
        _satellite["D"] = _d
        _res_links.append(_mission)

    return _temp, _res_links


def closest_duration(_temp, _final_links, data_frames, published_date):
    """
    8th Entities Finder step:

    @param _temp:
    @param _final_links:
    @param data_frames:
    @param published_date:
    @return: temp, final_links
    """
    # FIXME: CRITICAL deepcopy should work. Look at temp generation to understand
    # _fl_to_return = copy.deepcopy(_final_links)
    # _temp_to_return = copy.deepcopy(_temp)
    _fl_to_return = _final_links
    _temp_to_return = _temp
    sat_dict = data_frames[DataBankSheet.SATS]
    span_dict = data_frames[DataBankSheet.TIME_SPAN]
    dicts_index = 0
    for dicts in _temp_to_return:
        dist_list = []

        compteur_rang_aller = 0
        compteur_rang_retour = 0

        if dicts["type"] == "sat":
            sens_aller = dicts_index
            sens_retour = dicts_index

            # direction -->
            while sens_aller < len(_temp_to_return):
                if _temp_to_return[sens_aller]["type"] != "sat":
                    compteur_rang_aller += 1
                    if (
                        operating_span_checker(
                            dicts,
                            _temp_to_return[sens_aller],
                            sat_dict,
                            span_dict,
                            published_date,
                        )
                        == True
                    ):
                        dicts["R"] = compteur_rang_aller
                        dist_list.append(_temp_to_return[sens_aller])
                        sens_aller = len(_temp_to_return)
                sens_aller += 1

            # direction <--
            while sens_retour >= 0:
                if _temp_to_return[sens_retour]["type"] != "sat":
                    compteur_rang_retour += 1
                    if (
                        operating_span_checker(
                            dicts,
                            _temp_to_return[sens_retour],
                            sat_dict,
                            span_dict,
                            published_date,
                        )
                        == True
                    ):
                        dicts["R"] = compteur_rang_retour
                        dist_list.append(_temp_to_return[sens_retour])
                        sens_retour = -1
                sens_retour -= 1

            # check of the closest between outward and backward.
            if len(dist_list) == 2:
                if (abs(dicts["start"] - dist_list[0]["start"])) < (
                    abs(dicts["start"] - dist_list[1]["start"])
                ):
                    min_dist = abs(dicts["start"] - dist_list[0]["start"])
                    compteur = 0
                    for elems in _fl_to_return:
                        if elems[0] == dicts:
                            _fl_to_return[compteur].append(dist_list[0])
                            _fl_to_return[compteur][0]["D"] = min_dist
                        compteur += 1
                else:
                    min_dist = abs(dicts["start"] - dist_list[1]["start"])
                    compteur = 0
                    for elems in _fl_to_return:
                        if elems[0] == dicts:
                            _fl_to_return[compteur].append(dist_list[1])
                            _fl_to_return[compteur][0]["D"] = min_dist
                        compteur += 1
            elif len(dist_list) == 1:
                min_dist = abs(dicts["start"] - dist_list[0]["start"])
                compteur = 0
                for elems in _fl_to_return:
                    if elems[0] == dicts:
                        _fl_to_return[compteur].append(dist_list[0])
                        _fl_to_return[compteur][0]["D"] = min_dist
                    compteur += 1
        else:
            continue
        dicts_index += 1

    return _temp_to_return, _fl_to_return


def normalize_links(_final_links, TSO):
    for elements in _final_links:
        if ("D" not in elements[0]) and ("R" in elements[0]):
            elements[0]["D"] = 1
        elif ("D" in elements[0]) and ("R" not in elements[0]):
            elements[0]["R"] = 1
        elif ("D" not in elements[0]) and ("R" not in elements[0]):
            elements[0]["D"] = 1
            elements[0]["R"] = 1

        elements[0]["conf"] = int(
            (elements[0]["D"] * elements[0]["R"])
            / (elements[0]["SO"] / TSO["occur_sat"])
        )  # à normalizer par max de conf

    # maxi = max([elements[0]["conf"] for elements in _final_links])
    # for elements in _final_links:
    #    elements[0]["conf"] = (
    #        elements[0]["conf"] / maxi
    #    )  # normalisation by the maximum confidence index
    return _final_links


def remove_duplicated(_final_links):
    """Filter lines to have uniq tuple start, stop, mission, instrument, region, conf"""
    _fl = copy.deepcopy(_final_links)
    _fl_df = dicts_to_df(_fl)
    cols_for_dropping = ["inst", "sat", "start_time", "stop_time"]
    _fl_uniq = _fl_df.drop_duplicates(subset=cols_for_dropping)
    return df_to_dicts(_fl_uniq)


def clean_by_timespan(_final_links, dataframes):
    _fl = copy.deepcopy(_final_links)

    _fl_df = dicts_to_df(_fl)

    _r_df = _fl_df[_fl_df.apply(in_time_span, axis=1)]
    _r_fl = df_to_dicts(_r_df)
    return _r_fl

def filter_duplicates(data):

    def group_duplicates(data: List[dict]) -> Dict[Tuple, List[dict]]:
        """
        Groups entries based on (start_time, stop_time, sat, inst)

        Args:
            data: List of dictionaries containing the observations

        Returns:
            Dictionary with identifier tuple as key and list of matching entries as value
            All entries are returned, including non-duplicates
        """
        # Using defaultdict to automatically create an empty list if key doesn't exist
        groups = defaultdict(list)

        # Process each entry
        for entry in data:
            # Skip pipeline metadata entry
            if not isinstance(entry, dict) or "start_time" not in entry:
                continue

            # Create identifier tuple
            identifier = (
                entry["start_time"],
                entry["stop_time"],
                entry["sat"],
                entry["inst"],
            )

            # Add complete entry to corresponding group
            groups[identifier].append(entry)

        # Return all groups, not just duplicates
        return dict(groups)

    def remove_duplicates(groups: Dict[Tuple, List[dict]]) -> Dict[Tuple, List[dict]]:
        """
        Filters groups by keeping only the entry with minimum 'conf' value in each group

        Args:
            groups: Dictionary with identifier tuple as key and list of entries as value

        Returns:
            Dictionary with same structure but only one entry per group (minimum conf)
        """
        filtered_groups = {}

        for identifier, entries in groups.items():
            # Find entry with minimum conf value
            min_conf_entry = min(entries, key=lambda x: x["conf"])
            # Store only this entry
            filtered_groups[identifier] = [min_conf_entry]

        return filtered_groups

    def groups_to_list(groups: Dict[Tuple, List[dict]]) -> List[dict]:
        """
        Converts the groups dictionary back to a flat list of entries

        Args:
            groups: Dictionary with identifier tuple as key and list of entries as value

        Returns:
            List of dictionary entries, in the same format as the original input
        """
        # Flatten the list of lists using list comprehension
        entries = [entry for group in groups.values() for entry in group]
        return entries

    duplicates = group_duplicates(data)

    uniq = remove_duplicates(duplicates)

    entries = groups_to_list(uniq)

    return entries




def entities_finder(current_OCR_folder, doc_meta_info=None):
    _logger = init_logger()
    _logger.info("entities_finder ->   bibheliotech_V1.txt  ")

    def find_path(dict_obj, key, i=None):
        for k, v in dict_obj.items():
            # add key to path
            path.append(k)
            if isinstance(v, dict):
                # continue searching
                find_path(v, key, i)
            if isinstance(v, list):
                # search through list of dictionaries
                for i, item in enumerate(v):
                    # add the index of list that item dict is part of, to path
                    path.append(i)
                    if isinstance(item, dict):
                        # continue searching in item dict
                        find_path(item, key, i)
                    # if reached here, the last added index was incorrect, so removed
                    path.pop()
            if k == key:
                # add path to our result
                result.append(copy.copy(path))
            # remove the key added in the first line
            if path != []:
                path.pop()

    data_frames = load_dataframes()
    SAT_dict = data_frames[DataBankSheet.SATS]
    INST_dict = data_frames[DataBankSheet.INSTR]
    REG_general_list = data_frames[DataBankSheet.REG_GEN]
    REG_dict = data_frames[DataBankSheet.REG_TREE]
    AMDA_dict = data_frames[DataBankSheet.SATS_REG]
    SPAN_dict = data_frames[DataBankSheet.TIME_SPAN]

    # sanity checks
    DOI = doc_meta_info.get("doi") if doc_meta_info is not None else None
    publication_date = (
        doc_meta_info.get("pub_date") if doc_meta_info is not None else None
    )
    if DOI is None:
        # try to find in tei file
        import glob

        pattern = os.path.join(current_OCR_folder, "*.tei.xml")
        found = glob.glob(pattern)
        if len(found) == 0:
            raise BhtPipelineError("Couldn't find any tei.xml file")
        file_name = found[0]
        DOI = find_DOI(file_name)  # retrieving the DOI of the article being processed.

    if publication_date is None:
        publication_date = published_date_finder(token, v, DOI)

    # loading the text file (content of the article)
    content_path = os.path.join(current_OCR_folder, "out_filtered_text.txt")

    with open(content_path, "r") as file:
        content_upper = file.read()

    # loading transformed SUTime results
    files_path_json = os.path.join(current_OCR_folder, "res_sutime_2.json")
    with open(files_path_json, "r") as sutime_file:
        sutime_json = json.load(sutime_file)

    # 1- satellites recognition
    sat_dict_list = sat_recognition(content_upper, SAT_dict)
    raw_dumper.dump_to_raw(sat_dict_list, "Satellites Recognition", current_OCR_folder)

    # 2- Instruments recognition
    inst_dict_list = inst_recognition(content_upper, INST_dict)
    raw_dumper.dump_to_raw(
        inst_dict_list, "Instruments Recognition", current_OCR_folder
    )

    # 3- clean sats list when timespan included in instruments
    new_sat_dict_list = clean_sats_inside_insts(sat_dict_list, inst_dict_list)
    step_message = "Remove from list any satellites which time span is included in any instrument's time span."
    raw_dumper.dump_to_raw(new_sat_dict_list, step_message, current_OCR_folder)

    # - Get the uniq instruments list ordered
    inst_list = list(set([inst["text"] for inst in inst_dict_list]))

    # 4- Make a list of lists ... see make_final_links() for more details.
    final_links = make_final_links(new_sat_dict_list, inst_list, content_upper)
    raw_dumper.dump_to_raw(
        final_links, "Cleaned sats with instr list", current_OCR_folder
    )

    # 6- Change the names of all found satellites by their main name
    final_links = update_final_synonyms(final_links, data_frames)
    raw_dumper.dump_to_raw(
        final_links, "Change sat name with base synonym", current_OCR_folder
    )

    # 5- Update instruments list for each satellite in links list
    final_links = update_final_instruments(final_links, data_frames)
    raw_dumper.dump_to_raw(
        final_links, "Remove instruments not in stats", current_OCR_folder
    )

    # 7- Add satellites occurrences to the list
    temp, final_links = add_sat_occurrence(final_links, sutime_json)
    raw_dumper.dump_to_raw(
        final_links, 'Add sats\' occurences: "SO"', current_OCR_folder
    )

    # 8- Association of the closest duration of a satellite.
    temp, final_links = duration_to_mission(temp, final_links, data_frames)
    raw_dumper.dump_to_raw(
        final_links, "Add closest duration from sutime files", current_OCR_folder
    )

    # 9- Normalisation
    TSO = {"occur_sat": len(new_sat_dict_list), "nb_durations": len(sutime_json)}
    final_links = normalize_links(final_links, TSO)
    raw_dumper.dump_to_raw(
        final_links, "Normalize links attributes", current_OCR_folder
    )

    # 10- REG recognition
    regs_dict_list = []

    for regs in REG_general_list:
        test = re.finditer(
            "( |\n)" + "(" + regs + "|" + regs.lower() + ")" + "(\.|,| )", content_upper
        )
        regs_dict_list += [
            {
                "type": "region",
                "end": matches.end(),
                "start": matches.start(),
                "text": matches.group()
                .strip()
                .translate(str.maketrans("", "", string.punctuation)),
            }
            for matches in test
        ]
    raw_dumper.dump_to_raw(regs_dict_list, "Find Region", current_OCR_folder)

    # 11- Association of the low-level region name
    #     (e.g. magnetosphere) with the nearest high-level name (planet name).

    planet_list = [
        "earth",
        "jupiter",
        "mars",
        "mercury",
        "neptune",
        "saturn",
        "sun",
        "uranus",
        "venus",
        "pluto",
        "heliosphere",
        "asteroid",
        "comet",
        "interstellar",
    ]

    dicts_index = 0
    founded_regions_list = []
    for dicts in regs_dict_list:
        if dicts["text"].lower() in planet_list:
            temp = []
            sens_aller = dicts_index + 1
            sens_retour = dicts_index - 1
            # direction -->
            while sens_aller < len(regs_dict_list):
                if regs_dict_list[sens_aller]["text"] not in planet_list:
                    temp.append(regs_dict_list[sens_aller])
                    temp.append(dicts)
                    founded_regions_list.append(temp)
                    temp = []
                sens_aller += 1
            # direction <--
            while sens_retour >= 0:
                if regs_dict_list[sens_retour]["text"] not in planet_list:
                    temp.append(dicts)
                    temp.append(regs_dict_list[sens_retour])
                    founded_regions_list.append(temp)
                    temp = []
                sens_retour -= 1
        dicts_index += 1

    raw_dumper.dump_to_raw(
        founded_regions_list,
        "Association of the low-level region name",
        current_OCR_folder,
    )

    # 11- Association of the low-level region name
    #     (e.g. magnetosphere) with the nearest high-level name (planet name).
    compteur = 0
    for elements in founded_regions_list:
        if (
            elements[0]["text"].lower() in planet_list
            and elements[1]["text"].lower() in planet_list
        ):
            if (
                elements[0]["text"].lower() != elements[1]["text"].lower()
            ):  # deletion of planet/planet pairs when these are different.
                founded_regions_list[compteur].clear()
        elif (elements[0]["text"].lower() not in planet_list) and (
            elements[1]["text"].lower() not in planet_list
        ):  # removal of low-level/low-level pairs.
            founded_regions_list[compteur].clear()
        compteur += 1
    founded_regions_list = [
        elements for elements in founded_regions_list if elements != []
    ]

    raw_dumper.dump_to_raw(
        founded_regions_list, "Filter founded regions list", current_OCR_folder
    )

    # 12 Re-organisation of the dictionary list:
    #   planets in index 0
    #   low level in index 1
    compteur = 0
    for list_of_dicts in founded_regions_list:
        if (list_of_dicts[0]["text"].lower() not in planet_list) and (
            list_of_dicts[1]["text"].lower() in planet_list
        ):
            temp_0 = founded_regions_list[compteur][0]
            temp_1 = founded_regions_list[compteur][1]
            founded_regions_list[compteur][0] = temp_1
            founded_regions_list[compteur][1] = temp_0
        compteur += 1
    raw_dumper.dump_to_raw(
        founded_regions_list,
        "Reorganisation of founded regions list",
        current_OCR_folder,
    )

    # 13- Checking and deleting planet/low level pairs is not possible
    #     (e.g. Mercury/Atmosphere)
    path = []
    compteur = 0
    for elements in founded_regions_list:
        result = []
        result.append(elements[0]["text"])
        find_path(
            REG_dict[str(elements[0]["text"][0].upper() + elements[0]["text"][1:])],
            elements[1]["text"][0].upper() + elements[1]["text"][1:],
        )  # params = planet name, low level name
        final_path = ""
        for i in result:
            if isinstance(i, str):
                final_path += i + "."
            elif isinstance(i, list):
                for j in i:
                    if isinstance(j, str):
                        final_path += j + "."
        final_path = re.sub("\.$", "", final_path)
        result = []

        if elements[0]["text"].lower() != elements[1]["text"].lower():
            if final_path == elements[0]["text"]:
                elements[1] = elements[0]
        compteur += 1

    raw_dumper.dump_to_raw(
        founded_regions_list, "Delete planets from regions list", current_OCR_folder
    )

    # 14- Removal of duplicate pairs
    compteur = 0
    for i in founded_regions_list:
        compteur_2 = compteur
        for j in founded_regions_list[compteur + 1 :]:
            if j == i:
                founded_regions_list[compteur_2].clear()
            compteur_2 += 1
        compteur += 1
    founded_regions_list = [
        elements for elements in founded_regions_list if elements != []
    ]

    raw_dumper.dump_to_raw(
        founded_regions_list, "Remove duplicated from regions list", current_OCR_folder
    )

    # 15- case satellite mentioned in the article but no region concerning it:
    #   default association with the first item in its region list.
    if len(founded_regions_list) == 0:
        for elements in final_links:
            sat = elements[0]["text"]
            if sat in AMDA_dict:
                regs = AMDA_dict[sat]
                for regions in regs:
                    subs = regions.split(".")
                    founded_regions_list.append(
                        [
                            {"end": 2, "start": 4, "text": subs[0]},
                            {"end": 6, "start": 8, "text": subs[-1]},
                        ]
                    )
        compteur = 0
        for i in founded_regions_list:
            compteur_2 = compteur
            for j in founded_regions_list[compteur + 1 :]:
                if j == i:
                    founded_regions_list[compteur_2].clear()
                compteur_2 += 1
            compteur += 1
        founded_regions_list = [
            elements for elements in founded_regions_list if elements != []
        ]

    raw_dumper.dump_to_raw(
        founded_regions_list,
        "case satellite mentioned in the article but no region",
        current_OCR_folder,
    )

    # 16- SAT and REG linker
    #     result and path should be outside the scope of find_path
    #     to persist values during recursive calls to the function
    path = []

    temp = []
    compteur_sat = 0
    for elems in final_links:
        temp_reg = []
        temp_reg += founded_regions_list
        finish = False
        while finish == False:
            first_passe = True
            compteur = 0
            compteur_min = 0

            for regs in temp_reg:
                if first_passe == True:
                    dist_min = abs(elems[0]["start"] - regs[1]["start"])
                    compteur_min = compteur
                    first_passe = False
                else:
                    if abs(elems[0]["start"] - regs[1]["start"]) < dist_min:
                        dist_min = abs(elems[0]["start"] - regs[1]["start"])
                        compteur_min = compteur
                compteur += 1

            # build the SPASE path
            # search in the tree structure
            result = []
            result.append(temp_reg[compteur_min][0]["text"])
            find_path(
                REG_dict[
                    temp_reg[compteur_min][0]["text"][0].upper()
                    + temp_reg[compteur_min][0]["text"][1:]
                ],
                temp_reg[compteur_min][1]["text"][0].upper()
                + temp_reg[compteur_min][1]["text"][1:],
            )  # params = planet name, low level name
            final_path = ""
            for i in result:
                if isinstance(i, str):
                    final_path += i + "."
                elif isinstance(i, list):
                    for j in i:
                        if isinstance(j, str):
                            final_path += j + "."
            final_path = re.sub("\.$", "", final_path)
            result = []

            # check for the existence of this nearest region in REG_dict
            if elems[0]["text"] in AMDA_dict:
                nearest_region = None
                if final_path in AMDA_dict[elems[0]["text"]]:
                    finish = True
                    nearest_region = temp_reg[compteur_min]
                    if len(final_links[compteur_sat]) == 3 and len(nearest_region) != 0:
                        final_links[compteur_sat] = [
                            final_links[compteur_sat][0],
                            final_links[compteur_sat][1],
                            nearest_region[0],
                            nearest_region[1],
                            final_links[compteur_sat][2],
                        ]
                    elif len(nearest_region) != 0:
                        final_links[compteur_sat] = [
                            final_links[compteur_sat][0],
                            final_links[compteur_sat][1],
                            nearest_region[0],
                            nearest_region[1],
                        ]
                    break
                else:
                    del temp_reg[compteur_min]
                    if len(temp_reg) == 0:
                        finish = True
                        break
            else:
                nearest_region = None
                finish = True
                break

        # case: nothing was found
        if len(temp_reg) == 0 or nearest_region == None:
            if elems[0]["text"] in AMDA_dict:
                temp = AMDA_dict[elems[0]["text"]][0].split(".")
                nearest_region = [
                    {"end": 10, "start": 0, "text": temp[0], "type": "region"},
                    {"end": 30, "start": 20, "text": temp[-1], "type": "region"},
                ]
                if len(final_links[compteur_sat]) == 3 and len(nearest_region) != 0:
                    final_links[compteur_sat] = [
                        final_links[compteur_sat][0],
                        final_links[compteur_sat][1],
                        nearest_region[0],
                        nearest_region[1],
                        final_links[compteur_sat][2],
                    ]
                elif len(nearest_region) != 0:
                    final_links[compteur_sat] = [
                        final_links[compteur_sat][0],
                        final_links[compteur_sat][1],
                        nearest_region[0],
                        nearest_region[1],
                    ]
            else:
                first_passe = True
                compteur = 0
                temp_reg = []
                temp_reg += founded_regions_list
                for regs in temp_reg:
                    if first_passe == True:
                        dist_min = abs(elems[0]["start"] - regs[1]["start"])
                        compteur_min = compteur
                        first_passe = False
                    else:
                        if abs(elems[0]["start"] - regs[1]["start"]) < dist_min:
                            dist_min = abs(elems[0]["start"] - regs[1]["start"])
                            compteur_min = compteur
                    compteur += 1
                nearest_region = temp_reg[compteur_min]
                if len(final_links[compteur_sat]) == 3 and len(nearest_region) != 0:
                    final_links[compteur_sat] = [
                        final_links[compteur_sat][0],
                        final_links[compteur_sat][1],
                        nearest_region[0],
                        nearest_region[1],
                        final_links[compteur_sat][2],
                    ]
                elif len(nearest_region) != 0:
                    final_links[compteur_sat] = [
                        final_links[compteur_sat][0],
                        final_links[compteur_sat][1],
                        nearest_region[0],
                        nearest_region[1],
                    ]

        compteur_sat += 1

    raw_dumper.dump_to_raw(final_links, "Sats / Region linker", current_OCR_folder)

    # 17- Now create events list according to the formatting below

    final_amda_list = []

    for elems in final_links:
        # Initialize dict
        final_amda_dict = {
            "start_time": "",
            "stop_time": "",
            "DOI": "",
            "sat": elems[0]["text"],
            "inst": ",".join(elems[1]["text"]),
            "reg": "",
            "D": elems[0]["D"],
            "R": elems[0]["R"],
            "SO": elems[0]["SO"],
            "conf": elems[0]["conf"],
        }
        duration = structs_from_list(elems, "DURATION")
        if type(duration) is list and len(duration) > 0:
            final_amda_dict["start_time"] = duration[0]["value"]["begin"]
            final_amda_dict["stop_time"] = duration[0]["value"]["end"]

        # search in the tree structure
        result = [elems[2]["text"]]

        # TODO: fix this expression
        find_path(
            REG_dict[elems[2]["text"][0].upper() + elems[2]["text"][1:]],
            elems[3]["text"][0].upper() + elems[3]["text"][1:],
        )  # params = planet name, low level name

        final_path = ""
        for i in result:
            if isinstance(i, str):
                final_path += i + "."
            elif isinstance(i, list):
                for j in i:
                    if isinstance(j, str):
                        final_path += j + "."
        final_path = re.sub("\.$", "", final_path)
        result = []
        final_amda_dict["reg"] = final_path
        final_amda_list.append(final_amda_dict)

    # rhi 20240604: disable " ", "-" substitution
    # for dicts in final_amda_list:
    #     dicts["inst"] = ",".join(list(set(dicts["inst"].split(",")))).replace(" ", "-")
    #     dicts["sat"] = dicts["sat"].strip().replace(" ", "-")

    # insert DOI in the field provided.
    for elements in final_amda_list:
        elements["DOI"] = DOI

    final_amda_list = sorted(final_amda_list, key=lambda d: d["start_time"])

    raw_dumper.dump_to_raw(
        final_amda_list,
        f"Found {len(final_amda_list)} events (see json)",
        current_OCR_folder,
    )

    # 18- Filter Sats for to uniq

    distinct_sats = list(set([dicts["sat"] for dicts in final_amda_list]))

    for elems in final_amda_list:
        if elems["start_time"] == "" and elems["stop_time"] == "":
            elems.clear()

    final_amda_list = [i for i in final_amda_list if i != {}]

    temp = []
    temp_final = []
    for sats in distinct_sats:
        for dicts in final_amda_list:
            if dicts["sat"] == sats:
                temp.append(dicts)
        temp_final.append(temp)
        temp = []

    raw_dumper.dump_to_raw(
        final_amda_list,
        f"Events list cleaned to {len(final_amda_list)} elements (see json)",
        current_OCR_folder,
    )

    # 19- Remove duplicated tuple (start, stop, mission)
    final_amda_list = remove_duplicated(final_amda_list)
    raw_dumper.dump_to_raw(
        final_amda_list,
        f"Remove duplicated events",
        current_OCR_folder,
    )

    # write in file
    with open(
        os.path.join(current_OCR_folder, "reg_recognition_res.txt"), "w"
    ) as final_file:
        for elems in final_amda_list:
            final_file.write(str(elems))
            final_file.write("\n")

    # =============================================================================================================================================================
    # display results if debug mode
    columns_to_display = [
        "start_time",
        "stop_time",
        "doi",
        "sats",
        "insts",
        "regs",
        "d",
    ]
    cat = rows_to_catstring(
        final_amda_list, catalog_name=None, columns=columns_to_display
    )
    _logger.debug(cat)
    # =============================================================================================================================================================

    translated_doi = DOI.translate(str.maketrans("", "", string.punctuation))
    bht_pipeline_version = yml_settings["BHT_PIPELINE_VERSION"]
    catalog_name = f"{translated_doi}_bibheliotech_V{bht_pipeline_version}.txt"

    # add two more elements in hpevent dict:
    tso_dict = {
        "occur_sat": str(TSO["occur_sat"]),
        "nb_durations": str(TSO["nb_durations"]),
    }
    final_amda_list = [{**tso_dict, **hpevent_dict} for hpevent_dict in final_amda_list]

    columns_to_display.extend(["r", "so", "occur_sat", "nb_durations", "conf"])
    cat_as_txt = rows_to_catstring(
        final_amda_list, catalog_name=catalog_name, columns=columns_to_display
    )

    catalog_path = os.path.join(current_OCR_folder, catalog_name)
    with open(
        catalog_path,
        "w",
    ) as f:
        f.write(cat_as_txt)

    return catalog_path


if __name__ == "__main__":
    pass
