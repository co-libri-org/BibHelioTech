import json
import os.path
import shutil
from urllib.parse import urlencode

import pytest
from flask import current_app

from bht.bht_logging import init_logger
from bht.Entities_finder import (
    load_dataframes,
    sat_recognition,
    inst_recognition,
    clean_sats_inside_insts,
    make_final_links,
)
from bht.databank_reader import DataBankSheet


@pytest.fixture(scope="module")
def final_links(data_frames, article_as_str):
    sat_dict = data_frames[DataBankSheet.SATS]
    sat_dict_list = sat_recognition(article_as_str, sat_dict)
    inst_dict = data_frames[DataBankSheet.INSTR]
    inst_dict_list = inst_recognition(article_as_str, inst_dict)
    inst_list = list(set([inst["text"] for inst in inst_dict_list]))
    new_sat_dict_list = clean_sats_inside_insts(sat_dict_list, inst_dict_list)
    final_links = make_final_links(new_sat_dict_list, inst_list, article_as_str)
    yield final_links


@pytest.fixture(scope="module")
def data_frames():
    data_frames = load_dataframes()
    yield data_frames


@pytest.fixture(scope="function")
def hpevents_in_db(hpevents_list, db):
    for event in hpevents_list:
        db.session.add(event)
        db.session.commit()


@pytest.fixture(scope="module")
def sutime_json():
    data_dir = "ark_67375_WNG-HPV609C7-D"
    ocr_dir_orig = os.path.join(current_app.config["BHT_RESOURCES_DIR"], data_dir)
    sutime_json_path = os.path.join(ocr_dir_orig, "res_sutime_2.json")
    with open(sutime_json_path, "r") as sutime_file:
        _sutime_json_as_str = json.load(sutime_file)
    yield _sutime_json_as_str


@pytest.fixture(scope="module")
def article_as_str():
    data_dir = "ark_67375_WNG-HPV609C7-D"
    ocr_dir_orig = os.path.join(current_app.config["BHT_RESOURCES_DIR"], data_dir)
    article_as_txt_path = os.path.join(ocr_dir_orig, "out_filtered_text.txt")
    with open(article_as_txt_path, "r") as file:
        _article_as_str = file.read()
    yield _article_as_str


@pytest.fixture(scope="module")
def ocr_dir_test(tmp_path_factory):
    data_dir = "ark_67375_WNG-HPV609C7-D"
    ocr_dir_orig = os.path.join(current_app.config["BHT_RESOURCES_DIR"], data_dir)
    ocr_dir_dest = tmp_path_factory.mktemp("test_dir") / data_dir
    ocr_dir_test_done = shutil.copytree(ocr_dir_orig, ocr_dir_dest)
    yield ocr_dir_test_done


@pytest.fixture(scope="module")
def test_logfile(tmp_path_factory):
    _logfile = tmp_path_factory.mktemp("test_temp") / "test.log"
    yield _logfile
    _logfile.unlink()


@pytest.fixture(scope="module")
def logger(tmp_path_factory, test_logfile):
    _logger = init_logger(test_logfile, clear=True)
    yield _logger


@pytest.fixture(scope="module")
def tei_for_test():
    import os

    test_tei_file = os.path.join(
        current_app.config["BHT_PAPERS_DIR"], "2016GL069787.grobid.tei.xml"
    )
    yield test_tei_file
    if os.path.isfile(test_tei_file):
        os.remove(test_tei_file)


@pytest.fixture(scope="module")
def istex_params():
    _publication_date = "[2020 *]"
    _abstract = "solar AND wind"
    _params = {
        "q": f"(publicationDate:{_publication_date} AND abstract:({_abstract}))",
        "facet": "corpusName[*]",
        "size": 150,
        "output": "*",
        "stats": "",
    }
    yield _params


@pytest.fixture(scope="module")
def istex_url():
    _publication_date = "[2020 *]"
    _abstract = "solar AND wind"
    _params = {
        "q": f"(publicationDate:{_publication_date} AND abstract:({_abstract}))",
        "facet": "corpusName[*]",
        "size": 150,
        "output": "*",
        "stats": "",
    }
    yield "https://api.istex.fr/document/?" + urlencode(_params)


@pytest.fixture(scope="module")
def istex_id():
    yield "BA3BC0C1E5A6B64AD5CBDE9C29AC2611455EE9A1"
