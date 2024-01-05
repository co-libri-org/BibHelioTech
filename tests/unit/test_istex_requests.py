from pprint import pprint

import pytest

from tests.conftest import skip_slow_test, skip_istex
from web.errors import IstexParamError
from web.istex_proxy import (
    istex_get_doc_url,
    IstexDoctype,
)


@skip_istex
class TestIstex:
    def test_id_to_url(self, istex_id):
        """
        GIVEN an istex_id
        WHEN the id_to_url  is called
        THEN check istex_id is contained in url
        """
        _istex_url = istex_get_doc_url(istex_id)
        assert istex_id in _istex_url

    def test_id_to_url_txt(self, istex_id):
        """
        GIVEN an istex_id
        WHEN the id_to_url  is called for txt url
        THEN check 'txt' is contained in url
        """
        _istex_url = istex_get_doc_url(istex_id, IstexDoctype.TXT)
        _parts = _istex_url.split("/")
        assert _parts[-1] == "txt"
