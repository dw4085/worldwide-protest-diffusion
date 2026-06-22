"""Shared movement category definitions and variable-name mappings."""

from __future__ import annotations

CATEGORIES: list[tuple[str, str]] = [
    ("Governance & Politics", "gov_pol"),
    ("Education", "edu"),
    ("Labor", "labor"),
    ("Human Rights & Identity", "human_rights"),
    ("Justice & Accountability", "justice"),
    ("Security & Conflict", "security"),
    ("Health & Social Welfare", "health"),
    ("Religion & Belief", "religion"),
    ("Prices & Economy", "economy"),
    ("Public Services & Infrastructure", "pub_serv"),
    ("International Solidarity & Foreign Policy", "intl_solidarity"),
    ("Environment", "enviro"),
    ("Agriculture & Rural", "agri"),
    ("Land, Property & Housing", "land"),
    ("Other", "other"),
]

TITLE_TO_BASE = {title: base for title, base in CATEGORIES}
BASE_TO_TITLE = {base: title for title, base in CATEGORIES}

# Lag variable prefix -> movement title
LAG_VAR_TO_TITLE = {f"{base}_cnt_l1": title for title, base in CATEGORIES}

TABLE_HEADERS = [title for title, _ in CATEGORIES] + ["Security Conflict"]

TITLE_ALIASES = {
    "Security Conflict": "Security & Conflict",
}

def normalize_title(header: str) -> str:
    return TITLE_ALIASES.get(header, header)

def lag_var_to_title(var_name: str) -> str | None:
    if var_name.startswith("same_ctry_distw_"):
        return None
    return LAG_VAR_TO_TITLE.get(var_name)

def base_for_title(title: str) -> str:
    return TITLE_TO_BASE[normalize_title(title)]
