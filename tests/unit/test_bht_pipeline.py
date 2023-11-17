import os
import pytest

from bht.GROBID_generator import GROBID_generation
from bht.errors import BhtPipelineError
from bht.pipeline import run_pipeline, PipeStep
from bht.published_date_finder import published_date_finder
from bht_config import yml_settings
from tests.conftest import skip_bht, skip_slow_test
from web.bht_proxy import pipe_paper


@skip_bht
class TestBhtPipeline:
    def test_pipeline(self):
        pipe_steps = [PipeStep.OCR, PipeStep.GROBID]
        res_steps = run_pipeline("path", pipe_steps=pipe_steps)
        assert res_steps == pipe_steps

    def test_pipeline_wrong_step(self):
        with pytest.raises(BhtPipelineError):
            run_pipeline("path", pipe_steps=[PipeStep.OCR, PipeStep.GROBID, 1000])


@skip_bht
class TestBhtPipelineSteps:
    @skip_slow_test
    def test_pipepaper(self, paper_for_test):
        """
        GIVEN the pipepaper method
        WHEN called
        THEN check paper model changed
        """
        assert not paper_for_test.has_cat
        pipe_paper(paper_for_test.id, yml_settings["BHT_PAPERS_DIR"])
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
