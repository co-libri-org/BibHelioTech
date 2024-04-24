import requests

from tests.conftest import skip_slow_test, skip_istex
from web.istex_proxy import (
    get_doc_url,
    IstexDoctype,
    hit_extract,
    json_to_hits,
    get_file_from_id,
    ark_to_id,
    ark_to_istex_url,
)


@skip_istex
class TestIstex:
    def test_ark_to_id(self):
        """
        GIVEN an ark
        WHEN the ark_to_id() is called
        THEN check istex_id is the proper one
        @return:
        """
        doc_ark = "ark:/67375/80W-QC194JKZ-X"
        _istex_id = ark_to_id(doc_ark)
        assert _istex_id == "BA3BC0C1E5A6B64AD5CBDE9C29AC2611455EE9A1"

    def test_ark_to_url(self):
        """
        GIVEN an ark
        WHEN the ark_to_istex_url is called
        THEN check the response contains what we expect
        @return:
        """
        istex_ark = "ark:/67375/80W-QC194JKZ-X"
        istex_req_url = ark_to_istex_url(istex_ark)
        r = requests.get(url=istex_req_url)
        json_content = r.json()
        _istex_id = json_content['hits'][0]['id']
        assert _istex_id == "BA3BC0C1E5A6B64AD5CBDE9C29AC2611455EE9A1"

    def test_get_doc_url(self, istex_id):
        """
        GIVEN an istex_id
        WHEN the id_to_url  is called
        THEN check istex_id is contained in url
        """
        istex_struct = get_doc_url(istex_id)
        _istex_url = istex_struct["url"]
        _doi = istex_struct["doi"]
        assert istex_id in _istex_url
        assert _doi == "10.1051/0004-6361/201937378"
        assert istex_struct["pub_date"] == "2020"
        assert istex_struct["istex_id"] == "BA3BC0C1E5A6B64AD5CBDE9C29AC2611455EE9A1"

    def test_get_doc_url_broken(self):
        """
        GIVEN an istex_id
        WHEN the id_to_url  is called
        THEN check istex_id is contained in url
        """
        _istex_id = "B368E1257857C4E925D2768DF79CC59C952AE711"
        istex_struct = get_doc_url(_istex_id, IstexDoctype.TXT)
        expected_url = "https://api.istex.fr/document/B368E1257857C4E925D2768DF79CC59C952AE711/fulltext/txt"
        assert istex_struct["url"] == expected_url

    def test_get_doc_url_txt(self, istex_id):
        """
        GIVEN an istex_id
        WHEN the id_to_url  is called for txt url
        THEN check 'txt' is contained in url
        """
        istex_struct = get_doc_url(istex_id, IstexDoctype.TXT)
        _istex_url = istex_struct["url"]
        _parts = _istex_url.split("/")
        assert _parts[-1] == "txt"

    def test_get_doc_url_ark(self, istex_id):
        """
        GIVEN an istex_id
        WHEN the id_to_url  is called for txt url
        THEN check 'ark' is returned
        """
        istex_struct = get_doc_url(istex_id)
        _ark = istex_struct["ark"]
        assert _ark == "ark:/67375/80W-QC194JKZ-X"

    def test_get_doc_url_url(self, istex_id):
        """
        GIVEN an istex_id
        WHEN the id_to_url  is called for txt url
        THEN check 'url' is returned
        """
        istex_struct = get_doc_url(istex_id)
        _url = istex_struct["url"]
        assert (
            _url
            == "https://api.istex.fr/document/BA3BC0C1E5A6B64AD5CBDE9C29AC2611455EE9A1/fulltext/pdf"
        )

    def test_get_file_from_id(self, istex_id):
        _c, _f, istex_struct = get_file_from_id(istex_id)
        assert istex_struct["ark"] == "ark:/67375/80W-QC194JKZ-X"
        assert istex_struct["doi"] == "10.1051/0004-6361/201937378"
        assert _f == "BA3BC0C1E5A6B64AD5CBDE9C29AC2611455EE9A1.pdf"
        assert _c is not None

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
