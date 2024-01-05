# TODO: REFACTOR maybe this whole file should move to bht. module
from enum import StrEnum, auto
import re

import requests
from requests import RequestException

from web.errors import IstexParamError

ISTEX_BASE_URL = "https://api.istex.fr/document/"


# TODO: REFACTOR choose between IstexDocType or  web.models.BhtFileType
class IstexDoctype(StrEnum):
    PDF = auto()
    ZIP = auto()
    TXT = auto()
    TEI = auto()
    CLEANED = auto()


def istex_get_doc_url(istex_id, doc_type=IstexDoctype.PDF):
    """
    Build url to request Istex for pdf, txt, or any supported doctype.

    @param doc_type: the type of document to fetch
    @param istex_id:  the istex document id.
    @return: a http url returning a pdf file
    """
    doc_url = ISTEX_BASE_URL + istex_id
    print(doc_url)
    r = requests.get(url=doc_url)
    document_json = r.json()
    # Default url value
    _url = None
    # Iterate all fulltext elements till we found what we want
    for _elmnt in document_json["fulltext"]:
        if _elmnt["extension"] == doc_type.value:
            _url = _elmnt["uri"]
            break
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
        "txt_url": _txt_url,
    }
    return hit_extraction


def istex_json_to_json(istex_json):
    """
    Translate an istex request json response
    into a list of hits as dict

    @param istex_json:
    @return: list of dicts
    """
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

    istex_url = istex_get_doc_url(istex_id, doc_type)
    filename = f"{istex_id}.{doc_type}"
    try:
        with requests.get(istex_url) as r:
            return r.content, filename
    except RequestException as e:
        raise e


def get_file_from_url(url):
    # TODO: QUESTION is if possible to check TXT ? with some FileType ?
    # r = requests.get(url)
    # if not r.headers["Content-Type"] == "application/pdf" :
    #     raise PdfFileError("No pdf in url")
    try:
        with requests.get(url) as r:
            if "Content-Disposition" in r.headers.keys():
                filename = re.findall(
                    "filename=(.+)", r.headers["Content-Disposition"]
                )[0]
            else:
                filename = url.split("/")[-1]
    except RequestException as e:
        raise e
    return r.content, filename
