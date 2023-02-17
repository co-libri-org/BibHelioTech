import requests

from web.errors import IstexParamError

ISTEX_BASE_URL = "https://api.istex.fr/document/"


def istex_request_to_json(r):
    istex_response = r.json()
    our_response = []
    for hit in istex_response["hits"]:
        our_hit = {
            "small_title": hit["title"][0:61] + " ...",
            "title": hit["title"],
            "abstract": hit["abstract"],
            "first_author": hit["author"][0]["name"],
            "journal": hit["host"]["title"],
            "year": hit["publicationDate"],
            "pdf_url": hit["fulltext"][0]["uri"],
        }
        our_response.append(our_hit)
    return our_response


def istex_url_to_json(istex_url):
    r = requests.get(url=istex_url)
    return istex_request_to_json(r)


def istex_params_to_json(istex_params):
    mandatory_keys = ["q", "facet", "size", "output", "stats"]
    for k in mandatory_keys:
        if k not in istex_params:
            raise IstexParamError("HEY ! Should set all keys")
    r = requests.get(url=ISTEX_BASE_URL, params=istex_params)
    return istex_request_to_json(r)
