import os
import sys
import re
import json
from bs4 import BeautifulSoup
import lxml

v = sys.version
token = 'IXMbiJNANWTlkMSb4ea7Y5qJIGCFqki6IJPZjc1m' # API Key

def check_main_doi_exist(content):
    content = re.sub(".*<encodingDesc>\n[\s\S]+", "", content) # delete everything after <encodingDesc> markup in the xml file
    soup_2 = BeautifulSoup(content, features="xml")
    doi = soup_2.find("idno", {"type": "DOI"}) # recover DOI in the <idno> markup
    try:
        return doi.string # return DOI, if empty variable, error ...
    except:
        return 1 # ... so DOI doesn't exist in the xml file

def DOI_search_on_xml(content):
    # search and return DOI on the GROBID xml file.

    content = re.sub(".*<encodingDesc>\n[\s\S]+","",content) # delete everything after <encodingDesc> markup in the xml file
    soup = BeautifulSoup(content, features="xml")
    doi = soup.find("idno", {"type" : "DOI"}) # recover DOI in the <idno> markup

    return doi.string

def DOI_search_on_web(content):
    # request DOI with the title of the article to the NASA ADS API
    soup = BeautifulSoup(content,features="xml")

    title = soup.find("title", {"level" : "a"}, {"type" : "main"}).text # recover title in the <title type="main"> markup
    title = re.sub("\:.*","",title).lower()

    # encode the title to URL encode, exemple: "kinetic+study+of+the+mirror+mode"
    if int(v[0]) == 2:
        import urllib
        query = "title:"+title
        encoded_query = urllib.quote_plus(query)
    else:
        from urllib.parse import urlencode, quote_plus
        query = {"title": title}
        encoded_query = urlencode(query, quote_via=quote_plus)
    title = encoded_query.replace("title=","")

    # call ADS API with curl
    json_dict = os.popen("curl --silent -H 'Authorization: Bearer:" + token + "' 'https://api.adsabs.harvard.edu/v1/search/query?q=" + title + "&fl=title,doi'| python -m json.tool").read()
    json_object = json.loads(json_dict)
    if json_object['response']['numFound'] != 0:
        return json_object['response']['docs'][0]['doi'][0] # return the doi of the first result (already sorted by title similarity by ads)
    else:
        return 1

def find_DOI(file_path):
    file = open(file_path, 'r')
    content = file.read()
    if check_main_doi_exist(content) != 1: #if doi exist in the xml
        DOI = DOI_search_on_xml(content)
    else: # if doesn't exist, search doi on web with nasa ads api
        DOI = DOI_search_on_web(content)
    file.close()
    if DOI == 1:
        return ""
    else:
        return DOI
