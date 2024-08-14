import os
import sys

import yaml

__all__ = [
    "yml_settings",
]

BHT_ROOT_DIR = os.path.dirname(__file__)

config_filepath = os.path.join(BHT_ROOT_DIR, "bht-config.yml")
if not os.path.isfile(config_filepath):
    print(f"Please set {config_filepath} config file.")
    sys.exit()
with open(config_filepath) as f:
    yml_settings = yaml.safe_load(f)

yml_settings["BHT_ROOT_DIR"] = BHT_ROOT_DIR
yml_settings["BHT_LOGFILE_PATH"] = os.path.join(BHT_ROOT_DIR, yml_settings["BHT_LOGFILE_NAME"])

with open(os.path.join(BHT_ROOT_DIR, "VERSION.txt")) as version_file:
    yml_settings["VERSION"] = version_file.read().strip()

with open(os.path.join(BHT_ROOT_DIR, "bht", "PIPELINE_VERSION.txt")) as pipeline_version_file:
    yml_settings["BHT_PIPELINE_VERSION"] = pipeline_version_file.read().strip()

if not os.path.isabs(yml_settings["BHT_DATA_DIR"]):
    yml_settings["BHT_DATA_DIR"] = os.path.join(
        BHT_ROOT_DIR, yml_settings["BHT_DATA_DIR"]
    )
yml_settings["BHT_PAPERS_DIR"] = os.path.join(yml_settings["BHT_DATA_DIR"], "Papers")
yml_settings["BHT_RESOURCES_DIR"] = os.path.join(BHT_ROOT_DIR, "resources")
yml_settings["BHT_SATSCAT_DIR"] = os.path.join(
    yml_settings["BHT_RESOURCES_DIR"], "SATS_catalogues"
)
yml_settings["BHT_WORKSHEET_DIR"] = os.path.join(
    yml_settings["BHT_RESOURCES_DIR"], "Worksheet"
)

if not os.path.isabs(yml_settings["WEB_UPLOAD_DIR"]):
    yml_settings["WEB_UPLOAD_DIR"] = os.path.join(
        BHT_ROOT_DIR, yml_settings["WEB_UPLOAD_DIR"]
    )
yml_settings["WEB_DB_DIR"] = os.path.join(yml_settings["BHT_DATA_DIR"], "db")
if not os.path.isdir(yml_settings["WEB_DB_DIR"]):
    os.makedirs(yml_settings["WEB_DB_DIR"])
