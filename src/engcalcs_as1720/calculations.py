"""Selected strength calculations traceable to AS 1720.1:2010 Amd 3."""

from collections.abc import Mapping
from math import cos, isclose, radians, sin, sqrt
from typing import Any

from jsonschema import Draft202012Validator

from .schemas import (
    BEAM_INPUT_SCHEMA,
    BEARING_INPUT_SCHEMA,
    COLUMN_INPUT_SCHEMA,
    COMBINED_COMPRESSION_INPUT_SCHEMA,
    COMBINED_TENSION_INPUT_SCHEMA,
    OUTPUT_SCHEMA,
    TENSION_INPUT_SCHEMA,
)
from .standards import (
    BEAM_RHO,
    BEARING_PROPERTIES,
    COLUMN_RHO,
    F_GRADE_PROPERTIES,
    G13,
    K1,
    K7_EXACT_BEARING_LENGTH,
    K7_LONG_BEARING_LENGTH_MM,
    PHI_HIGH_GRADE,
    PHI_OTHER_GRADE,
)

_BASE_WARNINGS = [
    (
        "Only the checks and clauses listed in this result were evaluated; "
        "this is not a full AS 1720.1 compliance assessment."
    ),
    (
        "Supply governing design action effects from applicable load combinations; "
        "action analysis and combination selection are outside this calculation."
    ),
    (
        "Serviceability, deflection, connections, member notches, system effects and "
        "project-level checks are outside scope."
    ),
]


def _validate(inputs: Mapping[str, Any], schema: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(inputs), key=lambda e: list(e.path))
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.path) or "input"
        raise ValueError(f"Invalid {path}: {error.message}")


def _context(
    material: Mapping[str, Any], section: Mapping[str, float] | None = None
) -> dict[str, Any]:
    grade = material["stress_grade"]
    condition = material["moisture_condition"]
    duration = material["duration"]
    category = material["category"]
    if material["partially_seasoned_before_full_load"] and condition != "unseasoned":
        raise ValueError("Partial-seasoning k4 applies only to unseasoned timber inputs.")
    if material["partially_seasoned_before_full_load"] and section is not None:
        section_least_dimension = min(section["breadth_mm"], section["depth_mm"])
        if not isclose(material["least_dimension_mm"], section_least_dimension, abs_tol=1e-9):
            raise ValueError(
                "least_dimension_mm must match the rectangular section's least dimension "
                "when partial-seasoning k4 is selected."
            )
    if material["northern_region_factor_applies"] and condition != "seasoned":
        raise ValueError(
            "The k6 regional reduction specified here applies to seasoned timber only."
        )

    if condition == "seasoned":
        emc = material["expected_annual_emc_percent"]
        k4 = max(1.0 - 0.3 * (emc - 15.0) / 10.0, 0.7) if emc > 15.0 else 1.0
    elif material["partially_seasoned_before_full_load"]:
        least_dimension = material["least_dimension_mm"]
        if least_dimension <= 38.0:
            k4 = 1.15
        elif least_dimension <= 50.0:
            k4 = 1.10
        elif least_dimension <= 75.0:
            k4 = 1.05
        else:
            k4 = 1.0
    else:
        k4 = 1.0

    phi_values = PHI_HIGH_GRADE if int(grade[1:]) >= 17 else PHI_OTHER_GRADE
    return {
        "grade": grade,
        "timber_type": material["timber_type"],
        "moisture_condition": condition,
        "category": category,
        "phi": phi_values[category - 1],
        "k1": K1[duration],
        "k4": k4,
        "k6": 0.9 if material["northern_region_factor_applies"] else 1.0,
        "duration": duration,
        "expected_annual_emc_percent": material["expected_annual_emc_percent"],
        "partially_seasoned_before_full_load": material["partially_seasoned_before_full_load"],
        "northern_region_factor_applies": material["northern_region_factor_applies"],
    }


def _section(section: Mapping[str, float]) -> tuple[float, float, float]:
    breadth = section["breadth_mm"]
    depth = section["depth_mm"]
    if depth < breadth:
        raise ValueError("Rectangular F-grade member input requires depth_mm >= breadth_mm.")
    area = breadth * depth
    return breadth, depth, area


