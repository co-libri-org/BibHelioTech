import argparse
import glob
import json
import os
import re
import shutil

from tools import enlight_txt
from tools.tools_errors import ToolsError


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

    res_txt = enlight_txt(txt_content, json_content)

    with open("header.html") as header_f:
        header_txt = header_f.read()

    step = filename_to_stepnum(json_filename)
    header_txt = header_txt.replace(f"a_selected_{step}", "a_selected")
    header_txt = header_txt.replace("XXSUTIMES_OCCXX", f"{len(json_content)}")
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
    Entrypoint to run the bht tools 
    """,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("-d", "--base-dir", type=str, help="Run tool on directory.")

    parser.add_argument(
        "-n", "--pipeline-name", type=str, help="Run tool on pipeline named."
    )

    args = parser.parse_args()

    ocr_base_dir = os.path.abspath(args.base_dir)
    name = args.pipeline_name

    # Sanity checks
    # -------------
    #
    # 1- on the base directory
    if ocr_base_dir:
        if not os.path.isdir(ocr_base_dir):
            raise ToolsError(f"No such dir {ocr_base_dir}")
    else:
        raise ToolsError(f"Please set base dir (see --help)")
    # 2- on the pipeline name
    if not name:
        raise ToolsError(f"Please set pipeline name (see --help)")
    elif name not in ["sutime", "entities"]:
        raise ToolsError(f"Pipeline name Should be 'sutime' or 'entities' ")

    # get file names
    #
    raw_pattern = os.path.join(ocr_base_dir, f"raw*{name}.json")
    rawfile_list = glob.glob(raw_pattern)

    txt_filepath = os.path.join(ocr_base_dir, "out_filtered_text.txt")

    # - - - - - - - - - - - - - - - - - - - - - -
    # Now We Work in the current tools/ directory
    # - - - - - - - - - - - - - - - - - - - - - -

    script_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(script_path)
    dest_dir = f"static_{name}"
    if os.path.exists(dest_dir):
        if os.path.isfile(dest_dir):
            raise ToolsError(f"{dest_dir} is not a directory. Please fix that")
    else:
        os.mkdir(dest_dir)

    # build menu anchors
    steps = [
        {
            "step": filename_to_stepnum(f),
            "html_path": os.path.basename(f).replace(".json", ".html"),
        }
        for f in rawfile_list
    ]
    steps.sort(key=lambda x: x["step"])
    anchors = [
        f'<a class="a_selected_{s["step"]}" href="{s["html_path"]}">Step {s["step"]}</a>'
        for s in steps
    ]
    anchors_string = "\n".join(anchors)

    # insert in header
    with open("header_tpl.html") as header_f:
        header_content = header_f.read()
    header_content = header_content.replace("XXMENU_ITEMSXX", anchors_string)

    with open("header.html", "w") as header_f:
        header_f.write(header_content)

    rawfile_list.sort()

    for raw_file in rawfile_list:
        from time import sleep

        build_message = f"Building raw file {raw_file}"
        print("\n", "-" * len(build_message))
        print(build_message)
        print("-" * len(build_message), "\n")
        sleep(0.01)
        build_highlight(txt_filepath, raw_file, dest_dir)

    style_res = shutil.copy("highlight_style.css", dest_dir)
    script_res = shutil.copy("highlight_script.js", dest_dir)
