import glob
import os
from bht.errors import *

from grobid_client.grobid_client import GrobidClient

BHT_ROOT = os.path.dirname(os.path.dirname(__file__))
client = GrobidClient(config_path=os.path.join(BHT_ROOT, "grobid-client-config.json"))


def GROBID_generation(pdf_path):
    if not os.path.isdir(pdf_path):
        raise BhtPathError(f"{pdf_path} is not a directory")
    client.process("processFulltextDocument", input_path=pdf_path, output=pdf_path, n=20)
    tei_xml_files = glob.glob("*.tei.xml", root_dir=pdf_path)
    if len(tei_xml_files) == 0:
        raise BhtResultError(f"No tei fles found in {pdf_path}")
#