import glob
import json
import copy
import os
import pprint
import re

from bht_config import yml_settings
from tools.tools_errors import ToolsValueError, ToolsFileError


class JsonAnalyser:

    def __init__(self, json_struct, step, mode):
        self._structs = json_struct
        self.step = step
        self.mode = mode

    def get_maxlength(self, struct_key):
        """
        For print formating usage, get the max length among list of values by key
        """
        right_padding = 1

        val_lengths = [len(item[struct_key]) for item in self._structs]
        max_val_lgth = str(max(val_lengths) + right_padding)
        return max_val_lgth

    def dump_sats_instruments(self):
        """
        Show satellites with their instruments
        """
        # make a list of satellites and get the max length
        _sat_lengths = [len(str(_s[0]["text"])) for _s in self._structs]
        s_l = max(_sat_lengths)
        # make a list of concatenated instruments list as string
        _inst_lengths = [len(str(_s[1]["text"])) for _s in self._structs]
        # get the maximum lengths of it
        i_l = max(_inst_lengths)
        col_title = f'{"start":>6} {"end":>6} {"occ.":>5} {"satellite":{s_l}} {"instruments":{i_l}}\n'
        _str = f"\n{'-' * len(col_title)}\n"
        _str += col_title
        _str += f"{'-' * len(col_title)}\n"
        for _s in self._structs:
            _sat = _s[0]
            try:
                so = _sat["SO"]
            except KeyError:
                so = "."
            _insts = ",".join(_s[1]["text"])
            _str += f'{_sat["start"]:>6} {_sat["end"]:>6} {so:>5} {_sat["text"]:{s_l}} {_insts:{i_l}}\n'

        return _str

    def dump_rawentities(self, _type="sat"):
        """
        Show first json output of entities pipeline
        Contains Satellites
        """
        _names_lengths = [
            len(_s["text"])
            for _s in self._structs
            if "type" in _s.keys() and _s["type"] == _type
        ]
        nm_l = max(_names_lengths)
        col_names = {"sat": "Satellite", "instr": "Instrument", "region": "Region"}
        col_title = f'{"start":>6} {"end":>6} {col_names[_type]:{nm_l}}\n'
        _str = f"\n{'-' * len(col_title)}\n"
        _str += col_title
        _str += f"{'-' * len(col_title)}\n"
        for _s in self._structs:
            if "type" not in _s.keys() or _s["type"] != _type:
                continue
            _str += f'{_s["start"]:6} {_s["end"]:6} {_s["text"]:{nm_l}}\n'
        return _str

    def dump_sat2duration(self):
        """
        Data structure is the link between durations and satellites
        as a list of lists of structures :
        [
            [ {sat_struct},{unknown}, {event}],
            ...
        ]

        @param _structs:
        @return:
        """
        line_format = [
            {"name": "sat_name reg.", "format": "20"},
            {"name": "sat_start", "format": ">10"},
            {"name": "sut_start", "format": ">15"},
            {"name": "sutime_begin", "format": "25"},
            {"name": "sutime_end", "format": "25"},
        ]

        _str = self.line_dumper(line_format, header=True)

        for _ls in self._structs:
            # identify struct
            try:
                _sat = _ls[0]
                _sutime = _ls[2]
            except (IndexError, KeyError) as e:
                print(type(e), _ls)
                continue

            line_values = [
                _sat["text"],
                _sat["start"],
                _sutime["start"],
                _sutime["value"]["begin"],
                _sutime["value"]["end"],
            ]
            _str += self.line_dumper(line_format, _values=line_values)
        return _str

    def dump_sat_regions(self):
        """
        Structs reflects link between sats, durations and regions.
        looks like a lists:
        [
         [ {sat}, {instruments}, {region}, {region}, {duration} ]
          ....
        ]

        @return: tabulated string
        """

        line_format = [
            {"name": "sutime_begin", "format": "25"},
            {"name": "sutime_end", "format": "25"},
            {"name": "sat_name", "format": "20"},
            {"name": "regions", "format": "<20"},
            {"name": "conf", "format": "<6"},
        ]

        _str = self.line_dumper(line_format, header=True)

        for _ls in self._structs:
            if type(_ls) is not list:
                continue
            try:
                _sat = structs_from_list(_ls, "sat")[0]
                _reg1 = structs_from_list(_ls, "region")[0]
                _reg2 = structs_from_list(_ls, "region")[1]
                _sutime = structs_from_list(_ls, "DURATION")[0]
                line_values = [
                    _sutime["value"]["begin"],
                    _sutime["value"]["end"],
                    _sat["text"],
                    f'{_reg1["text"]}.{_reg2["text"]}'[:19],
                    f'{_sat["conf"]:.4f}',
                ]
                _str += self.line_dumper(line_format, _values=line_values)
            except (IndexError, KeyError) as e:
                _str += f"{e} JSON Syntax Error\n"
        return _str

    def dump_normalized(self):
        """
        Step 8

        @param _structs:
        @return:
        """
        # get the max sat name length
        sat_names_lengths = []
        for _ls in self._structs:
            for _s in _ls:
                if "type" not in _s.keys():
                    continue
                if _s["type"] == "sat":
                    sat_names_lengths.append(len(_s["text"]))
        max_sat_lgth = max(sat_names_lengths)
        line_format = [
            {"name": "event begin", "format": "24"},
            {"name": "event end", "format": "24"},
            {"name": "evt idx", "format": ">7"},
            {"name": "sat idx", "format": ">7"},
            {"name": "sat name", "format": max_sat_lgth},
            # {"name": "D", "format": ">2"},
            # {"name": "R", "format": ">2"},
            # {"name": "SO", "format": ">4"},
            {"name": "conf", "format": "<6"},
        ]

        _str = self.line_dumper(line_format, header=True)
        # _structs is a list of lists of structs
        for _l in self._structs:
            # let's look inside this _l list of structs which one we want
            # either type 'sat' or type 'DURATION'
            _sat, _dur = None, None
            for _s in _l:
                if "type" not in _s.keys():
                    continue
                if _s["type"] == "sat":
                    _sat = _s
                elif _s["type"] == "DURATION":
                    _dur = _s
            _values = [
                _dur["value"]["begin"],
                _dur["value"]["end"],
                _dur["start"],
                _sat["start"],
                _sat["text"],
                # _sat["D"],
                # _sat["R"],
                # _sat["SO"],
                f'{_sat["conf"]:.4f}',
            ]
            _str += self.line_dumper(line_format, _values=_values)
        return _str

    def dump_regions_links(self):
        """
        Data structure reflects the regions associations,

        @param _structs: it is a list of lists of 2 regions structs
        @return: dumped data structure as string
        """
        line_format = [
            {"name": "first reg.", "format": "15"},
            {"name": "f idx", "format": ">7"},
            {"name": "s idx", "format": ">7"},
            {"name": "secnd reg.", "format": "15"},
        ]

        _str = self.line_dumper(line_format, header=True)

        for _ls in self._structs:
            _first_reg = _ls[0]
            _scnd_reg = _ls[1]
            line_values = [
                _first_reg["text"],
                _first_reg["start"],
                _scnd_reg["start"],
                _scnd_reg["text"],
            ]
            _str += self.line_dumper(line_format, _values=line_values)
        return _str

    def dump_final(self):
        """
        Final structs list,  looking like
          {
            "D": 1141,
            "DOI": "10.1051/0004-6361/202140910",
            "R": 1,
            "SO": 3,
            "conf": 0.018560994257641565,
            "inst": "",
            "reg": "Venus",
            "sat": "Mariner-10",
            "start_time": "2018-10-03T00:00:00.000",
            "stop_time": "2019-12-26T23:59:59.000"
        },

        @param _structs:
        @return:
        """
        line_format = [
            {"name": "start_time", "format": "25"},
            {"name": "stop_time", "format": "25"},
            {"name": "sat", "format": self.get_maxlength("sat")},
            {"name": "inst", "format": self.get_maxlength("inst")},
            {"name": "reg", "format": self.get_maxlength("reg")},
            {"name": "conf", "format": "<6"},
        ]

        _str = self.line_dumper(line_format, header=True)

        for _s in self._structs:
            line_values = [
                _s["start_time"],
                _s["stop_time"],
                _s["sat"],
                _s["inst"],
                _s["reg"],
                f'{_s["conf"]:.0f}',
            ]
            _str += self.line_dumper(line_format, _values=line_values)
        return _str

    def line_dumper(self, _format, _values=None, header=False):
        """
        Will return a values line formatted as described in the _format dict argument
        Can return a header when header is set to True


        @param _format: list of dicts [ { name: name1 , format: format1 }, { name: name2 , format: format2 } ...]
        @param _values: list of values [ val1, val2, ...]
        @param header:
        @return:
        """
        _str = "\n"
        if header:
            col_titles = []
            for _d in _format:
                col_titles.append(f'{_d["name"]:{_d["format"]}}')
            title_line = "| ".join(col_titles)
            title_top = "-" * len(title_line)
            title_bots = ["-" * len(_t) for _t in col_titles]
            title_bottom = "+-".join(title_bots)
            _str += f"{title_top}\n{title_line}\n{title_bottom}"
        elif _values:
            col_values = []
            for i, _v in enumerate(_values):
                _f = _format[i]["format"]
                col_values.append(f"{_v:{_f}}")
            _str += "| ".join(col_values)
        return _str

    def analyse_entities_json(self, with_header=False):
        """
        @param with_header:
        @return:
        """

        # Run dumping method depending on step level
        if self.step in [0, 2]:
            _r_str = self.dump_rawentities()
        elif self.step == 1:
            _r_str = self.dump_rawentities(_type="instr")
        elif self.step in [3, 4, 5, 6]:
            _r_str = self.dump_sats_instruments()
        elif self.step == 7:
            _r_str = self.dump_sat2duration()
        elif self.step == 8:
            _r_str = self.dump_normalized()
        elif self.step == 9:
            _r_str = self.dump_rawentities(_type="region")
        elif self.step in [10, 11, 12, 13, 14, 15]:
            _r_str = self.dump_regions_links()
        elif self.step in [16]:
            _r_str = self.dump_sat_regions()
        elif self.step in [17, 18, 19, 20]:
            _r_str = self.dump_final()
        else:
            _title = f"No json dump for step {self.step}"
            _line = "-" * len(_title)
            _r_str = f"\n{_line}\n{_title}\n{_line}"
        return _r_str

    def analyse_sutime_json(self, with_header=False):
        """
        Given a json file from Sutime output, analyse entities, output as text
        @return: String with sutime dict's keys [text, timex-value, value]
        """

        if len(self._structs) == 0:
            return "Empty list"
        # compute types
        all_types = [elmt["type"] for elmt in self._structs]
        uniq_types = sorted(set(all_types))
        count_types = {_t: all_types.count(_t) for _t in uniq_types}
        _res_str = "\n"

        # Show types report, id the number of each types like this:
        #
        #            13 DATE
        #            7 DURATION
        #            1 TIME
        written_types = 0
        for k, v in count_types.items():
            written_types += 1
            type_number = f"{v:>3} {k:8}"
            _res_str += f"{type_number:^50}\n"

        # now, make sure types report height is always the same
        types_report_height = 5
        more_cr = types_report_height - written_types
        _res_str += more_cr * "\n"

        # convert all dict values to string
        for _elmnt in self._structs:
            if type(_elmnt["value"]) is dict:
                _elmnt["value"] = _elmnt["value"].__repr__()

        # get fields lengths
        _type_max_lgth = max([len(elmt["type"]) for elmt in self._structs]) + 2
        _text_max_lgth = max([len(elmt["text"]) for elmt in self._structs]) + 2
        _value_max_lgth = max([len(elmt["value"]) for elmt in self._structs])

        title_str = f'{"type":{_type_max_lgth}}|{"value":{_value_max_lgth}}|{"text":{_text_max_lgth}}\n'
        _res_str += title_str
        # _res_str += len(title_str) * "-" + "\n"
        _res_str += (
            f'{"-" * _type_max_lgth}+{"-" * _value_max_lgth}+ {"-" * _text_max_lgth}\n'
        )

        for elmt in self._structs:
            if type(elmt) is not dict:
                continue
            if "timex-value" not in elmt:
                elmt["timex-value"] = "None"
            _type = elmt["type"]
            _text = f'"{elmt["text"]}"'
            _timex = elmt["timex-value"]
            _value = elmt["value"]
            _res_str += f"{_type:{_type_max_lgth}}|{_value:{_value_max_lgth}}|{_text:{_text_max_lgth}}\n"

        return _res_str


