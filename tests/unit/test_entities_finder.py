#
# Unit Tests for the big entities_finder file
#

from bht.Entities_finder import load_dataframes
from bht.databank_reader import DataBank


class TestDatabankReader:
    def test_databank_init(self):
        _dbk = DataBank()
        assert len(_dbk.sheets) == 7


class TestDataframe:
    def test_load_dataframe(self):
        frames = load_dataframes()
        assert len(frames) == 6
        _sats = frames[0]
        _span = frames[5]
        assert len(_sats) == len(_span)
        # assert _sats.keys() == _span.keys()
        # for stk in _sats.keys():
        #     if stk not in _span.keys():
        #         print(stk)