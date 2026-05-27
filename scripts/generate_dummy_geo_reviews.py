"""
Generate Dummy Geo Reviews

Creates realistic review data for a random 37% sample of
detections.N-dse.dummy-geo.csv. Each reviewed row gets an
is_valid decision, optional species correction, reviewer
assignment, notes, and review date.

Output: outputs/model_review.N-dse.dummy-geo.csv

License: BSD 3-Clause
"""
import csv
import random


#
# CONSTANTS
#
INPUT_PATH = "data/detections.N-dse.dummy-geo.csv"
OUTPUT_PATH = "outputs/model_review.N-dse.dummy-geo.csv"
SAMPLE_RATE = 0.37
SEED = 42

OUTPUT_COLUMNS = [
    "detection_id", "start_time", "end_time",
    "is_valid", "verified_common_name", "verification_confidence",
    "notes", "reviewer_name", "review_date",
]

REVIEWERS = {
    "brookie": {"weight": 0.30, "accuracy": 0.92, "notes_rate": 0.40, "bias": "high"},
    "alex":    {"weight": 0.20, "accuracy": 0.88, "notes_rate": 0.30, "bias": "medium"},
    "sam":     {"weight": 0.20, "accuracy": 0.85, "notes_rate": 0.50, "bias": "medium"},
    "jordan":  {"weight": 0.20, "accuracy": 0.90, "notes_rate": 0.20, "bias": "high"},
    "casey":   {"weight": 0.10, "accuracy": 0.83, "notes_rate": 0.60, "bias": "low"},
}

REVIEWER_NAMES = list(REVIEWERS.keys())
REVIEWER_WEIGHTS = [REVIEWERS[n]["weight"] for n in REVIEWER_NAMES]

CONFUSION_MAP = {
    "Common Poorwill": ["Common Nighthawk", "Western Screech-Owl"],
    "Hermit Thrush": ["Spotted Towhee", "Song Thrush"],
    "Spotted Towhee": ["California Towhee", "Collared Towhee"],
    "Pacific-slope Flycatcher": ["Gray Flycatcher", "Cordilleran Flycatcher"],
    "Great Horned Owl": ["Barn Owl", "Long-eared Owl"],
    "California Towhee": ["Spotted Towhee", "Canyon Towhee"],
    "Tree Swallow": ["Violet-green Swallow", "Barn Owl"],
    "Wrentit": ["Bushtit", "Bewick's Wren"],
    "Engine": ["Fireworks", "Engine"],
}

POSITIVE_NOTES = [
    "Clear recording", "Good example", "Strong vocalization",
    "Typical call pattern", "Confirmed with visual",
]
UNCERTAIN_NOTES = [
    "Some background noise", "Faint call", "Partially obscured by wind",
    "Dawn chorus interference", "Distant call", "Multiple species present",
    "Uncertain - needs second review",
]
NEGATIVE_NOTES = [
    "Wrong habitat for species", "Call pattern doesn't match",
    "Frequency range incorrect", "Likely mechanical noise",
    "Different species entirely",
]
CONTEXT_NOTES = [
    "Breeding season call", "Juvenile begging calls", "Alarm call",
    "Flight call", "Contact call", "Territorial song",
]

REVIEW_DATES = [f"2026052{d}" for d in range(2, 8)]

CONFIDENCE_WEIGHTS = {
    "high":   {"low": 0.1, "medium": 0.3, "high": 0.6},
    "medium": {"low": 0.3, "medium": 0.4, "high": 0.3},
    "low":    {"low": 0.5, "medium": 0.4, "high": 0.1},
}


#
# PUBLIC
#
def main() -> None:
    """Sample rows, generate reviews, write output."""
    random.seed(SEED)

    with open(INPUT_PATH) as f:
        rows = list(csv.DictReader(f))

    species_list = list({r["common_name"] for r in rows})
    species_accuracy = _build_species_accuracy(species_list)

    sampled = [r for r in rows if random.random() < SAMPLE_RATE]
    print(f"Sampled {len(sampled)} / {len(rows)} rows ({len(sampled)/len(rows):.0%})")

    reviews: list[dict[str, str]] = []
    for row in sampled:
        reviews.append(_generate_review(row, species_accuracy, species_list))

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(reviews)

    _print_stats(reviews)
    print(f"\nSaved to {OUTPUT_PATH}")


