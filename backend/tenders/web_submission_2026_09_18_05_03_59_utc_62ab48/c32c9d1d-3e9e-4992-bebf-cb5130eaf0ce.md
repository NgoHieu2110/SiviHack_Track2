# Grundhafte Erneuerung der Gutenbergstraße in Gießen, 1. BA

**Matched company:** Web submission 2026-09-18 05:03:59 UTC (62ab48)
**Buyer:** Magistrat der Universitätsstadt Gießen - Tiefbauamt -
**Value (as matched):** 1,415,446.92 EUR
**CPV codes (as matched):** 45233120, 45112000, 45230000, 45232410, 45232400, 45231000, 45232140, 45232150, 45231220, 45231400, 45232300, 45316110, 45316200, 45112700
**Region(s) (as matched):** DE711, DE721
**Published:** 2026-09-13T16:14:04Z
**Notice ID:** c32c9d1d-3e9e-4992-bebf-cb5130eaf0ce
**OCID:** ocds-mnwr74-b679846b-c3e8-4e8f-82ae-380fa802ebfd

_Matched against the `web_submission_2026_09_18_05_03_59_utc_62ab48` profile in filters.yaml (match). Notes: Company focused on railway construction and service projects based or operating in Hungary, with an extremely large maximum financial capacity. [Generated at tolerance: cpv=0.50, nuts=0.50, value=0.50, exclude=0.50, role_hint=0.50]_

## Field inventory

What's actually populated on this release, beyond the handful of fields fetch_tenders.py currently filters on. Useful when deciding whether a field is reliable enough to add to filters.yaml as a real filter (see filters.yaml's own header for that workflow).

| Field (path) | What it would let you filter on | Status on this release |
|---|---|---|
| `tender.lots` | Per-lot breakdown (value/CPV/region can differ from tender-level) | list of 1 item(s), first: `{"id": "LOT-0001", "title": "Grundhafte Erneuerung der Gutenbergstraße in Gießen, 1. BA - 66.26.039 -", "description": "Gegenstand der Ausschreibung ist die grundhafte Erneuerung der Gutenbergstraße in Gießen (zwischen Grünberger Straße und Nahrungsberg) als Gemeinschaftsmaßnahme des Tiefbauamtes de` |
| `tender.lotDetails` | Lot-bidding constraints (maximumLotsBidPerSupplier etc.) | _NOT PRESENT_ |
| `tender.additionalClassifications` | Secondary CPV/classification codes beyond the primary one | _NOT PRESENT_ |
| `tender.otherRequirements` | reservedParticipation, requiresStaffNamesAndQualifications, securityClearance, etc. | _NOT PRESENT_ |
| `tender.otherRequirements.reservedParticipation` | Sheltered-workshop / social-enterprise reservation codes | _NOT PRESENT_ |
| `tender.procurementMethod` | open / restricted / negotiated / etc. | open |
| `tender.procurementMethodDetails` | Free-text procedure detail | Open |
| `tender.tenderPeriod` | Submission deadline window | _NOT PRESENT_ |
| `tender.submissionMethodDetails` | How/where to submit a bid | _NOT PRESENT_ |
| `tender.value` | Tender-level estimated value | object with keys: `amount, currency` |
| `tender.items` | Item list (CPV classification lives here today) | list of 1 item(s), first: `{"id": "LOT-0001", "classification": {"scheme": "CPV", "id": "45233120", "description": "Road construction works"}, "additionalClassifications": [{"scheme": "CPV", "id": "45112000", "description": "Excavating and earthmoving work"}, {"scheme": "CPV", "id": "45230000", "description": "Construction wo` |
| `parties` | All organizations involved, with roles[] per party | list of 2 item(s), first: `{"name": "Magistrat der Universitätsstadt Gießen - Tiefbauamt -", "id": "ORG-0001", "identifier": {"id": "DE112591347", "legalName": "Magistrat der Universitätsstadt Gießen - Tiefbauamt -"}, "address": {"streetAddress": "Berliner Platz 1", "locality": "Gießen", "region": "DE721", "postalCode": "3539` |
| `buyer` | The buyer party reference | object with keys: `name, id, identifier, address, contactPoint` |
| `awards` | Award-stage data (not usually present on a pre-award notice) | _NOT PRESENT_ |
| `contracts` | Contract-stage data (not usually present on a pre-award notice) | _NOT PRESENT_ |

