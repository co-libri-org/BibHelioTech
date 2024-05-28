import csv
import datetime
import textwrap

from bht_config import yml_settings

hpevent_keys_ordered = [
    "start_time",
    "stop_time",
    "doi",
    "sats",
    "insts",
    "regs",
    "d",
    "r",
    "so",
    "occur_sat",
    "nb_durations",
    "conf",
]

hpevent_parameters = {
    "start_time": {"col_name": "START_TIME", "size": 1, "type": "date"},
    "stop_time": {"col_name": "STOP_TIME", "size": 1, "type": "date"},
    "doi": {"col_name": "DOI", "size": 1, "type": "char"},
    "sats": {"col_name": "SATS", "size": 1, "type": "char"},
    "insts": {"col_name": "INSTS", "size": 1, "type": "char"},
    "regs": {"col_name": "REGS", "size": 1, "type": "char"},
    "d": {"col_name": "D", "size": 1, "type": "int"},
    "r": {"col_name": "R", "size": 1, "type": "int"},
    "so": {"col_name": "SO", "size": 1, "type": "int"},
    "occur_sat": {"col_name": "OCCUR_SAT", "size": 1, "type": "int"},
    "nb_durations": {"col_name": "NB_DURATIONS", "size": 1, "type": "int"},
    "conf": {"col_name": "CONF", "size": 1, "type": "float"},
}


def row_to_dict(event_row):
    """
    From a row of value, transform to a dict with keys.
    The row values may follow the  order of hpevent_keys_ordered list

    @param event_row:  row of hpevent values
    @return:  hpevent_dict
    """
    _r_dict = {}
    num_cols = len(event_row)
    hpevent_keys = hpevent_keys_ordered[0:num_cols]
    hpevent_tuple = zip(hpevent_keys, event_row)
    for k, v in hpevent_tuple:
        _r_dict[k] = v
    return _r_dict


def dict_to_dict(event_dict):
    """
    Sometimes, an incoming hpevent dictionnary needs tweaking to fullfill our standards:
        - rewriting some keys
        - converting keys string to lower case
    @param event_dict:
    @return:
    """
    # translate keys
    key_matrix = {
        "start_time": ["START_TIME", "start_date"],
        "stop_time": ["STOP_TIME", "stop_date"],
        "doi": ["DOI"],
        "sats": ["SATS", "sat"],
        "insts": ["INSTS", "inst"],
        "regs": ["REGS", "reg"],
        "d": ["D"],
        "r": ["R"],
        "so": ["SO"],
        "occur_sat": ["OCCUR_SAT"],
        "nb_durations": ["NB_DURATIONS"],
        "conf": ["CONF"],
    }
    # replace any synonym key with the proper one
    _proper_dict = {}
    for proper_key, syn_keys in key_matrix.items():
        for event_key, event_value in event_dict.items():
            if event_key in syn_keys:
                # convert key to proper one
                _proper_dict[proper_key] = event_value
            elif event_key in list(key_matrix.keys()):
                # keep already proper key
                _proper_dict[event_key] = event_value
            else:
                # well, don't keep that wrong key
                pass

    # convert incoming dict to a lowered keys dict
    lowered_dict = {}
    for k, v in _proper_dict.items():
        lowered_dict[k.lower()] = v

    return lowered_dict


def dict_to_string(event_dict, values_lengths=None):
    """
    From an event dict, transform to a string as expected in catalog line

    @param values_lengths:
    @param event_dict:  hpevent dictionnary with variable number of keys
    @return:  row as a string for catalog
    """

    _value_separator = " "
    # make a list of keys:
    #   - ordered as expected
    #   - with the same length as incoming dict
    hpevent_keys = hpevent_keys_ordered[0: len(event_dict.keys())]

    _r_str = ""
    # transform to row of values, concatenation on oneline by ordered keys
    for _k in hpevent_keys:
        _key_length = 0 if values_lengths is None else values_lengths[_k]
        _key_type = hpevent_parameters[_k]["type"]
        _key_value = event_dict[_k]
        if _key_type == "date" or _k == "doi":
            _r_str += f'{_key_value}'
        elif _key_type == "char":
            _key_value = f'"{_key_value}"'
            _r_str += f'{_key_value:<{_key_length+2}}'
        elif _key_type == "int":
            _key_value = int(_key_value)
            _r_str += f'{_key_value:>{_key_length}}'
        elif _key_type == "float":
            _key_value = float(_key_value)
            _r_str += f'{_key_value:.5f}'
        else:
            raise Exception(f"No Such Type <{_key_type}>")
        _r_str += _value_separator

    # remove leading/trailing slashes
    return _r_str.strip()


def rows_to_catstring(events_list, catalog_name, columns=None):
    """
    Build a text file of events in amda catalog format

    Events are given as a list of dicts with at least the keys

        ['doi','instrument','mission','region','start_date','stop_date']

    @param events_list: a list of events as dicts
    @param catalog_name:  the name of the catalog being created
    @param columns: the keys of the event dict we want to write down
    @return: a string containing the events' catalog as text
    """

    if columns is None:
        columns = list(hpevent_parameters.keys())

    # Print catalog's general header
    date_now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    r_string = f"""
    # Name: {catalog_name};
    # BibHelioTechVersion: V{yml_settings["BHT_PIPELINE_VERSION"]};
    # Creation Date: {date_now};
    # Description: Catalogue of events resulting from the HelioNER code
    # (Dablanc & Génot, "https://github.com/ADablanc/BibHelioTech.git")
    #
    # Dynamically generated by the BibHelioTech web service.
    #
    # The two first columns are the start/stop times of the event.
    # The third column is the DOI of the paper,
    # The fourth column is the mission that observed the event with the list of instruments listed in the fifth column.
    # The sixth column is the most probable region of space where the observation took place (SPASE ObservedRegions term);
    #
    """
    r_string = textwrap.dedent(r_string)

    # Print parameters header
    #
    p_index = 0
    for k, v in hpevent_parameters.items():
        if k not in columns:
            continue
        r_string += f'# Parameter {p_index}: id:column{p_index}; name: {v["col_name"]}; size:{v["size"]}; type:{v["type"]};\n'
        p_index += 1

    # store max lengths in a dictionnary with same keys as events
    values_lengths = {k: [] for k in events_list[0].keys()}
    # first, fill keys with a table of all length
    for e in events_list:
        for k, v in e.items():
            vl = len(str(v))
            values_lengths[k].append(vl)
    # then get max only
    for k, v in values_lengths.items():
        max_length = max(values_lengths[k])
        values_lengths[k] = max_length

    # Dump dicts as rows after converting
    for e in events_list:
        # reduce dict to given columns
        e = {k:e[k] for k in columns}
        r_string += dict_to_string(e, values_lengths) + "\n"
    return r_string


def catfile_to_rows(catfile):
    """Get all rows of a catalog file as  dict
       -  read each line, rid of comments
       -  create a hp_event_dict

       Trick: we may get catfiles with different number of columns.
           sometimes  6 (start, stop, doi, mission, instruments, region)
           sometimes 12 ( ..., D, R, SO, occur_sat, nb_durations, conf)

       This is the reason of row_to_dict use.

    :return: hpevent_dict list
    """
    hpeventdict_list = []
    with open(catfile, newline="") as csvfile:
        reader = csv.reader(
            filter(lambda r: r[0] != "#", csvfile), delimiter=" ", quotechar='"'
        )
        for row in reader:
            hpevent_dict = row_to_dict(row)
            hpeventdict_list.append(hpevent_dict)
    return hpeventdict_list
