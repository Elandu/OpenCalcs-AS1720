# Provision coverage and source trace

## Reviewed edition

AS 1720.1:2010, incorporating Amendments 1, 2 and 3 (Amd 3:2015). Standards Australia lists this publication as pending revision. Reconfirm the governing edition and amendment status for each project. The licensed source was reviewed locally; this repository contains only selected numerical material properties, equations implemented in code, clause identifiers and this coverage map.

## Included checks

| Feature | Implemented provision | Implementation note |
|---|---|---|
| Design capacity form and member capacity factors | 2.1.2, 2.3, Table 2.1 | F17 and higher vs lower F-grades; category 1–3 |
| Strength load duration | 2.4.1, Table 2.3 | Timber k1 entries for the six listed durations |
| Moisture modification | 2.4.2, Table 2.5 | Seasoned EMC reduction; optional partial seasoning for unseasoned timber |
| Regional modification | 2.4.3 | k6 = 0.9 only when the supplied flag identifies the standard's seasoned-timber region |
| Bearing length enhancement | 2.4.4, Table 2.6 | Exact tabulated lengths only; otherwise k7 = 1.0 |
| Beam bending and biaxial interaction | 3.2.1, Table 3.1, Table H2.1 | Rectangular major/minor section moduli; size reduction above table limits |
| Beam stability | 3.2.3–3.2.4, Table 3.1 | Discrete edge-restraint equations or continuous-restraint check under Eq. 3.2(6) |
| Beam shear | 3.2.5, Table H2.1 | Unnotched rectangular major-axis beam shear area |
| Column compression | 3.3.1–3.3.3, Tables 3.2–3.3, Table H2.1 | Both principal axes; discrete or specified continuous lateral restraint |
| Tension parallel to grain | 3.4.1, Table H2.1 | Net area; size reduction when the largest cross-section dimension exceeds 150 mm |
| Bearing at angle to grain | 3.2.6, Table H2.2 | Declared strength group; Hankinson interpolation; perpendicular k7 where eligible |
| Combined actions | 3.5.1–3.5.2 | Both listed compression equations and both listed tension equations |

## Inputs that require engineering judgement

- Select a stress grade from grading evidence and a timber type (hardwood or softwood). These are not inferred from a species name.
- Select design category, the governing shortest load duration, service moisture information, and whether the regional k6 condition applies.
- Supply design action effects from the governing load combinations. This package does not generate combinations or analyse a structure.
- Confirm beam restraint spacing and whether the compression or tension edge is restrained. For continuous restraint, the calculation checks the supplied spacing against Eq. 3.2(6).
- Confirm column end conditions and effective restraint spacings. A continuous major-axis restraint means the Eq. 3.3(7) case; a continuous minor-axis restraint uses Eq. 3.3(10).
- For bearing, identify the Appendix H strength group for the same moisture condition and verify the rectangular contact area and end distance.
- Confirm member geometry is unnotched and rectangular, and provide net tension area where applicable.

## Explicit exclusions

No serviceability or deflection assessment, load combinations, analysis, joints, notches, spaced columns, strength-sharing credit, nonrectangular members, Appendix E higher-order methods, plywood, round timber, glulam or LVL. Strength sharing is deliberately held at k9 = 1.0 for an isolated member. A result marked satisfied applies only to the reported checks.

## Source table storage

Selected F-grade strength/modulus values (Table H2.1), stability constants (Tables 3.1 and 3.3), bearing properties (Table H2.2), duration factors (Table 2.3), end factors (Table 3.2), and bearing factors (Table 2.6) are encoded in `src/opencalcs_as1720/standards.py`. The licensed standard, text extracts, OCR, and page renders are not distributed here.
