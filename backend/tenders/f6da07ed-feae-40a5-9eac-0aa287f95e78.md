# RV Fahrbahnreinigung nach Unfällen, AM Braunschweig-Rüningen

**Matched company:** company
**Buyer:** Die Autobahn GmbH des Bundes - NL Nordwest
**Value (as matched):** 685,881.75 EUR
**CPV codes (as matched):** 90000000
**Region(s) (as matched):** DE300, DE911, DE929, DEA22
**Published:** 2026-09-16T02:06:15Z
**Notice ID:** f6da07ed-feae-40a5-9eac-0aa287f95e78
**OCID:** ocds-mnwr74-64e5eece-3162-4fd0-9f92-1ff5107b6b8e

_Matched against the filters.yaml profile (partial match (2/3 core criteria: nuts, value; missed: cpv)). Notes: Building construction (Hochbau) contractor based in Berlin, handling contracts from roughly EUR 5k up to about EUR 98m, with broadening reach into Brandenburg and the wider eastern/northern German states. Explicitly excludes any offshore or underwater work. [Generated at tolerance: cpv=0.50, nuts=0.50, value=0.50, exclude=0.50, role_hint=0.50]_

## Filter tolerance at match time

Per-criterion tolerance (0.0 = strict, 1.0 = no filtering) that filters.yaml had when this tender was matched. See 2_company_details_to_initial_filter.py for what each dial means.

```json
{
  "cpv": 0.5,
  "nuts": 0.5,
  "value": 0.5,
  "exclude": 0.5,
  "role_hint": 0.5
}
```

## Field inventory

What's actually populated on this release, beyond the handful of fields fetch_tenders.py currently filters on. Useful when deciding whether a field is reliable enough to add to filters.yaml as a real filter (see filters.yaml's own header for that workflow).

