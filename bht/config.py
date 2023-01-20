import os
import sys

import yaml

__all__ = [
    "settings",
    "BHT_ROOT",
]

BHT_ROOT = os.path.dirname(os.path.dirname(__file__))

config_file = os.path.join(BHT_ROOT, "bht-config.yml")
if not os.path.isfile(config_file):
    print(f"Please set {config_file} config file.")
    sys.exit()
with open(config_file) as f:
    settings = yaml.safe_load(f)

if not os.path.isabs(settings["BHT_DATA_DIR"]):
    settings["BHT_DATA_DIR"] = os.path.join(BHT_ROOT, settings["BHT_DATA_DIR"])
settings["BHT_PAPERS_DIR"] = os.path.join(settings["BHT_DATA_DIR"], 'Papers')
settings["BHT_SATSCAT_DIR"] = os.path.join(settings["BHT_DATA_DIR"], 'SATS_catalogues')
settings["BHT_WORKSHEET_DIR"] = os.path.join(settings["BHT_DATA_DIR"], 'Worksheet')
