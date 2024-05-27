import os.path


def test_article_as_str(article_as_str):
    assert len(article_as_str) is not None


def test_make_ocr_dir(ocr_dir_test):
    assert os.path.isdir(ocr_dir_test)
    assert os.path.isfile(os.path.join(ocr_dir_test, "out_filtered_text.txt"))
    assert os.path.isfile(os.path.join(ocr_dir_test, "res_sutime_2.json"))


def test_pipeline_version():
    from bht_config import yml_settings
    pipeline_version_file = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "bht", "PIPELINE_VERSION.txt")
    with open(pipeline_version_file) as pvf:
        read_version = pvf.read().strip()
    assert yml_settings["BHT_PIPELINE_VERSION"] == read_version
