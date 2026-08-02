"""Which lines actually carry each macro? Decides where an authored-quantity band bites."""
from __future__ import annotations

from core.planner.plan import load_library

DISCRETIONARY = {
    "salt_iodised", "sunflower_oil", "gingelly_oil", "ghee", "mustard_seed",
    "cumin_seed", "garam_masala", "turmeric", "red_chilli_powder",
    "ginger_garlic_paste", "green_chilli", "curry_leaf", "coriander_leaf",
    "asafoetida", "tamarind", "sambar_powder", "urad_dal_raw",
}
MACROS = ("energy_kcal", "protein_g", "fat_g", "carb_g", "sodium_mg")

lib = load_library()
for rid, recipe in sorted(lib.recipes.recipes.items()):
    totals = {m: 0.0 for m in MACROS}
    disc = {m: 0.0 for m in MACROS}
    mass = disc_mass = 0.0
    for line in recipe.ingredients:
        v = lib.ingredients[line.ingredient_id].for_grams(line.quantity_g)
        mass += line.quantity_g
        is_disc = line.ingredient_id in DISCRETIONARY
        if is_disc:
            disc_mass += line.quantity_g
        for m in MACROS:
            totals[m] += getattr(v, m)
            if is_disc:
                disc[m] += getattr(v, m)
    print(f"{rid:<14} mass {disc_mass:5.1f}/{mass:6.1f} = {disc_mass/mass:5.1%}  " + "  ".join(
        f"{m.split('_')[0]}={disc[m]/totals[m]:5.1%}" if totals[m] else f"{m.split('_')[0]}=  n/a"
        for m in MACROS))
    for line in recipe.ingredients:
        if line.ingredient_id in DISCRETIONARY:
            print(f"                 - {line.ingredient_id:<22} {line.quantity_g:6.2f} g")
