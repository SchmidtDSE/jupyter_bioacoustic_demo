import csv
import random

random.seed(42)

DET_PATH = "data/detections.N-dse.csv"
SPC_PATH = "data/species_counts.N-dse.csv"
OUT_PATH = "outputs/simple_annotator.csv"
DATES = ["20260522", "20260523", "20260524", "20260525", "20260526", "20260527"]
SPECIES_MATCH_RATE = 0.88
FREQ_NULL_RATE = 0.5


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def main():
    det = load_csv(DET_PATH)
    spc = load_csv(SPC_PATH)
    species_list = [r["common_name"] for r in spc]

    indices = list(range(8))
    pool_a = list(range(10, 100))
    pool_b = list(range(100, min(200, len(det))))
    random.shuffle(pool_a)
    random.shuffle(pool_b)
    indices += sorted(pool_a[: int(len(pool_a) * 0.6)])
    indices += sorted(pool_b[: int(len(pool_b) * 0.3)])

    rows = []
    for i in indices:
        row = det[i]
        species = row["common_name"] if random.random() < SPECIES_MATCH_RATE else random.choice(species_list)
        src_start = float(row["start_time"])
        src_end = float(row["end_time"])
        duration = src_end - src_start
        if duration > 1:
            new_start = round(src_start + random.random() * (duration - 1), 2)
            new_end = round(new_start + 1 + random.random() * (src_end - new_start - 1), 2)
        else:
            new_start = round(src_start, 2)
            new_end = round(src_end, 2)

        if random.random() < FREQ_NULL_RATE:
            min_freq, max_freq = "", ""
        else:
            min_freq = round(random.random() * 500, 1)
            max_freq = round(2000 + random.random() * 6000, 1)

        rows.append({
            "species": species,
            "detection_id": row["id"],
            "start_time": new_start,
            "end_time": new_end,
            "min_frequency": min_freq,
            "max_frequency": max_freq,
            "annotator_name": "brookie",
            "annotate_date": random.choice(DATES),
        })

    with open(OUT_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "species", "detection_id", "start_time", "end_time",
            "min_frequency", "max_frequency", "annotator_name", "annotate_date",
        ])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
