# TODO: REFACTOR maybe this whole file should move to bht. module
from enum import StrEnum, auto
import re

import requests
from requests import RequestException

from web.errors import IstexParamError

ISTEX_BASE_URL = "https://api.istex.fr/"


# TODO: REFACTOR choose between IstexDocType or  web.models.BhtFileType
class IstexDoctype(StrEnum):
    PDF = auto()
    ZIP = auto()
    TXT = auto()
    TEI = auto()
    CLEANED = auto()


def json_to_hits(istex_json):
    """
    Translate an istex request json response
    into a list of hits as dict

    @param istex_json:
    @return: list of dicts
    """
    our_json = []
    for hit in istex_json["hits"]:
        try:
            our_hit = hit_extract(hit)
            our_json.append(our_hit)
        except IndexError:
            continue
    return our_json


def ark_to_id(ark):
    """
    When given an ark, request istex api and grab documents' id
    @param ark:  ark identifier
    @return:  istex_id
    """
    ark_url = f"{ISTEX_BASE_URL}{ark}"
    r = requests.get(url=ark_url)
    document_json = r.json()
    return document_json["idIstex"]


def ark_to_istex_url(ark_istex):
    """ "
    From an ark_istex, build the request url so we can call it and get the papers' json
    """
    req_url = f'{ISTEX_BASE_URL}document/?q=(arkIstex:"{ark_istex}")&facet=corpusName[*]&size=10&output=*&stats'
    return req_url


def get_file_from_id(istex_id, doc_type=IstexDoctype.PDF):
    """
    Get file content from istex by id and doctype

    @param istex_id:  istex id
    @param doc_type: doc type (PDF, TXT, TEI ,....)
    @return: (file_stream, file_name, doi, ark)
    """
    istex_struct = get_doc_url(istex_id, doc_type)
    content, filename = get_file_from_url(istex_struct["url"])
    filename = f"{istex_id}.{doc_type}"
    return content, filename, istex_struct


def get_file_from_url(url):
    """
    Download a file from a given url

    @param url:  the file url
    @return: (file_stream, file_name)
    """
    try:
        with requests.get(url) as r:
            content = r.content
            if "Content-Disposition" in r.headers.keys():
                filename = re.findall(
                    "filename=(.+)", r.headers["Content-Disposition"]
                )[0]
            else:
                filename = url.split("/")[-1]
    except RequestException as e:
        raise e
    filename = re.sub(r"[^a-zA-Z0-9-.]", "_", filename)
    return content, filename


def get_doc_url(istex_id, doc_type=IstexDoctype.PDF):
    """
    Build url to request file from Istex for pdf, txt, or any supported doctype.

    @param doc_type: the type of document to fetch
    @param istex_id:  the istex document id.
    @return: a dict struct with http url, and other doc attributes
    """
    doc_url = f"{ISTEX_BASE_URL}document/{istex_id}"
    r = requests.get(url=doc_url)
    document_json = r.json()
    # Default url value
    _url = None
    # Iterate all fulltext elements till we found what we want
    # TODO: see something similar in hit_extract
    for _elmnt in document_json["fulltext"]:
        if _elmnt["extension"] == doc_type.value:
            _url = _elmnt["uri"]
            break
    _res_dict = {
        "url": _url,
        "istex_id": document_json["id"],
        "doi": document_json["doi"][0],
        "ark": document_json["ark"][0],
        "title": document_json["title"],
        "pub_date": document_json["publicationDate"],
    }
    return _res_dict


def hit_extract(hit):
    """
    From an istex search response's hit, extract info to dict

    @param hit:  the istex hit
    @return:  bht dict
    """
    # build dictionnary with all docs urls
    _doc_urls = {}
    # TODO: see something similar in get_doc_url
    for fulltext in hit["fulltext"]:
        for _doc_type in IstexDoctype:
            if fulltext["extension"] == _doc_type:
                _doc_urls[_doc_type] = fulltext["uri"]
    hit_extraction = {
        "small_title": hit["title"][0:61] + " ...",
        "title": hit["title"],
        "id": hit["id"],
        "ark": hit["arkIstex"],
        "abstract": hit["abstract"],
        "first_author": hit["author"][0]["name"],
        "journal": hit["host"]["title"],
        "year": hit["publicationDate"],
        "doc_urls": _doc_urls,
    }
    return hit_extraction
