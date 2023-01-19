import os

from grobid_client.grobid_client import  GrobidClient
client = GrobidClient(config_path="./grobid-client-config.json")

def GROBID_generation(pdf_path):
    client.process("processFulltextDocument", input_path=pdf_path, output=pdf_path,   n=20)
