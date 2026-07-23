"""The user's body, goal and — load-bearingly — their clinical flags.

Lives in ``core/schemas`` because three packages need it and it may depend on
none of them (CLAUDE.md, "Architecture"): ``core/nutrition`` will derive
targets from the body fields, ``core/planner`` reads ``clinical_flags`` to
decide which constraints the relaxation ladder may never touch, and ``api/``
accepts it over HTTP.

## Why ``clinical_flags`` is an enum and not free text

The flag is not a label shown back to the user — it is the key that locks a
constraint out of ``core/planner/validator.RELAXATION_ORDER``. A free-text
field would mean a typo ("hypertenson") silently produces a profile whose
sodium ceiling *does* relax, with no error anywhere, which is the failure mode
this whole project is organised around: a safety mechanism that quietly
degrades to no mechanism. An unrecognised enum value fails at construction.

The body fields needed to derive an energy target are modelled, plus ``diet``:
protein quality (DIAAS) varies by diet pattern, so ``core/nutrition/targets``
must read it to inflate the gram target for lower-quality-protein diets — a
vegan hitting a protein number on plant sources needs more grams than a
non-vegetarian to deliver the same utilisable protein. ``diet`` is therefore a
target-math input, not merely a later candidate-filtering key. Only the
``DietPattern`` enum is carried here; allergens and region preferences wait for
``core/planner``, which has nothing to filter against yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from core.schemas.common import DietPattern


class ClinicalFlag(str, Enum):
    """A disclosed medical condition that hard-locks a dietary constraint.

    Not a diagnosis and not exhaustive — this is a portfolio project, and
    ``docs/methodology.md`` says plainly that it is not a substitute for
    clinical nutrition guidance. Each member exists because it maps to a
    specific constraint the relaxation ladder must refuse to loosen, not
    because it is a clinically interesting condition in general. A condition
    with no such mapping does not belong here; adding one without wiring it
    into ``validator.LOCKED_CONSTRAINTS`` would produce a flag that reads as
    protective and does nothing.
    """

    HYPERTENSION = "hypertension"
    CHRONIC_KIDNEY_DISEASE = "chronic_kidney_disease"
    DIABETES = "diabetes"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class Goal(str, Enum):
    LOSE_FAT = "lose_fat"
    MAINTAIN = "maintain"
    GAIN_MUSCLE = "gain_muscle"


class Sex(str, Enum):
    """Used only as the Mifflin-St Jeor equation's constant term.

    Named ``Sex`` rather than ``gender`` because the equation is fitted on
    measured body composition, which is what the term stands in for; it is not
    a claim about identity, and nothing outside the BMR calculation reads it.
    """

    MALE = "male"
    FEMALE = "female"


@dataclass(frozen=True)
class Profile:
    """One user's inputs to target derivation.

    Raises on impossible input and records implausible-but-valid input in
    ``warnings`` rather than clamping silently (CLAUDE.md, "Errors").
    """

    weight_kg: float
    height_cm: float
    age_years: int
    sex: Sex
    activity: ActivityLevel
    goal: Goal
    #: Read by ``core/nutrition/targets`` to quality-adjust the protein target
    #: (DIAAS varies by pattern), not only by a later candidate filter.
    diet: DietPattern
    clinical_flags: frozenset[ClinicalFlag] = frozenset()
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name, value in (
            ("weight_kg", self.weight_kg),
            ("height_cm", self.height_cm),
            ("age_years", self.age_years),
        ):
            if value <= 0:
                raise ValueError(f"Profile.{name} must be positive, got {value!r}")

        warnings = list(self.warnings)
        # Bounds chosen to be well outside any plausible adult, so these fire
        # on data-entry errors (cm entered as m, kg as lb) rather than on
        # genuinely unusual bodies. They warn rather than raise for exactly
        # that reason: an unusual body is valid input.
        if not 25.0 <= self.weight_kg <= 250.0:
            warnings.append(
                f"weight_kg={self.weight_kg} is outside the usual adult range; "
                "targets derived from it may be unreliable"
            )
        if not 120.0 <= self.height_cm <= 220.0:
            warnings.append(
                f"height_cm={self.height_cm} is outside the usual adult range; "
                "check the units"
            )
        if not 18 <= self.age_years <= 90:
            warnings.append(
                f"age_years={self.age_years} is outside the range the target "
                "equations were fitted on (adults 18-90)"
            )
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "clinical_flags", frozenset(self.clinical_flags))

    def has_flag(self, flag: ClinicalFlag) -> bool:
        return flag in self.clinical_flags
