import os
from bht.errors import *

from grobid_client.grobid_client import  GrobidClient
BHT_ROOT = os.path.dirname(os.path.dirname(__file__))
client = GrobidClient(config_path=os.path.join(BHT_ROOT, "grobid-client-config.json"))

def GROBID_generation(pdf_path):
    if not os.path.isdir(pdf_path):
        raise BhtPathError(f"{pdf_path} is not a directory")
    client.process("processFulltextDocument", input_path=pdf_path, output=pdf_path,   n=20)
