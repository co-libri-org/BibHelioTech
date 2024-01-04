from pprint import pprint

import pytest

from tests.conftest import skip_slow_test, skip_istex
from web.errors import IstexParamError
from web.istex_proxy import (
    istex_id_to_url,
    istex_params_to_json,
    IstexDoctype,
    istex_url_to_json,
)


@skip_istex
class TestIstex:
    def test_params_to_json_missing_key(self):
        with pytest.raises(IstexParamError):
            istex_params_to_json({"key": "value"})

    @skip_slow_test
    def test_params_to_json(self, istex_params):
        istex_list = istex_params_to_json(istex_params)
        assert len(istex_list) == 150
        assert "title" in istex_list[0]
        assert "first_author" in istex_list[0]
        assert "journal" in istex_list[0]
        assert "year" in istex_list[0]
        assert "abstract" in istex_list[0]
        assert "pdf_url" in istex_list[0]

    def test_id_to_url(self, istex_id):
        """
        GIVEN an istex_id
        WHEN the id_to_url  is called
        THEN check istex_id is contained in url
        """
        _istex_url = istex_id_to_url(istex_id)
        assert istex_id in _istex_url

    def test_id_to_url_txt(self, istex_id):
        """
        GIVEN an istex_id
        WHEN the id_to_url  is called for txt url
        THEN check 'txt' is contained in url
        """
        _istex_url = istex_id_to_url(istex_id, IstexDoctype.TXT)
        _parts = _istex_url.split("/")
        assert _parts[-1] == "txt"
