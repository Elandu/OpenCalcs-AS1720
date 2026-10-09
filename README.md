# EngCalcs AS 1720.1

An installable EngCalcs plugin for selected strength checks to AS 1720.1:2010 incorporating Amendments 1, 2 and 3. It currently covers unnotched rectangular solid-sawn F-grade timber members: beam bending and shear, column compression stability, axial tension, bearing, and the standard's combined bending/axial interaction checks.

This is a bounded calculation tool. A passing result means only that the listed strength checks pass for the supplied design actions, material classification, geometry and restraint assumptions. It does not establish compliance of a member, connection, structure, or project with all of AS 1720.1 or other applicable standards.

## Install

```powershell
python -m pip install .
```

EngCalcs discovers the plugin through the `engcalcs.plugins` entry point. The package has no structural-analysis solver dependency.

## Calculations

| Calculation ID | Checks | Principal provisions |
|---|---|---|
| `structural.as1720.beam_design` | Major/minor-axis bending, biaxial interaction, flexural shear | 3.2.1, 3.2.3–3.2.5; Tables 3.1, H2.1 |
| `structural.as1720.column_design` | Compression capacity about both axes | 3.3.1–3.3.3; Tables 3.2, 3.3, H2.1 |
| `structural.as1720.tension_design` | Tension parallel to grain | 3.4.1; Table H2.1 |
| `structural.as1720.bearing_design` | Bearing at an angle to grain | 2.4.2–2.4.4, 3.2.6; Tables 2.1, 2.3, 2.5, 2.6, H2.2 |
| `structural.as1720.combined_compression` | Bending with compression, both interaction equations | 3.5.1 |
| `structural.as1720.combined_tension` | Bending with tension, both interaction equations | 3.5.2 |

Inputs and reported capacities use mm, MPa, kN and kN·m; interaction results identify themselves as ratios. The input schemas and runnable cases in `examples/` show the required fields. The restraint inputs represent engineering assumptions that must be verified for the actual member and support system.

## Source and verification

The implementation was checked against the licensed AS 1720.1:2010 text incorporating Amendments 1–3, including the cited clauses and tables. Standards Australia lists AS 1720.1:2010 Amd 3:2015 as pending revision: https://store.standards.org.au/product/as-1720-1-2010. The standard contains tabulated properties and a numerical parallel-system illustration, but no worked numerical beam or column design example. `docs/verification.md` therefore identifies the source-based worked cases as independently hand-calculated verification examples; it does not present them as published examples from the standard.

Licensed standard PDFs, extracted text, OCR and page images are not included in this repository. Refer to the official publication for the complete requirements.

## Scope limits

Not included: serviceability and deflection; load combinations or structural analysis; connections and joints; notched, spaced, round, plywood, glulam or LVL members; biaxial beam-column cases beyond the listed AS 1720.1 equations; Appendix E higher-order methods; strength-sharing between parallel members; or project-level compliance assessment. The bending calculation uses `k9 = 1.0` for an isolated member. It does not award strength-sharing credit.

The user remains responsible for the governing edition, material identification and grading evidence, design actions, load duration, service moisture and exposure, restraint and effective lengths, support and bearing details, and all checks outside this plugin's stated scope.

## License

AGPL-3.0-only. See `LICENSE`.
