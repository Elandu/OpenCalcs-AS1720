"""Reviewed edition metadata and selected tabular design values."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StandardReference:
    code: str = "AS 1720.1"
    edition: str = "2010"
    title: str = "Timber structures"

    def descriptor(self) -> dict[str, str]:
        return {
            "code": self.code,
            "edition": self.edition,
            "title": self.title,
            "amendments": "Amendments 1, 2 and 3 (Amd 3:2015)",
        }


STANDARD = StandardReference()

# AS 1720.1:2010 Table H2.1, F-grade values. Values are MPa except E and G.
F_GRADE_PROPERTIES = {
    "F34": {
        "bending": 84.0,
        "tension_hardwood": 51.0,
        "tension_softwood": 42.0,
        "shear": 6.1,
        "compression": 63.0,
        "elastic_modulus": 21_500.0,
        "shear_modulus": 1_430.0,
    },
    "F27": {
        "bending": 67.0,
        "tension_hardwood": 42.0,
        "tension_softwood": 34.0,
        "shear": 5.1,
        "compression": 51.0,
        "elastic_modulus": 18_500.0,
        "shear_modulus": 1_230.0,
    },
    "F22": {
        "bending": 55.0,
        "tension_hardwood": 34.0,
        "tension_softwood": 29.0,
        "shear": 4.2,
        "compression": 42.0,
        "elastic_modulus": 16_000.0,
        "shear_modulus": 1_070.0,
    },
    "F17": {
        "bending": 42.0,
        "tension_hardwood": 25.0,
        "tension_softwood": 22.0,
        "shear": 3.6,
        "compression": 34.0,
        "elastic_modulus": 14_000.0,
        "shear_modulus": 930.0,
    },
    "F14": {
        "bending": 36.0,
        "tension_hardwood": 22.0,
        "tension_softwood": 19.0,
        "shear": 3.3,
        "compression": 27.0,
        "elastic_modulus": 12_000.0,
        "shear_modulus": 800.0,
    },
    "F11": {
        "bending": 31.0,
        "tension_hardwood": 18.0,
        "tension_softwood": 15.0,
        "shear": 2.8,
        "compression": 22.0,
        "elastic_modulus": 10_500.0,
        "shear_modulus": 700.0,
    },
    "F8": {
        "bending": 22.0,
        "tension_hardwood": 13.0,
        "tension_softwood": 12.0,
        "shear": 2.2,
        "compression": 18.0,
        "elastic_modulus": 9_100.0,
        "shear_modulus": 610.0,
    },
    "F7": {
        "bending": 18.0,
        "tension_hardwood": 11.0,
        "tension_softwood": 8.9,
        "shear": 1.9,
        "compression": 13.0,
        "elastic_modulus": 7_900.0,
        "shear_modulus": 530.0,
    },
    "F5": {
        "bending": 14.0,
        "tension_hardwood": 9.0,
        "tension_softwood": 7.3,
        "shear": 1.6,
        "compression": 11.0,
        "elastic_modulus": 6_900.0,
        "shear_modulus": 460.0,
    },
    "F4": {
        "bending": 12.0,
        "tension_hardwood": 7.0,
        "tension_softwood": 5.8,
        "shear": 1.3,
        "compression": 8.6,
        "elastic_modulus": 6_100.0,
        "shear_modulus": 410.0,
    },
}

# AS 1720.1:2010 Table 3.1, seasoned / unseasoned.
BEAM_RHO = {
    "F34": (1.12, 1.21),
    "F27": (1.08, 1.17),
    "F22": (1.05, 1.15),
    "F17": (0.98, 1.08),
    "F14": (0.98, 1.08),
    "F11": (0.98, 1.07),
    "F8": (0.89, 0.99),
    "F7": (0.86, 0.96),
    "F5": (0.82, 0.91),
    "F4": (0.80, 0.90),
}

# AS 1720.1:2010 Table 3.3, seasoned / unseasoned.
COLUMN_RHO = {
    "F34": (1.17, 1.34),
    "F27": (1.14, 1.31),
    "F22": (1.12, 1.28),
    "F17": (1.08, 1.25),
    "F14": (1.05, 1.21),
    "F11": (1.02, 1.18),
    "F8": (1.00, 1.16),
    "F7": (0.92, 1.08),
    "F5": (0.91, 1.07),
    "F4": (0.87, 1.02),
}

# AS 1720.1:2010 Table 2.3 timber strength load-duration values.
K1 = {
    "5_seconds": 1.00,
    "5_minutes": 1.00,
    "5_hours": 0.97,
    "5_days": 0.94,
    "5_months": 0.80,
    "50_plus_years": 0.57,
}

# AS 1720.1:2010 Table 2.1; category order 1, 2, 3.
PHI_HIGH_GRADE = (0.95, 0.85, 0.75)
PHI_OTHER_GRADE = (0.90, 0.70, 0.60)

# AS 1720.1:2010 Table H2.2: f'p and f'l in MPa.
BEARING_PROPERTIES = {
    "SD1": (26.0, 76.0),
    "SD2": (23.0, 67.0),
    "SD3": (19.0, 59.0),
    "SD4": (17.0, 51.0),
    "SD5": (13.0, 40.0),
    "SD6": (10.0, 30.0),
    "SD7": (8.6, 23.0),
    "SD8": (6.8, 20.0),
    "S1": (17.0, 51.0),
    "S2": (13.0, 40.0),
    "S3": (10.0, 30.0),
    "S4": (8.6, 23.0),
    "S5": (6.8, 20.0),
    "S6": (5.5, 17.0),
    "S7": (4.4, 13.0),
}

# AS 1720.1:2010 Table 2.6. Other lengths use no enhancement in this module.
K7_EXACT_BEARING_LENGTH = {12.0: 1.75, 25.0: 1.40, 50.0: 1.20, 75.0: 1.15, 125.0: 1.10}
K7_LONG_BEARING_LENGTH_MM = 150.0

# AS 1720.1:2010 Table 3.2, selected restraint condition / g13.
G13 = {
    "flat_ends": 0.70,
    "fixed_both_ends": 0.70,
    "two_bolts_each_end": 0.75,
    "one_end_fixed_other_position": 0.85,
    "light_framing_studs": 0.90,
    "position_both_ends": 1.00,
    "fixed_one_end_partial_direction_other": 1.50,
    "fixed_one_end_free_other": 2.00,
}
