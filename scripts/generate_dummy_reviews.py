"""Generate realistic review data with interesting distributions."""
import pandas as pd
import numpy as np
import random
from collections import defaultdict

# Set seeds for reproducibility
np.random.seed(42)
random.seed(42)

# Load the input data to understand what we're reviewing
input_df = pd.read_csv('data/dev-review.csv')

# Bird species list (matching the input data)
bird_species = list(input_df['common_name'].unique())

# Create species-specific accuracy profiles
# Some species the model is very good at, others it struggles with
SPECIES_ACCURACY = {}
for species in bird_species:
    r = random.random()
    if r < 0.3:  # 30% of species have high accuracy
        SPECIES_ACCURACY[species] = random.uniform(0.85, 0.95)
    elif r < 0.6:  # 30% have medium accuracy
        SPECIES_ACCURACY[species] = random.uniform(0.60, 0.85)
    else:  # 40% have lower accuracy
        SPECIES_ACCURACY[species] = random.uniform(0.30, 0.60)

# Common misidentification patterns (what the model confuses)
CONFUSION_MATRIX = {
    'Common nighthawk': ['Common poorwill', 'Vaux\'s swift'],
    'Hermit thrush': ['Swainson\'s thrush', 'Varied thrush'],
    'Downy woodpecker': ['Hairy woodpecker', 'Red-breasted sapsucker'],
    'Steller\'s jay': ['California scrub-jay', 'Blue jay'],
    'Dark-eyed junco': ['White-crowned sparrow', 'Song sparrow'],
    'Anna\'s hummingbird': ['Rufous hummingbird', 'Black-chinned hummingbird'],
}

# Reviewer profiles (some reviewers are more experienced)
REVIEWERS = {
    'brookie': {'accuracy': 0.92, 'notes_rate': 0.4, 'confidence_bias': 'high'},
    'alex': {'accuracy': 0.88, 'notes_rate': 0.3, 'confidence_bias': 'medium'},
    'sam': {'accuracy': 0.85, 'notes_rate': 0.5, 'confidence_bias': 'medium'},
    'jordan': {'accuracy': 0.90, 'notes_rate': 0.2, 'confidence_bias': 'high'},
    'casey': {'accuracy': 0.83, 'notes_rate': 0.6, 'confidence_bias': 'low'},
}

# Notes templates grouped by context
POSITIVE_NOTES = [
    "Clear recording",
    "Good example",
    "Strong vocalization",
    "Typical call pattern",
    "Confirmed with visual",
]

UNCERTAIN_NOTES = [
    "Some background noise",
    "Faint call",
    "Partially obscured by wind",
    "Dawn chorus interference",
    "Distance call",
    "Multiple species present",
    "Uncertain - needs second review",
]

NEGATIVE_NOTES = [
    "Wrong habitat for species",
    "Call pattern doesn't match",
    "Frequency range incorrect",
    "Likely mechanical noise",
    "Different species entirely",
]

CONTEXT_NOTES = [
    "Breeding season call",
    "Juvenile begging calls",
    "Alarm call",
    "Flight call",
    "Contact call",
    "Territorial song",
    "Mating display",
]

# Generate reviews based on the input data
data = []
review_count = defaultdict(int)  # Track how many times each row has been reviewed

