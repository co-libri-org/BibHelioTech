import json
import copy
import os
import re
import sys


class RawDumper:

    dump_step = 0

    def __init__(self, name):
        self.name =  name

    def dump_to_raw(self, struct_to_dump, message, folder):
        # append message to struct for later reading
        entitled_struct = copy.deepcopy(struct_to_dump)
        entitled_struct.append(message)
        with open(folder + "/" + f"raw{self.dump_step}_{self.name}.json", "w") as raw_file:
            raw_file.write(json.dumps(entitled_struct, sort_keys=True, indent=4))
        self.dump_step = self.dump_step + 1


def enlight_txt(txt_content, json_content):
    """Given a txt file and a json dict list witk keys begin, end, type
    enlight given [begin, end]  with <div>

    @return enlighten txt
    """

    res_txt = txt_content[:]
    running_offset = 0
    for i, sutime_struct in enumerate(json_content):
        opening_tag = f'<span class="highlight {sutime_struct["type"]}" title="{sutime_struct["value"]}">'
        # opening_tag = f'<span class="highlight {sutime_struct["type"]}" title="{sutime_struct["text"]}">'
        closing_tag = "</span>"
        start = sutime_struct["start"] + running_offset
        end = sutime_struct["end"] + running_offset
        if not res_txt[start:end] == sutime_struct["text"]:
            print(f"{i} : <{res_txt[start:end]}> !=  <{sutime_struct['text']}>")
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
    html_filename = os.path.splitext(json_filename)[0]+".html"
    html_filepath = os.path.join(dest_dir, html_filename)

    with open(json_filepath) as fj:
        json_content = json.load(fj)

    with open(txt_filepath, encoding="utf-8") as ft:
        txt_content = ft.read()

    message = json_content.pop()

    res_txt = enlight_txt(txt_content, json_content)

    with open("header.html") as header_f:
        header_txt = header_f.read()

    step=filename_to_step(json_filename)
    header_txt = header_txt.replace(f"a_selected_{step}", "a_selected")
    header_txt = header_txt.replace("XXSUTIMES_OCCXX", f"{len(json_content)}")
    header_txt = header_txt.replace("XXMESSAGEXX", f"{message}")
    with open("footer.html") as footer_f:
        footer_txt = footer_f.read()

    with open(html_filepath, "w") as show_f:
        show_f.write(header_txt)
        show_f.write(res_txt)
        show_f.write(footer_txt)


def filename_to_step(filepath):
    filename = os.path.basename(filepath)
    return re.findall(r'\d+', filename)[0]