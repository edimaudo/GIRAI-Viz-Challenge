from __future__ import annotations

import json
import math
from pathlib import Path

import plotly.graph_objects as go
import polars as pl
#import numpy

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OBS_PATH = DATA_DIR / "observations.ndjson"
RANK_PATH = DATA_DIR / "rankings.ndjson"
META_PATH = DATA_DIR / "metadata.json"

OBS = pl.read_ndjson(OBS_PATH).with_columns([
    pl.col("ta_score").cast(pl.Float64, strict=False),
    pl.col("fr_norm_score").cast(pl.Float64, strict=False),
    pl.col("ga_norm_score").cast(pl.Float64, strict=False),
    pl.col("nsa_norm_score").cast(pl.Float64, strict=False),
])
RANK = pl.read_ndjson(RANK_PATH).with_columns([
    pl.col("index_score").cast(pl.Float64, strict=False),
    pl.col("human_rights_score").cast(pl.Float64, strict=False),
    pl.col("governance_score").cast(pl.Float64, strict=False),
    pl.col("capacities_score").cast(pl.Float64, strict=False),
    pl.col("frameworks_score").cast(pl.Float64, strict=False),
    pl.col("actions_score").cast(pl.Float64, strict=False),
    pl.col("nonstate_score").cast(pl.Float64, strict=False),
])

with META_PATH.open(encoding="utf-8") as _f:
    META = json.load(_f)

DIM_COLS = {
    "Human Rights and AI": "human_rights_score",
    "Responsible AI Governance": "governance_score",
    "Responsible AI Capacities": "capacities_score",
}
PILLAR_COLS = {
    "Government frameworks": "frameworks_score",
    "Government actions": "actions_score",
    "Non-state actors": "nonstate_score",
}
THEME_PILLAR_COLS = {
    "Thematic score": "ta_score",
    "Government frameworks": "fr_norm_score",
    "Government actions": "ga_norm_score",
    "Non-state actors": "nsa_norm_score",
}

BG = "rgba(0,0,0,0)"
BLUE = "#175A7A"
BLUE_DARK = "#0E405A"
BLUE_MID = "#4A88A9"
BLUE_LIGHT = "#A9C9DA"
BLUE_PALE = "#DCEBF2"
INK = "#171717"
MUTED = "#65615D"
GRID = "#C7D1D7"
CREAM = "#F3F5F6"
LAND = "#D8DEE2"
CHORO = [
    [0.00, "#EEF4F7"],
    [0.20, "#D7E7EF"],
    [0.40, "#B3CFDE"],
    [0.60, "#7FA9BF"],
    [0.80, "#4C829F"],
    [1.00, "#154E70"],
]
REGION_ORDER = META["regions"]
COMPARISON_METRICS = [
    ("Overall index", "index_score"),
    ("Human rights", "human_rights_score"),
    ("Governance", "governance_score"),
    ("Capacities", "capacities_score"),
    ("Government frameworks", "frameworks_score"),
    ("Government actions", "actions_score"),
    ("Non-state actors", "nonstate_score"),
]


