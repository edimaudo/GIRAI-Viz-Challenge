from data_engine import META, OBS, RANK, get_comparison, get_country_profile, get_explore, get_rankings


def test_dataset_shape():
    assert len(set(OBS.get_column("ISO3").drop_nulls().to_list())) == 138
    assert RANK.height == 138
    assert len(META["themes"]) == 19


def test_explore_contract_uses_median_and_region():
    payload = get_explore(view="thematic", metric="Gender Equality", pillar="Government actions", region="Europe")
    assert payload["map"]
    assert payload["regional"]
    assert payload["headline"]["median"] is not None
    assert all(row["region"] == "Europe" for row in payload["map"])


def test_country_profile():
    profile = get_country_profile("CAN")
    assert profile["summary"]["country"] == "Canada"
    assert len(profile["themes"]) == 19


def test_rankings_region_filter():
    rows = get_rankings(region="Europe")
    assert rows
    assert all(row["region"] == "Europe" for row in rows)


def test_comparison_regions():
    result = get_comparison("regions", "Europe", "Africa")
    assert result["first_label"] == "Europe"
    assert result["second_label"] == "Africa"
    assert len(result["rows"]) == 7


def test_comparison_countries():
    result = get_comparison("countries", "CAN", "USA")
    assert result["first_label"] == "Canada"
    assert result["second_label"] == "United States of America"
    assert len(result["rows"]) == 7
