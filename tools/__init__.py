import glob
import json
import copy
import os
import pprint
import re

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
            {"pipeline_version": yml_settings["BHT_PIPELINE_VERSION"], "message": f"{self.dump_step}- {message}"}
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
        Given a json file from Sutime output, analyse entities, output as text
        @return: String with sutime dict's keys [text, timex-value, value]
        """
        with open(self.json_filepath, "r") as json_df:
            dicts_list = json.load(json_df)
        # remove step message at end of json
        msg = dicts_list.pop()

        # compute types
        all_types = [elmt["type"] for elmt in dicts_list]
        uniq_types = sorted(set(all_types))
        count_types = {_t: all_types.count(_t) for _t in uniq_types}
        _res_str = "\n"

        if with_header:
            msg = f"{msg}: {len(dicts_list)} elmnts"
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
        for _elmnt in dicts_list:
            if type(_elmnt["value"]) is dict:
                _elmnt["value"] = _elmnt["value"].__repr__()

        # get fields lengths
        _type_max_lgth = max([len(elmt["type"]) for elmt in dicts_list]) + 2
        _text_max_lgth = max([len(elmt["text"]) for elmt in dicts_list]) + 2
        _value_max_lgth = max([len(elmt["value"]) for elmt in dicts_list])

        title_str = f'{"type":{_type_max_lgth}}|{"value":{_value_max_lgth}}|{"text":{_text_max_lgth}}\n'
        _res_str += title_str
        # _res_str += len(title_str) * "-" + "\n"
        _res_str += (
            "-" * _type_max_lgth
            + "+"
            + "-" * _value_max_lgth
            + "+"
            + "-" * _text_max_lgth
            + "\n"
        )

        for elmt in dicts_list:
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