## Fields fetch_tenders.py used to decide this match

- `tender.items[].classification.id` (CPV codes)
- `tender.items[].deliveryAddress.region`, `buyer.address.region`, `parties[].address.region` (NUTS codes)
- `tender.value.amount` / `tender.value.currency`, falling back to summed `tender.lots[].value`
- `tender.title`, `tender.description`, `tender.procurementMethodRationale`, `tender.lots[].title`, `tender.lots[].description` (as one lowercased text blob for keyword matching)
- `tender.additionalClassifications[].id`, `tender.items[].additionalClassifications[].id` (secondary CPV codes, folded into the same CPV match pool as the primary code)
- `tender.procurementMethod` (if `procurement_methods_allowed` is set)
- `tender.tenderPeriod.startDate`/`.endDate` (if `min_bid_prep_days` is set)
- `tender.otherRequirements.reservedParticipation` (if `reject_reserved_participation` is set)
- `tender.lots[].contractPeriod.startDate` (if `contract_starts_after`/`contract_starts_before` is set)

## Full raw release JSON

```json
{
  "ocid": "ocds-mnwr74-b679846b-c3e8-4e8f-82ae-380fa802ebfd",
  "id": "c32c9d1d-3e9e-4992-bebf-cb5130eaf0ce",
  "date": "2026-09-13T16:14:04Z",
  "tag": [
    "tender"
  ],
  "initiationType": "tender",
  "parties": [
    {
      "name": "Magistrat der Universitätsstadt Gießen - Tiefbauamt -",
      "id": "ORG-0001",
      "identifier": {
        "id": "DE112591347",
        "legalName": "Magistrat der Universitätsstadt Gießen - Tiefbauamt -"
      },
      "address": {
        "streetAddress": "Berliner Platz 1",
        "locality": "Gießen",
        "region": "DE721",
        "postalCode": "35390",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "submissionsstelle@giessen.de",
        "telephone": "0641 306-1330",
        "url": "https://www.giessen.de"
      },
      "roles": [
        "buyer"
      ]
    },
    {
      "name": "Vergabekammer des Landes Hessen beim Regierungspräsidium Darmstadt",
      "id": "ORG-0002",
      "identifier": {
        "id": "+49 6151126603",
        "legalName": "Vergabekammer des Landes Hessen beim Regierungspräsidium Darmstadt"
      },
      "address": {
        "streetAddress": "Wilhelmstraße 1 - 3 (Postanschrift)",
        "locality": "Darmstadt",
        "region": "DE711",
        "postalCode": "64283",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "vergabekammer@rpda.hessen.de",
        "telephone": "+49 6151126603",
        "faxNumber": "+49 6151125816"
      },
      "roles": [
        "reviewBody"
      ]
    }
  ],
  "buyer": {
    "name": "Magistrat der Universitätsstadt Gießen - Tiefbauamt -",
    "id": "DE112591347",
    "identifier": {
      "id": "ORG-0001",
      "legalName": "Magistrat der Universitätsstadt Gießen - Tiefbauamt -"
    },
    "address": {
      "streetAddress": "Berliner Platz 1",
      "locality": "Gießen",
      "region": "DE721",
      "postalCode": "35390",
      "countryName": "DEU"
    },
    "contactPoint": {
      "email": "submissionsstelle@giessen.de",
      "telephone": "0641 306-1330",
      "url": "https://www.giessen.de"
    }
  },
  "tender": {
    "id": "b679846b-c3e8-4e8f-82ae-380fa802ebfd",
    "title": "Grundhafte Erneuerung der Gutenbergstraße in Gießen, 1. BA",
    "description": "Straßenbau-, Ver- und Entsorgungsleitungen und Landschaftsbauarbeiten",
    "procuringEntity": {
      "name": "Magistrat der Universitätsstadt Gießen - Tiefbauamt -",
      "id": "DE112591347"
    },
    "items": [
      {
        "id": "LOT-0001",
        "classification": {
          "scheme": "CPV",
          "id": "45233120",
          "description": "Road construction works"
        },
        "additionalClassifications": [
          {
            "scheme": "CPV",
            "id": "45112000",
            "description": "Excavating and earthmoving work"
          },
          {
            "scheme": "CPV",
            "id": "45230000",
            "description": "Construction work for pipelines, communication and power lines, for highways, roads, airfields and railways; flatwork"
          },
          {
            "scheme": "CPV",
            "id": "45232410",
            "description": "Sewerage work"
          },
          {
            "scheme": "CPV",
            "id": "45232400",
            "description": "Sewer construction work"
          },
          {
            "scheme": "CPV",
            "id": "45231000",
            "description": "Construction work for pipelines, communication and power lines"
          },
          {
            "scheme": "CPV",
            "id": "45232140",
            "description": "District-heating mains construction work"
          },
          {
            "scheme": "CPV",
            "id": "45232150",
            "description": "Works related to water-distribution pipelines"
          },
          {
            "scheme": "CPV",
            "id": "45231220",
            "description": "Construction work for gas pipelines"
          },
          {
            "scheme": "CPV",
            "id": "45231400",
            "description": "Construction work for electricity power lines"
          },
          {
            "scheme": "CPV",
            "id": "45232300",
            "description": "Construction and ancillary works for telephone and communication lines"
          },
          {
            "scheme": "CPV",
            "id": "45316110",
            "description": "Installation of road lighting equipment"
          },
          {
            "scheme": "CPV",
            "id": "45316200",
            "description": "Installation of signalling equipment"
          },
          {
            "scheme": "CPV",
            "id": "45112700",
            "description": "Landscaping work"
          }
        ],
        "deliveryAddress": {
          "streetAddress": "Gutenbergstraße",
          "locality": "Gießen",
          "region": "DE721",
          "postalCode": "35390",
          "countryName": "DEU"
        },
        "relatedLot": "LOT-0001"
      }
    ],
    "value": {
      "amount": 1415446.92,
      "currency": "EUR"
    },
    "procurementMethod": "open",
    "procurementMethodDetails": "Open",
    "mainProcurementCategory": "works",
    "numberOfTenderers": 0,
    "documents": [
      {
        "id": "DOC-0001",
        "url": "https://www.subreport.de/E44916179",
        "language": "DEU",
        "relatedLots": [
          "LOT-0001"
        ]
      }
    ],
    "lots": [
      {
        "id": "LOT-0001",
        "title": "Grundhafte Erneuerung der Gutenbergstraße in Gießen, 1. BA - 66.26.039 -",
        "description": "Gegenstand der Ausschreibung ist die grundhafte Erneuerung der Gutenbergstraße in Gießen (zwischen Grünberger Straße und Nahrungsberg) als Gemeinschaftsmaßnahme des Tiefbauamtes der Stadt Gießen, der Stadtwerke Gießen, der Mittelhessischen Wasserbetriebe und des Ordnungsamtes.\nDie zu erbringenden Leistungen umfassen im Wesentlichen:\n1. Straßenbau (Tiefbauamt):\n•\tGrundhafter Ausbau der Fahrbahn in Asphaltbauweise \n•\tErneuerung der Gehwege in Pflasterbauweise.\n•\tNeuaufteilung des Straßenraumes inkl. Optimierung des Bordsteinverlaufs zur Schaffung von Park- und Grünflächen.\n•\tBarrierefreier Ausbau der Einmündungsbereiche (Grünberger Straße und Nahrungsberg).                                                                                                                                                           \n\n2. Kanalbauarbeiten (MWB):\n•\tOffene Bauweise: Rückbau und Neuverlegung von Regenwasserkanal und Reparaturen am Schmutzwasserkanal.\n•\tGeschlossene Bauweise: Kanalsanierung mittels GFK-Liner\n\n3. Leitungsbauarbeiten (Stadtwerke Gießen):\n•\tVerlegung von Versorgungsleitungen im Ausbaubereich, Fernwärme, Wasserhauptrohr, Gashauptrohr sowie Microverbundrohre und Fernmeldekabel.\n•\tVerlegung von Strom- und Straßenbeleuchtungskabeln.\n•\tErneuerung der Hausanschlüsse (Gas, Wasser, Strom).\n\n4. Verkehrstechnik (Ordnungsamt):\n•\tErneuerung von zwei Peitschenmasten inkl. Fundamenten.“"
      }
    ]
  },
  "language": "DEU"
}
```
