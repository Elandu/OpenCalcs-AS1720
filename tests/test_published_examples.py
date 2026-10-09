"""External calculator cross-checks kept separate from standard-equation benchmarks."""

import json
import math
from pathlib import Path

import pytest

from engcalcs_as1720.calculations import run_beam_design, run_bearing_design, run_column_design

ROOT = Path(__file__).resolve().parents[1]
REPORT = json.loads((ROOT / "validation" / "published_examples.json").read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in REPORT["cases"]}


def _inputs(case_id: str) -> dict:
    case = CASES[case_id]
    return json.loads((ROOT / case["input_file"]).read_text(encoding="utf-8"))


def _assert_matches_displayed(value: float, published: float, increment: float) -> None:
    assert abs(value - published) <= increment / 2


def test_f17_column_matches_published_calculator_example_at_displayed_precision():
    case = CASES["new_future_solutions_f17_column"]
    result = run_column_design(_inputs(case["id"]))
    major, minor = result["checks"]
    actual = {
        "major_axis_capacity_kn": major["limit_value"],
        "minor_axis_capacity_kn": minor["limit_value"],
        "utilisation_percent": major["utilisation"] * 100,
        "s3": major["details"]["S3"],
        "s4": minor["details"]["S4"],
        "k12": major["details"]["k12"],
    }
    for name, expected in case["plugin_outputs"].items():
        assert actual[name] == pytest.approx(expected, abs=1e-9)
    _assert_matches_displayed(
        min(major["limit_value"], minor["limit_value"]),
        case["published_outputs"]["governing_capacity_kn"],
        case["displayed_increment"]["governing_capacity_kn"],
    )
    _assert_matches_displayed(
        actual["utilisation_percent"],
        case["published_outputs"]["utilisation_percent"],
        case["displayed_increment"]["utilisation_percent"],
    )
    assert case["comparison"] == "matches_at_displayed_precision"


def test_f17_beam_uses_standard_based_discrete_restraint_equation_and_records_site_mismatch():
    case = CASES["new_future_solutions_f17_beam"]
    inputs = _inputs(case["id"])
    result = run_beam_design(inputs)
    major = result["checks"][0]
    actual = {
        "slenderness_coefficient_s1": major["details"]["slenderness_coefficient_s1"],
        "stability_factor_k12": major["details"]["k12"],
        "design_bending_capacity_knm": major["limit_value"],
        "utilisation_percent": major["utilisation"] * 100,
    }

    breadth = inputs["section"]["breadth_mm"]
    depth = inputs["section"]["depth_mm"]
    restraint_spacing = inputs["restraint"]["spacing_mm"]
    s1_from_guide = 1.25 * (depth / breadth) * math.sqrt(restraint_spacing / depth)
    rho_b = 0.98  # AS 1720.1 Table 3.1, seasoned F17.
    k12_from_guide = 1.5 - 0.05 * rho_b * s1_from_guide
    z_mm3 = breadth * depth**2 / 6
    md_from_guide = 0.85 * 0.80 * k12_from_guide * 42.0 * z_mm3 / 1e6
    guide_calculation = {
        "slenderness_coefficient_s1": s1_from_guide,
        "stability_factor_k12": k12_from_guide,
        "design_bending_capacity_knm": md_from_guide,
        "utilisation_percent": inputs["actions"]["moment_major_knm"] / md_from_guide * 100,
    }
    equation = case["standard_equation_reference"]["expected_outputs"]
    for name, expected in guide_calculation.items():
        assert guide_calculation[name] == pytest.approx(expected, abs=1e-12)
    for name, expected in equation.items():
        assert actual[name] == pytest.approx(expected, abs=1e-9)
        assert actual[name] == pytest.approx(guide_calculation[name], abs=1e-9)

    # The third-party page's calculated value is consistent with a different
    # exponent placement than the guide's Clause 3.2.3.2 equation.
    page_s1 = (depth / breadth) ** 1.25 * math.sqrt(restraint_spacing / depth)
    page_k12 = 1.5 - 0.05 * rho_b * page_s1
    page_md = 0.85 * 0.80 * page_k12 * 42.0 * z_mm3 / 1e6
    page_utilisation = inputs["actions"]["moment_major_knm"] / page_md * 100
    page_calculation = {
        "slenderness_coefficient_s1": page_s1,
        "stability_factor_k12": page_k12,
        "design_bending_capacity_knm": page_md,
        "utilisation_percent": page_utilisation,
    }
    published = case["published_outputs"]
    for name, value in page_calculation.items():
        _assert_matches_displayed(value, published[name], case["displayed_increment"][name])
    assert (
        abs(actual["design_bending_capacity_knm"] - published["design_bending_capacity_knm"])
        > case["displayed_increment"]["design_bending_capacity_knm"] / 2
    )
    assert case["comparison"] == "documented_third_party_discrepancy"
    assert "Clause 3.2.3.2" in case["note"]


def test_f17_sd2_bearing_matches_published_calculator_output_at_displayed_precision():
    case = CASES["new_future_solutions_f17_sd2_bearing"]
    result = run_bearing_design(_inputs(case["id"]))
    check = result["checks"][0]
    actual = {
        "design_capacity_kn": check["limit_value"],
        "utilisation_percent": check["utilisation"] * 100,
        "k4": result["factors"]["k4"],
        "k7": result["factors"]["k7"],
    }
    for name, expected in case["plugin_outputs"].items():
        assert actual[name] == pytest.approx(expected, abs=1e-9)
    for name, published in case["published_outputs"].items():
        _assert_matches_displayed(actual[name], published, case["displayed_increment"][name])
    assert case["comparison"] == "matches_at_displayed_precision"
