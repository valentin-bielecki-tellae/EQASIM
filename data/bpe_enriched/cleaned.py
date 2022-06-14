import pandas as pd
import numpy as np

import shapely.geometry as geo
import data.spatial.utils as spatial_utils

"""
This stage cleans the enterprise census:
  - Filter out enterprises that do not have a valid municipality or IRIS
  - Assign coordinates randomly to enterprises that do not have coordinates
  - Simplify activity types for all enterprises
"""

def configure(context):
    context.stage("data.bpe.raw")

    context.stage("data.spatial.iris")
    context.stage("data.spatial.municipalities")

    context.config("bpe_random_seed", 0)

ACTIVITY_TYPE_MAP = [
    ("A", "other"),         # Police, post office, etc ...
    ("A504", "leisure"),    # Restaurant
    ("B", "shop"),          # Shopping
    ("C", "study"),         # Education
    ("C1", "education"),    # Education
    ("D", "other"),         # Health
    ("E", "other"),         # Transport
    ("F", "leisure"),       # Sports
    ("F3", "culture"),      # & Culture
    ("G", "other"),         # Tourism, hotels, etc. (Hôtel = G102)
]

def find_outside(context, commune_id):
    df_municipalities = context.data("df_municipalities")
    df = context.data("df")

    df = df[df["commune_id"] == commune_id]
    zone = df_municipalities[df_municipalities["commune_id"] == commune_id]["geometry"].values[0]

    indices = [
        index for index, x, y in df[["x", "y"]].itertuples()
        if not zone.contains(geo.Point(x, y))
    ]

    context.progress.update()
    return indices

