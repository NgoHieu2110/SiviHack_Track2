"""
webscrape/company_profiles.py

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
    structure doesn't fit this company's role. Best-effort text heuristic,
    not a real OCDS field, so keep this list conservative.

CPV prefixes below were verified against the official CPV tree (not guessed):
  45111*/45112*  Site preparation, earthmoving, excavation, trench-digging
  45231300       Construction work for water and sewage pipelines
  452313*        (children of 45231300: water mains, sewer laterals, etc.)
  45233*         Construction, foundation and surface work for highways/roads
                 (45233120 road construction, 45233140 roadworks,
                  45233220 surface work for roads, 45233223 resurfacing, etc.)
  45210000       Building construction work (parent of building-type codes)
  45211*         Multi-dwelling / individual houses (residential)
  45213*         Commercial/warehouse/industrial/transport buildings
  45214*         Education & research buildings (incl. 45214200 schools)
  45215*         Health, social, recreational, religious buildings
                 (incl. 45215140 hospital construction)
  45310000       Electrical installation work (parent)
  45311*         Electrical wiring and fitting work
  45312*         Alarm system and antenna installation (incl. 45312100 fire alarm)
  45315*         Electrical installation of heating/building-equipment (automation)
  45316*         Illumination and signalling systems installation
  45317*         Other electrical installation work

NUTS-1/2 prefixes (source: Destatis / Eurostat NUTS:DE):
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
            "45233",    # road construction, foundation, surface works
            "45231300", # water/sewage pipeline construction
            "452313",   # sub-codes of the above (mains, laterals, etc.)
            "45111",    # demolition, site prep, clearance (earthworks)
            "45112",    # excavating and earthmoving work
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
            "fachlos", "nachunternehmer",  # smells like a subcontract package
        ],
        "notes": "Regional civil contractor: roads, sewers, earthworks. Bavaria only, own machinery, no rail/bridges.",
    },
    "elektro_vogtland": {
        "display_name": "Elektro Vogtland GmbH",
        "cpv_prefixes": [
            "45310",  # electrical installation work (parent)
            "45311",  # wiring and fitting work
            "45312",  # alarm systems incl. fire alarm (45312100)
            "45315",  # electrical installation of heating/building-equipment (automation)
            "45316",  # illumination and signalling systems
            "45317",  # other electrical installation work
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
            "45210",  # building construction work (parent)
            "45211",  # multi-dwelling / individual houses (residential quarters)
            "45213",  # commercial, warehouse, industrial, transport buildings (logistics)
            "45214",  # education & research buildings (schools, universities)
            "45215",  # health, social, recreational buildings (hospitals)
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