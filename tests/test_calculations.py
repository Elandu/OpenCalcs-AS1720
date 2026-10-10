"""Calculation, validation and plugin contract tests."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from opencalcs_as1720.calculations import (
    _stability_factor,
    run_beam_design,
    run_bearing_design,
    run_column_design,
    run_combined_compression,
    run_combined_tension,
    run_tension_design,
)
from opencalcs_as1720.plugin import get_plugin
from opencalcs_as1720.schemas import (
    BEAM_INPUT_SCHEMA,
    BEARING_INPUT_SCHEMA,
    COLUMN_INPUT_SCHEMA,
    COMBINED_COMPRESSION_INPUT_SCHEMA,
    COMBINED_TENSION_INPUT_SCHEMA,
    OUTPUT_SCHEMA,
    TENSION_INPUT_SCHEMA,
)
from opencalcs_as1720.standards import F_GRADE_PROPERTIES, PHI_HIGH_GRADE, PHI_OTHER_GRADE
from tests.verification_report import build_report

ROOT = Path(__file__).resolve().parents[1]


def example(filename):
    return json.loads((ROOT / "examples" / filename).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("filename", "runner"),
    [
        ("f17_blackbutt_beam.json", run_beam_design),
        ("f17_blackbutt_column.json", run_column_design),
        ("f17_blackbutt_tension.json", run_tension_design),
        ("f17_blackbutt_bearing.json", run_bearing_design),
        ("f17_blackbutt_combined_compression.json", run_combined_compression),
        ("f17_blackbutt_combined_tension.json", run_combined_tension),
    ],
)
def test_published_table_based_example_outputs_validate(filename, runner):
    result = runner(example(filename))
    Draft202012Validator(OUTPUT_SCHEMA).validate(result)
    assert result["standard"] == "AS 1720.1:2010 Amd 3:2015"
    assert result["full_standard_compliance"] is False
    assert result["standard_compliance_evaluated"] is False
    assert all(check["satisfied"] for check in result["checks"])


def test_independent_hand_calculated_benchmarks_match():
    report = build_report()
    assert report["passed"]
    assert len(report["cases"]) == 11
    assert all(
        case["absolute_difference"] <= case["absolute_tolerance"] for case in report["cases"]
    )


def test_material_tables_cover_each_supported_f_grade():
    assert list(F_GRADE_PROPERTIES) == [
        "F34",
        "F27",
        "F22",
        "F17",
        "F14",
        "F11",
        "F8",
        "F7",
        "F5",
        "F4",
    ]
    assert all(
        values["bending"] > 0 and values["compression"] > 0
        for values in F_GRADE_PROPERTIES.values()
    )
    assert PHI_HIGH_GRADE == (0.95, 0.85, 0.75)
    assert PHI_OTHER_GRADE == (0.90, 0.70, 0.60)


def test_seasoned_moisture_factor_and_f17_beam_stability():
    data = example("f17_blackbutt_beam.json")
    result = run_beam_design(data)
    assert result["factors"]["k4"] == pytest.approx(0.91)
    assert result["checks"][0]["details"]["k12"] == 1.0
    assert result["checks"][0]["details"]["slenderness_coefficient_s1"] == 0.0


def test_discrete_edge_restraint_equations_and_stability_regions():
    data = example("f17_blackbutt_beam.json")
    data["restraint"] = {"type": "discrete_compression_edge", "spacing_mm": 1200}
    result = run_beam_design(data)
    rho_b = 0.98
    s1 = 1.25 * 240 / 90 * (1200 / 240) ** 0.5
    rho_s = rho_b * s1
    expected_k12 = 1.0 if rho_s <= 10 else (1.5 - 0.05 * rho_s if rho_s <= 20 else 200 / rho_s**2)
    assert result["checks"][0]["details"]["slenderness_coefficient_s1"] == pytest.approx(s1)
    assert result["checks"][0]["details"]["k12"] == pytest.approx(expected_k12)


def test_stability_factor_piecewise_boundaries():
    assert _stability_factor(1.0, 10.0) == 1.0
    assert _stability_factor(1.0, 10.01) == pytest.approx(1.5 - 0.05 * 10.01)
    assert _stability_factor(1.0, 20.0) == pytest.approx(0.5)
    assert _stability_factor(1.0, 20.001) == pytest.approx(200.0 / 20.001**2)


def test_continuous_restraint_requires_equation_3_2_6():
    data = example("f17_blackbutt_beam.json")
    data["restraint"]["spacing_mm"] = 5000
    with pytest.raises(ValueError, match=r"Eq. 3.2\(6\)"):
        run_beam_design(data)


def test_column_minor_axis_governs_example():
    result = run_column_design(example("f17_blackbutt_column.json"))
    assert result["checks"][1]["utilisation"] > result["checks"][0]["utilisation"]
    assert result["checks"][1]["details"]["k12"] < 1.0


def test_partial_seasoning_factor_uses_least_dimension_bands():
    data = example("f17_blackbutt_beam.json")
    data["section"]["breadth_mm"] = 50
    data["material"].update(
        {
            "moisture_condition": "unseasoned",
            "partially_seasoned_before_full_load": True,
            "least_dimension_mm": 50,
        }
    )
    result = run_beam_design(data)
    assert result["factors"]["k4"] == 1.10


def test_partial_seasoning_dimension_must_match_the_section():
    data = example("f17_blackbutt_beam.json")
    data["material"].update(
        {
            "moisture_condition": "unseasoned",
            "partially_seasoned_before_full_load": True,
            "least_dimension_mm": 38,
        }
    )
    with pytest.raises(ValueError, match="must match the rectangular section"):
        run_beam_design(data)


@pytest.mark.parametrize(
    ("bearing_length", "end_distance", "expected_k7"),
    [(75, 75, 1.15), (75, 74.9, 1.0), (80, 100, 1.0), (150, 100, 1.0)],
)
def test_bearing_k7_only_uses_eligible_table_lengths(bearing_length, end_distance, expected_k7):
    data = example("f17_blackbutt_bearing.json")
    data["bearing_length_mm"] = bearing_length
    data["distance_from_end_mm"] = end_distance
    result = run_bearing_design(data)
    assert result["factors"]["k7"] == expected_k7


def test_bearing_angle_endpoints_and_hankinson_interpolation():
    data = example("f17_blackbutt_bearing.json")
    perpendicular = run_bearing_design(data)["checks"][0]["details"][
        "design_capacity_perpendicular_kn"
    ]
    parallel = run_bearing_design({**data, "bearing_angle_deg": 0})["checks"][0]["limit_value"]
    assert (
        run_bearing_design({**data, "bearing_angle_deg": 90})["checks"][0]["limit_value"]
        == perpendicular
    )
    assert parallel == pytest.approx(279.8523)
    at_45 = run_bearing_design({**data, "bearing_angle_deg": 45})["checks"][0]["limit_value"]
    assert at_45 == pytest.approx(parallel * perpendicular / (parallel + perpendicular) * 2.0)


def test_rejects_strength_group_for_wrong_moisture_condition():
    data = example("f17_blackbutt_bearing.json")
    data["material"]["moisture_condition"] = "unseasoned"
    with pytest.raises(ValueError, match="strength group must match"):
        run_bearing_design(data)


def test_combined_action_equations_are_both_reported():
    compression = run_combined_compression(example("f17_blackbutt_combined_compression.json"))
    tension = run_combined_tension(example("f17_blackbutt_combined_tension.json"))
    assert [item["clause"] for item in compression["checks"]] == ["3.5.1", "3.5.1"]
    assert [item["clause"] for item in tension["checks"]] == ["3.5.2", "3.5.2"]
    assert compression["checks"][0]["details"]["equation"] == "(Mx/Mdx)^2 + N/Nd,cy <= 1"
    assert tension["checks"][1]["details"]["adjusted_moment_knm"] == pytest.approx(2.0)
    assert compression["checks"][0]["unit"] == "ratio"
    assert run_beam_design(example("f17_blackbutt_beam.json"))["checks"][0]["unit"] == "kN·m"


@pytest.mark.parametrize(
    ("runner", "filename", "schema", "field", "value"),
    [
        (run_beam_design, "f17_blackbutt_beam.json", BEAM_INPUT_SCHEMA, "unknown", 1),
        (run_column_design, "f17_blackbutt_column.json", COLUMN_INPUT_SCHEMA, "unknown", 1),
        (run_tension_design, "f17_blackbutt_tension.json", TENSION_INPUT_SCHEMA, "unknown", 1),
        (run_bearing_design, "f17_blackbutt_bearing.json", BEARING_INPUT_SCHEMA, "unknown", 1),
        (
            run_combined_compression,
            "f17_blackbutt_combined_compression.json",
            COMBINED_COMPRESSION_INPUT_SCHEMA,
            "unknown",
            1,
        ),
        (
            run_combined_tension,
            "f17_blackbutt_combined_tension.json",
            COMBINED_TENSION_INPUT_SCHEMA,
            "unknown",
            1,
        ),
    ],
)
def test_calculation_schemas_reject_unexpected_fields(runner, filename, schema, field, value):
    data = example(filename)
    data[field] = value
    assert list(Draft202012Validator(schema).iter_errors(data))
    with pytest.raises(ValueError, match="Additional properties are not allowed"):
        runner(data)


def test_plugin_descriptor_is_solver_independent_and_deep_copied():
    plugin = get_plugin()
    descriptor = plugin.descriptor()
    assert plugin.id == "structural.as1720"
    assert descriptor["license"] == "LicenseRef-EngCalcs-Proprietary"
    assert len(descriptor["calculations"]) == 6
    assert all(
        calc["standard"]["amendments"] == "Amendments 1, 2 and 3 (Amd 3:2015)"
        for calc in descriptor["calculations"]
    )
    first = plugin.calculations[0]
    exposed = first.descriptor()
    exposed["input_schema"].clear()
    assert first.input_schema


def test_plugin_exposes_all_requested_calculation_ids():
    ids = {item.id for item in get_plugin().calculations}
    assert ids == {
        "structural.as1720.beam_design",
        "structural.as1720.column_design",
        "structural.as1720.tension_design",
        "structural.as1720.bearing_design",
        "structural.as1720.combined_compression",
        "structural.as1720.combined_tension",
    }
