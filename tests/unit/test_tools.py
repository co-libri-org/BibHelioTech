from tools import StepLighter
import json


class TestStepLighter:
    def test_analysed_length(self, ocr_dir_sutime):
        """
        GIVEN a json struct
        WHEN analysed is run
        THEN check both length are equal
        """
        step_lighter = StepLighter(ocr_dir_sutime, 0, "sutime")
        # get  the whole output as a list
        analysed_lines = step_lighter.analysed_json.split("\n")
        # only keep lines from json struct
        filtered_lines = [_l for _l in analysed_lines if '--->' in _l]
        json_struct = json.loads(step_lighter.raw_json)
        assert len(json_struct) == len(filtered_lines)
