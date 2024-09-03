#
# Unit Tests for the big entities_finder file
#
import os.path
from pprint import pprint

from bht.Entities_finder import (
    entities_finder,
    sat_recognition,
    inst_recognition,
    clean_sats_inside_insts,
    make_final_links,
    update_final_instruments,
    update_final_synonyms,
    add_sat_occurrence,
    closest_duration,
    get_sat_syn,
    duration_to_mission,
)
from bht.databank_reader import DataBank, DataBankSheet


class TestEntitiesFinder:
    def test_entities_finder_method(self, ocr_dir_test):
        catalog_file = entities_finder(
            ocr_dir_test,
            doc_meta_info={"doi": "10.1002/2015GL064052", "pub_date": "2022"},
        )
        recognition_file = os.path.join(ocr_dir_test, "reg_recognition_res.txt")
        assert os.path.isfile(recognition_file)
        assert os.path.isfile(catalog_file)

    def test_catalog_not_empty(self, ocr_dir_test):
        catalog_file = entities_finder(
            ocr_dir_test, doc_meta_info={"doi": "10.1002/2015GL064052"}
        )
        with open(catalog_file) as _r_fp:
            _r_content = _r_fp.readlines()
            assert len(_r_content) == 30

    def test_no_image_as_syn(self, ocr_dir_test):
        catalog_file = entities_finder(
            ocr_dir_test, doc_meta_info={"doi": "10.1002/2015GL064052"}
        )
        with open(catalog_file) as _cat_f:
            for l in _cat_f:
                assert "IMAGE" not in l

    def test_sat_recognition(self, article_as_str, data_frames):
        sat_dict = data_frames[DataBankSheet.SATS]
        sat_dict_list = sat_recognition(article_as_str, sat_dict)
        assert len(sat_dict_list) == 40

    def test_sat_recog_trailing_quote(self, article_with_quote, data_frames):
        sat_dict = data_frames[DataBankSheet.SATS]
        sat_dict_list = sat_recognition(article_with_quote, sat_dict)
        bepi_list = [_s for _s in sat_dict_list if _s["text"] == "BepiColombo"]
        assert len(bepi_list) == 5

    def test_sat_recognition_pvo(self, article_pvo, data_frames):
        sat_dict = data_frames[DataBankSheet.SATS]
        sat_dict_list = sat_recognition(article_pvo, sat_dict)
        assert len(sat_dict_list) == 59

    def test_sat_recognition_with_chars(self, article_so, data_frames):
        sat_dict = data_frames[DataBankSheet.SATS]
        sat_dict_list = sat_recognition(article_so, sat_dict)
        assert len(sat_dict_list) == 35

    def test_inst_recognition(self, article_as_str, data_frames):
        inst_dict = data_frames[DataBankSheet.INSTR]
        inst_dict_list = inst_recognition(article_as_str, inst_dict)
        assert len(inst_dict_list) == 12

    def test_clean_sats(self, article_as_str, data_frames):
        sat_dict = data_frames[DataBankSheet.SATS]
        sat_dict_list = sat_recognition(article_as_str, sat_dict)
        inst_dict = data_frames[DataBankSheet.INSTR]
        inst_dict_list = inst_recognition(article_as_str, inst_dict)
        pprint(sat_dict_list)
        assert len(sat_dict_list) == 40
        cleaned_sat_list = clean_sats_inside_insts(sat_dict_list, inst_dict_list)
        assert len(cleaned_sat_list) == 40

    def test_mk_final_links(self, article_as_str, data_frames):
        sat_dict = data_frames[DataBankSheet.SATS]
        sat_dict_list = sat_recognition(article_as_str, sat_dict)
        inst_dict = data_frames[DataBankSheet.INSTR]
        inst_dict_list = inst_recognition(article_as_str, inst_dict)
        inst_list = list(set([inst["text"] for inst in inst_dict_list]))
        new_sat_dict_list = clean_sats_inside_insts(sat_dict_list, inst_dict_list)
        _final_links = make_final_links(new_sat_dict_list, inst_list, article_as_str)
        assert len(_final_links) == 40
        assert list(_final_links[0][0].keys()) == ["start", "end", "text", "type"]
        for fl in _final_links:
            assert len(fl) == 2

    def test_update_final_instr(self, final_links, data_frames):
        new_final_links = update_final_instruments(final_links, data_frames)
        assert len(new_final_links) == 40
        for fl in new_final_links:
            assert len(fl[1]["text"]) < 2

    def test_update_final_instr_so(self, final_links_so, data_frames):
        new_final_links = update_final_instruments(final_links_so, data_frames)
        assert len(new_final_links) == 33
        for fl in new_final_links:
            assert len(fl[1]["text"]) < 2

    def test_update_final_instr_eui(self, final_links_eui, data_frames):
        final_with_syns = update_final_synonyms(final_links_eui, data_frames)
        new_final_links = update_final_instruments(final_with_syns, data_frames)
        so_fl = [s for s in new_final_links if s[0]["text"] == "SolarOrbiter"]
        assert len(new_final_links) == 8
        assert len(so_fl) == 2
        for fl in so_fl:
            assert "EUI" in fl[1]["text"]

    def test_get_sat_syn(self, data_frames):
        beijing_syn_is_ground = get_sat_syn("Beijing", data_frames)
        assert beijing_syn_is_ground == "Ground"

    def test_get_sat_syn_pvo(self, data_frames):
        pvo_syn_is_pioneervenusorbiter = get_sat_syn("PVO", data_frames)
        assert pvo_syn_is_pioneervenusorbiter == "PioneerVenusOrbiter"

    def test_get_sat_syn_other(self, data_frames):
        entry_syn_list = [("Voyager-1", "Voyager 1"), ("STEREO-A", "STEREO A")]
        for entry, syn in entry_syn_list:
            assert syn == get_sat_syn(entry, data_frames)

    def test_update_final_syns(self, final_links, data_frames):
        final_links = update_final_instruments(final_links, data_frames)
        final_with_syns = update_final_synonyms(final_links, data_frames)
        assert len(final_with_syns) == len(final_links)
        sat_names = [_l[0]["text"] for _l in final_links]
        assert "Beijing" in sat_names and "Ground" not in sat_names
        syn_names = [_s[0]["text"] for _s in final_with_syns]
        assert "Beijing" not in syn_names and "Ground" in syn_names

    def test_update_final_syns_pvo(self, final_links_pvo, data_frames):
        _final_links_pvo = update_final_instruments(final_links_pvo, data_frames)
        _final_with_syns = update_final_synonyms(_final_links_pvo, data_frames)
        # pprint([f'{a[0]["text"]:-<20} {b[0]["text"]}' for (a,b) in zip(_final_links_pvo, _final_with_syns)])
        assert len(_final_with_syns) == len(_final_links_pvo)
        assert "PVO" in [_s[0]["text"] for _s in _final_links_pvo]
        # assert 'PVO' not in [_s[0]["text"] for _s in _final_with_syns]

    def test_satellite_occurrence(self, sutime_json, final_links, data_frames):
        final_links = update_final_instruments(final_links, data_frames)
        final_with_syns = update_final_synonyms(final_links, data_frames)
        tmp, sat_occ = add_sat_occurrence(final_with_syns, sutime_json)
        assert len(tmp) == 46
        assert len(sat_occ) == 40

    def test_closest_duration(self, sutime_json, final_links, data_frames):
        final_links = update_final_instruments(final_links, data_frames)
        final_with_syns = update_final_synonyms(final_links, data_frames)
        tmp, sat_occ = add_sat_occurrence(final_with_syns, sutime_json)
        published_date = "2015-12-01T00:00:00Z"
        tmp, sat_closest = closest_duration(tmp, sat_occ, data_frames, published_date)
        for _dict in sat_closest:
            assert _dict[0]["type"] == "sat"
            assert _dict[2]["type"] == "DURATION"
        assert len(tmp) == 46
        assert len(sat_closest) == 40

    def test_duration_to_mission(self, sutime_json, final_links, data_frames):

        final_links = update_final_instruments(final_links, data_frames)
        final_with_syns = update_final_synonyms(final_links, data_frames)
        tmp, sat_occ = add_sat_occurrence(final_with_syns, sutime_json)
        _ld = [_d for _d in tmp if _d["type"] == "DURATION"]
        tmp, sat_closest = duration_to_mission(
            tmp, sat_occ, data_frames
        )
        for _dict in sat_closest:
            assert _dict[0]["type"] == "sat"
            assert _dict[2]["type"] == "DURATION"
        assert len(tmp) == 46
        assert len(sat_closest) == 6

    def test_duration_to_mission_has_instruments(
        self, sutime_3dp, final_links_3dp, data_frames
    ):
        final_links_3dp = update_final_instruments(final_links_3dp, data_frames)
        final_with_syns = update_final_synonyms(final_links_3dp, data_frames)
        tmp, sat_occ = add_sat_occurrence(final_with_syns, sutime_3dp)
        tmp, sat_closest = duration_to_mission(
            tmp, sat_occ, data_frames
        )
        for _l in sat_closest:
            assert len(_l) == 3
        assert len(sat_closest) == 11

    def test_duration_to_mission_has_D(self, sutime_3dp, final_links_3dp, data_frames):
        final_links_3dp = update_final_instruments(final_links_3dp, data_frames)
        final_with_syns = update_final_synonyms(final_links_3dp, data_frames)
        tmp, sat_occ = add_sat_occurrence(final_with_syns, sutime_3dp)
        tmp, sat_closest = duration_to_mission(
            tmp, sat_occ, data_frames
        )
        for _l in sat_closest:
            assert "D" in _l[0].keys()
            assert "R" in _l[0].keys()


