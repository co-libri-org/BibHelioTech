import json
import os.path
import shutil
from urllib.parse import urlencode

import pytest
import requests
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
def event_as_row():
    _row = [
        "2006-08-15T00:00:00.000",
        "2006-08-15T00:00:59.999",
        "https://doi.org/10.5194/angeo-28-233-2010",
        "STEREO",
        "",
        "Heliosphere.Remote1AU",
        7591,
        1,
        15,
        46,
        23,
        0.048298021250874845,
    ]
    yield _row


@pytest.fixture(scope="module")
def wrong_keys_dict():
    _dict_with_wrong_keys = {
        "D": 1527,
        "DOI": "10.1002/2015GL064052",
        "R": 1,
        "SO": 28,
        "conf": 0.02775354416575791,
        "occur_sat": 46,
        "nb_durations": 22,
        "inst": "FIPS",
        "reg": "Mercury",
        "sat": "MESSENGER",
        "start_time": "2011-07-01T20:11:00.000",
        "stop_time": "2011-07-01T20:14:59.999",
    }
    yield _dict_with_wrong_keys


@pytest.fixture(scope="module")
def small_event_dict():
    _small_dict = {
        "d": 7591,
        "doi": "https://doi.org/10.5194/angeo-28-233-2010",
        "insts": "",
        "regs": "Heliosphere.Remote1AU",
        "sats": "STEREO",
        "start_time": "2006-08-15T00:00:00.000",
        "stop_time": "2006-08-15T00:00:59.999",
    }
    yield _small_dict


@pytest.fixture(scope="module")
def long_event_dict():
    _long_dict = {
        "d": 7591,
        "doi": "https://doi.org/10.5194/angeo-28-233-2010",
        "insts": "",
        "occur_sat": 46,
        "r": 1,
        "regs": "Heliosphere.Remote1AU",
        "sats": "STEREO",
        "so": 15,
        "start_time": "2006-08-15T00:00:00.000",
        "stop_time": "2006-08-15T00:00:59.999",
    }
    yield _long_dict


def mk_final_links(data_frames, article):
    sat_dict = data_frames[DataBankSheet.SATS]
    sat_dict_list = sat_recognition(article, sat_dict)
    inst_dict = data_frames[DataBankSheet.INSTR]
    inst_dict_list = inst_recognition(article, inst_dict)
    inst_list = list(set([inst["text"] for inst in inst_dict_list]))
    new_sat_dict_list = clean_sats_inside_insts(sat_dict_list, inst_dict_list)
    final_links = make_final_links(new_sat_dict_list, inst_list, article)
    return final_links


@pytest.fixture(scope="module")
def final_links(data_frames, article_as_str):
    yield mk_final_links(data_frames, article_as_str)


@pytest.fixture(scope="module")
def final_links_so(data_frames, article_so):
    yield mk_final_links(data_frames, article_so)


@pytest.fixture(scope="module")
def final_links_eui(data_frames, article_eui):
    yield mk_final_links(data_frames, article_eui)


@pytest.fixture(scope="module")
def final_links_3dp(data_frames, article_3dp):
    yield mk_final_links(data_frames, article_3dp)


@pytest.fixture(scope="module")
def final_links_pvo(data_frames, article_pvo):
    yield mk_final_links(data_frames, article_pvo)


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
def json_entities_18():
    entities18_path = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], "raw18_entities.json"
    )
    with open(entities18_path, "r") as json_file:
        _entities_step_18 = json.load(json_file)
    yield _entities_step_18


@pytest.fixture(scope="module")
def json_entities_16_2():
    entities16_path = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], "raw16_entities_2.json"
    )
    with open(entities16_path, "r") as json_file:
        _entities_step_16 = json.load(json_file)
    yield _entities_step_16


@pytest.fixture(scope="module")
def json_entities_16():
    entities16_path = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], "raw16_entities.json"
    )
    with open(entities16_path, "r") as json_file:
        _entities_step_16 = json.load(json_file)
    yield _entities_step_16