def _clean(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _records(df: pl.DataFrame):
    return [{k: _clean(v) for k, v in row.items()} for row in df.to_dicts()]


def get_meta():
    return {
        **META,
        "pillar_options": list(PILLAR_COLS.keys()),
        "theme_pillar_options": list(THEME_PILLAR_COLS.keys()),
        "comparison_metrics": [x[0] for x in COMPARISON_METRICS],
        "country_options": _records(RANK.select(["iso3", "country", "region"]).sort("country")),
    }


def _base_map(view: str, metric: str, pillar: str, region: str) -> pl.DataFrame:
    if region != "All regions":
        R = RANK.filter(pl.col("region") == region)
    else:
        R = RANK

    if view == "overall":
        return R.select(["iso3", "country", "region", pl.col("index_score").alias("score")])

    if view == "dimension":
        metric = metric if metric in DIM_COLS else "Human Rights and AI"
        col = DIM_COLS[metric]
        return R.select(["iso3", "country", "region", pl.col(col).alias("score")])

    if view == "thematic":
        metric = metric if metric in META["themes"] else META["themes"][0]
        pillar = pillar if pillar in THEME_PILLAR_COLS else "Thematic score"
        col = THEME_PILLAR_COLS[pillar]
        O = OBS.filter(pl.col("thematic_area") == metric)
        if region != "All regions":
            O = O.filter(pl.col("GIRAI_region") == region)
        return (
            O.group_by(["ISO3", "country", "GIRAI_region"])
            .agg(pl.col(col).median().alias("score"))
            .rename({"ISO3": "iso3", "GIRAI_region": "region"})
        )

    raise ValueError(f"Unknown view: {view}")


def _regional_summary(df: pl.DataFrame, selected_region: str = "All regions"):
    if df.is_empty():
        return []
    out = (
        df.group_by("region")
        .agg([
            pl.col("score").median().round(1).alias("median_score"),
            pl.len().alias("countries"),
        ])
        .sort("median_score", descending=True)
        .with_columns((pl.col("region") == selected_region).alias("selected"))
    )
    return _records(out)


def _pillar_summary(df: pl.DataFrame):
    if df.is_empty():
        return []
    values = {
        label: df.select(pl.col(col).median().round(1)).item()
        for label, col in PILLAR_COLS.items()
    }
    return [{"pillar": key, "score": _clean(value)} for key, value in values.items()]


def _theme_pillars(theme: str, region: str = "All regions"):
    O = OBS.filter(pl.col("thematic_area") == theme)
    if region != "All regions":
        O = O.filter(pl.col("GIRAI_region") == region)
    if O.is_empty():
        return []
    values = {
        "Government frameworks": O.select(pl.col("fr_norm_score").median().round(1)).item(),
        "Government actions": O.select(pl.col("ga_norm_score").median().round(1)).item(),
        "Non-state actors": O.select(pl.col("nsa_norm_score").median().round(1)).item(),
    }
    return [{"pillar": key, "score": _clean(value)} for key, value in values.items()]


def _dimension_theme_ladder(dimension: str, region: str = "All regions"):
    O = OBS.filter(pl.col("dimension") == dimension)
    if region != "All regions":
        O = O.filter(pl.col("GIRAI_region") == region)
    if O.is_empty():
        return []
    out = (
        O.group_by("thematic_area")
        .agg([
            pl.col("ta_score").median().round(1).alias("median_score"),
            pl.len().alias("observations"),
        ])
        .sort("median_score", descending=False)
    )
    return _records(out)


def _headline(view: str, metric: str, pillar: str, df: pl.DataFrame, regions):
    median = df.select(pl.col("score").median().round(1)).item() if not df.is_empty() else None
    n = df.height
    if view == "overall":
        title = f"The median overall index score is {median:.1f} out of 100." if median is not None else "Overall index"
        sub = f"The supplied 2024 dataset contains {n} country-level scores in this view."
    elif view == "dimension":
        title = f"{metric} has a median score of {median:.1f} out of 100." if median is not None else metric
        sub = "Use the three dimensions to examine where responsible AI conditions converge or diverge."
    else:
        title = f"{metric} has a median score of {median:.1f} out of 100." if median is not None else metric
        sub = f"Showing {pillar.lower()} for this thematic area across {n} countries."

    if regions:
        high = max(regions, key=lambda x: x["median_score"])
        low = min(regions, key=lambda x: x["median_score"])
        if df.height and any(r.get("selected") for r in regions):
            chosen = next(r for r in regions if r.get("selected"))
            regional = f"{chosen['region']} median: {chosen['median_score']:.1f} across {chosen['countries']} countries."
        else:
            regional = f"Regional median: {high['region']} {high['median_score']:.1f} vs {low['region']} {low['median_score']:.1f}."
    else:
        regional = "No regional observations match the current filter."
    return {"title": title, "sub": sub, "regional": regional, "median": median, "countries": n}


def get_explore(view="overall", metric="Overall index", pillar="Thematic score", region="All regions"):
    if view == "thematic" and metric not in META["themes"]:
        metric = META["themes"][0]
    if region not in ["All regions", *META["regions"]]:
        region = "All regions"
    df = _base_map(view, metric, pillar, region)
    context_df = _base_map(view, metric, pillar, "All regions")
    regions = _regional_summary(context_df, region)
    dimension_for_ladder = META["theme_dimension"].get(metric, "Human Rights and AI")
    ladder = _dimension_theme_ladder(dimension_for_ladder, region)
    return {
        "metric": metric,
        "view": view,
        "pillar": pillar,
        "region": region,
        "map": _records(df.sort("country")),
        "regional": regions,
        "headline": _headline(view, metric, pillar, df, regions),
        "global_pillars": _pillar_summary(RANK.filter(pl.col("region") == region) if region != "All regions" else RANK),
        "theme_pillars": _theme_pillars(metric, region) if view == "thematic" else [],
        "theme_ladder": ladder,
    }


def get_rankings(region="All regions", sort="ranking", direction="asc"):
    df = RANK
    if region != "All regions":
        df = df.filter(pl.col("region") == region)
    allowed = {
        "ranking", "country", "region", "index_score", "human_rights_score",
        "governance_score", "capacities_score"
    }
    sort_col = sort if sort in allowed else "ranking"
    desc = direction.lower() == "desc"
    df = df.sort(sort_col, descending=desc, nulls_last=True)
    return _records(df)


def get_country_profile(iso3: str):
    row = RANK.filter(pl.col("iso3") == iso3).to_dicts()
    if not row:
        return None
    r = row[0]
    themes = (
        OBS.filter(pl.col("ISO3") == iso3)
        .select(["dimension", "thematic_area", "ta_score", "fr_norm_score", "ga_norm_score", "nsa_norm_score"])
        .sort("ta_score", descending=True)
    )
    return {"summary": {k: _clean(v) for k, v in r.items()}, "themes": _records(themes)}


def _comparison_row(source, label, values_a, values_b):
    return {"metric": label, "a": _clean(values_a), "b": _clean(values_b)}


def get_comparison(mode: str, first: str, second: str):
    mode = mode if mode in {"regions", "countries"} else "regions"
    if mode == "regions":
        if first not in REGION_ORDER or second not in REGION_ORDER or first == second:
            raise ValueError("Choose two different regions.")
        A = RANK.filter(pl.col("region") == first)
        B = RANK.filter(pl.col("region") == second)
        name_a, name_b = first, second
    else:
        A = RANK.filter(pl.col("iso3") == first)
        B = RANK.filter(pl.col("iso3") == second)
        if A.is_empty() or B.is_empty() or first == second:
            raise ValueError("Choose two different countries.")
        name_a = A.select("country").item()
        name_b = B.select("country").item()

    rows = []
    for label, col in COMPARISON_METRICS:
        agg = (lambda df: df.select(pl.col(col).median()).item()) if mode == "regions" else (lambda df: df.select(pl.col(col).first()).item())
        rows.append(_comparison_row(mode, label, agg(A), agg(B)))

    return {"mode": mode, "first": first, "second": second, "first_label": name_a, "second_label": name_b, "rows": rows}


def _figure_layout(font_color=INK, paper=BG):
    return {
        "paper_bgcolor": paper,
        "plot_bgcolor": paper,
        "font": {"family": "Arial, Helvetica, sans-serif", "color": font_color, "size": 12},
        "margin": {"l": 26, "r": 24, "t": 26, "b": 36},
        "hoverlabel": {"font": {"family": "Arial, Helvetica, sans-serif"}},
    }


def figure_map(view="overall", metric="Overall index", pillar="Thematic score", region="All regions"):
    df = _base_map(view, metric, pillar, region)
    label = {"overall": "Overall index score", "dimension": metric, "thematic": f"{metric} — {pillar}"}.get(view, metric)
    fig = go.Figure(go.Choropleth(
        locations=df["iso3"].to_list(),
        z=df["score"].to_list(),
        locationmode="ISO-3",
        text=df["country"].to_list(),
        # customdata=df.select(["iso3", "region"]).to_numpy().tolist(),
        customdata=df.select(["iso3", "region"]).rows(),
        colorscale=CHORO,
        zmin=0,
        zmax=100,
        showscale=False,
        marker_line_color="#6B7680",
        marker_line_width=0.35,
        hovertemplate="<b>%{text}</b><br>Score: %{z:.1f}<extra></extra>",
    ))
    fig.update_geos(
        scope="world",
        showcountries=True,
        countrycolor="#6B7680",
        showframe=False,
        showcoastlines=False,
        showland=True,
        landcolor=LAND,
        showocean=True,
        oceancolor=CREAM,
        projection_type="natural earth",
    )
    fig.update_layout(**_figure_layout(), height=510)
    fig.update_layout(title={"text": label, "x": 0.02, "xanchor": "left", "font": {"size": 15}})
    return fig.to_plotly_json()


def figure_regional(view="overall", metric="Overall index", pillar="Thematic score", region="All regions"):
    context = _base_map(view, metric, pillar, "All regions")
    reg = _regional_summary(context, region)
    reg = sorted(reg, key=lambda x: x["median_score"])
    fig = go.Figure(go.Bar(
        x=[r["median_score"] for r in reg],
        y=[r["region"] for r in reg],
        orientation="h",
        marker={"color": [BLUE if r["selected"] else BLUE_LIGHT for r in reg]},
        text=[f"{r['median_score']:.1f}  ·  {r['countries']} countries" for r in reg],
        textposition="outside",
        cliponaxis=False,
        customdata=[[r["selected"]] for r in reg],
        hovertemplate="<b>%{y}</b><br>Median: %{x:.1f}<extra></extra>",
    ))
    fig.update_layout(**_figure_layout(), height=420)
    fig.update_xaxes(range=[0, 105], title="Median score (0–100)", gridcolor=GRID, zeroline=False)
    fig.update_yaxes(title=None, automargin=True)
    return fig.to_plotly_json()


def figure_pillars(view="overall", metric="Overall index", pillar="Thematic score", region="All regions"):
    if view == "thematic":
        data = _theme_pillars(metric, region)
    else:
        R = RANK.filter(pl.col("region") == region) if region != "All regions" else RANK
        data = _pillar_summary(R)
    fig = go.Figure(go.Bar(
        x=[d["score"] for d in data],
        y=[d["pillar"] for d in data],
        orientation="h",
        marker={"color": [BLUE, BLUE_MID, BLUE_LIGHT]},
        text=[f"{d['score']:.1f}" for d in data],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Median: %{x:.1f}<extra></extra>",
    ))
    fig.update_layout(**_figure_layout(), height=310)
    fig.update_xaxes(range=[0, 105], title="Median score (0–100)", gridcolor=GRID, zeroline=False)
    fig.update_yaxes(title=None, automargin=True)
    return fig.to_plotly_json()


def figure_theme_ladder(view="overall", metric="Overall index", pillar="Thematic score", region="All regions"):
    dimension = metric if view == "dimension" else META["theme_dimension"].get(metric, "Human Rights and AI")
    ladder = _dimension_theme_ladder(dimension, region)
    ladder = sorted(ladder, key=lambda x: x["median_score"])
    fig = go.Figure(go.Bar(
        x=[d["median_score"] for d in ladder],
        y=[d["thematic_area"] for d in ladder],
        orientation="h",
        marker={"color": BLUE_PALE, "line": {"color": BLUE_MID, "width": 0.5}},
        text=[f"{d['median_score']:.1f}" for d in ladder],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Median: %{x:.1f}<extra></extra>",
    ))
    fig.update_layout(**_figure_layout(), height=max(360, 22 * len(ladder) + 80))
    fig.update_xaxes(range=[0, 105], title="Median thematic score (0–100)", gridcolor=GRID, zeroline=False)
    fig.update_yaxes(title=None, automargin=True)
    return fig.to_plotly_json()


def figure_country_profile(iso3: str):
    p = get_country_profile(iso3)
    if not p:
        return {"data": [], "layout": _figure_layout()}
    r = p["summary"]
    labels = ["Human rights", "Governance", "Capacities", "Frameworks", "Actions", "Non-state actors"]
    values = [r["human_rights_score"], r["governance_score"], r["capacities_score"], r["frameworks_score"], r["actions_score"], r["nonstate_score"]]
    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker={"color": [BLUE, BLUE, BLUE, BLUE_MID, BLUE_MID, BLUE_LIGHT]},
        text=[f"{v:.1f}" for v in values],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:.1f}<extra></extra>",
    ))
    fig.update_layout(**_figure_layout(), height=340)
    fig.update_xaxes(range=[0, 105], title="Score (0–100)", gridcolor=GRID, zeroline=False)
    fig.update_yaxes(title=None, automargin=True)
    return fig.to_plotly_json()


