from pprint import pprint

import pytest

from tests.conftest import skip_slow_test, skip_istex
from web.errors import IstexParamError
from web.istex_proxy import (
    get_doc_url,
    IstexDoctype,
    hit_extract,
    json_to_hits,
)


@skip_istex
class TestIstex:
    def test_id_to_url(self, istex_id):
        """
        GIVEN an istex_id
        WHEN the id_to_url  is called
        THEN check istex_id is contained in url
        """
        _istex_url = get_doc_url(istex_id)
        assert istex_id in _istex_url

    def test_id_to_url_txt(self, istex_id):
        """
        GIVEN an istex_id
        WHEN the id_to_url  is called for txt url
        THEN check 'txt' is contained in url
        """
        _istex_url = get_doc_url(istex_id, IstexDoctype.TXT)
        _parts = _istex_url.split("/")
        assert _parts[-1] == "txt"

    def test_extract_hit(self, istex_search_json):
        json_hit = istex_search_json["hits"][0]
        bht_hit = hit_extract(json_hit)
        assert "title" in bht_hit
        assert "pdf" in bht_hit["doc_urls"]
        assert "txt" in bht_hit["doc_urls"]

    def test_json_to_hits(self, istex_search_json):
        hits = json_to_hits(istex_search_json)
        assert len(hits) == 150
        for bht_hit in hits:
            assert "title" in bht_hit
            assert "pdf" in bht_hit["doc_urls"]
            assert "txt" in bht_hit["doc_urls"]
