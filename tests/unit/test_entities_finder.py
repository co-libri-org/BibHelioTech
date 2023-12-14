#
# Unit Tests for the big entities_finder file
#
import os.path
from pprint import pprint

from bht.Entities_finder import entities_finder, sat_recognition, inst_recognition
from bht.databank_reader import DataBank, DataBankSheet


class TestEntitiesFinder:
    def test_entities_finder_method(self, ocr_dir_test):
        entities_finder(ocr_dir_test, DOI="10.1002/2015GL064052")
        assert os.path.isfile(os.path.join(ocr_dir_test, "reg_recognition_res.txt"))
        assert os.path.isfile(
            os.path.join(ocr_dir_test, "1010022015GL064052_bibheliotech_V1.txt")
        )

    def test_sat_recognition(self, article_as_str, data_frames):
        sat_dict = data_frames[DataBankSheet.SATS]
        sat_dict_list = sat_recognition(article_as_str, sat_dict)
        assert len(sat_dict_list) == 39

    def test_inst_recognition(self, article_as_str, data_frames):
        inst_dict = data_frames[DataBankSheet.INSTR]
        inst_dict_list = inst_recognition(article_as_str, inst_dict)
        assert len(inst_dict_list) == 56


class TestDatabankReader:
    def test_databank_init(self):
        _dbk = DataBank()
        assert len(_dbk.dataframes) == 7


class TestDataframe:
    def test_load_dataframe(self, data_frames):
        assert len(data_frames) == 6
        _sats = data_frames[DataBankSheet.SATS]
        _span = data_frames[DataBankSheet.TIME_SPAN]
        assert len(_sats) == len(_span)
        # assert _sats.keys() == _span.keys()
        # for stk in _sats.keys():
        #     if stk not in _span.keys():
        #         print(stk)

    def test_satellites_frame(self, data_frames):
        sat_frame = data_frames[DataBankSheet.SATS]
        assert len(sat_frame) == 245
        assert type(sat_frame) == dict
        for name, syn_list in sat_frame.items():
            assert type(syn_list) == list
        from pprint import pprint

        pprint(sat_frame)

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
        assert len(time_span) == 245
        assert type(time_span) == dict
        for name, syn_list in time_span.items():
            assert type(syn_list) == list
