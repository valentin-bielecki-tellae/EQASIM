import os
import pandas as pd

from .format import HOUSEHOLD_FORMAT, PERSON_FORMAT, TRIP_FORMAT
"""
This stage loads the raw data of the specified HTS (EMC² Vendée).

Adapted from the first implementation by Valentin Le Besond (IFSTTAR Nantes)
"""

def configure(context):
    context.config("data_path")


HOUSEHOLD_COLUMNS = {
    "MP2": str, "ECH": str, "COEM": float,
    "M14": int, "M20": int, "M5": int
}

PERSON_COLUMNS = {
    "ECH": str,  "PER": int, "PP2": str, "PENQ": int,
    "P3": int, "P2": int, "P4": int,
    "P7": str, "P12": str,
    "P9": str, "P5": str,
    "COEP": float, "COEQ": float,
}

TRIP_COLUMNS = {
    "ECH": str, "PER": int, "NDEP": int, "DP2": str,
    "D2A": int, "D5A": int, "D3": str, "D4": int,
    "D7": str, "D8": int, 
    "D8C": int, "MODP": int, "DOIB": int, "DIST": int
}

def execute(context):
    # Load households
    df_household_dictionary = pd.DataFrame.from_records(
        HOUSEHOLD_FORMAT, columns = ["position", "size", "variable", "description"]
    )

    column_widths = df_household_dictionary["size"].values
    column_names = df_household_dictionary["variable"].values

    df_households = pd.read_fwf(
        "%s/emc_85/03a_EMC2_Vendee_2020_Men_CoefRed_190221.txt"
        % context.config("data_path"), widths = column_widths, header = None,
        names = column_names, usecols = list(HOUSEHOLD_COLUMNS.keys()), dtype = HOUSEHOLD_COLUMNS
    )

    # Load persons
    df_person_dictionary = pd.DataFrame.from_records(
        PERSON_FORMAT, columns = ["position", "size", "variable", "description"]
    )

    column_widths = df_person_dictionary["size"].values
    column_names = df_person_dictionary["variable"].values

    df_persons = pd.read_fwf(
        "%s/emc_85/03b_EMC2_Vendee_2020_Per_DT_030321.txt"
        % context.config("data_path"), widths = column_widths, header = None,
        names = column_names, usecols = list(PERSON_COLUMNS.keys()), dtype = PERSON_COLUMNS
    )

    # Load trips
    df_trip_dictionary = pd.DataFrame.from_records(
        TRIP_FORMAT, columns = ["position", "size", "variable", "description"]
    )

    column_widths = df_trip_dictionary["size"].values
    column_names = df_trip_dictionary["variable"].values

    df_trips = pd.read_fwf(
        "%s/emc_85/03c_EMC2_Vendee_2020_Dep_Dist_040321.txt"
        % context.config("data_path"), widths = column_widths, header = None,
        names = column_names, usecols = list(TRIP_COLUMNS.keys()), dtype = TRIP_COLUMNS
    )

    return df_households, df_persons, df_trips

FILES = [
    "03c_EMC2_Vendee_2020_Dep_Dist_040321.txt",
    "03a_EMC2_Vendee_2020_Men_CoefRed_190221.txt",
    "03b_EMC2_Vendee_2020_Per_DT_030321.txt",
]

def validate(context):
    for name in FILES:
        if not os.path.exists("%s/emc_85/%s" % (context.config("data_path"), name)):
            raise RuntimeError("File missing from EMC² vendée: %s" % name)

    return [
        os.path.getsize("%s/emc_85/%s" % (context.config("data_path"), name))
        for name in FILES
    ]