def figure_comparison(mode: str, first: str, second: str):
    data = get_comparison(mode, first, second)
    rows = data["rows"]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[r["a"] for r in rows],
        y=[r["metric"] for r in rows],
        orientation="h",
        name=data["first_label"],
        marker={"color": BLUE},
        text=[f"{r['a']:.1f}" if r["a"] is not None else "—" for r in rows],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.add_trace(go.Bar(
        x=[r["b"] for r in rows],
        y=[r["metric"] for r in rows],
        orientation="h",
        name=data["second_label"],
        marker={"color": BLUE_LIGHT, "line": {"color": BLUE_MID, "width": 0.5}},
        text=[f"{r['b']:.1f}" if r["b"] is not None else "—" for r in rows],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(**_figure_layout(), height=430, barmode="group", legend={"orientation": "h", "y": 1.06, "x": 0})
    fig.update_xaxes(range=[0, 105], title="Score (0–100)", gridcolor=GRID, zeroline=False)
    fig.update_yaxes(title=None, automargin=True)
    return fig.to_plotly_json()


def get_figure(name: str, **kwargs):
    funcs = {
        "map": figure_map,
        "regional": figure_regional,
        "pillars": figure_pillars,
        "theme_ladder": figure_theme_ladder,
        "country_profile": figure_country_profile,
        "comparison": figure_comparison,
    }
    return funcs[name](**kwargs)