#
# INTERNAL
#
def _build_species_accuracy(species_list: list[str]) -> dict[str, float]:
    """Assign each species a model accuracy profile."""
    acc: dict[str, float] = {}
    for sp in species_list:
        r = random.random()
        if r < 0.3:
            acc[sp] = random.uniform(0.85, 0.95)
        elif r < 0.6:
            acc[sp] = random.uniform(0.60, 0.85)
        else:
            acc[sp] = random.uniform(0.30, 0.60)
    return acc


def _generate_review(
    row: dict[str, str],
    species_accuracy: dict[str, float],
    species_list: list[str],
) -> dict[str, str]:
    """Generate a single review row."""
    species = row["common_name"]
    confidence = float(row.get("confidence", 0.5))

    reviewer_name = random.choices(REVIEWER_NAMES, weights=REVIEWER_WEIGHTS)[0]
    reviewer = REVIEWERS[reviewer_name]

    sp_acc = species_accuracy.get(species, 0.7)
    if confidence > 0.8:
        is_correct = random.random() < min(sp_acc * 1.2, 1.0)
    elif confidence < 0.4:
        is_correct = random.random() < sp_acc * 0.7
    else:
        is_correct = random.random() < sp_acc

    if random.random() > reviewer["accuracy"]:
        is_correct = not is_correct

    if is_correct:
        is_valid = "yes"
        verified = ""
        ver_conf = ""
        notes = _pick_notes_valid(confidence, reviewer["notes_rate"])
    else:
        is_valid = "no"
        verified = _pick_correction(species, species_list)
        ver_conf = _pick_confidence(reviewer["bias"])
        notes = _pick_notes_invalid(verified, ver_conf, reviewer["notes_rate"])

    return {
        "detection_id": row["id"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "is_valid": is_valid,
        "verified_common_name": verified,
        "verification_confidence": ver_conf,
        "notes": notes,
        "reviewer_name": reviewer_name,
        "review_date": random.choice(REVIEW_DATES),
    }


def _pick_correction(species: str, species_list: list[str]) -> str:
    """Pick a corrected species name."""
    if species in CONFUSION_MAP and random.random() < 0.7:
        return random.choice(CONFUSION_MAP[species])
    others = [s for s in species_list if s != species]
    return random.choice(others) if others else species


def _pick_confidence(bias: str) -> str:
    """Pick verification confidence based on reviewer bias."""
    w = CONFIDENCE_WEIGHTS[bias]
    return random.choices(
        ["low", "medium", "high"],
        weights=[w["low"], w["medium"], w["high"]],
    )[0]


def _pick_notes_valid(confidence: float, notes_rate: float) -> str:
    """Pick notes for a valid review."""
    if random.random() >= notes_rate:
        return ""
    if confidence > 0.8:
        return random.choice(POSITIVE_NOTES + CONTEXT_NOTES)
    return random.choice(UNCERTAIN_NOTES + CONTEXT_NOTES)


def _pick_notes_invalid(
    verified: str,
    ver_conf: str,
    notes_rate: float,
) -> str:
    """Pick notes for an invalid review."""
    if random.random() >= notes_rate * 1.5:
        return ""
    if ver_conf == "high":
        return random.choice(
            NEGATIVE_NOTES + [f"Definitely {verified}", "Clear misidentification"],
        )
    return random.choice(
        UNCERTAIN_NOTES + [f"Possibly {verified}", "Not sure but likely wrong"],
    )


def _print_stats(reviews: list[dict[str, str]]) -> None:
    """Print summary statistics."""
    total = len(reviews)
    valid = sum(1 for r in reviews if r["is_valid"] == "yes")
    invalid = total - valid
    with_notes = sum(1 for r in reviews if r["notes"])

    print(f"\nGenerated {total} reviews")
    print(f"  Valid:   {valid} ({valid/total:.1%})")
    print(f"  Invalid: {invalid} ({invalid/total:.1%})")
    print(f"  Notes:   {with_notes} ({with_notes/total:.1%})")

    print("\nReviewer distribution:")
    for name in REVIEWER_NAMES:
        count = sum(1 for r in reviews if r["reviewer_name"] == name)
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
