"""
Company fit-filter configuration.

Each company is defined by hard filters applied to a single OCDS "release":
  - cpv_prefixes: list of CPV code prefixes considered relevant (matches if
    ANY item's CPV starts with ANY of these prefixes)
  - nuts_prefixes: list of NUTS region-code prefixes considered "in territory"
    (matches if the tender's delivery region, buyer region, OR procuring
    entity's region starts with ANY of these prefixes)
  - value_min / value_max: EUR contract value must fall in [min, max]
    inclusive. Use None for no bound.
  - exclude_keywords: if any of these (case-insensitive, substring) appear in
    the tender title or description, the notice is rejected outright
    regardless of the above (used to rule out rail, high-voltage, etc. that
    the company explicitly cannot deliver)
  - role_hint_reject: substrings in title/description suggesting the tender
    structure doesn't fit this company's role (e.g. asking a small sub to
    bid as lead contractor on a multi-trade job). Best-effort text heuristic,
    not a real OCDS field, so keep this list conservative.

NUTS-1/2 prefixes used below (source: Destatis / Eurostat NUTS:DE):
  DE1  Baden-Württemberg      DE6  Hamburg
  DE2  Bayern (DE21 Oberbayern, DE27 Schwaben, DE23 Oberpfalz, etc.)
  DE3  Berlin                 DE7  Hessen
  DE4  Brandenburg            DE8  Mecklenburg-Vorpommern
  DE5  Bremen                 DE9  Niedersachsen
  DEA  Nordrhein-Westfalen    DEB  Rheinland-Pfalz
  DEC  Saarland               DED  Sachsen
  DEE  Sachsen-Anhalt         DEF  Schleswig-Holstein
  DEG  Thüringen
"""

COMPANIES = {
    "brenner_sohn_tiefbau": {
        "display_name": "Brenner & Sohn Tiefbau GmbH",
        "cpv_prefixes": [
            "4523",   # road construction
            "4524",   # bridges/tunnels (kept out via exclude_keywords below)
            "4525",   # general construction works (earthworks etc. live here)
            "4523312",  # sewer/pipeline construction (more specific, still under 45)
            "4521",   # building of pipeline, comms, power lines (sewers/utilities)
        ],
        "nuts_prefixes": [
            "DE21",  # Oberbayern
            "DE27",  # Schwaben
            "DE2",   # fallback: rest of Bayern, looser fit, kept for volume
        ],
        "value_min": 400_000,
        "value_max": 4_000_000,
        "exclude_keywords": [
            "brücke", "brueck",           # bridges - can't show this
            "tunnel",
            "bahnsteig", "gleis", "schiene", "db infrago", "eisenbahn",  # rail
            "ausland",
        ],
        "role_hint_reject": [
            "gewerk", "fachlos", "nachunternehmer",  # smells like a subcontract package
        ],
        "notes": "Regional civil contractor: roads, sewers, earthworks. Bavaria only, own machinery, no rail/bridges.",
    },
    "elektro_vogtland": {
        "display_name": "Elektro Vogtland GmbH",
        "cpv_prefixes": [
            "4531",   # electrical installation work
            "4521421", # fire alarm
            "4531432", # fire alarm systems (specific)
            "4521613", # building automation (approx family under 4521)
        ],
        "nuts_prefixes": [
            "DED",   # Sachsen
            "DEG",   # Thüringen
            "DE2",   # eastern Bayern (loose - Bavaria as a whole, refine later if noisy)
        ],
        "value_min": 80_000,
        "value_max": 900_000,
        "exclude_keywords": [
            "hochspannung",              # high voltage
            "ex-schutz", "explosionsschutz", "atex",  # explosion protection
            "generalunternehmer",        # explicitly seeking a GC role
        ],
        "role_hint_reject": [
            "gesamtmassnahme", "gesamtmaßnahme", "schlüsselfertig", "generalunternehmer",
        ],
        "notes": "Small electrical specialist, usually subcontractor. Saxony/Thuringia/east Bavaria, small contract sizes.",
    },
    "hanseatische_bau": {
        "display_name": "Hanseatische Bau AG",
        "cpv_prefixes": [
            "4521",   # building construction work (general)
            "4521420", # hospital-type buildings
            "4521410", # school buildings
            "4521460", # office buildings
        ],
        "nuts_prefixes": [
            "DE6",   # Hamburg
            "DE5",   # Bremen
            "DE9",   # Niedersachsen
            "DEF",   # Schleswig-Holstein
            "DE8",   # Mecklenburg-Vorpommern
        ],
        "value_min": 8_000_000,
        "value_max": 90_000_000,
        "exclude_keywords": [
            "tiefbau", "straßenbau", "strassenbau", "kanalbau", "brückenbau",
            "sielbau",
        ],
        "role_hint_reject": [
            "eigenleistung",  # tenders demanding high self-performed work share hurt them
        ],
        "notes": "Large GC, turnkey building projects. Northern Germany only, high value floor, coordination not self-perform.",
    },
}