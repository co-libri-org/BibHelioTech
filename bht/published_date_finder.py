import re
import requests

# from bht.DOI_finder import *


def published_date_finder(token, v, doi):
    # encode the title to URL encode, exemple: "kinetic+study+of+the+mirror+mode"
    if int(v[0]) == 2:
        import urllib

        query = "doi:" + doi
        encoded_query = urllib.quote_plus(query)
    else:
        from urllib.parse import urlencode, quote_plus

        query = {"doi": doi}
        encoded_query = urlencode(query, quote_via=quote_plus)
    doi = encoded_query.replace("doi=", "")

    requests.packages.urllib3.disable_warnings()
    url = "https://api.adsabs.harvard.edu/v1/search/query?q=" + doi + "&fl=date"
    r = requests.get(url, headers={"Authorization": "Bearer " + token}, verify=False)
    json_object = r.json()
    # json_object = json.loads(json_dict)
    # print(type(json_object))
    # sys.exit()
    if json_object["responseHeader"]["status"] == 0:
        publish_date = json_object["response"]["docs"][0]["date"]
        if re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))", publish_date):
            return publish_date
        else:
            return None
    else:
        return None
