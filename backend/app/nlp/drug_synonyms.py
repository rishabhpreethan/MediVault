"""MV-049: Drug synonym normalization dictionary.

Maps lowercase brand/regional drug names to their canonical (INN) forms.
Covers common Indian and global brand names.
"""
from __future__ import annotations

# Maps lowercase synonym → canonical INN name (title-cased)
DRUG_SYNONYMS: dict[str, str] = {
    # Acetaminophen (paracetamol) — Indian + global brands
    "paracetamol": "Acetaminophen",
    "crocin": "Acetaminophen",
    "calpol": "Acetaminophen",
    "dolo": "Acetaminophen",
    "tylenol": "Acetaminophen",
    # Ibuprofen — Indian + global brands
    # combiflam is ibuprofen+paracetamol; normalise to ibuprofen (primary component)
    "brufen": "Ibuprofen",
    "advil": "Ibuprofen",
    "nurofen": "Ibuprofen",
    "combiflam": "Ibuprofen",
    # Metformin
    "glucophage": "Metformin",
    "glycomet": "Metformin",
    # Atorvastatin
    "lipitor": "Atorvastatin",
    "atorva": "Atorvastatin",
    # Omeprazole
    "prilosec": "Omeprazole",
    "omez": "Omeprazole",
    # Pantoprazole
    "pantocid": "Pantoprazole",
    "pan": "Pantoprazole",
    # Amlodipine
    "norvasc": "Amlodipine",
    "amlip": "Amlodipine",
    # Metoprolol
    "lopressor": "Metoprolol",
    "toprol": "Metoprolol",
    # Cetirizine
    "zyrtec": "Cetirizine",
    "cetzine": "Cetirizine",
    # Amoxicillin
    "amoxil": "Amoxicillin",
    "mox": "Amoxicillin",
    # Azithromycin
    "zithromax": "Azithromycin",
    "azee": "Azithromycin",
}


def normalize_drug_name(name: str) -> str:
    """Normalize a drug name to its canonical (INN) form.

    1. Strips leading/trailing whitespace and lowercases the input for lookup.
    2. Returns the canonical title-cased name if a synonym mapping is found.
    3. Returns the original input unchanged if no mapping exists.

    Args:
        name: Raw drug name as extracted from text.

    Returns:
        Canonical drug name (title-cased) if a synonym is found, otherwise
        the original input string (casing preserved).
    """
    key = name.strip().lower()
    if key in DRUG_SYNONYMS:
        return DRUG_SYNONYMS[key]
    return name
