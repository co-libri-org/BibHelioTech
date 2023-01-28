import os
import sys

import yaml

__all__ = [
    "yml_settings",
]

yml_settings = {}

BHT_ROOT_DIR = os.path.dirname(__file__)
yml_settings["BHT_ROOT_DIR"] = BHT_ROOT_DIR

config_file = os.path.join(BHT_ROOT_DIR, "bht-config.yml")
if not os.path.isfile(config_file):
    print(f"Please set {config_file} config file.")
    sys.exit()
with open(config_file) as f:
    yml_settings = yaml.safe_load(f)


if not os.path.isabs(yml_settings["BHT_DATA_DIR"]):
    yml_settings["BHT_DATA_DIR"] = os.path.join(BHT_ROOT_DIR, yml_settings["BHT_DATA_DIR"])
if not os.path.isabs(yml_settings["WEB_UPLOAD_DIR"]):
    yml_settings["WEB_UPLOAD_DIR"] = os.path.join(BHT_ROOT_DIR, yml_settings["WEB_UPLOAD_DIR"])
yml_settings["BHT_PAPERS_DIR"] = os.path.join(yml_settings["BHT_DATA_DIR"], 'Papers')
yml_settings["BHT_SATSCAT_DIR"] = os.path.join(yml_settings["BHT_DATA_DIR"], 'SATS_catalogues')
yml_settings["BHT_WORKSHEET_DIR"] = os.path.join(yml_settings["BHT_DATA_DIR"], 'Worksheet')
yml_settings["BHT_RESSOURCES_DIR"] = os.path.join(BHT_ROOT_DIR, 'ressources')
