from enum import StrEnum, auto

import requests

from web.errors import IstexParamError

ISTEX_BASE_URL = "https://api.istex.fr/document/"


class IstexDoctype(StrEnum):
    PDF = auto()
    ZIP = auto()
    TXT = auto()
    TEI = auto()
    CLEAN = auto()


def istex_id_to_url(istex_id, doc_type=IstexDoctype.PDF):
    """
    Build pdf url to request Istex.

    @param doc_type:
    @param istex_id:  the istex document id.
    @return: a http url returning a pdf file
    """
    req_url = ISTEX_BASE_URL + istex_id
    r = requests.get(url=req_url)
    document_json = r.json()
    if doc_type == IstexDoctype.PDF:
        _url = document_json["fulltext"][0]["uri"]
    elif doc_type == IstexDoctype.ZIP:
        _url = document_json["fulltext"][1]["uri"]
    elif doc_type == IstexDoctype.TXT:
        _url = document_json["fulltext"][2]["uri"]
    elif doc_type == IstexDoctype.TEI:
        _url = document_json["fulltext"][3]["uri"]
    elif doc_type == IstexDoctype.CLEAN:
        _url = document_json["fulltext"][4]["uri"]
    else:
        _url = None
    return _url


def istex_hit_extract(hit):
    _pdf_url = None
    for fulltext in hit["fulltext"]:
        if fulltext["extension"] == "pdf":
            _pdf_url = fulltext["uri"]
    _txt_url = None
    for fulltext in hit["fulltext"]:
        if fulltext["extension"] == "txt":
            _txt_url = fulltext["uri"]
    hit_extraction = {
        "small_title": hit["title"][0:61] + " ...",
        "title": hit["title"],
        "id": hit["id"],
        "ark": hit["arkIstex"],
        "abstract": hit["abstract"],
        "first_author": hit["author"][0]["name"],
        "journal": hit["host"]["title"],
        "year": hit["publicationDate"],
        "pdf_url": _pdf_url,
        "txt_url": _txt_url
    }
    return hit_extraction


def istex_json_to_json(istex_json):
    our_json = []
    for hit in istex_json["hits"]:
        try:
            our_hit = istex_hit_extract(hit)
            our_json.append(our_hit)
        except IndexError:
            continue
    return our_json


def istex_url_to_json(istex_url):
    r = requests.get(url=istex_url)
    return istex_json_to_json(r.json())


def istex_params_to_json(istex_params):
    mandatory_keys = ["q", "facet", "size", "output", "stats"]
    for k in mandatory_keys:
        if k not in istex_params:
            raise IstexParamError("HEY ! Should set all keys")
    r = requests.get(url=ISTEX_BASE_URL, params=istex_params)
    return istex_json_to_json(r.json())


def get_file_from_id(istex_id, doc_type=IstexDoctype.PDF):
    from requests import RequestException
    istex_url = istex_id_to_url(istex_id, doc_type)
    filename = f"{istex_id}.{doc_type}"
    try:
        with requests.get(istex_url) as r:
            return r.content, filename
    except RequestException as e:
        raise e
