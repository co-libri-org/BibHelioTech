import requests

from web.errors import IstexParamError

ISTEX_BASE_URL = "https://api.istex.fr/document/"


def istex_params_to_json(istex_params):
    mandatory_keys = ["q", "facet", "size", "output", "stats"]
    for k in mandatory_keys:
        if k not in istex_params:
            raise IstexParamError("HEY ! Should set all keys")
    r = requests.get(url=ISTEX_BASE_URL, params=istex_params)
    istex_response = r.json()
    return istex_response
    # assert len(istex_response['hits']) == 150