def _grade_values(context: Mapping[str, Any]) -> dict[str, float]:
    values = F_GRADE_PROPERTIES[context["grade"]]
    return {
        **values,
        "tension": values[
            "tension_hardwood" if context["timber_type"] == "hardwood" else "tension_softwood"
        ],
    }


def _beam_size_factor(depth_mm: float) -> float:
    return (300.0 / depth_mm) ** 0.167 if depth_mm > 300.0 else 1.0


def _tension_size_factor(max_dimension_mm: float) -> float:
    return (150.0 / max_dimension_mm) ** 0.167 if max_dimension_mm > 150.0 else 1.0


def _stability_factor(rho: float, slenderness: float) -> float:
    rho_s = rho * slenderness
    if rho_s <= 10.0:
        return 1.0
    if rho_s <= 20.0:
        return 1.5 - 0.05 * rho_s
    return 200.0 / (rho_s**2)


def _check(
    clause: str,
    name: str,
    demand: float,
    limit: float,
    details: Mapping[str, Any] | None = None,
    *,
    unit: str = "kN",
) -> dict[str, Any]:
    if limit <= 0.0:
        raise ValueError(f"Calculated limit for {name} must be positive.")
    utilisation = demand / limit
    return {
        "clause": clause,
        "name": name,
        "unit": unit,
        "demand_value": demand,
        "limit_value": limit,
        "utilisation": utilisation,
        "satisfied": utilisation <= 1.0,
        "details": dict(details or {}),
    }


def _interaction(
    clause: str, name: str, value: float, components: Mapping[str, float]
) -> dict[str, Any]:
    return {
        "clause": clause,
        "name": name,
        "unit": "ratio",
        "demand_value": value,
        "limit_value": 1.0,
        "utilisation": value,
        "satisfied": value <= 1.0,
        "details": dict(components),
    }


def _beam_stability(
    context: Mapping[str, Any], breadth: float, depth: float, restraint: Mapping[str, Any]
) -> tuple[float, float, dict[str, float]]:
    grade = context["grade"]
    condition_index = 0 if context["moisture_condition"] == "seasoned" else 1
    rho = BEAM_RHO[grade][condition_index]
    spacing = restraint["spacing_mm"]
    kind = restraint["type"]
    if kind.startswith("continuous_"):
        criterion_lhs = spacing / depth
        criterion_rhs = 64.0 * (breadth / (rho * depth)) ** 2
        if criterion_lhs > criterion_rhs + 1e-12:
            raise ValueError(
                "Continuous restraint does not meet AS 1720.1 Eq. 3.2(6) for the supplied spacing; "
                "model the actual discrete restraints instead."
            )
        slenderness = 0.0 if kind == "continuous_compression_edge" else 2.25 * breadth / depth
    elif kind == "discrete_compression_edge":
        slenderness = 1.25 * depth / breadth * sqrt(spacing / depth)
    else:
        slenderness = (depth / breadth) ** 1.35 * (spacing / depth) ** 0.25
    k12 = _stability_factor(rho, slenderness)
    return (
        slenderness,
        k12,
        {
            "rho_b": rho,
            "continuous_criterion_lhs": spacing / depth,
            "continuous_criterion_rhs": 64.0 * (breadth / (rho * depth)) ** 2,
        },
    )


def _beam_capacities(inputs: Mapping[str, Any]) -> dict[str, Any]:
    breadth, depth, area = _section(inputs["section"])
    context = _context(inputs["material"], inputs["section"])
    grade = _grade_values(context)
    restraint = inputs["restraint"] if "restraint" in inputs else inputs["beam_restraint"]
    slenderness, k12x, stability_details = _beam_stability(context, breadth, depth, restraint)
    fb_major = grade["bending"] * _beam_size_factor(depth)
    fb_minor = grade["bending"] * _beam_size_factor(breadth)
    z_major = breadth * depth**2 / 6.0
    z_minor = depth * breadth**2 / 6.0
    common = context["phi"] * context["k1"] * context["k4"] * context["k6"]
    mdx_knm = common * k12x * fb_major * z_major / 1e6  # k9 = 1 for an isolated member.
    mdy_knm = common * fb_minor * z_minor / 1e6  # Minor-axis S2 = 0, so k12 = 1.
    shear_area = 2.0 * area / 3.0
    vd_kn = common * grade["shear"] * shear_area / 1000.0
    return {
        "context": context,
        "breadth_mm": breadth,
        "depth_mm": depth,
        "area_mm2": area,
        "z_major_mm3": z_major,
        "z_minor_mm3": z_minor,
        "fb_major_mpa": fb_major,
        "fb_minor_mpa": fb_minor,
        "mdx_knm": mdx_knm,
        "mdy_knm": mdy_knm,
        "shear_area_mm2": shear_area,
        "vd_kn": vd_kn,
        "rho_b": stability_details["rho_b"],
        "slenderness_major": slenderness,
        "k12_major": k12x,
        "k12_minor": 1.0,
        "stability_details": stability_details,
        "grade_properties": grade,
        "k9": 1.0,
    }


