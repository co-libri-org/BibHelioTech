import glob
import json
import copy
import os
import re
import sys


class ToolsError(Exception):
    """Tools exception"""

    def __init__(self, message="Tools Error"):
        self.message = message
        super().__init__(self.message)


class RawDumper:
    dump_step = 0

    def __init__(self, name):
        self.name = name

    def dump_to_raw(self, struct_to_dump, message, folder):
        # append message to struct for later reading
        entitled_struct = copy.deepcopy(struct_to_dump)
        entitled_struct.append(message)
        with open(
            folder + "/" + f"raw{self.dump_step}_{self.name}.json", "w"
        ) as raw_file:
            raw_file.write(json.dumps(entitled_struct, sort_keys=True, indent=4))
        self.dump_step = self.dump_step + 1


def enlight_step(dir_name, step, enlight_mode="sutime"):
    """
    Given a directory, and a step, build the enlighted text for the given mode

    @param step: the integer for the pipeline step
    @param dir_name: an ocr directory
    @param enlight_mode: sutime or entities
    @return: the out_filtered_txt with <div> colored from json
    """
    jsonfile_pattern = os.path.join(dir_name, f"raw{step}_{enlight_mode}.json")
    jsonfilename = glob.glob(jsonfile_pattern, recursive=True)[0]
    with open(jsonfilename) as json_fd:
        json_content = json.load(json_fd)
    json_content.pop()
    txtfile_pattern = os.path.join(dir_name, "out_filtered_text.txt")
    txtfilename = glob.glob(txtfile_pattern, recursive=True)[0]
    with open(txtfilename) as txt_fd:
        txt_content = txt_fd.read()

    return enlight_txt(txt_content, json_content)


def enlight_txt(txt_content, json_content):
    """
    Given a txt file and a json dict list with keys begin, end, type
    enlight given [begin, end]  with <div>

    @return enlighten txt
    """

    res_txt = txt_content[:]
    running_offset = 0
    for i, sutime_struct in enumerate(json_content):
        if type(sutime_struct) == dict and "type" not in sutime_struct.keys():
            sutime_struct["type"] = "notype"

        opening_tag = f'<span class="highlight {sutime_struct["type"]}" title="{sutime_struct["text"]}">'
        # opening_tag = f'<span class="highlight {sutime_struct["type"]}" title="{sutime_struct["text"]}">'
        closing_tag = "</span>"
        start = int(sutime_struct["start"] + running_offset)
        end = int(sutime_struct["end"] + running_offset)
        # try:
        #     if type(sutime_struct["text"]) == "tring" and not res_txt[start:end] == sutime_struct["text"]:
        #         print(f"{i} : <{res_txt[start:end]}> !=  <{sutime_struct['text']}>")
        # except TypeError:
        #     print()
        #     raise TypeError
        opener = res_txt[0:start]
        inner = opening_tag[:] + res_txt[start:end] + closing_tag[:]
        closer = res_txt[end:-1]
        res_txt = opener + inner + closer
        running_offset += len(opening_tag) + len(closing_tag)

    res_txt = res_txt.replace("\n", "")
    return res_txt


def build_highlight(txt_filepath, json_filepath, dest_dir):
    """
    Given an entities directory, and a step, enlight the filtered txt file,
    and make an html file with it.

    @param txt_filepath:
    @param json_filepath:
    @param dest_dir:
    @return:
    """
    if not os.path.isdir(dest_dir):
        raise FileExistsError(f"{dest_dir} is not a directory. Please fix that")
    json_filename = os.path.basename(json_filepath)
    html_filename = os.path.splitext(json_filename)[0] + ".html"
    html_filepath = os.path.join(dest_dir, html_filename)

    with open(json_filepath) as fj:
        json_content = json.load(fj)

    with open(txt_filepath, encoding="utf-8") as ft:
        txt_content = ft.read()

    # wrangling json structure
    # remove message at the end
    message = json_content.pop()
    # flatten dict list
    flattened_dicts = []
    for i in json_content:
        if type(i) == list:
            for j in i:
                flattened_dicts.append(j)
        elif type(i) == dict:
            flattened_dicts.append(i)

    res_txt = enlight_txt(txt_content, flattened_dicts)

    with open("header.html") as header_f:
        header_txt = header_f.read()

    step = filename_to_stepnum(json_filename)
    header_txt = header_txt.replace(f"a_selected_{step}", "a_selected")
    header_txt = header_txt.replace("XXSUTIMES_OCCXX", f"{len(flattened_dicts)}")
    header_txt = header_txt.replace("XXMESSAGEXX", f"{message}")
    with open("footer.html") as footer_f:
        footer_txt = footer_f.read()

    with open(html_filepath, "w") as show_f:
        show_f.write(header_txt)
        show_f.write(res_txt)
        show_f.write(footer_txt)


def filename_to_stepnum(filepath):
    filename = os.path.basename(filepath)
    return re.findall(r"\d+", filename)[0]
