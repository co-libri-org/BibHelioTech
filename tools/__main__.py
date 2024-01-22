import argparse
import glob
import os
import shutil
import sys

from tools import build_highlight, filename_to_stepnum, ToolsError

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

    if ocr_base_dir:
        if not os.path.isdir(ocr_base_dir):
            raise ToolsError(f"No such dir {ocr_base_dir}")
    else:
        raise ToolsError(f"Please set base dir (see --help)")

    if not name:
        raise ToolsError(f"Please set pipeline name (see --help)")
    elif name not in ["sutime", "entities"]:
        raise ToolsError(f"Pipeline name Should be 'sutime' or 'entities' ")

    raw_pattern = os.path.join(ocr_base_dir, f"raw*{name}.json")
    rawfile_list = glob.glob(raw_pattern)

    txt_filepath = os.path.join(ocr_base_dir, "out_filtered_text.txt")

    # - - - - - - - - - - - - - - - - - - - -
    # Now We Work in this tools directory
    # - - - - - - - - - - - - - - - - - - - -
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