class RawDumper:
    """
    Write a python structure to a json file with a message for later use by StepLighter
    """

    def __init__(self, name):
        self.name = name
        self.dump_step = 0

    def dump_to_raw(self, struct_to_dump, message, folder, start_step=None):

        if start_step is not None:
            try:
                self.dump_step = int(start_step)
            except ValueError:
                raise ToolsValueError(f"Dump_step has to be an integer '{start_step}' is not")
        # append version and message to struct for later reading
        entitled_struct = copy.deepcopy(struct_to_dump)
        entitled_struct.append(
            {
                "step": f"{self.dump_step}",
                "pipeline_version": yml_settings["BHT_PIPELINE_VERSION"],
                "message": f"{self.dump_step}- {message}",
            }
        )
        with open(
                os.path.join(folder, f"raw{self.dump_step}_{self.name}.json"), "w"
        ) as raw_file:
            raw_file.write(json.dumps(entitled_struct, sort_keys=True, indent=4))
        self.dump_step = self.dump_step + 1


class StepLighter:

    def __init__(self, ocr_dir, step_num=0, enlight_mode="sutime"):
        self.all_steps = None
        self.txt_enlighted = None
        self.txt_content = None
        self.txt_filepath = None
        self.json_analysed = None
        self.json_string = None
        self.json_struct = None
        self.caption = None
        self.json_filepath = None
        self.json_dumper = None

        self.step = int(step_num)
        self.ocr_dir = ocr_dir
        self.enlight_mode = enlight_mode

        self.initialize()

    def initialize(self):

        # Read the cleaned text version of the article
        self.txt_filepath = os.path.join(self.ocr_dir, "out_filtered_text.txt")
        with open(self.txt_filepath) as txt_fd:
            self.txt_content = txt_fd.read()

        # Read the json file corresponding to step_number/enlight_mode
        self.json_filepath = os.path.join(
            self.ocr_dir, f"raw{self.step}_{self.enlight_mode}.json"
        )
        if not os.path.isfile(self.json_filepath):
            raise ToolsFileError(f"No such file {self.json_filepath}")
        with open(self.json_filepath) as json_fd:
            _json_raw = json.load(json_fd)

        # Initialize json attributes
        self.caption = _json_raw.pop()  # meta info in the last dict of the list
        self.json_struct = _json_raw.copy()
        self.json_string = json.dumps(self.json_struct, indent=4)

        # Instantiate the JsonDumper
        self.json_dumper = JsonAnalyser(self.json_struct, self.step, self.enlight_mode)

        # Create the json table dump
        self.json_analysed = self.analyse_json()

        # Enlight raw text as html marked
        self.txt_enlighted = enlight_txt(self.txt_content, self.json_struct)

        # set the captions list for this directory
        self.all_steps = self.list_steps()

    def list_steps(self):
        """
        Given a directory, and a mode, get the number of raw steps found

        @return: number of steps in the directory
        """
        _all_captions = []
        jsonfiles_pattern = os.path.join(self.ocr_dir, f"raw*_{self.enlight_mode}.json")
        all_files = glob.glob(jsonfiles_pattern)
        # sort list by step number extracted from file name
        all_files.sort(
            key=lambda path: int(re.sub(r".*raw(\d+)_.*\.json", r"\1", path))
        )
        # now build the list of captions
        for f in all_files:
            with open(f) as json_fd:
                json_content = json.load(json_fd)
                step_caption = json_content.pop()
                _all_captions.append(step_caption)

        return _all_captions

    def analyse_json(self, with_header=False):
        """
        Wrapper for json convert to text from sutime or entities output
        """

        if self.enlight_mode == "entities":
            return self.json_dumper.analyse_entities_json(with_header)
        elif self.enlight_mode == "sutime":
            return self.json_dumper.analyse_sutime_json(with_header)


