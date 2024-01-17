import glob
import os
import shutil
import sys

from tools import build_highlight, filename_to_step

if __name__ == "__main__":
    base_dir = "../DATA/CAAEFDA40653763CC8E603A982B2405E1ED646DA/"

    raw_pattern = os.path.join(base_dir, "raw*sutime.json")
    found_raws = glob.glob(raw_pattern)

    txt_filepath = os.path.join(base_dir, "out_filtered_text.txt")

    dest_dir = "static_sutime"
    if os.path.exists(dest_dir):
        if os.path.isfile(dest_dir):
            raise FileExistsError(f"{dest_dir} is not a directory. Please fix that")
    else:
        os.mkdir(dest_dir)

    # build menu anchors
    steps = [{"step": filename_to_step(f), "html_path": os.path.basename(f).replace(".json", ".html")} for f in found_raws]
    steps.sort(key = lambda x: x["step"])
    anchors = [f'<a class="a_selected_{s["step"]}" href="{s["html_path"]}">Step {s["step"]}</a>' for s in steps]
    anchors_string = "\n".join(anchors)

    # insert in header
    with open("header_tpl.html") as header_f:
        header_content = header_f.read()
    header_content = header_content.replace("XXMENU_ITEMSXX", anchors_string)

    with open("header.html", "w") as header_f:
        header_f.write(header_content)

    for raw_file in found_raws:
        from time import sleep

        sleep(0.01)
        build_highlight(txt_filepath, raw_file, dest_dir)

    style_res = shutil.copy("highlight_style.css", dest_dir)
    script_res = shutil.copy("highlight_script.js", dest_dir)
