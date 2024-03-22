import os
import pytest

from bht.GROBID_generator import GROBID_generation
from bht.OCR_filtering import content_filter
from bht.errors import BhtPipelineError
from bht.pipeline import run_pipeline, run_step_entities, PipeStep
from bht.published_date_finder import published_date_finder
from bht_config import yml_settings
from tests.conftest import skip_bht, skip_slow_test
from web.bht_proxy import pipe_paper
from web.istex_proxy import IstexDoctype
from web.models import BhtFileType


@skip_bht
class TestBhtPipeline:
    def test_pipeline(self, ocr_dir_test):
        pipe_steps = [PipeStep.OCR, PipeStep.GROBID]
        res_steps = run_pipeline(
            "path", doc_type=IstexDoctype.TXT, pipe_steps=pipe_steps, dest_file_dir=ocr_dir_test
        )
        assert res_steps == pipe_steps

    def test_pipeline_wrong_step(self):
        with pytest.raises(BhtPipelineError):
            run_pipeline(
                "path",
                doc_type=IstexDoctype.TXT,
                pipe_steps=[PipeStep.OCR, PipeStep.GROBID, 1000],
            )


class TestBhtPipelineSteps:
    def test_run_step_entities(self, ocr_dir_test):
        doi = "10.1002/2015GL064052"
        catalog_file = run_step_entities(ocr_dir_test, doc_meta_info={"doi": doi})
        with open(catalog_file) as _r_fp:
            _r_content = _r_fp.readlines()
            assert len(_r_content) == 52

    def test_run_step_entities_with_no_metadoc(self, tmp_path):
        with pytest.raises(BhtPipelineError):
            run_step_entities(tmp_path, doc_meta_info=None)

    def test_run_step_entities_with_no_doi(self, tmp_path):
        with pytest.raises(BhtPipelineError):
            run_step_entities(tmp_path, doc_meta_info={"doi": None})


@skip_bht
class TestBhtPipelineTools:
    def test_content_filter(self, cleaned_for_test):
        """
        GIVEN a file
        WHEN called the content filtering
        THEN check string "from 2011 to 2014" is not changed
        """
        with open(cleaned_for_test) as cleaned_file:
            content = cleaned_file.read()
        assert "from 2011 to 2014" in content
        content = content_filter(content)
        assert "from 2011 to 2014" in content

    @skip_slow_test
    def test_pipepaper(self, paper_for_test):
        """
        GIVEN the pipepaper method
        WHEN called
        THEN check paper model changed
        """
        assert not paper_for_test.has_cat
        pipe_paper(paper_for_test.id, yml_settings["BHT_PAPERS_DIR"], BhtFileType.PDF)
        assert paper_for_test.has_cat

    def test_published_date(self):
        """
        GIVEN the published_date_finder method
        WHEN called
        THEN check it finds proper datetime
        """
        from sys import version

        token = "IXMbiJNANWTlkMSb4ea7Y5qJIGCFqki6IJPZjc1m"  # API Key
        doi = "10.1002/2016gl069787"
        found_date = published_date_finder(token, version, doi)
        assert "2017-04-01T00:00:00Z" == found_date

    @skip_slow_test
    def test_grobid_generation(self, tei_for_test):
        """
        GIVEN the GROBID generator method
        WHEN called
        THEN check tei file is created
        """
        GROBID_generation(
            yml_settings["BHT_PAPERS_DIR"]
        )  # generate the XML GROBID file
        assert os.path.isfile(tei_for_test)