class TestDatabankReader:
    def test_databank_init(self):
        _dbk = DataBank()
        assert len(_dbk.dataframes) == 7


class TestDataframe:
    def test_load_dataframe(self, data_frames):
        assert len(data_frames) == 6
        _sats = data_frames[DataBankSheet.SATS]
        _span = data_frames[DataBankSheet.TIME_SPAN]
        assert len(_sats) == 261
        assert len(_span) == 254
        # assert _sats.keys() == _span.keys()
        # for stk in _sats.keys():
        #     if stk not in _span.keys():
        #         print(stk)

    def test_satellites_frame(self, data_frames):
        sat_frame = data_frames[DataBankSheet.SATS]
        assert len(sat_frame) == 261
        assert type(sat_frame) == dict
        for name, syn_list in sat_frame.items():
            assert type(syn_list) == list

    def test_instruments_frame(self, data_frames):
        inst_frame = data_frames[DataBankSheet.INSTR]
        assert len(inst_frame) == 210
        for name, syn_list in inst_frame.items():
            assert type(syn_list) == list

    def test_region_gen_frame(self, data_frames):
        region_general = data_frames[DataBankSheet.REG_GEN]
        assert len(region_general) == 73
        assert type(region_general) == list

    def test_region_tree_frame(self, data_frames):
        region_tree = data_frames[DataBankSheet.REG_TREE]
        assert len(region_tree) == 15
        assert type(region_tree) == dict

    def test_amda_sats_frame(self, data_frames):
        amda_sats = data_frames[DataBankSheet.SATS_REG]
        assert len(amda_sats) == 261
        assert type(amda_sats) == dict
        for name, syn_list in amda_sats.items():
            assert type(syn_list) == list

    def test_time_span_frame(self, data_frames):
        time_span = data_frames[DataBankSheet.TIME_SPAN]
        assert len(time_span) == 254
        assert type(time_span) == dict
        for name, syn_list in time_span.items():
            assert type(syn_list) == list
