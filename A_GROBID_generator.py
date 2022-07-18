import os

def GROBID_generation(pdf_paths):
    os.popen("grobid_client --config ../../grobid_client_python/config.json --input"+" \""+pdf_paths+"\" "+"--output"" \""+pdf_paths+"\" "+"processFulltextDocument").read() # GROBID call
