import datetime
import json
import textwrap

import pandas as pd

from bht.errors import BhtCsvError
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
    "nconf",
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
    "nconf": {"col_name": "NCONF", "size": 1, "type": "float"},
}


def row_to_dict(event_row):
    """
    From a row of value as string, transform to a dict with keys.
    The row values may follow the order of hpevent_keys_ordered list

    This function is able to count the number of fields, and decide what keys to fill in.

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


def dict_to_dict(event_dict, columns=None):
    """
    Sometimes, an incoming hpevent dictionnary needs tweaking to fulfill our standards:
        - rewriting some keys
        - converting keys string to lower case
    @param columns:
    @param event_dict:
    @return:
    """

    if columns is None:
        columns = list(hpevent_parameters.keys())

    # translate keys
    key_matrix = {
        "start_time": ["START_TIME", "start_date"],
        "stop_time": ["STOP_TIME", "stop_date"],
        "doi": ["DOI"],
        "sats": ["SATS", "sat", "mission"],
        "insts": ["INSTS", "inst", "instrument"],
        "regs": ["REGS", "reg", "region"],
        "d": ["D"],
        "r": ["R"],
        "so": ["SO"],
        "occur_sat": ["OCCUR_SAT"],
        "nb_durations": ["NB_DURATIONS"],
        "conf": ["CONF"],
        "nconf": ["NCONF"],
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

    # keep only given columns
    from pprint import pprint
    pprint(lowered_dict)
    _r_dict = {k: lowered_dict[k] for k in columns if k in lowered_dict.keys()}

    return _r_dict


def dict_to_string(event_dict, values_lengths=None):
    """
    From an event dict, transform to a string as expected in catalog line

    @param values_lengths:
    @param event_dict:  hpevent dictionnary with variable number of keys
    @return:  row as a string for catalog
    """

    _value_separator = " "
    # make a list of incoming dict keys ordered as expected
    hpevent_keys = []
    for k in hpevent_keys_ordered:
        if k in event_dict.keys():
            hpevent_keys.append(k)

    _r_str = ""
    # transform to row of values, concatenation on oneline by ordered keys
    for _k in hpevent_keys:
        _key_length = 0 if values_lengths is None else values_lengths[_k]
        _key_type = hpevent_parameters[_k]["type"]
        _key_value = event_dict[_k]
        # Set instrument to "<empty_space>" when no instruments
        # AMDA Need
        if _k == 'insts' and _key_value in ['', 'nan']:
            _key_value = ' '

        if _k == 'doi' and 'http' not in _key_value:
            _key_value = f"https://doi.org/{_key_value}"
            _key_length += 16

        # Now format the string depending on its type
        if _key_type == "date" or _k == "doi":
            _r_str += f"{_key_value:{_key_length}}"
        elif _key_type == "char":
            _key_value = f'"{_key_value}"'
            _r_str += f"{_key_value:<{_key_length+2}}"
        elif _key_type == "int":
            _key_value = int(_key_value)
            _r_str += f"{_key_value:>{_key_length}}"
        elif _key_type == "float":
            _key_value = float(_key_value)
            _r_str += f"{_key_value:.5f}"
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
    r_string = f"""\
    # Name: {catalog_name};
    # BibHelioTechVersion: V{yml_settings["BHT_PIPELINE_VERSION"]};
    # Creation Date: {date_now};
    # Description: Catalog of events resulting from the BibHelioTech code
    # Ref.: Dablanc, Génot & Hitier, "https://github.com/co-libri-org/BibHelioTech"
    #                                "https://doi.org/10.5281/zenodo.14901201"
    #
    # Dynamically generated by the BibHelioTech web service.
    #
    # The two first columns are the start/stop times of the event.
    #
    # The other columns/parameters appear in the following order:
    #
    #  DOI       Digital Object Identifier of the document from which the event is extracted
    #  SATS      Spatial mission that observed the event
    #  INSTS     Instruments of the mission involved in the observation
    #  REGS      Region of space where the observation took place (SPASE Observed Regions)
    #  D         Distance in the text (number of characters) between the Duration and the Mission
    #  R         Rank of the mission (missions skipped in text before match)
    #  CONF      A confidence indice 
    #  NCONF     The previous indice normalized on the whole database
    #
    #
    """
    r_string = textwrap.dedent(r_string)

    # Print parameters header
    for i, c in enumerate(columns[2:]):
        v = hpevent_parameters[c]
        r_string += f'# Parameter {i+1}: id:column{i+1}; name: {v["col_name"]}; size:{v["size"]}; type:{v["type"]};\n'

    if len(events_list) == 0:
        return r_string

    # Rewrite each dict in list
    events_list = [dict_to_dict(e, columns) for e in events_list]

    # Find max string lengths
    # and store in a dictionnary with same keys as events

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

    # Finally, dump dicts as rows after converting
    for e in events_list:
        r_string += dict_to_string(e, values_lengths) + "\n"

    return r_string

def catfile_to_rows(catfile):
    """Get all rows of a catalog file as dict.

    - Reads each line, removes comments
    - Converts each row to a dictionary with dynamic column mapping

    @param catfile: file containing the catalog (space-separated fields)
    @return: List of hpevent_dict
    """
    try:
        my_df = pd.read_csv(catfile, delimiter=r"\s+", comment="#", quotechar='"', header=None)
    except pd.errors.EmptyDataError:
        return []

    my_df = my_df.astype(str).fillna("")

    return [
        dict(zip(hpevent_keys_ordered[:len(row)], row))
        for row in my_df.itertuples(index=False, name=None)
    ]



def dicts_to_df(_final_links):
    """Convert a list of dicts to a pandas dataframe"""
    return pd.DataFrame.from_records(_final_links)


def df_to_dicts(_fl_df):
    """Convert a pandas dataframe to a list of dicts"""
    return json.loads(_fl_df.to_json(orient="records"))
    pass