| Field (path) | What it would let you filter on | Status on this release |
|---|---|---|
| `tender.lots` | Per-lot breakdown (value/CPV/region can differ from tender-level) | list of 1 item(s), first: `{"id": "LOT-0000", "title": "RV Fahrbahnreinigung nach Unfällen, AM Braunschweig-Rüningen", "description": "Der Autobahn GmbH des Bundes, vertreten durch die Niederlassung Nordwest, Außenstelle Hannover ist mit ihren Autobahnmeistereien durch die Planung, den Bau und die Unterhaltung maßgeblich für ` |
| `tender.lotDetails` | Lot-bidding constraints (maximumLotsBidPerSupplier etc.) | _NOT PRESENT_ |
| `tender.additionalClassifications` | Secondary CPV/classification codes beyond the primary one | _NOT PRESENT_ |
| `tender.otherRequirements` | reservedParticipation, requiresStaffNamesAndQualifications, securityClearance, etc. | _NOT PRESENT_ |
| `tender.otherRequirements.reservedParticipation` | Sheltered-workshop / social-enterprise reservation codes | _NOT PRESENT_ |
| `tender.procurementMethod` | open / restricted / negotiated / etc. | open |
| `tender.procurementMethodDetails` | Free-text procedure detail | Open |
| `tender.tenderPeriod` | Submission deadline window | _NOT PRESENT_ |
| `tender.submissionMethodDetails` | How/where to submit a bid | _NOT PRESENT_ |
| `tender.value` | Tender-level estimated value | object with keys: `amount, currency` |
| `tender.items` | Item list (CPV classification lives here today) | list of 1 item(s), first: `{"id": "LOT-0000", "classification": {"scheme": "CPV", "id": "90000000", "description": "Sewage, refuse, cleaning and environmental services"}, "deliveryLocation": {"description": "In Bezirk von Autobahnmeisterei Braunschweig-Rüningen"}, "deliveryAddress": {"streetAddress": "Westerbergstr. 85-87", "` |
| `parties` | All organizations involved, with roles[] per party | list of 4 item(s), first: `{"name": "Die Autobahn GmbH des Bundes - NL Nordwest", "id": "ORG-0001", "identifier": {"id": "USt-ID DE329214156", "legalName": "Die Autobahn GmbH des Bundes - NL Nordwest"}, "address": {"streetAddress": "Gradestraße 18", "locality": "Hannover", "region": "DE929", "postalCode": "30163", "countryNam` |
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
  "ocid": "ocds-mnwr74-64e5eece-3162-4fd0-9f92-1ff5107b6b8e",
  "id": "f6da07ed-feae-40a5-9eac-0aa287f95e78",
  "date": "2026-09-16T02:06:15Z",
  "tag": [
    "tender"
  ],
  "initiationType": "tender",
  "parties": [
    {
      "name": "Die Autobahn GmbH des Bundes - NL Nordwest",
      "id": "ORG-0001",
      "identifier": {
        "id": "USt-ID DE329214156",
        "legalName": "Die Autobahn GmbH des Bundes - NL Nordwest"
      },
      "address": {
        "streetAddress": "Gradestraße 18",
        "locality": "Hannover",
        "region": "DE929",
        "postalCode": "30163",
        "countryName": "DEU"
      },
      "contactPoint": {
        "name": "Vergabestelle",
        "email": "Vergabe.nordwest@autobahn.de",
        "telephone": "+49 511 23 51 050",
        "url": "https://www.autobahn.de"
      },
      "roles": [
        "buyer",
        "processContactPoint",
        "submissionReceiptBody"
      ]
    },
    {
      "name": "Bundeskartellamt - Vergabekammern des Bundes",
      "id": "ORG-0002",
      "identifier": {
        "id": "N.N.",
        "legalName": "Bundeskartellamt - Vergabekammern des Bundes"
      },
      "address": {
        "streetAddress": "Kaiser-Friedrich-Straße 16",
        "locality": "Bonn",
        "region": "DEA22",
        "postalCode": "53113",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "vk@bundeskartellamt.bund.de",
        "telephone": "+49 22894990",
        "url": "https://www.bundeskartellamt.de/DE/Vergaberecht/vergaberecht_node.html"
      },
      "roles": [
        "reviewBody"
      ]
    },
    {
      "name": "Die Autobahn GmbH des Bundes",
      "id": "ORG-0003",
      "identifier": {
        "id": "USt.-ID DE329214156",
        "legalName": "Die Autobahn GmbH des Bundes"
      },
      "address": {
        "streetAddress": "Heidestraße 15",
        "locality": "Berlin",
        "region": "DE300",
        "postalCode": "10557",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "recht@autobahn.de",
        "telephone": "+49 30640964911",
        "url": "https://www.autobahn.de"
      },
      "roles": [
        "reviewContactPoint"
      ]
    },
    {
      "name": "Die Autobahn GmbH des Bundes",
      "id": "ORG-0004",
      "identifier": {
        "id": "USt. ID DE329214156",
        "legalName": "Die Autobahn GmbH des Bundes"
      },
      "address": {
        "streetAddress": "Heidestraße 15",
        "locality": "Berlin",
        "region": "DE300",
        "postalCode": "10557",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "recht@autobahn.de",
        "telephone": "+49 30640964911",
        "url": "https://www.autobahn.de"
      },
      "roles": [
        "mediationBody"
      ]
    }
  ],
  "buyer": {
    "name": "Die Autobahn GmbH des Bundes - NL Nordwest",
    "id": "USt-ID DE329214156",
    "identifier": {
      "id": "ORG-7001",
      "legalName": "Die Autobahn GmbH des Bundes - NL Nordwest"
    },
    "address": {
      "streetAddress": "Gradestraße 18",
      "locality": "Hannover",
      "region": "DE929",
      "postalCode": "30163",
      "countryName": "DEU"
    },
    "contactPoint": {
      "name": "Vergabestelle",
      "email": "Vergabe.nordwest@autobahn.de",
      "telephone": "+49 511 23 51 050",
      "url": "https://www.autobahn.de"
    }
  },
  "tender": {
    "id": "64e5eece-3162-4fd0-9f92-1ff5107b6b8e",
    "title": "RV Fahrbahnreinigung nach Unfällen, AM Braunschweig-Rüningen",
    "description": "RV Fahrbahnreinigung nach Unfällen, AM Braunschweig-Rüningen",
    "procuringEntity": {
      "name": "Die Autobahn GmbH des Bundes - NL Nordwest",
      "id": "USt-ID DE329214156"
    },
    "items": [
      {
        "id": "LOT-0000",
        "classification": {
          "scheme": "CPV",
          "id": "90000000",
          "description": "Sewage, refuse, cleaning and environmental services"
        },
        "deliveryLocation": {
          "description": "In Bezirk von Autobahnmeisterei Braunschweig-Rüningen"
        },
        "deliveryAddress": {
          "streetAddress": "Westerbergstr. 85-87",
          "locality": "Braunschweig",
          "region": "DE911",
          "postalCode": "38122",
          "countryName": "DEU"
        },
        "relatedLot": "LOT-0000"
      }
    ],
    "value": {
      "amount": 685881.75,
      "currency": "EUR"
    },
    "procurementMethod": "open",
    "procurementMethodDetails": "Open",
    "mainProcurementCategory": "services",
    "numberOfTenderers": 0,
    "documents": [
      {
        "id": "DOC-0001",
        "url": "https://vergabe.autobahn.de/NetServer/TenderingProcedureDetails?function=_Details&TenderOID=54321-Tender-1a061cab455-6c9617b1f0b355de",
        "language": "DEU",
        "relatedLots": [
          "LOT-0000"
        ]
      }
    ],
    "lots": [
      {
        "id": "LOT-0000",
        "title": "RV Fahrbahnreinigung nach Unfällen, AM Braunschweig-Rüningen",
        "description": "Der Autobahn GmbH des Bundes, vertreten durch die Niederlassung Nordwest, Außenstelle Hannover ist mit ihren Autobahnmeistereien durch die Planung, den Bau und die Unterhaltung maßgeblich für die Verkehrssicherheit auf den\ndeutschen Bundesautobahnen verantwortlich. Die Außenstelle Hannover betreut mit ihren vier Autobahnmeistereien die Bundesautobahnen 2, 7, 36, 37, 39, 352, 369, 391 und die A392. Auf diesen Straßen ereignen sich Unfälle oder sonstige unvorhersehbare Vorkommnisse, bei denen wassergefährdende Stoffe freigesetzt werden. Zur Wiederherstellung der Verkehrssicherheit auf den betroffenen\nBundesautobahnen, sowie deren Nebenbetrieben (Park- und Rastanlagen), sowie zur Vermeidung und zur Verhinderung weiterer negativen Auswirkungen auf die Umwelt ist eine schnellstmögliche und effektive Beseitigung der ausgetretenen Stoffe erforderlich.\n\nEs handelt sich um voraussichtlich folgende Leistungsbestandteile:\n- Maschinelle Fahrbahnreinigung von Längeren Verschmutzten Spuren.\n- Maschinelle Fahrbahnreinigung auf offenporigen Asphalt.\n- Machinelle Fanhrbaahnreinigung auf Einzelflächen.\n- Ölsperre auf befestigtem Untergrund herstellen, aufnehmen und entsorgen.\n- Feststoffen, Oberboden und Gefährlichee Bodenmaterialien entsorgen.",
        "value": {
          "amount": 685881.75,
          "currency": "EUR"
        },
        "contractPeriod": {
          "startDate": "2026-12-01T00:00:00+01:00",
          "endDate": "2028-11-30T00:00:00+01:00"
        }
      }
    ]
  },
  "language": "DEU"
}
```