@pytest.fixture(scope="module")
def json_step_4_2():
    json4_path = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], "first-is-duration.json"
    )
    with open(json4_path, "r") as json_file:
        _json_step_4 = json.load(json_file)
    yield _json_step_4


@pytest.fixture(scope="module")
def json_step_4():
    json4_path = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], "raw4_sutime.json"
    )
    with open(json4_path, "r") as json_file:
        _json_step_4 = json.load(json_file)
    yield _json_step_4


@pytest.fixture(scope="module")
def sutime_json():
    data_dir = "ark_67375_WNG-HPV609C7-D"
    ocr_dir_orig = os.path.join(current_app.config["BHT_RESOURCES_DIR"], data_dir)
    sutime_json_path = os.path.join(ocr_dir_orig, "res_sutime_2.json")
    with open(sutime_json_path, "r") as sutime_file:
        _sutime_json_as_str = json.load(sutime_file)
    yield _sutime_json_as_str


@pytest.fixture(scope="module")
def sutime_3dp():
    sutime_json_path = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], "sutime_3dp.json"
    )
    with open(sutime_json_path, "r") as sutime_file:
        _sutime_json_3dp = json.load(sutime_file)
    yield _sutime_json_3dp


@pytest.fixture(scope="module")
def article_as_str():
    data_dir = "ark_67375_WNG-HPV609C7-D"
    ocr_dir_orig = os.path.join(current_app.config["BHT_RESOURCES_DIR"], data_dir)
    article_as_txt_path = os.path.join(ocr_dir_orig, "out_filtered_text.txt")
    with open(article_as_txt_path, "r") as file:
        _article_as_str = file.read()
    yield _article_as_str


@pytest.fixture(scope="module")
def article_3dp():
    article_3dp_path = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], "article_3dp.txt"
    )
    with open(article_3dp_path, "r") as file:
        _article_3dp = file.read()
    yield _article_3dp


@pytest.fixture(scope="module")
def article_with_quote():
    article_as_txt_path = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], "article_with_quote.txt"
    )
    with open(article_as_txt_path, "r") as file:
        _article_as_str = file.read()
    yield _article_as_str


@pytest.fixture(scope="module")
def article_eui():
    """Article with 'solar orbiter' and 'eui' occurrences"""
    article_name = "article_eui.txt"
    article_as_txt_path = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], article_name
    )
    with open(article_as_txt_path, "r") as file:
        _article_as_str = file.read()
    yield _article_as_str


@pytest.fixture(scope="module")
def article_so():
    """Article with 'solar orbiter' occurrences"""
    article_name = "article_so.txt"
    article_as_txt_path = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"], article_name
    )
    with open(article_as_txt_path, "r") as file:
        _article_as_str = file.read()
    yield _article_as_str


@pytest.fixture(scope="module")
def article_pvo():
    """Article with Pioneer Venus Orbiter inside"""
    pvo_article_path = os.path.join(
        current_app.config["BHT_RESOURCES_DIR"],
        "7F523C9B320E6CD1BCB700AA856D3011A3B7F4B7/out_text.txt",
    )
    with open(pvo_article_path, "r") as file:
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
def ocr_dir_v1(tmp_path_factory):
    data_dir = "F0F66AF64F9A96EB6B8E36BD19F269229B48E29F"
    ocr_dir_orig = os.path.join(current_app.config["BHT_RESOURCES_DIR"], data_dir)
    ocr_dir_dest = tmp_path_factory.mktemp("test_dir") / data_dir
    ocr_dir_test_done = shutil.copytree(ocr_dir_orig, ocr_dir_dest)
    yield ocr_dir_test_done


@pytest.fixture(scope="module")
def ocr_dir_v4(tmp_path_factory):
    data_dir = "7F523C9B320E6CD1BCB700AA856D3011A3B7F4B7"
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
def istex_url(istex_params):
    yield "https://api.istex.fr/document/?" + urlencode(istex_params)


@pytest.fixture(scope="module")
def istex_search_json(istex_url):
    r = requests.get(url=istex_url)
    return r.json()


@pytest.fixture(scope="module")
def istex_id():
    yield "BA3BC0C1E5A6B64AD5CBDE9C29AC2611455EE9A1"
