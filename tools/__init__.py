import glob
import json
import copy
import os
import pprint
import re
from textwrap import dedent

from bht_config import yml_settings
from tools.tools_errors import ToolsValueError, ToolsFileError


class RawDumper:
    """
    Write a python structure to a json file with message for later use by StepLighter
    """

    dump_step = 0

    def __init__(self, name):
        self.name = name

    def dump_to_raw(self, struct_to_dump, message, folder):
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


# TODO: shall we move this to models.paper ?
class StepLighter:
    def __init__(self, ocr_dir, step_num=0, enlight_mode="sutime"):
        self._all_captions = []
        self.step = int(step_num)
        self.ocr_dir = ocr_dir
        self.enlight_mode = enlight_mode
        self.enlighted_txt_content = ""
        self.caption_content = ""
        self.raw_json_text = ""
        self.analysed_json_text = ""

    @property
    def caption(self):
        if not self.caption_content:
            self.caption_content, self.enlighted_txt_content = self.enlight_step()
        return self.caption_content

    @property
    def enlighted_txt(self):
        if not self.enlighted_txt_content:
            self.caption_content, self.enlighted_txt_content = self.enlight_step()
        return self.enlighted_txt_content

    @property
    def raw_json(self):
        if not self.raw_json_text:
            self.raw_json_text = self.dump_json()
        return self.raw_json_text

    @property
    def analysed_json(self):
        if not self.analysed_json_text:
            self.analysed_json_text = self.analyse_json()
        return self.analysed_json_text

    @property
    def all_steps(self):
        """
        Given a directory, and a mode, get the number of raw steps found

        @return: number of steps in the directory
        """
        if self._all_captions:
            return self._all_captions
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
                self._all_captions.append(step_caption)

        return self._all_captions

    @property
    def json_filepath(self):
        """Given a pipeline mode and a step num, return the json filepath"""
        jsonfile_pattern = os.path.join(
            self.ocr_dir, f"raw{self.step}_{self.enlight_mode}.json"
        )
        print(jsonfile_pattern)
        _json_filepath = glob.glob(jsonfile_pattern, recursive=True)[0]
        if not os.path.isfile(_json_filepath):
            raise ToolsFileError(f"No such file {_json_filepath}")
        return _json_filepath

    def enlight_step(self):
        """
        Given a directory, and a step, build the enlighted text for the given mode

        @return: the out_filtered_txt with <div> colored from json
        """
        with open(self.json_filepath) as json_fd:
            json_content = json.load(json_fd)
        step_caption = json_content.pop()
        txtfile_pattern = os.path.join(self.ocr_dir, "out_filtered_text.txt")
        txtfilename = glob.glob(txtfile_pattern, recursive=True)[0]
        with open(txtfilename) as txt_fd:
            txt_content = txt_fd.read()

        return step_caption, enlight_txt(txt_content, json_content)

    def dump_json(self):
        with open(self.json_filepath, "r") as json_df:
            dicts_list = json.load(json_df)
        dicts_list.pop()
        return json.dumps(dicts_list, indent=4)

    def analyse_json(self, with_header=False):
        """
        Wrapper for json convert to text from sutime or entities output
        """
        with open(self.json_filepath, "r") as json_df:
            structs_list = json.load(json_df)
        if self.enlight_mode == "entities":
            return self.analyse_entities_json(structs_list, with_header)
        elif self.enlight_mode == "sutime":
            return self.analyse_sutime_json(structs_list, with_header)

    def analyse_entities_json(self, structs_list, with_header=False):
        """
        @param structs_list:
        @param with_header:
        @return:
        """

        def dump_sats_instruments(_structs):
            """ "
            Show satellites with their instruments
            """
            # make a list of satellites and get the max length
            _sat_lengths = [len(str(_s[0]["text"])) for _s in _structs]
            s_l = max(_sat_lengths)
            # make a list of concatenated instruments list as string
            _inst_lengths = [len(str(_s[1]["text"])) for _s in _structs]
            # get the maximum lengths of it
            i_l = max(_inst_lengths)
            col_title = f'{"start":>6} {"end":>6} {"occ.":>5} {"satellite":{s_l}} {"instruments":{i_l}}\n'
            _str = f"\n{'-' * len(col_title)}\n"
            _str += col_title
            _str += f"{'-' * len(col_title)}\n"
            for _s in _structs:
                _sat = _s[0]
                try:
                    so = _sat["SO"]
                except KeyError:
                    so = "."
                _insts = ",".join(_s[1]["text"])
                _str += f'{_sat["start"]:>6} {_sat["end"]:>6} {so:>5} {_sat["text"]:{s_l}} {_insts:{i_l}}\n'

            return _str

        def dump_rawentities(_structs, _type="sat"):
            """
            Show first json output of entities pipeline
            Contains Satellites
            """
            _names_lengths = [
                len(_s["text"])
                for _s in _structs
                if "type" in _s.keys() and _s["type"] == _type
            ]
            nm_l = max(_names_lengths)
            col_names = {"sat": "Satellite", "instr": "Instrument", "region": "Region"}
            col_title = f'{"start":>6} {"end":>6} {col_names[_type]:{nm_l}}\n'
            _str = f"\n{'-' * len(col_title)}\n"
            _str += col_title
            _str += f"{'-' * len(col_title)}\n"
            for _s in _structs:
                if "type" not in _s.keys() or _s["type"] != _type:
                    continue
                _str += f'{_s["start"]:6} {_s["end"]:6} {_s["text"]:{nm_l}}\n'
            return _str

        def dump_sat2duration(_structs):
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
            (nm_l, sat_l, sut_l, beg_l, end_l) = (20, 10, 15, 25, 25)
            line_format = [
                {"name": "sat_name reg.", "format": "20"},
                {"name": "sat_start", "format": ">10"},
                {"name": "sut_start", "format": ">15"},
                {"name": "sutime_begin", "format": "25"},
                {"name": "sutime_end", "format": "25"},
            ]

            _str = line_dumper(line_format, header=True)

            for _ls in _structs:
                _sat = _ls[0]
                _sutime = _ls[2]
                line_values = [
                    _sat["text"],
                    _sat["start"],
                    _sutime["start"],
                    _sutime["value"]["begin"],
                    _sutime["value"]["end"],
                ]
                _str += line_dumper(line_format, _values=line_values)
            return _str

        def dump_normalized(_structs):
            """
            Step 8

            @param _structs:
            @return:
            """
            # get the max sat name length
            sat_names_lgths = []
            for _ls in _structs:
                for _s in _ls:
                    if "type" not in _s.keys():
                        continue
                    if _s["type"] == "sat":
                        sat_names_lgths.append(len(_s["text"]))
            max_sat_lgth = max(sat_names_lgths)
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

            _str = line_dumper(line_format, header=True)
            # _structs is a list of lists of structs
            for _l in _structs:
                # lets look inside this _l list of structs which one we want
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
                    f"{_sat["conf"]:.4f}",
                ]
                _str += line_dumper(line_format, _values=_values)
            return _str

        def dump_regions_links(_structs):
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

            _str = line_dumper(line_format, header=True)

            for _ls in _structs:
                _first_reg = _ls[0]
                _scnd_reg = _ls[1]
                line_values = [
                    _first_reg["text"],
                    _first_reg["start"],
                    _scnd_reg["start"],
                    _scnd_reg["text"],
                ]
                _str += line_dumper(line_format, _values=line_values)
            return _str

        def line_dumper(_format, _values=None, header=False):
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
                title_line = " | ".join(col_titles)
                title_top = "-" * len(title_line)
                title_bots = ["-" * len(_t) for _t in col_titles]
                title_bottom = "-+-".join(title_bots)
                _str += f"{title_top}\n{title_line}\n{title_bottom}"
            elif _values:
                col_values = []
                for i, _v in enumerate(_values):
                    _f = _format[i]["format"]
                    col_values.append(f"{_v:{_f}}")
                _str += " | ".join(col_values)
            return _str

        #  Get step number and choose which json 2 table dumper to use
        caption = structs_list.pop()
        # 1- from caption key
        try:
            step = caption["step"]
        except KeyError:
            step = None
        # 2- or from guessed from message
        if step is None:
            try:
                step = caption["message"].split("-")[0]
            except KeyError:
                step = None

        # Run dumping method depending on step level
        if step in ["0", "2"]:
            _r_str = dump_rawentities(structs_list)
        elif step == "1":
            _r_str = dump_rawentities(structs_list, _type="instr")
        elif step in ["3", "4", "5", "6"]:
            _r_str = dump_sats_instruments(structs_list)
        elif step == "7":
            _r_str = dump_sat2duration(structs_list)
        elif step == "8":
            _r_str = dump_normalized(structs_list)
        elif step == "9":
            _r_str = dump_rawentities(structs_list, _type="region")
        elif step in ["10", "11", "12", "13", "14", "15"]:
            _r_str = dump_regions_links(structs_list)
        else:
            _title = f"No json dump for step {step} of pipeline  V{caption["pipeline_version"]}"
            _line = "-" * len(_title)
            _r_str = f"\n{_line}\n{_title}\n{_line}"
        return _r_str

    def analyse_sutime_json(self, structs_list, with_header=False):
        """
        Given a json file from Sutime output, analyse entities, output as text
        @return: String with sutime dict's keys [text, timex-value, value]
        """

        # remove step message at end of json
        msg = structs_list.pop()

        # compute types
        all_types = [elmt["type"] for elmt in structs_list]
        uniq_types = sorted(set(all_types))
        count_types = {_t: all_types.count(_t) for _t in uniq_types}
        _res_str = "\n"

        if with_header:
            msg = f"{msg}: {len(structs_list)} elmnts"
            msg_sub = len(msg) * "-"
            _res_str += f"{msg_sub:^50}\n"
            _res_str += f"{msg:^50}\n"
            _res_str += f"{msg_sub:^50}\n"
            _res_str += "\n"

        # Show types report
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
        for _elmnt in structs_list:
            if type(_elmnt["value"]) is dict:
                _elmnt["value"] = _elmnt["value"].__repr__()

        # get fields lengths
        _type_max_lgth = max([len(elmt["type"]) for elmt in structs_list]) + 2
        _text_max_lgth = max([len(elmt["text"]) for elmt in structs_list]) + 2
        _value_max_lgth = max([len(elmt["value"]) for elmt in structs_list])

        title_str = f'{"type":{_type_max_lgth}}|{"value":{_value_max_lgth}}|{"text":{_text_max_lgth}}\n'
        _res_str += title_str
        # _res_str += len(title_str) * "-" + "\n"
        _res_str += (
            f"{"-" * _type_max_lgth}+{ "-" * _value_max_lgth}+ {"-" * _text_max_lgth}\n"
        )

        for elmt in structs_list:
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
    res_txt = txt_content[:]
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