# Process a subset of the input data (first 752 unique rows)
for idx, row in input_df.head(752).iterrows():
    species = row['common_name']
    confidence = row['confidence']
    county = row.get('county', 'Unknown')

    # Select reviewer (rotate through them with some bias)
    reviewer_name = random.choices(
        list(REVIEWERS.keys()),
        weights=[0.3, 0.2, 0.2, 0.2, 0.1]  # brookie reviews more
    )[0]
    reviewer = REVIEWERS[reviewer_name]

    # Determine if the model prediction is correct based on species accuracy
    species_acc = SPECIES_ACCURACY.get(species, 0.7)

    # Higher confidence predictions are more likely to be correct
    if confidence > 0.8:
        is_correct = random.random() < (species_acc * 1.2)  # Boost accuracy for high confidence
    elif confidence < 0.4:
        is_correct = random.random() < (species_acc * 0.7)  # Reduce accuracy for low confidence
    else:
        is_correct = random.random() < species_acc

    # Apply reviewer accuracy
    if random.random() > reviewer['accuracy']:
        is_correct = not is_correct  # Reviewer makes a mistake

    # Generate the review
    if is_correct:
        is_valid = 'yes'
        verified_common_name = ''
        verification_confidence = ''

        # Add notes based on context
        if random.random() < reviewer['notes_rate']:
            if confidence > 0.8:
                notes = random.choice(POSITIVE_NOTES + CONTEXT_NOTES)
            else:
                notes = random.choice(UNCERTAIN_NOTES + CONTEXT_NOTES)
        else:
            notes = ''
    else:
        is_valid = 'no'

        # Choose what the correct species is
        if species in CONFUSION_MATRIX and random.random() < 0.7:
            # 70% of the time, use a commonly confused species
            verified_common_name = random.choice(CONFUSION_MATRIX[species])
        else:
            # Otherwise, pick a random different species
            other_species = [s for s in bird_species if s != species]
            verified_common_name = random.choice(other_species)

        # Verification confidence based on reviewer profile
        confidence_bias = reviewer['confidence_bias']
        if confidence_bias == 'high':
            verification_confidence = random.choices(['low', 'medium', 'high'], weights=[0.1, 0.3, 0.6])[0]
        elif confidence_bias == 'low':
            verification_confidence = random.choices(['low', 'medium', 'high'], weights=[0.5, 0.4, 0.1])[0]
        else:
            verification_confidence = random.choices(['low', 'medium', 'high'], weights=[0.3, 0.4, 0.3])[0]

        # Add notes for corrections
        if random.random() < reviewer['notes_rate'] * 1.5:  # More likely to add notes for corrections
            if verification_confidence == 'high':
                notes = random.choice(NEGATIVE_NOTES + ["Clear misidentification", "Definitely " + verified_common_name])
            else:
                notes = random.choice(UNCERTAIN_NOTES + ["Possibly " + verified_common_name, "Not sure but likely wrong"])
        else:
            notes = ''

    # Add time columns to match with input data (ensure they're floats)
    data.append({
        'detection_id': int(row['id']),
        'start_time': float(row['start_time']),
        'end_time': float(row['end_time']),
        'is_valid': is_valid,
        'notes': notes,
        'verified_common_name': verified_common_name,
        'verification_confidence': verification_confidence,
        'reviewer_name': reviewer_name,
        'review_date': 20260413 + random.randint(0, 7)
    })

# Create DataFrame and save
df = pd.DataFrame(data)

# Print statistics
print(f"Generated {len(df)} rows of review data")
print(f"\nValidation results:")
print(f"  Yes (valid): {(df['is_valid'] == 'yes').sum()} ({(df['is_valid'] == 'yes').mean():.1%})")
print(f"  No (invalid): {(df['is_valid'] == 'no').sum()} ({(df['is_valid'] == 'no').mean():.1%})")

print(f"\nReviewer distribution:")
for reviewer in REVIEWERS:
    count = (df['reviewer_name'] == reviewer).sum()
    print(f"  {reviewer}: {count} reviews")

print(f"\nTop 5 most commonly corrected species:")
corrections = df[df['is_valid'] == 'no'].groupby('verified_common_name').size()
if len(corrections) > 0:
    for species, count in corrections.nlargest(5).items():
        print(f"  {species}: {count} times")

print(f"\nNotes added: {(df['notes'] != '').sum()} ({(df['notes'] != '').mean():.1%})")

# Save to file
df.to_csv('outputs/review-data.csv', index=False)
print(f"\nSaved to outputs/review-data.csv")