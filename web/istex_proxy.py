import requests

from web.errors import IstexParamError

ISTEX_BASE_URL = "https://api.istex.fr/document/"


def istex_id_to_url(istex_id):
    req_url = ISTEX_BASE_URL + istex_id
    from pprint import pprint

    pprint(req_url)
    r = requests.get(url=req_url)
    document_json = r.json()
    pprint(document_json)
    pdf_url = document_json["fulltext"][0]["uri"]
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
