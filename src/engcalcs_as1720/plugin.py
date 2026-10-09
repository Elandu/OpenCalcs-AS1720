"""EngCalcs entry point and calculation descriptors."""

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from engcalcs_as1720 import __version__
from engcalcs_as1720.calculations import (
    run_beam_design,
    run_bearing_design,
    run_column_design,
    run_combined_compression,
    run_combined_tension,
    run_tension_design,
)
from engcalcs_as1720.schemas import (
    BEAM_INPUT_SCHEMA,
    BEARING_INPUT_SCHEMA,
    COLUMN_INPUT_SCHEMA,
    COMBINED_COMPRESSION_INPUT_SCHEMA,
    COMBINED_TENSION_INPUT_SCHEMA,
    OUTPUT_SCHEMA,
    TENSION_INPUT_SCHEMA,
)
from engcalcs_as1720.standards import STANDARD, StandardReference


@dataclass(frozen=True)
class Calculation:
    id: str
    name: str
    description: str
    input_schema: dict[str, Any]
    runner: Callable[[Mapping[str, Any]], dict[str, Any]]
    version: str = "1"
    standard: StandardReference = STANDARD
    output_schema: dict[str, Any] = field(default_factory=lambda: deepcopy(OUTPUT_SCHEMA))

    def run(self, inputs: Mapping[str, Any]) -> dict[str, Any]:
        return self.runner(inputs)

    def descriptor(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "discipline": "structural",
            "category": "timber-design",
            "jurisdiction": "AU",
            "version": self.version,
            "standard": self.standard.descriptor(),
            "input_schema": deepcopy(self.input_schema),
            "output_schema": deepcopy(self.output_schema),
        }


def _calculations() -> tuple[Calculation, ...]:
    common = (
        "Selected strength checks for unnotched rectangular solid-sawn F-grade timber; "
        "not a full standard-compliance assessment."
    )
    return (
        Calculation(
            "structural.as1720.beam_design",
            "F-grade beam strength",
            f"{common} Bending, biaxial interaction and flexural shear.",
            deepcopy(BEAM_INPUT_SCHEMA),
            run_beam_design,
        ),
        Calculation(
            "structural.as1720.column_design",
            "F-grade column compression",
            f"{common} Compression stability about both principal axes.",
            deepcopy(COLUMN_INPUT_SCHEMA),
            run_column_design,
        ),
        Calculation(
            "structural.as1720.tension_design",
            "F-grade tension member",
            f"{common} Axial tension parallel to grain.",
            deepcopy(TENSION_INPUT_SCHEMA),
            run_tension_design,
        ),
        Calculation(
            "structural.as1720.bearing_design",
            "Timber bearing strength",
            "Selected F-grade timber bearing checks using a declared Appendix H strength group.",
            deepcopy(BEARING_INPUT_SCHEMA),
            run_bearing_design,
        ),
        Calculation(
            "structural.as1720.combined_compression",
            "Combined bending and compression",
            (
                "AS 1720.1 Clause 3.5.1 interaction checks, with bending and column "
                "capacities calculated from the supplied member inputs."
            ),
            deepcopy(COMBINED_COMPRESSION_INPUT_SCHEMA),
            run_combined_compression,
        ),
        Calculation(
            "structural.as1720.combined_tension",
            "Combined bending and tension",
            (
                "AS 1720.1 Clause 3.5.2 interaction checks, with bending and tension "
                "capacities calculated from the supplied member inputs."
            ),
            deepcopy(COMBINED_TENSION_INPUT_SCHEMA),
            run_combined_tension,
        ),
    )


@dataclass(frozen=True)
class AS1720Plugin:
    id: str = "structural.as1720"
    name: str = "EngCalcs Timber Design"
    version: str = __version__
    revision: str | None = None
    license: str = "AGPL-3.0-only"
    source: str = "https://github.com/Elandu/OpenCalcs-AS1720"
    calculations: tuple[Calculation, ...] = field(default_factory=_calculations)

    def descriptor(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "revision": self.revision,
            "license": self.license,
            "source": self.source,
            "calculations": [calculation.descriptor() for calculation in self.calculations],
        }


def get_plugin() -> AS1720Plugin:
    """Return the plugin descriptor without starting a service or analysis solver."""
    return AS1720Plugin()
