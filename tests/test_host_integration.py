"""Optional integration checks against an installed EngCalcs host."""

import json
from importlib.metadata import entry_points
from pathlib import Path

import pytest

PLUGIN_ENTRY = next(
    (item for item in entry_points(group="engcalcs.plugins") if item.name == "as1720"),
    None,
)
if PLUGIN_ENTRY is None:
    pytest.skip(
        "Install this wheel and the EngCalcs host to run integration checks.",
        allow_module_level=True,
    )

ROOT = Path(__file__).resolve().parents[1]


def _inputs(filename):
    return json.loads((ROOT / "examples" / filename).read_text(encoding="utf-8"))


def test_entry_point_registers_all_calculations_and_registry_runs_examples():
    pytest.importorskip("engcalcs")
    from engcalcs.registry import CalculationRegistry

    plugin = PLUGIN_ENTRY.load()()
    assert plugin.id == "structural.as1720"
    registry = CalculationRegistry()
    examples = {
        "structural.as1720.beam_design": ("f17_blackbutt_beam.json", 0, "limit_value", 22.4550144),
        "structural.as1720.column_design": (
            "f17_blackbutt_column.json",
            1,
            "limit_value",
            206.5442176870748,
        ),
        "structural.as1720.tension_design": (
            "f17_blackbutt_tension.json",
            0,
            "limit_value",
            398.889405894025,
        ),
        "structural.as1720.bearing_design": (
            "f17_blackbutt_bearing.json",
            0,
            "limit_value",
            110.479005,
        ),
        "structural.as1720.combined_compression": (
            "f17_blackbutt_combined_compression.json",
            0,
            "demand_value",
            0.8256225582993648,
        ),
        "structural.as1720.combined_tension": (
            "f17_blackbutt_combined_tension.json",
            0,
            "demand_value",
            0.8418192863454977,
        ),
    }
    assert {item.id for item in plugin.calculations} == set(examples)
    for calculation_id, (filename, check_index, value_key, expected) in examples.items():
        result = registry.run(calculation_id, _inputs(filename))
        assert result["_provenance"]["engine"]["id"] == "structural.as1720"
        assert result["_provenance"]["calculation"]["id"] == calculation_id
        assert result["checks"][check_index][value_key] == pytest.approx(expected, abs=1e-9)


def test_host_http_catalog_and_calculation_run():
    pytest.importorskip("engcalcs")
    from engcalcs.api import create_app
    from engcalcs.auth import AllowAllAuthenticator
    from fastapi.testclient import TestClient

    with TestClient(create_app(authenticator=AllowAllAuthenticator())) as client:
        descriptor = client.get("/api/v1/calculations/structural.as1720.column_design")
        assert descriptor.status_code == 200
        result = client.post(
            "/api/v1/calculations/structural.as1720.column_design/run",
            json={"inputs": _inputs("f17_blackbutt_column.json")},
        )
    assert result.status_code == 200
    body = result.json()
    assert body["checks"][1]["limit_value"] == pytest.approx(206.5442176870748)
    assert body["_provenance"]["standard"]["edition"] == "2010"