def _output(
    operation: str,
    checks: list[dict[str, Any]],
    factors: Mapping[str, Any],
    clauses: list[str],
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    result = {
        "standard": "AS 1720.1:2010 Amd 3:2015",
        "operation": operation,
        "checks": checks,
        "factors": dict(factors),
        "clauses": clauses,
        "warnings": list(_BASE_WARNINGS if warnings is None else warnings),
        "full_standard_compliance": False,
        "standard_compliance_evaluated": False,
    }
    Draft202012Validator(OUTPUT_SCHEMA).validate(result)
    return result


def run_beam_design(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Check unnotched rectangular solid-sawn F-grade beam strength."""
    _validate(inputs, BEAM_INPUT_SCHEMA)
    capacity = _beam_capacities(inputs)
    actions = inputs["actions"]
    major = _check(
        "3.2.1.1",
        "Major-axis bending capacity",
        actions["moment_major_knm"],
        capacity["mdx_knm"],
        {
            "design_capacity_knm": capacity["mdx_knm"],
            "characteristic_bending_mpa": capacity["fb_major_mpa"],
            "section_modulus_mm3": capacity["z_major_mm3"],
            "slenderness_coefficient_s1": capacity["slenderness_major"],
            "k12": capacity["k12_major"],
            "k9": 1.0,
        },
        unit="kN·m",
    )
    minor = _check(
        "3.2.1.1",
        "Minor-axis bending capacity",
        actions["moment_minor_knm"],
        capacity["mdy_knm"],
        {
            "design_capacity_knm": capacity["mdy_knm"],
            "characteristic_bending_mpa": capacity["fb_minor_mpa"],
            "section_modulus_mm3": capacity["z_minor_mm3"],
            "slenderness_coefficient_s2": 0.0,
            "k12": 1.0,
        },
        unit="kN·m",
    )
    biaxial = _interaction(
        "3.2.1.2",
        "Biaxial bending interaction",
        major["utilisation"] + minor["utilisation"],
        {"major_axis_ratio": major["utilisation"], "minor_axis_ratio": minor["utilisation"]},
    )
    shear = _check(
        "3.2.5",
        "Flexural shear capacity",
        actions["shear_kn"],
        capacity["vd_kn"],
        {
            "design_capacity_kn": capacity["vd_kn"],
            "characteristic_beam_shear_mpa": capacity["grade_properties"]["shear"],
            "shear_area_mm2": capacity["shear_area_mm2"],
        },
    )
    return _output(
        "beam_design",
        [major, minor, biaxial, shear],
        capacity["context"],
        [
            "2.1.2",
            "2.3",
            "2.4.1",
            "2.4.2",
            "2.4.3",
            "3.2.1.1",
            "3.2.1.2",
            "3.2.3.2",
            "3.2.4",
            "3.2.5",
            "Tables 2.1, 2.3, 3.1, H2.1",
        ],
        [
            *_BASE_WARNINGS,
            (
                "k9 is 1.0 for an isolated member; no parallel-system strength-sharing "
                "credit is applied."
            ),
            (
                "Check beam shear action effects using the support-region rule in "
                "Clause 3.2.5 where applicable."
            ),
        ],
    )


def _column_capacities(inputs: Mapping[str, Any]) -> dict[str, Any]:
    breadth, depth, area = _section(inputs["section"])
    context = _context(inputs["material"], inputs["section"])
    restraint = inputs["restraint"] if "restraint" in inputs else inputs["column_restraint"]
    length = restraint["length_mm"]
    major_spacing = restraint["major_axis_restraint_spacing_mm"]
    minor_spacing = restraint["minor_axis_restraint_spacing_mm"]
    if major_spacing > length or minor_spacing > length:
        raise ValueError("Column restraint spacing cannot exceed the member length.")
    g13 = G13[restraint["end_restraint_condition"]]
    if restraint["continuous_major_axis_restraint"]:
        s3 = 0.0
    else:
        s3 = min(major_spacing / depth, g13 * length / depth)
    if restraint["continuous_minor_axis_restraint"]:
        s4 = 3.5 * depth / breadth
    else:
        s4 = min(minor_spacing / breadth, g13 * length / breadth)
    condition_index = 0 if context["moisture_condition"] == "seasoned" else 1
    rho_c = COLUMN_RHO[context["grade"]][condition_index]
    k12x = _stability_factor(rho_c, s3)
    k12y = _stability_factor(rho_c, s4)
    fc = _grade_values(context)["compression"]
    common = context["phi"] * context["k1"] * context["k4"] * context["k6"] * fc * area / 1000.0
    ndcx = common * k12x
    ndcy = common * k12y
    return {
        "context": context,
        "breadth_mm": breadth,
        "depth_mm": depth,
        "area_mm2": area,
        "fc_mpa": fc,
        "rho_c": rho_c,
        "g13": g13,
        "s3": s3,
        "s4": s4,
        "k12x": k12x,
        "k12y": k12y,
        "ndcx_kn": ndcx,
        "ndcy_kn": ndcy,
    }


def run_column_design(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Check unnotched rectangular solid-sawn F-grade column compression stability."""
    _validate(inputs, COLUMN_INPUT_SCHEMA)
    capacity = _column_capacities(inputs)
    action = inputs["compression_kn"]
    x = _check(
        "3.3.1.2",
        "Compression with major-axis buckling",
        action,
        capacity["ndcx_kn"],
        {
            "design_capacity_kn": capacity["ndcx_kn"],
            "S3": capacity["s3"],
            "rho_c": capacity["rho_c"],
            "k12": capacity["k12x"],
            "characteristic_compression_mpa": capacity["fc_mpa"],
        },
    )
    y = _check(
        "3.3.1.2",
        "Compression with minor-axis buckling",
        action,
        capacity["ndcy_kn"],
        {
            "design_capacity_kn": capacity["ndcy_kn"],
            "S4": capacity["s4"],
            "rho_c": capacity["rho_c"],
            "k12": capacity["k12y"],
            "characteristic_compression_mpa": capacity["fc_mpa"],
        },
    )
    return _output(
        "column_design",
        [x, y],
        capacity["context"],
        [
            "2.1.2",
            "2.3",
            "2.4.1",
            "2.4.2",
            "2.4.3",
            "3.3.1",
            "3.3.2.2",
            "3.3.3",
            "Tables 2.1, 2.3, 3.2, 3.3, H2.1",
        ],
    )


def _tension_capacity(inputs: Mapping[str, Any]) -> dict[str, Any]:
    breadth, depth, gross_area = _section(inputs["section"])
    context = _context(inputs["material"], inputs["section"])
    net_area = inputs["net_area_mm2"]
    if net_area > gross_area:
        raise ValueError("Net tension area cannot exceed the gross rectangular section area.")
    size_factor = _tension_size_factor(max(breadth, depth))
    grade = _grade_values(context)
    characteristic = grade["tension"] * size_factor
    capacity = (
        context["phi"]
        * context["k1"]
        * context["k4"]
        * context["k6"]
        * characteristic
        * net_area
        / 1000.0
    )
    return {
        "context": context,
        "gross_area_mm2": gross_area,
        "net_area_mm2": net_area,
        "size_factor": size_factor,
        "characteristic_tension_mpa": characteristic,
        "ndt_kn": capacity,
    }


def run_tension_design(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Check unnotched rectangular solid-sawn F-grade axial tension strength."""
    _validate(inputs, TENSION_INPUT_SCHEMA)
    capacity = _tension_capacity(inputs)
    check = _check(
        "3.4.1",
        "Tension parallel to grain",
        inputs["tension_kn"],
        capacity["ndt_kn"],
        {
            "design_capacity_kn": capacity["ndt_kn"],
            "characteristic_tension_mpa": capacity["characteristic_tension_mpa"],
            "net_area_mm2": capacity["net_area_mm2"],
            "tension_size_factor": capacity["size_factor"],
        },
    )
    return _output(
        "tension_design",
        [check],
        capacity["context"],
        ["2.1.2", "2.3", "2.4.1", "2.4.2", "2.4.3", "3.4.1", "Table H2.1"],
    )


def _k7(inputs: Mapping[str, Any]) -> float:
    if not inputs["rectangular_bearing_verified"] or inputs["distance_from_end_mm"] < 75.0:
        return 1.0
    length = inputs["bearing_length_mm"]
    for tabulated, factor in K7_EXACT_BEARING_LENGTH.items():
        if isclose(length, tabulated, abs_tol=1e-9):
            return factor
    if length >= K7_LONG_BEARING_LENGTH_MM:
        return 1.0
    # Table 2.6 gives discrete listed lengths. No interpolation is assumed here.
    return 1.0


def run_bearing_design(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Check a rectangular timber bearing area at an angle to grain."""
    _validate(inputs, BEARING_INPUT_SCHEMA)
    context = _context(inputs["material"])
    group = inputs["strength_group"]
    seasoned = context["moisture_condition"] == "seasoned"
    if seasoned != group.startswith("SD"):
        raise ValueError(
            "Bearing strength group must match the seasoned or unseasoned timber condition."
        )
    characteristic_perp, characteristic_parallel = BEARING_PROPERTIES[group]
    k7 = _k7(inputs)
    common = context["phi"] * context["k1"] * context["k4"] * context["k6"]
    area = inputs["area_mm2"]
    ndp_kn = common * k7 * characteristic_perp * area / 1000.0
    ndl_kn = common * characteristic_parallel * area / 1000.0
    theta = radians(inputs["bearing_angle_deg"])
    denominator = ndl_kn * sin(theta) ** 2 + ndp_kn * cos(theta) ** 2
    ndtheta_kn = (
        ndp_kn
        if isclose(inputs["bearing_angle_deg"], 90.0)
        else (
            ndl_kn if isclose(inputs["bearing_angle_deg"], 0.0) else ndl_kn * ndp_kn / denominator
        )
    )
    check = _check(
        "3.2.6",
        "Bearing capacity at angle to grain",
        inputs["bearing_kn"],
        ndtheta_kn,
        {
            "design_capacity_kn": ndtheta_kn,
            "design_capacity_perpendicular_kn": ndp_kn,
            "design_capacity_parallel_kn": ndl_kn,
            "characteristic_perpendicular_mpa": characteristic_perp,
            "characteristic_parallel_mpa": characteristic_parallel,
            "strength_group": group,
            "bearing_angle_deg": inputs["bearing_angle_deg"],
            "bearing_factor_k7": k7,
        },
    )
    factors = {**context, "k7": k7, "strength_group": group}
    return _output(
        "bearing_design",
        [check],
        factors,
        ["2.3", "2.4.1", "2.4.2", "2.4.3", "2.4.4", "3.2.6", "Tables 2.1, 2.3, 2.5, 2.6, H2.2"],
        [
            *_BASE_WARNINGS,
            (
                "k7 is used only for a verified rectangular bearing area at least "
                "75 mm from the member end and an exact Table 2.6 bearing length; "
                "otherwise k7 = 1.0."
            ),
        ],
    )


def run_combined_compression(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Check AS 1720.1 Clause 3.5.1 bending and axial compression interactions."""
    _validate(inputs, COMBINED_COMPRESSION_INPUT_SCHEMA)
    beam_inputs = {
        "material": inputs["material"],
        "section": inputs["section"],
        "beam_restraint": inputs["beam_restraint"],
    }
    column_inputs = {
        "material": inputs["material"],
        "section": inputs["section"],
        "column_restraint": inputs["column_restraint"],
    }
    beam = _beam_capacities(beam_inputs)
    column = _column_capacities(column_inputs)
    moment_ratio = inputs["moment_major_knm"] / beam["mdx_knm"]
    axial_x = inputs["compression_kn"] / column["ndcx_kn"]
    axial_y = inputs["compression_kn"] / column["ndcy_kn"]
    checks = [
        _interaction(
            "3.5.1",
            "Bending and compression interaction (major buckling)",
            moment_ratio**2 + axial_y,
            {
                "moment_ratio": moment_ratio,
                "axial_ratio_minor_buckling": axial_y,
                "equation": "(Mx/Mdx)^2 + N/Nd,cy <= 1",
            },
        ),
        _interaction(
            "3.5.1",
            "Bending and compression interaction (minor buckling)",
            moment_ratio + axial_x,
            {
                "moment_ratio": moment_ratio,
                "axial_ratio_major_buckling": axial_x,
                "equation": "Mx/Mdx + N/Nd,cx <= 1",
            },
        ),
    ]
    factors = {
        **beam["context"],
        "k12_bending": beam["k12_major"],
        "k12_compression_major_axis": column["k12x"],
        "k12_compression_minor_axis": column["k12y"],
        "bending_capacity_knm": beam["mdx_knm"],
        "compression_capacity_major_kn": column["ndcx_kn"],
        "compression_capacity_minor_kn": column["ndcy_kn"],
    }
    return _output(
        "combined_compression",
        checks,
        factors,
        [
            "3.2.1",
            "3.2.3.2",
            "3.2.4",
            "3.3.1",
            "3.3.2.2",
            "3.3.3",
            "3.5.1",
            "Tables 3.1, 3.2, 3.3, H2.1",
        ],
    )


def run_combined_tension(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Check AS 1720.1 Clause 3.5.2 bending and axial tension interactions."""
    _validate(inputs, COMBINED_TENSION_INPUT_SCHEMA)
    beam_inputs = {
        "material": inputs["material"],
        "section": inputs["section"],
        "beam_restraint": inputs["beam_restraint"],
    }
    tension_inputs = {
        "material": inputs["material"],
        "section": inputs["section"],
        "net_area_mm2": inputs["net_area_mm2"],
    }
    beam = _beam_capacities(beam_inputs)
    tension = _tension_capacity(tension_inputs)
    moment = inputs["moment_major_knm"]
    tension_action = inputs["tension_kn"]
    bending_capacity = beam["mdx_knm"]
    bending_ratio = moment / bending_capacity
    tension_ratio = tension_action / tension["ndt_kn"]
    z_over_a_mm = beam["z_major_mm3"] / tension["gross_area_mm2"]
    axial_bending_reduction_knm = z_over_a_mm * tension_action / 1000.0
    adjusted_bending_ratio = (moment - axial_bending_reduction_knm) / bending_capacity
    checks = [
        _interaction(
            "3.5.2",
            "Bending and tension interaction",
            beam["k12_major"] * bending_ratio + tension_ratio,
            {
                "k12": beam["k12_major"],
                "bending_ratio": bending_ratio,
                "tension_ratio": tension_ratio,
                "equation": "k12*M/Md + Nt/Nd,t <= 1",
            },
        ),
        _interaction(
            "3.5.2",
            "Adjusted major-axis bending interaction",
            adjusted_bending_ratio,
            {
                "moment_knm": moment,
                "z_over_area_mm": z_over_a_mm,
                "tension_action_kn": tension_action,
                "adjusted_moment_knm": moment - axial_bending_reduction_knm,
                "bending_capacity_knm": bending_capacity,
                "equation": "(Mx - (Z/A)*Nt)/Md <= 1",
            },
        ),
    ]
    factors = {
        **beam["context"],
        "k12_bending": beam["k12_major"],
        "bending_capacity_knm": bending_capacity,
        "tension_capacity_kn": tension["ndt_kn"],
        "characteristic_tension_mpa": tension["characteristic_tension_mpa"],
    }
    return _output(
        "combined_tension",
        checks,
        factors,
        ["3.2.1", "3.2.3.2", "3.2.4", "3.4.1", "3.5.2", "Tables 3.1, H2.1"],
    )
