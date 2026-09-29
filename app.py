from flask import Flask, abort, jsonify, render_template, request

from data_engine import (
    get_comparison,
    get_country_profile,
    get_explore,
    get_figure,
    get_meta,
    get_rankings,
)

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


@app.get("/")
def index():
    return render_template("index.html", meta=get_meta())


@app.get("/api/meta")
def api_meta():
    return jsonify(get_meta())


@app.get("/api/explore")
def api_explore():
    return jsonify(get_explore(
        view=request.args.get("view", "overall"),
        metric=request.args.get("metric", "Overall index"),
        pillar=request.args.get("pillar", "Thematic score"),
        region=request.args.get("region", "All regions"),
    ))


@app.get("/api/figure/<figure_name>")
def api_figure(figure_name):
    allowed = {"map", "regional", "pillars", "theme_ladder", "country_profile", "comparison"}
    if figure_name not in allowed:
        abort(404)

    if figure_name == "country_profile":
        return jsonify(get_figure(figure_name, iso3=request.args.get("iso3", "")))

    if figure_name == "comparison":
        try:
            return jsonify(get_figure(
                figure_name,
                mode=request.args.get("mode", "regions"),
                first=request.args.get("first", ""),
                second=request.args.get("second", ""),
            ))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    kwargs = {
        "view": request.args.get("view", "overall"),
        "metric": request.args.get("metric", "Overall index"),
        "pillar": request.args.get("pillar", "Thematic score"),
        "region": request.args.get("region", "All regions"),
    }
    return jsonify(get_figure(figure_name, **kwargs))


@app.get("/api/rankings")
def api_rankings():
    return jsonify(get_rankings(
        region=request.args.get("region", "All regions"),
        sort=request.args.get("sort", "ranking"),
        direction=request.args.get("direction", "asc"),
        iso3=request.args.get("iso3", ""),
    ))


@app.get("/api/comparison")
def api_comparison():
    try:
        return jsonify(get_comparison(
            mode=request.args.get("mode", "regions"),
            first=request.args.get("first", ""),
            second=request.args.get("second", ""),
        ))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/country/<iso3>")
def api_country(iso3):
    profile = get_country_profile(iso3.upper())
    if not profile:
        abort(404)
    return jsonify(profile)


if __name__ == "__main__":
    app.run(debug=True)
