
from itertools import product
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from perfrec.retrieve.search import search

WHEEL = ["Fresh", "Floral", "Amber", "Woody"]   # circular order on the fragrance wheel


def harmony(fam_a, fam_b):
    if fam_a not in WHEEL or fam_b not in WHEEL:
        return 0.5
    if fam_a == fam_b:
        return 1.0
    i, j = WHEEL.index(fam_a), WHEEL.index(fam_b)
    dist = min((i - j) % 4, (j - i) % 4)   # 1 = adjacent, 2 = opposite
    return {1: 0.8, 2: 0.5}[dist]


def jaccard(a, b):
    A, B = set(a), set(b)
    return len(A & B) / len(A | B) if A and B else 0.0


def bridge(a, b):
    j = jaccard(a, b)
    return max(0.0, 1.0 - abs(j - 0.3) / 0.7)


BRIGHT = {"Fresh", "Floral"}
DEEP   = {"Woody", "Amber"}
# expert-validated accord pairings (Perfume Cultures layering guide)
GOOD_RECIPES = [
    ({"citrus"},                         {"woody", "sandalwood", "cedar"}),
    ({"vanilla", "sweet"},               {"warm spicy", "soft spicy", "fresh spicy", "cinnamon"}),
    ({"fresh", "aromatic", "green"},     {"musky"}),
    ({"gourmand", "sweet"},              {"smoky"}),
    ({"floral", "white floral", "yellow floral"}, {"leather", "leathery"}),
    ({"aquatic", "marine", "ozonic"},    {"amber"}),
]

def recipe_bonus(acc_a, acc_b):
    A, B = set(acc_a), set(acc_b)
    for s1, s2 in GOOD_RECIPES:
        if (A & s1 and B & s2) or (A & s2 and B & s1):
            return 1.0     # this pair matches an expert-recommended combination
    return 0.0


def layering_harmony(lifter_fam, anchor_fam):
    # layering works best as a BRIGHT lifter over a DEEP anchor
    if lifter_fam in BRIGHT and anchor_fam in DEEP: return 1.0   # classic bright-over-deep
    if lifter_fam in DEEP and anchor_fam in BRIGHT: return 0.8
    if lifter_fam == anchor_fam: return 0.5                       # same family = redundant
    return 0.7



# in pair_score — reward a strong anchor + a present-but-light lifter (best ~0.45)
def pair_score(anchor, lifter):
    a, l = anchor.payload, lifter.payload
    anchor_str = a["longevity"]
    lifter_fit = max(0.0, 1.0 - abs(l["longevity"] - 0.45) / 0.55)
    role   = 0.5 * anchor_str + 0.5 * lifter_fit
    harm   = layering_harmony(l["family"], a["family"])
    brdg   = bridge(a["accords"], l["accords"])
    clim   = 0.5 * (a["climate_hot_humid"] + l["climate_hot_humid"])
    recipe = recipe_bonus(a["accords"], l["accords"])          # NEW
    total  = 0.22*role + 0.18*harm + 0.13*brdg + 0.17*clim + 0.30*recipe
    return round(total, 3), {"role": round(role,2), "harmony": harm, "bridge": round(brdg,2),
                             "climate": round(clim,2), "recipe": recipe}
def suggest_layers(query, top=5):
    from itertools import product
    # two deliberately different pools
    lifters = search(query + " fresh light bright citrus", min_climate=0.6, limit=15)
    anchors = search(query + " long lasting deep woody amber musk base", min_longevity=0.8, limit=15)
    # keep lifters that are light but still PRESENT (drops the 0.0 vanishers)
    lifters = [h for h in lifters if 0.3 <= h.payload["longevity"] < 0.7]

    pairs = []
    for anc, lif in product(anchors, lifters):
        if anc.id == lif.id:
            continue
        score, parts = pair_score(anc, lif)
        pairs.append((score, anc, lif, parts))
    pairs.sort(key=lambda x: x[0], reverse=True)
    return pairs[:top]




def application_tip(anchor, lifter):
    return (f"~3 sprays {lifter.payload['name']} (accent) to ~1 spray {anchor.payload['name']} "
            f"(base). Base on pulse points (neck) where body heat lifts it; accent on wrists/chest — "
            f"or mist the accent in the air and walk through it for a softer blend. "
            f"Judge it after 20–30 min, not immediately; it'll smell different on your skin than anyone else's.")


if __name__ == "__main__":
    q = "fresh compliment-getter for hot humid Delhi weather"
    print("\n=== TOP LAYERING PAIRS ===\n")
    for score, anc, lif, parts in suggest_layers(q):
        print(f"{score}  {lif.payload['name']}  +  {anc.payload['name']}   {parts}")
        print("   ", application_tip(anc, lif), "\n")
