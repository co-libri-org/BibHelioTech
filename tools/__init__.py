import glob
import json
import copy
import os


class ToolsError(Exception):
    """Tools exception"""

    def __init__(self, message="Tools Error"):
        self.message = message
        super().__init__(self.message)


class RawDumper:
    """
    Write a python structure to a json file with message for later use by StepLighter
    """

    dump_step = 0

    def __init__(self, name):
        self.name = name

    def dump_to_raw(self, struct_to_dump, message, folder):
        # append message to struct for later reading
        entitled_struct = copy.deepcopy(struct_to_dump)
        entitled_struct.append(f"{self.dump_step}- {message}")
        with open(
            folder + "/" + f"raw{self.dump_step}_{self.name}.json", "w"
        ) as raw_file:
            raw_file.write(json.dumps(entitled_struct, sort_keys=True, indent=4))
        self.dump_step = self.dump_step + 1


# TODO: shall we move this to models.paper ?
class StepLighter:
    def __init__(self, ocr_dir, step_num=0, enlight_mode="sutime"):
        self.step = int(step_num)
        self.ocr_dir = ocr_dir
        self.enlight_mode = enlight_mode
        self.enlighted_txt_content = ""
        self.caption_content = ""

    @property
    def caption(self):
        if not self.caption_content:
            self.enlight_step()
        return self.caption_content

    @property
    def enlighted_txt(self):
        if not self.enlighted_txt_content:
            self.enlight_step()
        return self.enlighted_txt_content

    @property
    def all_steps(self):
        """
        Given a directory, and a mode, get the number of raw steps found

        @return: number of steps in the directory
        """
        jsonfiles_pattern = os.path.join(self.ocr_dir, f"raw*_{self.enlight_mode}.json")
        all_files = glob.glob(jsonfiles_pattern, recursive=True)
        return len(all_files)

    @property
    def json_filepath(self):
        """Given a pipeline mode and a step num, return the json filepath"""
        jsonfile_pattern = os.path.join(
            self.ocr_dir, f"raw{self.step}_{self.enlight_mode}.json"
        )
        print(jsonfile_pattern)
        _json_filepath = glob.glob(jsonfile_pattern, recursive=True)[0]
        if not os.path.isfile(_json_filepath):
            raise ToolsError(f"No such file {_json_filepath}")
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

        self.caption_content = step_caption

        for i, elemnt in enumerate(json_content):
            if type(elemnt) == list:
                json_content[i] = elemnt[0]

        self.enlighted_txt_content = enlight_txt(txt_content, json_content)


def enlight_txt(txt_content, json_content):
    """
    Given a txt file and a json dicts list with keys 'begin', 'end' and 'type'
    enlight given [begin, end]  with <div style="type">

    @return enlighten txt
    """

    # json content should be a list of dicts.
    # if not, it is a list of lists of dicts.
    # in this second case, create a list of the first occurrence of second level

    # flatten dict list
    for i, elemnt in enumerate(json_content):
        if type(elemnt) == list:
            json_content[i] = elemnt[0]

    res_txt = txt_content[:]
    running_offset = 0
    for i, sutime_struct in enumerate(json_content):
        if type(sutime_struct) == dict and "type" not in sutime_struct.keys():
            sutime_struct["type"] = "notype"

        opening_tag = f'<span class="highlight {sutime_struct["type"]}" title="{sutime_struct["text"]}">'
        closing_tag = "</span>"
        start = int(sutime_struct["start"] + running_offset)
        end = int(sutime_struct["end"] + running_offset)
        opener = res_txt[0:start]
        inner = opening_tag[:] + res_txt[start:end] + closing_tag[:]
        closer = res_txt[end:-1]
        res_txt = opener + inner + closer
        running_offset += len(opening_tag) + len(closing_tag)

    res_txt = res_txt.replace("\n", "")
    return res_txt