def convert_long_chars(content=None):
    """ "
    Replace long chars with 2 1 octet char.

    SUtime tends to offset the index when it encounters long utf8 characters (4 byes long).
    In order to interpret properly those indexes ('start', 'end' in json) we replace those with 2 ascii chars ('AA')
    """
    _content = content[:]
    for i in range(len(_content)):
        c = _content[i]
        if len(c.encode("utf-8")) >= 4:
            _content = _content[:i] + "AA" + _content[i + 1:]
    return _content


def struct_to_title_0(content_struct):
    content_type = content_struct["type"]
    content_title = pprint.pformat(content_struct)
    return content_type, content_title.replace("\n", "&#10;")


def struct_to_title_1(content_struct):
    """Convert a sutime struct to a html tooltip"""
    content_type = content_struct["type"]
    content_title = f'Text: {content_struct["text"]}'
    if content_type == "DURATION":
        if "value" in content_struct.keys():
            if "begin" in content_struct["value"]:
                content_title += f'&#10;Begin: {content_struct["value"]["begin"]}'
            if "end" in content_struct["value"]:
                content_title += f'&#10;End: {content_struct["value"]["end"]}'
    elif content_type == "sat":
        if "D" in content_struct.keys():
            content_title += f'&#10;D: {content_struct["D"]}'
        if "R" in content_struct.keys():
            content_title += f'&#10;R: {content_struct["R"]}'
        if "SO" in content_struct.keys():
            content_title += f'&#10;SO: {content_struct["SO"]}'
        if "conf" in content_struct.keys():
            content_title += f'&#10;conf: {content_struct["conf"]}'
        # pass
    return content_type, content_title


