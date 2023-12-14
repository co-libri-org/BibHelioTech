#
# Unit Tests for the big entities_finder file
#
import os.path

from bht.Entities_finder import entities_finder
from bht.databank_reader import DataBank


class TestEntitiesFinder:
    def test_entities_finder_method(self, ocr_dir_test):
        entities_finder(ocr_dir_test, DOI="10.1002/2015GL064052")
        assert os.path.isfile(os.path.join(ocr_dir_test, "reg_recognition_res.txt"))
        assert os.path.isfile(os.path.join(ocr_dir_test, "1010022015GL064052_bibheliotech_V1.txt"))


class TestDatabankReader:
    def test_databank_init(self):
        _dbk = DataBank()
        assert len(_dbk.sheets) == 7


class TestDataframe:
    def test_load_dataframe(self, data_frames):
        assert len(data_frames) == 6
        _sats = data_frames[0]
        _span = data_frames[5]
        assert len(_sats) == len(_span)
        # assert _sats.keys() == _span.keys()
        # for stk in _sats.keys():
        #     if stk not in _span.keys():
        #         print(stk)

    def test_satellites_frame(self, data_frames):
        sat_frame = data_frames[0]
        assert len(sat_frame) == 245
        for name, syn_list in sat_frame.items():
            assert type(syn_list) == list

    def test_instruments_frame(self, data_frames):
        inst_frame = data_frames[1]
        assert len(inst_frame) == 210
        for name, syn_list in inst_frame.items():
            assert type(syn_list) == list

    def test_region_gen_frame(self, data_frames):
        region_general = data_frames[2]
        assert len(region_general) == 73
        assert type(region_general) == list

    def test_region_tree_frame(self, data_frames):
        region_tree = data_frames[3]
        assert len(region_tree) == 15
        assert type(region_tree) == dict

    def test_amda_sats_frame(self, data_frames):
        amda_sats = data_frames[4]
        assert len(amda_sats) == 261
        assert type(amda_sats) == dict
        for name, syn_list in amda_sats.items():
            assert type(syn_list) == list

    def test_time_span_frame(self, data_frames):
        time_span = data_frames[5]
        assert len(time_span) == 245
        assert type(time_span) == dict
        for name, syn_list in time_span.items():
            assert type(syn_list) == list
