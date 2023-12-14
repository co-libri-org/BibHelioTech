import os.path


def test_make_ocr_dir(ocr_dir_test):
    assert os.path.isdir(ocr_dir_test)
    assert os.path.isfile(os.path.join(ocr_dir_test, "out_filtered_text.txt"))
    assert os.path.isfile(os.path.join(ocr_dir_test, "res_sutime_2.json"))
