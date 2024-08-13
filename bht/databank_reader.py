import os
from enum import StrEnum

import numpy as np

import pandas as pd

from bht_config import yml_settings


class DataBankSheet(StrEnum):
    SATS = "satellites"
    SATS_REG = "satellites_regions"
    INSTR = "instruments"
    REG_GEN = "regions_general"
    REG_TREE = "regions_tree"
    PROCESSES = "processes"
    TIME_SPAN = "time_span"


class DataBank:
    dataframes = {}

    def __init__(self):
        self._databank_path = os.path.join(
            yml_settings["BHT_WORKSHEET_DIR"], "Entities_DataBank.xls"
        )
        sheets = [s for s in DataBankSheet]
        self.dataframes = pd.read_excel(self._databank_path, sheet_name=sheets)
        for sheet in sheets:
            _df = self.dataframes[sheet]
            _df = _df.map(lambda x: x.strip() if isinstance(x, str) else x)
            self.dataframes[sheet] = _df

    @property
    def databank_path(self):
        return self._databank_path

    def get_sheet_as_df(self, dbk_sheet: DataBankSheet):
        df_sheet = None
        try:
            df_sheet = self.dataframes[dbk_sheet]
        except KeyError:
            pass
        return df_sheet

    def show_df(self, sheet="satellites"):
        print(self.dataframes[sheet].head())

    def satellites_intersect(self, sheet="satellites_regions"):
        satellites = self.dataframes["satellites"]
        to_intersect = self.dataframes[sheet]
        sat_names = satellites["NAME"]
        amda_names = to_intersect["NAME"]
        # amda_mask = amda_names.isin(sat_names)
        # amda_notfound = amda_names[~amda_mask]
        amda_not_in_sats = []
        amda_syns = {}
        for a in amda_names:
            r = locate_row_in_df(satellites, a)
            if r is None:
                amda_not_in_sats.append(a)
                continue
            syn = satellites.iloc[r, 0]
            if syn != a:
                amda_syns[a] = syn
        print(f"\n{sheet} Not in Sats  {len(amda_not_in_sats)}")
        for a in amda_not_in_sats:
            print(f"{a:20} not in sats")
        print(f"\n{sheet} has syn: {len(amda_syns)}")
        for a, s in amda_syns.items():
            print(f"{a:20} -> {s}")


def locate_row_in_df(df, value):
    a = df.to_numpy()
    try:
        row = np.where(a == value)[0][0]
        # col = np.where(a == value)[1][0]
        row = int(row)
    except IndexError:
        row = None
    return row


if __name__ == "__main__":
    from datetime import datetime

    before_date = datetime.now()
    databank = DataBank()
    print(databank.databank_path)
    after_date = datetime.now()
    # databank.show_df()
    databank.satellites_intersect("time_span")
    # databank.rename_from_satellites("time_span")
    print(f"Loaded in {after_date - before_date}")