def execute(context):
    df, df_so = context.stage("data.bpe.raw")

    # Collect information on cultural and education activities in Rennes Métropole
    df_so = df_so[(df_so['nom_theme_principal'] == "Culture/Socioculturel") | df_so['nom_activite_principale'].isin(['Secondaire', 'Supérieur'])].copy()
    df_so['enterprise_id'] = np.arange(len(df), len(df) + len(df_so))
    df_so.rename(columns={"code_insee": "commune_id", "X": "x", "Y": "y"}, inplace=True)
    df_so['activity_type'] = "education"
    df_so.loc[df_so["nom_theme_principal"] == "Culture/Socioculturel", "activity_type"] = "leisure"

    df_so["activity_type"] = df_so["activity_type"].astype("category")
    df_so['imputed'] = "False"

    # I used QGIS to filter and convert to Lambert 93
    df_so["x"] = df_so["x"].astype(np.float)
    df_so["y"] = df_so["y"].astype(np.float)
    df_so = df_so.round(3)

    # Clean IDs
    df["enterprise_id"] = np.arange(len(df))

    # Clean activity type
    df["activity_type"] = "other"
    for prefix, activity_type in ACTIVITY_TYPE_MAP:
        df.loc[df["TYPEQU"].str.startswith(prefix), "activity_type"] = activity_type

    df["activity_type"] = df["activity_type"].astype("category")

    # Clean coordinates
    df["x"] = df["LAMBERT_X"].astype(np.float)
    df["y"] = df["LAMBERT_Y"].astype(np.float)

    # Clean IRIS and commune
    df["iris_id"] = df["DCIRIS"].str.replace("_", "")
    df.loc[df["DEPCOM"] == df["DCIRIS"], "iris_id"] = "undefined"
    df.loc[df["DCIRIS"].str.endswith("0000"), "iris_id"] = "undefined"

    df["iris_id"] = df["iris_id"].astype("category")
    df["commune_id"] = df["DEPCOM"].astype("category")

    print("Found %d/%d (%.2f%%) observations without IRIS" % (
        (df["iris_id"] == "undefined").sum(), len(df), 100 * (df["iris_id"] == "undefined").mean()
    ))

    # Check whether all communes in BPE are within our set of requested data
    df_municipalities = context.stage("data.spatial.municipalities")
    excess_communes = set(df["commune_id"].unique()) - set(df_municipalities["commune_id"].unique())

    if len(excess_communes) > 0:
        raise RuntimeError("Found additional communes: %s" % excess_communes)

    # We notice that we have some additional IRIS. Make sure they will be placed randomly in their commune later.
    df_iris = context.stage("data.spatial.iris")
    excess_iris = set(df[df["iris_id"] != "undefined"]["iris_id"].unique()) - set(df_iris["iris_id"].unique())
    df.loc[df["iris_id"].isin(excess_iris), "iris_id"] = "undefined"
    print("Excess IRIS without valid code:", excess_iris)

    # Impute missing coordinates for known IRIS
    random = np.random.RandomState(context.config("bpe_random_seed"))

    f_undefined = df["iris_id"] == "undefined"
    f_missing = df["x"].isna()

    print("Found %d/%d (%.2f%%) observations without coordinate" % (
        ((f_missing & ~f_undefined).sum(), len(df), 100 * (f_missing & ~f_undefined).mean()
    )))

    df.update(spatial_utils.sample_from_zones(
        context, df_iris, df[f_missing & ~f_undefined], "iris_id", random, label = "Imputing IRIS coordinates ..."))

    # Impute missing coordinates for unknown IRIS
    df.update(spatial_utils.sample_from_zones(
        context, df_municipalities, df[f_missing & f_undefined], "commune_id", random, label = "Imputing municipality coordinates ..."))
    # Consolidate
    df["imputed"] = f_missing
    assert not df["x"].isna().any()

    # Interestingly, some of the given coordinates are not really inside of the respective municipality. Find them and move them back in.
    outside_indices = []

    with context.progress(label = "Finding outside observations ...", total = len(df["commune_id"].unique())):
        with context.parallel(dict(df = df, df_municipalities = df_municipalities)) as parallel:
            for partial in parallel.imap(find_outside, df["commune_id"].unique()):
                outside_indices += partial

    if len(outside_indices) > 0:
        df.loc[outside_indices, "x"] = np.nan
        df.loc[outside_indices, "y"] = np.nan

        df.update(spatial_utils.sample_from_zones(
            context, df_municipalities, df.loc[outside_indices], "commune_id", random, label = "Fixing outside locations ..."))

        df.loc[outside_indices, "imputed"] = True

    Rennes_Métropole = [35001, 35022, 35024, 35032, 35039, 35047, 35051, 35055, 35058, 35059, 35065, 35066, 35076, 35079, 35080, 35081, 35088, 35120, 35131, 35139, 35144, 35180, 35189, 35196, 35204, 35206, 35208, 35210, 35216, 35238, 35240, 35245, 35250, 35266, 35275, 35278, 35281, 35315, 35334, 35351, 35352, 35353, 35363]
    Rennes_Métropole = [str(x) for x in Rennes_Métropole]

    # Package up data set
    print('ALL BPE', len(df))
    df = df[["enterprise_id", "activity_type", "commune_id", "imputed", "x", "y"]]
    df_so = df_so[["enterprise_id", "activity_type", "commune_id", "imputed", "x", "y"]]

    # Replace cultural and education activities locations inside Rennes Métropole
    df_out = df[~df['commune_id'].isin(Rennes_Métropole)]
    print('BPE OUTSIDE RM', len(df_out))
    df_in = df[df['commune_id'].isin(Rennes_Métropole)]
    print('BPE INSIDE RM', len(df_in))
    df_in = df_in[~df_in['activity_type'].isin(['study', 'culture'])]
    print('BPE INSIDE RM OTHER THAN STUDY OR CULTURE', len(df_in))
    df_in = pd.concat([df_in, df_so])
    print('NEW BPE INSIDE RM', len(df_in))
    df = pd.concat([df_in, df_out])
    df.replace({'culture': 'leisure', 'study': 'education'}, inplace=True)

    # df = df[df['commune_id'].isin(Rennes_Métropole)]
    # print(df)

    df = spatial_utils.to_gpd(context, df.copy())
    # df.to_csv('cleaned_bpe.csv')
    # print(df['activity_type'].unique())

    return df
