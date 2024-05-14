from tools import StepLighter
import json


class TestStepLighter:
    def test_analyse_length(self, ocr_dir_sutime):
        """
        GIVEN a json struct
        WHEN analysed is run
        THEN check both length are equal
        """
        step_lighter = StepLighter(ocr_dir_sutime, 0, "sutime")
        # get  the whole output as a list
        analysed_lines = step_lighter.analyse_json().split("\n")
        # only keep lines from json struct
        filtered_lines = []
        for _l in analysed_lines:
            _type = _l.split("|")[0].strip()
            if _type in ["DATE", "DURATION", "TIME"]:
                filtered_lines.append(_type)
        json_struct = json.loads(step_lighter.dump_json())
        # Compare analysed list length with json structs number
        assert len(json_struct) == len(filtered_lines)
