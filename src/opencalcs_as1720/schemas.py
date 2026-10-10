# SPDX-License-Identifier: LicenseRef-EngCalcs-Proprietary

"""Strict JSON schemas for the public calculation inputs and outputs."""

from copy import deepcopy

from .standards import BEARING_PROPERTIES, F_GRADE_PROPERTIES, G13, K1

NUMBER = {"type": "number", "exclusiveMinimum": 0, "maximum": 1e9}
NONNEGATIVE = {"type": "number", "minimum": 0, "maximum": 1e9}
F_GRADE = {"enum": list(F_GRADE_PROPERTIES)}
DURATION = {"enum": list(K1)}
G13_CODE = {"enum": list(G13)}

MATERIAL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "stress_grade",
        "timber_type",
        "moisture_condition",
        "category",
        "duration",
        "expected_annual_emc_percent",
        "northern_region_factor_applies",
        "partially_seasoned_before_full_load",
        "least_dimension_mm",
    ],
    "properties": {
        "stress_grade": F_GRADE,
        "timber_type": {"enum": ["hardwood", "softwood"]},
        "moisture_condition": {"enum": ["seasoned", "unseasoned"]},
        "category": {"type": "integer", "minimum": 1, "maximum": 3},
        "duration": DURATION,
        "expected_annual_emc_percent": {
            "type": "number",
            "minimum": 0,
            "maximum": 40,
        },
        "northern_region_factor_applies": {"type": "boolean"},
        "partially_seasoned_before_full_load": {"type": "boolean"},
        "least_dimension_mm": NUMBER,
    },
}

SECTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["breadth_mm", "depth_mm"],
    "properties": {"breadth_mm": NUMBER, "depth_mm": NUMBER},
}

BEAM_RESTRAINT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["type", "spacing_mm"],
    "properties": {
        "type": {
            "enum": [
                "discrete_compression_edge",
                "discrete_tension_edge",
                "continuous_compression_edge",
                "continuous_tension_edge",
            ]
        },
        "spacing_mm": NUMBER,
    },
}

COLUMN_RESTRAINT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "length_mm",
        "major_axis_restraint_spacing_mm",
        "minor_axis_restraint_spacing_mm",
        "end_restraint_condition",
        "continuous_major_axis_restraint",
        "continuous_minor_axis_restraint",
    ],
    "properties": {
        "length_mm": NUMBER,
        "major_axis_restraint_spacing_mm": NUMBER,
        "minor_axis_restraint_spacing_mm": NUMBER,
        "end_restraint_condition": G13_CODE,
        "continuous_major_axis_restraint": {"type": "boolean"},
        "continuous_minor_axis_restraint": {"type": "boolean"},
    },
}

COMMON_MATERIAL_AND_SECTION = {
    "material": MATERIAL_SCHEMA,
    "section": SECTION_SCHEMA,
}

BEAM_INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["material", "section", "actions", "restraint"],
    "properties": {
        **deepcopy(COMMON_MATERIAL_AND_SECTION),
        "actions": {
            "type": "object",
            "additionalProperties": False,
            "required": ["moment_major_knm", "moment_minor_knm", "shear_kn"],
            "properties": {
                "moment_major_knm": NONNEGATIVE,
                "moment_minor_knm": NONNEGATIVE,
                "shear_kn": NONNEGATIVE,
            },
        },
        "restraint": BEAM_RESTRAINT_SCHEMA,
    },
}

COLUMN_INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["material", "section", "compression_kn", "restraint"],
    "properties": {
        **deepcopy(COMMON_MATERIAL_AND_SECTION),
        "compression_kn": NONNEGATIVE,
        "restraint": COLUMN_RESTRAINT_SCHEMA,
    },
}

TENSION_INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["material", "section", "net_area_mm2", "tension_kn"],
    "properties": {
        **deepcopy(COMMON_MATERIAL_AND_SECTION),
        "net_area_mm2": NUMBER,
        "tension_kn": NONNEGATIVE,
    },
}

BEARING_INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "material",
        "strength_group",
        "bearing_angle_deg",
        "area_mm2",
        "bearing_kn",
        "bearing_length_mm",
        "distance_from_end_mm",
        "rectangular_bearing_verified",
    ],
    "properties": {
        "material": MATERIAL_SCHEMA,
        "strength_group": {"enum": list(BEARING_PROPERTIES)},
        "bearing_angle_deg": {"type": "number", "minimum": 0, "maximum": 90},
        "area_mm2": NUMBER,
        "bearing_kn": NONNEGATIVE,
        "bearing_length_mm": NUMBER,
        "distance_from_end_mm": {"type": "number", "minimum": 0, "maximum": 1e9},
        "rectangular_bearing_verified": {"const": True},
    },
}

COMBINED_COMPRESSION_INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "material",
        "section",
        "moment_major_knm",
        "compression_kn",
        "beam_restraint",
        "column_restraint",
    ],
    "properties": {
        **deepcopy(COMMON_MATERIAL_AND_SECTION),
        "moment_major_knm": NONNEGATIVE,
        "compression_kn": NONNEGATIVE,
        "beam_restraint": BEAM_RESTRAINT_SCHEMA,
        "column_restraint": COLUMN_RESTRAINT_SCHEMA,
    },
}

COMBINED_TENSION_INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "material",
        "section",
        "net_area_mm2",
        "moment_major_knm",
        "tension_kn",
        "beam_restraint",
    ],
    "properties": {
        **deepcopy(COMMON_MATERIAL_AND_SECTION),
        "net_area_mm2": NUMBER,
        "moment_major_knm": NONNEGATIVE,
        "tension_kn": NONNEGATIVE,
        "beam_restraint": BEAM_RESTRAINT_SCHEMA,
    },
}

CHECK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "clause",
        "name",
        "unit",
        "demand_value",
        "limit_value",
        "utilisation",
        "satisfied",
        "details",
    ],
    "properties": {
        "clause": {"type": "string"},
        "name": {"type": "string"},
        "unit": {"enum": ["kN", "kN·m", "ratio"]},
        "demand_value": {"type": "number"},
        "limit_value": {"type": "number", "exclusiveMinimum": 0},
        "utilisation": {"type": "number"},
        "satisfied": {"type": "boolean"},
        "details": {"type": "object"},
    },
}

OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "standard",
        "operation",
        "checks",
        "factors",
        "clauses",
        "warnings",
        "full_standard_compliance",
        "standard_compliance_evaluated",
    ],
    "properties": {
        "standard": {"const": "AS 1720.1:2010 Amd 3:2015"},
        "operation": {"type": "string"},
        "checks": {"type": "array", "items": CHECK_SCHEMA},
        "factors": {"type": "object"},
        "clauses": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "full_standard_compliance": {"const": False},
        "standard_compliance_evaluated": {"const": False},
    },
}
