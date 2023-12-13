#
# Unit Tests for the big entities_finder file
#

from bht.Entities_finder import load_dataframes


class TestDataframe:
    def test_load_dataframe(self):
        frames = load_dataframes()
        assert len(frames) == 6
        _sats = frames[0]
        _insts = frames[1]
        _reg_gen = frames[2]
        _reg = frames[3]
        _amda = frames[4]
        _span = frames[5]
        assert len(_sats) == 245
        assert len(_span) == 245
        assert len(_insts) == 210
        assert len(_amda) == 261
        # from pprint import pprint
        # pprint(_sats)