def structs_from_list(structs_list, struct_type):
    """
    Return the list of structs in list that has the struct_type

    returns [] if nothing found
    """
    if type(structs_list) is not list:
        return []
    _structs = []
    for _s in structs_list:
        if "type" not in _s.keys():
            continue
        if _s["type"] == struct_type:
            _structs.append(_s)
    return _structs


def enlight_txt(txt_content, json_content):
    """
    Given a txt file and a json dicts list with keys 'begin', 'end' and 'type'
    enlight given [begin, end]  with <div style="type">

    @return enlighten txt
    """

    # json content should be a list of dicts.
    # if not, it is a list of lists of dicts.
    # in any case, create a list of any dict containing the 'type' key

    # flatten dict list
    flattened_content = []
    for elemnt in json_content:
        if type(elemnt) is dict:
            flattened_content.append(elemnt)
        elif type(elemnt) is list:
            for nested_elmnt in elemnt:
                flattened_content.append(nested_elmnt)
        else:
            raise ToolsValueError(
                f"No such type allowed in json struct: {type(elemnt)}"
            )
    # filter only dict with type key
    filtered_content = [
        elmnt
        for elmnt in flattened_content
        if type(elmnt) is dict and "type" in elmnt.keys()
    ]

    filtered_content.sort(key=lambda x: x["start"])

    # remove duplicates
    uniq_content = []
    for elmnt in filtered_content:
        if elmnt not in uniq_content:
            uniq_content.append(elmnt)
    res_txt = convert_long_chars(txt_content)
    running_offset = 0
    for i, content_struct in enumerate(uniq_content):
        content_type, content_title = struct_to_title_0(content_struct)

        opening_tag = f'<span class="highlight {content_type}" title="{content_title}">'
        closing_tag = "</span>"
        start = int(content_struct["start"]) + running_offset
        end = int(content_struct["end"]) + running_offset
        opener = res_txt[0:start]
        inner = opening_tag[:] + res_txt[start:end] + closing_tag[:]
        closer = res_txt[end:-1]
        res_txt = opener + inner + closer
        running_offset += len(opening_tag) + len(closing_tag)

    res_txt = res_txt.replace("\n", "")
    return res_txt
