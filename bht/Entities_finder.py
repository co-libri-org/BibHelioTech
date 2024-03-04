import string
import collections
import copy
from datetime import *

from bht.DOI_finder import *
from bht.bht_logging import init_logger
from bht.databank_reader import DataBank, DataBankSheet
from bht.errors import BhtPipelineError
from bht.published_date_finder import *
from tools import RawDumper

v = sys.version
token = "IXMbiJNANWTlkMSb4ea7Y5qJIGCFqki6IJPZjc1m"  # API Key

dump_step = 0

raw_dumper = RawDumper("entities")


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
    From string, look for main misison synonymous

    @param sat_name:  sat name to search for
    @param _data_frames:  give access to sat_dict and amda_dict
    @return: main synonymous
    """
    sat_dict = _data_frames[DataBankSheet.SATS]
    amda_dict = _data_frames[DataBankSheet.SATS_REG]

    # for k, v in sat_dict.items():
    #     print(k, v)

    # join both dict keys in one list, and see if the searched name is in
    main_names = list(sat_dict.keys()) + list(amda_dict.keys())
    if sat_name in main_names:
        return sat_name

    # Now look for mais synonymous in the sat_dict
    for main_syn, syns_list in sat_dict.items():
        if sat_name in syns_list:
            return main_syn

    return None


def sat_recognition(content_as_str, sats_dict):
    """
    1st Entities Finder step:

    Find satellites and their synonyms in the Article's content

    @param content_as_str:  article's content as string
    @param sats_dict:  dict of satellites synonymous
    @return: dict of satellites found in the article
    """
    sat_dict_list = []
    for SATs, Synonymes in sats_dict.items():
        for syns in Synonymes:
            test = re.finditer("( |\n)" + syns + "(\.|,| )", content_as_str)
            sat_dict_list += [
                {
                    "start": matches.start(),
                    "end": matches.end(),
                    "text": re.sub("(\n|\.|,)", "", matches.group()).strip(),
                    "type": "sat",
                }
                for matches in test
            ]
    sat_dict_list.sort(key=lambda matched_dict: matched_dict["start"])
    return sat_dict_list


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
                    .translate(str.maketrans("", "", string.punctuation)),
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
                        .translate(str.maketrans("", "", string.punctuation)),
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
        except:
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
        _name = _link[0]["text"] = sat_syn

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

        elements[0]["conf"] = (elements[0]["D"] * elements[0]["R"]) / (
            elements[0]["SO"] / TSO["occur_sat"]
        )  # à normalizé par max de conf

    maxi = max([elements[0]["conf"] for elements in _final_links])
    for elements in _final_links:
        elements[0]["conf"] = (
            elements[0]["conf"] / maxi
        )  # normalisation by the maximum confidence index
    return _final_links


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
    publication_date = doc_meta_info.get("pub_date") if doc_meta_info is not None else None
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

    # 5- Update instruments list for each satellite in links list
    final_links = update_final_instruments(final_links, data_frames)
    raw_dumper.dump_to_raw(
        final_links, "Remove instruments not in stats", current_OCR_folder
    )

    # 6- Change the names of all found satellites by their main name
    final_links = update_final_synonyms(final_links, data_frames)
    raw_dumper.dump_to_raw(
        final_links, "Change sat name with base synonym", current_OCR_folder
    )

    # 7- Add satellites occurrences to the list
    temp, final_links = add_sat_occurrence(final_links, sutime_json)
    raw_dumper.dump_to_raw(
        final_links, 'Add sats\' occurences: "SO"', current_OCR_folder
    )

    # 8- Association of the closest duration of a satellite.
    temp, final_links = closest_duration(
        temp, final_links, data_frames, publication_date
    )
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
                            final_links[compteur_sat][2]["value"],
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
                    {"end": 10, "start": 0, "text": temp[0]},
                    {"end": 30, "start": 20, "text": temp[-1]},
                ]
                if len(final_links[compteur_sat]) == 3 and len(nearest_region) != 0:
                    final_links[compteur_sat] = [
                        final_links[compteur_sat][0],
                        final_links[compteur_sat][1],
                        nearest_region[0],
                        nearest_region[1],
                        final_links[compteur_sat][2]["value"],
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
                        final_links[compteur_sat][2]["value"],
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

    final_amda_dict = {
        "start_time": "",
        "stop_time": "",
        "DOI": "",
        "sat": "",
        "inst": "",
        "reg": "",
        "D": "",
        "R": "",
        "SO": "",
    }
    final_amda_list = []

    for elems in final_links:
        final_amda_dict["sat"] = elems[0]["text"]
        final_amda_dict["inst"] = ",".join(elems[1]["text"])
        final_amda_dict["D"] = elems[0]["D"]
        final_amda_dict["R"] = elems[0]["R"]
        final_amda_dict["SO"] = elems[0]["SO"]
        final_amda_dict["conf"] = elems[0]["conf"]
        if len(elems) >= 5:
            final_amda_dict["start_time"] = elems[4]["begin"]
            final_amda_dict["stop_time"] = elems[4]["end"]
        # search in the tree structure
        result = []

        result.append(elems[2]["text"])

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
        final_amda_dict = {
            "start_time": "",
            "stop_time": "",
            "DOI": "",
            "sat": "",
            "inst": "",
            "reg": "",
            "D": "",
            "R": "",
            "SO": "",
        }

    for dicts in final_amda_list:
        dicts["inst"] = ",".join(list(set(dicts["inst"].split(",")))).replace(" ", "-")
        dicts["sat"] = dicts["sat"].strip().replace(" ", "-")

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
        f"Final events list cleaned to {len(final_amda_list)} elements (see json)",
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
    # For displaying results, comment for disable.
    start_time = "start_time"
    stop_time = "stop_time"
    DOI_2 = "DOI"
    sat = "sat"
    inst = "inst"
    reg = "reg"
    print(
        f"{start_time:30}",
        f"{stop_time:30}",
        f"{DOI_2:30}",
        f"{sat:30}",
        f"{inst:50}" f"{reg:30}",
    )
    for elements in final_amda_list:
        temp = [value for key, value in elements.items()]
        print(
            f"{temp[0]:30}",
            f"{temp[1]:30}",
            f"{temp[2]:30}",
            f"{temp[3]:30}",
            f"{temp[4]:50}" f"{temp[5]:30}",
        )
        print(
            "------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"
        )
    print("\n")
    # =============================================================================================================================================================

    with open(
        os.path.join(
            current_OCR_folder,
            DOI.translate(str.maketrans("", "", string.punctuation))
            + "_bibheliotech_V"
            + "1.txt",
        ),
        "w",
    ) as f:
        f.write(
            "# Name: "
            + DOI.translate(str.maketrans("", "", string.punctuation))
            + "_bibheliotech_V"
            + "1"
            + ";"
            + "\n"
        )
        f.write("# Creation Date: " + datetime.now().isoformat() + ";" + "\n")
        f.write(
            "# Description: Catalogue of events resulting from the HelioNER code (Dablanc & Génot, "
            + '"https://github.com/ADablanc/BibHelioTech.git"'
            + ") on the paper "
            + '"'
            + "https://doi.org/"
            + str(DOI)
            + '"'
            + ". The two first columns are the start/stop times of the event. the third column is the DOI of the paper, the fourth column is the mission that observed the event with the list of instruments (1 or more) listed in the fifth column. The sixth column is the most probable region of space where the observation took place (SPASE ObservedRegions term);\n"
        )
        f.write("# Parameter 1: id:column1; name:DOI; size:1; type:char;" + "\n")
        f.write("# Parameter 2: id:column2; name:SATS; size:1; type:char;" + "\n")
        f.write("# Parameter 3: id:column3; name:INSTS; size:1; type:char;" + "\n")
        f.write("# Parameter 4: id:column4; name:REGS; size:1; type:char;" + "\n")
        f.write("# Parameter 5: id:column5; name:D; size:1; type:int;" + "\n")
        f.write("# Parameter 6: id:column6; name:R; size:1; type:int;" + "\n")
        f.write("# Parameter 7: id:column7; name:SO; size:1; type:int;" + "\n")
        f.write("# Parameter 8: id:column8; name:occur_sat; size:1; type:int;" + "\n")
        f.write(
            "# Parameter 9: id:column9; name:nb_durations; size:1; type:int;" + "\n"
        )
        f.write("# Parameter 10: id:column10; name:conf; size:1; type:float;" + "\n")
        compteur = 0
        for elements in final_amda_list:
            f.write(
                elements["start_time"]
                + " "
                + elements["stop_time"]
                + " "
                + "https://doi.org/"
                + str(elements["DOI"])
                + " "
                + '"'
                + elements["sat"]
                + '"'
                + " "
                + '"'
                + elements["inst"].strip()
                + '"'
                + " "
                + '"'
                + elements["reg"]
                + '"'
                + " "
                + str(elements["D"])
                + " "
                + str(elements["R"])
                + " "
                + str(elements["SO"])
                + " "
                + str(TSO["occur_sat"])
                + " "
                + str(TSO["nb_durations"])
                + " "
                + str(elements["conf"])
                + " "
                + "\n"
            )
            compteur += 1


if __name__ == "__main__":
    pass
