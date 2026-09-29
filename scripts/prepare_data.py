"""Rebuild the compact Polars snapshot from the source GIRAI Excel workbook."""
from pathlib import Path
import polars as pl
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "GIRAI_2024_Edition_Data.xlsx"
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)

obs = pl.read_excel(SOURCE, sheet_name="Data", engine="fastexcel")
rank = pl.read_excel(SOURCE, sheet_name="Rankings and Scores", engine="fastexcel")

obs.select([
    "country","ISO3","GIRAI_region","GIRAI_subregion","UN_region","UN_sub_region",
    "dimension","thematic_area","enforceability_benchmark","ta_score",
    "fr_norm_score","ga_norm_score","nsa_norm_score",
]).filter(pl.col("country").is_not_null()).write_ndjson(OUT / "observations.ndjson")

rank.select([
    pl.col("Ranking").alias("ranking"), pl.col("ISO3").alias("iso3"),
    pl.col("Country").alias("country"), pl.col("GIRAI_region").alias("region"),
    pl.col("UN_region").alias("un_region"), pl.col("UN_subregion").alias("un_subregion"),
    pl.col("Index score").alias("index_score"),
    pl.col("DIMENSION SCORES - Human Rights and AI (0-100)").alias("human_rights_score"),
    pl.col("DIMENSION SCORES - Responsible AI Governance (0-100)").alias("governance_score"),
    pl.col("DIMENSION SCORES - Responsible AI Capacities (0-100)").alias("capacities_score"),
    pl.col("PILLAR SCORES - Government frameworks (0-100)").alias("frameworks_score"),
    pl.col("PILLAR SCORES - Government actions (0-100)").alias("actions_score"),
    pl.col("PILLAR SCORES - Non-state actors (0-100)").alias("nonstate_score"),
]).filter(pl.col("iso3").is_not_null()).write_ndjson(OUT / "rankings.ndjson")

print("Snapshot rebuilt in", OUT)
