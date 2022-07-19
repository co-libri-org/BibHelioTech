import os
import sys
import re
import json
from DOI_finder import *

main_path = "./DATA/Papers"

def published_date_finder(token,v,DOI):
    # encode the title to URL encode, exemple: "kinetic+study+of+the+mirror+mode"
    if int(v[0]) == 2:
        import urllib

        query = "doi:" + DOI
        encoded_query = urllib.quote_plus(query)
    else:
        from urllib.parse import urlencode, quote_plus

        query = {"doi": DOI}
        encoded_query = urlencode(query, quote_via=quote_plus)
    doi = encoded_query.replace("doi=", "")

    # call ADS API with curl
    json_dict = os.popen("curl --silent -H 'Authorization: Bearer:" + token + "' 'https://api.adsabs.harvard.edu/v1/search/query?q=" + doi + "&fl=date'| python -m json.tool").read()
    json_object = json.loads(json_dict)
    if json_object['responseHeader']['status'] == 0:
        publish_date = json_object['response']['docs'][0]['date']
        if re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",publish_date):
            return publish_date
        else:
            return None
    else:
        return None