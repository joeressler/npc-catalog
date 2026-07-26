ALIGNMENT_DISPLAY: dict[str, str] = {
    "LG": "Lawful Good",
    "NG": "Neutral Good",
    "CG": "Chaotic Good",
    "LN": "Lawful Neutral",
    "N": "True Neutral",
    "CN": "Chaotic Neutral",
    "LE": "Lawful Evil",
    "NE": "Neutral Evil",
    "CE": "Chaotic Evil",
}

VALID_ALIGNMENTS = frozenset(ALIGNMENT_DISPLAY.keys())

RELATION_POLARITIES = frozenset({"positive", "negative", "neutral", "complex"})
VALID_NODE_KINDS = frozenset({"npc", "party"})
PARTY_NODE_LABEL = "Party"

DEFAULT_RELATION_TYPES: tuple[tuple[str, str], ...] = (
    ("Ally", "positive"),
    ("Trusts", "positive"),
    ("Protects", "positive"),
    ("Mentors", "positive"),
    ("Serves", "positive"),
    ("Romantic interest", "positive"),
    ("Blood kin", "positive"),
    ("Owes life-debt", "positive"),
    ("Business partner", "positive"),
    ("Devoted follower", "positive"),
    ("Enemy", "negative"),
    ("Hates", "negative"),
    ("Fears", "negative"),
    ("Rival", "negative"),
    ("Betrayed", "negative"),
    ("Blackmails", "negative"),
    ("Hunts", "negative"),
    ("Despises", "negative"),
    ("Secretly related", "complex"),
    ("Unrequited love", "complex"),
    ("Frenemies", "complex"),
    ("Political pawn", "complex"),
    ("Owes debt", "complex"),
    ("Suspects", "complex"),
    ("Manipulates", "complex"),
    ("Former lover", "complex"),
)
