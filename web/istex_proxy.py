from enum import IntEnum, auto

import requests

from web.errors import IstexParamError

ISTEX_BASE_URL = "https://api.istex.fr/document/"


class IstexDoctype(IntEnum):
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
        pdf_url = document_json["fulltext"][0]["uri"]
    elif doc_type == IstexDoctype.ZIP:
        pdf_url = document_json["fulltext"][1]["uri"]
    elif doc_type == IstexDoctype.TXT:
        pdf_url = document_json["fulltext"][2]["uri"]
    elif doc_type == IstexDoctype.TEI:
        pdf_url = document_json["fulltext"][3]["uri"]
    elif doc_type == IstexDoctype.CLEAN:
        pdf_url = document_json["fulltext"][4]["uri"]
    return pdf_url


def istex_json_to_json(istex_json):
    our_json = []
    for hit in istex_json["hits"]:
        our_hit = {
            "small_title": hit["title"][0:61] + " ...",
            "title": hit["title"],
            "id": hit["id"],
            "ark": hit["arkIstex"],
            "abstract": hit["abstract"],
            "first_author": hit["author"][0]["name"],
            "journal": hit["host"]["title"],
            "year": hit["publicationDate"],
            "pdf_url": hit["fulltext"][0]["uri"],
        }
        our_json.append(our_hit)
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
