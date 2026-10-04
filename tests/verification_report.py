"""Independent hand-calculated benchmark values for representative examples."""

import json
from pathlib import Path
from typing import Any

from opencalcs_as1720.calculations import (
    run_beam_design,
    run_bearing_design,
    run_column_design,
    run_combined_compression,
    run_combined_tension,
    run_tension_design,
)
from opencalcs_as1720.standards import STANDARD

ROOT = Path(__file__).resolve().parents[1]
TOLERANCE = 1e-9

# Values below were evaluated separately from the plugin helpers using the
# printed clause equations and the selected table entries in docs/verification.md.
BENCHMARKS = (
    (
        "F17 hardwood beam: Md,x",
        "f17_blackbutt_beam.json",
        run_beam_design,
        lambda r: r["checks"][0]["limit_value"],
        22.4550144,
        "Eq. 3.2(2); Tables 2.1, 2.3, 3.1, H2.1",
    ),
    (
        "F17 hardwood beam: Md,y",
        "f17_blackbutt_beam.json",
        run_beam_design,
        lambda r: r["checks"][1]["limit_value"],
        8.4206304,
        "Eq. 3.2(2); Table H2.1",
    ),
    (
        "F17 hardwood beam: Vd",
        "f17_blackbutt_beam.json",
        run_beam_design,
        lambda r: r["checks"][3]["limit_value"],
        32.078592,
        "Eq. 3.2(14); Table H2.1",
    ),
    (
        "F17 hardwood column: Nd,cx",
        "f17_blackbutt_column.json",
        run_column_design,
        lambda r: r["checks"][0]["limit_value"],
        655.8192,
        "Eqs. 3.3(2), (5), (6), (11); Tables 3.2, 3.3, H2.1",
    ),
    (
        "F17 hardwood column: Nd,cy",
        "f17_blackbutt_column.json",
        run_column_design,
        lambda r: r["checks"][1]["limit_value"],
        206.5442176870748,
        "Eqs. 3.3(2), (8), (9), (11); Tables 3.2, 3.3, H2.1",
    ),
    (
        "F17 hardwood tension: Nd,t",
        "f17_blackbutt_tension.json",
        run_tension_design,
        lambda r: r["checks"][0]["limit_value"],
        398.889405894025,
        "Eq. 3.4(2); Table H2.1",
    ),
    (
        "Seasoned Blackbutt SD2 bearing: Nd,90",
        "f17_blackbutt_bearing.json",
        run_bearing_design,
        lambda r: r["checks"][0]["limit_value"],
        110.479005,
        "Eqs. 3.2(16), (18), (19); Tables 2.1, 2.3, 2.6, H2.2",
    ),
    (
        "Combined compression Eq. 3.5(1)",
        "f17_blackbutt_combined_compression.json",
        run_combined_compression,
        lambda r: r["checks"][0]["demand_value"],
        0.8256225582993648,
        "Eq. 3.5(1)",
    ),
    (
        "Combined compression Eq. 3.5(2)",
        "f17_blackbutt_combined_compression.json",
        run_combined_compression,
        lambda r: r["checks"][1]["demand_value"],
        0.5763156611731336,
        "Eq. 3.5(2)",
    ),
    (
        "Combined tension Eq. 3.5(3)",
        "f17_blackbutt_combined_tension.json",
        run_combined_tension,
        lambda r: r["checks"][0]["demand_value"],
        0.8418192863454977,
        "Eq. 3.5(3)",
    ),
    (
        "Combined tension Eq. 3.5(4)",
        "f17_blackbutt_combined_tension.json",
        run_combined_tension,
        lambda r: r["checks"][1]["demand_value"],
        0.0890669658176661,
        "Eq. 3.5(4)",
    ),
)


def build_report() -> dict[str, Any]:
    cases = []
    results: dict[tuple[str, str], dict[str, Any]] = {}
    for name, filename, runner, getter, expected, source in BENCHMARKS:
        key = (filename, runner.__name__)
        if key not in results:
            inputs = json.loads((ROOT / "examples" / filename).read_text(encoding="utf-8"))
            results[key] = runner(inputs)
        actual = getter(results[key])
        difference = abs(actual - expected)
        cases.append(
            {
                "name": name,
                "source_basis": source,
                "actual": actual,
                "expected": expected,
                "absolute_tolerance": TOLERANCE,
                "absolute_difference": difference,
                "passed": difference <= TOLERANCE,
            }
        )
    return {
        "package_version": "0.1.0",
        "standard": "AS 1720.1:2010 Amd 3:2015",
        "standard_reference": STANDARD.descriptor(),
        "method": (
            "Independent equation arithmetic compared with plugin outputs; "
            "see docs/verification.md."
        ),
        "passed": all(case["passed"] for case in cases),
        "cases": cases,
    }


if __name__ == "__main__":
    report = build_report()
    path = ROOT / "validation" / "benchmarks.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    status = "PASS" if report["passed"] else "FAIL"
    print(f"{status}: {len(report['cases'])} independent calculations -> {path}")
