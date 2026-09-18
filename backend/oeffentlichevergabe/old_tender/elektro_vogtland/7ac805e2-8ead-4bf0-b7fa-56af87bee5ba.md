# Optimierung/Dekarbonisierung der Kläranlage, Elektrotechnische Einbindung Rechengebäude mit PV und Gasspeicher

**Matched company:** Elektro Vogtland GmbH
**Buyer:** Stadt Bad Kissingen
**Value (as matched):** 682,600.00 EUR
**CPV codes (as matched):** 45311000, 45312310, 48921000, 45311200, 45317300, 45315700, 72318000
**Region(s) (as matched):** DE251, DE265, DE271
**Published:** 2026-08-04T22:00:00Z
**Notice ID:** 7ac805e2-8ead-4bf0-b7fa-56af87bee5ba
**OCID:** ocds-mnwr74-6319b06b-4d10-467d-a7e7-84f93c2010a0

_Matched against the `elektro_vogtland` profile in filters.yaml (match). Notes: Small electrical specialist, usually subcontractor. Saxony/Thuringia/east Bavaria, small contract sizes._

## Field inventory

What's actually populated on this release, beyond the handful of fields fetch_tenders.py currently filters on. Useful when deciding whether a field is reliable enough to add to filters.yaml as a real filter (see filters.yaml's own header for that workflow).

| Field (path) | What it would let you filter on | Status on this release |
|---|---|---|
| `tender.lots` | Per-lot breakdown (value/CPV/region can differ from tender-level) | list of 1 item(s), first: `{"id": "LOT-0001", "title": "Optimierung/Dekarbonisierung der Kläranlage, Elektrotechnische Einbindung Rechengebäude mit PV und Gasspeicher", "description": "Weiterer Leistungsumfang: - Installation Niederspannungsschaltanlagen Rechengebäude und Faulgasspeicher - Installation von Mess-, Steuer-, Reg` |
| `tender.lotDetails` | Lot-bidding constraints (maximumLotsBidPerSupplier etc.) | _NOT PRESENT_ |
| `tender.additionalClassifications` | Secondary CPV/classification codes beyond the primary one | _NOT PRESENT_ |
| `tender.otherRequirements` | reservedParticipation, requiresStaffNamesAndQualifications, securityClearance, etc. | _NOT PRESENT_ |
| `tender.otherRequirements.reservedParticipation` | Sheltered-workshop / social-enterprise reservation codes | _NOT PRESENT_ |
| `tender.procurementMethod` | open / restricted / negotiated / etc. | open |
| `tender.procurementMethodDetails` | Free-text procedure detail | Open |
| `tender.tenderPeriod` | Submission deadline window | _NOT PRESENT_ |
| `tender.submissionMethodDetails` | How/where to submit a bid | _NOT PRESENT_ |
| `tender.value` | Tender-level estimated value | object with keys: `amount, currency` |
| `tender.items` | Item list (CPV classification lives here today) | list of 1 item(s), first: `{"id": "LOT-0001", "classification": {"scheme": "CPV", "id": "45311000", "description": "Electrical wiring and fitting work"}, "additionalClassifications": [{"scheme": "CPV", "id": "45312310", "description": "Lightning-protection works"}, {"scheme": "CPV", "id": "48921000", "description": "Automatio` |
| `parties` | All organizations involved, with roles[] per party | list of 3 item(s), first: `{"name": "Stadt Bad Kissingen", "id": "ORG-0001", "identifier": {"id": "09672114-KG0001-55", "legalName": "Stadt Bad Kissingen"}, "address": {"streetAddress": "Rathausplatz 1", "locality": "Bad Kissingen", "region": "DE265", "postalCode": "97688", "countryName": "DEU"}, "contactPoint": {"name": "Ref` |
| `buyer` | The buyer party reference | object with keys: `name, id, identifier, address, contactPoint` |
| `awards` | Award-stage data (not usually present on a pre-award notice) | list of 1 item(s), first: `{"id": "LOT-0001", "title": "Elektrotechnische Einbindung Rechengebäude mit PV und Gasspeicher", "status": "active", "date": "2026-08-04T00:00:00+02:00", "value": {"amount": 771756.63, "currency": "EUR"}, "relatedLots": ["LOT-0001"]}` |
| `contracts` | Contract-stage data (not usually present on a pre-award notice) | list of 1 item(s), first: `{"id": "CON-0001", "awardID": "CON-0001", "title": "Elektrotechnische Einbindung Rechengebäude mit PV und Gasspeicher", "status": "active", "value": {"amount": 752591.15, "currency": "EUR"}, "items": [{"id": "LOT-0001", "relatedLot": "LOT-0001"}], "dateSigned": "2026-08-03T22:00:00.000Z"}` |

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
  "ocid": "ocds-mnwr74-6319b06b-4d10-467d-a7e7-84f93c2010a0",
  "id": "7ac805e2-8ead-4bf0-b7fa-56af87bee5ba",
  "date": "2026-08-04T22:00:00Z",
  "tag": [
    "award"
  ],
  "initiationType": "tender",
  "parties": [
    {
      "name": "Stadt Bad Kissingen",
      "id": "ORG-0001",
      "identifier": {
        "id": "09672114-KG0001-55",
        "legalName": "Stadt Bad Kissingen"
      },
      "address": {
        "streetAddress": "Rathausplatz 1",
        "locality": "Bad Kissingen",
        "region": "DE265",
        "postalCode": "97688",
        "countryName": "DEU"
      },
      "contactPoint": {
        "name": "Referat Tiefbau Stadt Bad Kissingen",
        "email": "vergabestelle-vgv@stadt.badkissingen.de",
        "telephone": "+49 9718073313",
        "url": "https://www.badkissingen.de"
      },
      "roles": [
        "buyer",
        "processContactPoint"
      ]
    },
    {
      "name": "Vergabekammer Nordbayern",
      "id": "ORG-0002",
      "identifier": {
        "id": "09-0358002-61",
        "legalName": "Vergabekammer Nordbayern"
      },
      "address": {
        "streetAddress": "Postfach 6 06",
        "locality": "Ansbach",
        "region": "DE251",
        "postalCode": "91511",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "vergabekammer.nordbayern@reg-mfr.bayern.de",
        "telephone": "+49 98153-1277",
        "url": "http://www.regierung.mittelfranken.bayern.de/"
      },
      "roles": [
        "reviewContactPoint",
        "reviewBody"
      ]
    },
    {
      "name": "Siemens AG, NL Augsburg",
      "id": "ORG-0003",
      "identifier": {
        "id": "DE129274202",
        "legalName": "Siemens AG, NL Augsburg"
      },
      "address": {
        "streetAddress": "Melli-Beese-Str. 5",
        "locality": "Augsburg",
        "region": "DE271",
        "postalCode": "86159",
        "countryName": "DEU"
      },
      "contactPoint": {
        "name": "Herr Christian Sturm",
        "email": "christian.cs.sturm@siemens.com",
        "telephone": "+49 (152) 22706977",
        "url": "http://siemens.de"
      },
      "roles": [
        "tenderer",
        "supplier"
      ]
    }
  ],
  "buyer": {
    "name": "Stadt Bad Kissingen",
    "id": "09672114-KG0001-55",
    "identifier": {
      "id": "ORG-0001",
      "legalName": "Stadt Bad Kissingen"
    },
    "address": {
      "streetAddress": "Rathausplatz 1",
      "locality": "Bad Kissingen",
      "region": "DE265",
      "postalCode": "97688",
      "countryName": "DEU"
    },
    "contactPoint": {
      "name": "Referat Tiefbau Stadt Bad Kissingen",
      "email": "vergabestelle-vgv@stadt.badkissingen.de",
      "telephone": "+49 9718073313",
      "url": "https://www.badkissingen.de"
    }
  },
  "tender": {
    "id": "6319b06b-4d10-467d-a7e7-84f93c2010a0",
    "title": "Optimierung/Dekarbonisierung der Kläranlage, Elektrotechnische Einbindung Rechengebäude mit PV und Gasspeicher",
    "description": "Im Rahmen der Maßnahme \"Optimierung / Dekarbonisierung der Kläranlage\" werden das Rechengebäude sowie die Faulgas-Speicherung der Kläranlage Bad Kissingen elektrotechnisch und leittechnisch modernisiert. Ziel ist die Verbesserung der Energieeffizienz, die Steigerung des Eigenversorgungsgrades sowie die Schaffung der technischen Voraussetzungen für einen nachhaltigen und zukunftsfähigen Anlagenbetrieb.  Das Untergeschoss des bestehenden Rechengebäudes wird saniert, während mit der Rechenhalle der überwiegende Teil des Erdgeschosses neu errichtet wird. Im Zuge der Maßnahme werden die maschinelle Ausrüstung des Rechengebäudes sowie die gesamte elektrotechnische Ausrüstung der mechanischen Reinigungsstufe erneuert. Hierfür wird eine neue Niederspannungsschaltanlage mit moderner Mess-, Steuer-, Regel- und Elektrotechnik errichtet und an das zentrale Prozessleitsystem der Kläranlage angebunden. Darüber hinaus werden Photovoltaikanlagen auf dem Dach und an der Fassade des Rechengebäudes installiert und in das Energienetz der Kläranlage integriert.  Ein weiterer Bestandteil der Maßnahme ist die elektrotechnische und leittechnische Einbindung eines neuen Faulgasspeichers einschließlich eigener Niederspannungsschaltanlage.",
    "procuringEntity": {
      "name": "Stadt Bad Kissingen",
      "id": "09672114-KG0001-55"
    },
    "items": [
      {
        "id": "LOT-0001",
        "classification": {
          "scheme": "CPV",
          "id": "45311000",
          "description": "Electrical wiring and fitting work"
        },
        "additionalClassifications": [
          {
            "scheme": "CPV",
            "id": "45312310",
            "description": "Lightning-protection works"
          },
          {
            "scheme": "CPV",
            "id": "48921000",
            "description": "Automation system"
          },
          {
            "scheme": "CPV",
            "id": "45311200",
            "description": "Electrical fitting work"
          },
          {
            "scheme": "CPV",
            "id": "45317300",
            "description": "Electrical installation work of electrical distribution apparatus"
          },
          {
            "scheme": "CPV",
            "id": "45315700",
            "description": "Switching station installation work"
          },
          {
            "scheme": "CPV",
            "id": "72318000",
            "description": "Data transmission services"
          }
        ],
        "deliveryLocation": {
          "description": "Die Große Kreisstadt Bad Kissingen liegt im Bundesland Bayern, Regie-rungsbezirk Unterfranken, Landkreis Bad Kissingen. Die Kläranlage liegt im Süden von Bad Kissingen am linken Ufer der fränkischen Saale. Adresse: Im Lindes 11, 97688 Bad Kissingen Die Kläranlage ist über einen asphaltierten Zufahrtsweg gut zu erreichen."
        },
        "deliveryAddress": {
          "streetAddress": "Im Lindes 11",
          "locality": "Bad Kissingen",
          "region": "DE265",
          "postalCode": "97688",
          "countryName": "DEU"
        },
        "relatedLot": "LOT-0001"
      }
    ],
    "value": {
      "amount": 682600.0,
      "currency": "EUR"
    },
    "procurementMethod": "open",
    "procurementMethodDetails": "Open",
    "mainProcurementCategory": "works",
    "awardPeriod": {
      "endDate": "2026-07-31T00:00:00+02:00"
    },
    "numberOfTenderers": 1,
    "tenderers": [
      {
        "name": "Siemens AG, NL Augsburg",
        "identifier": {
          "id": "ORG-0003",
          "legalName": "Siemens AG, NL Augsburg"
        },
        "address": {
          "streetAddress": "Melli-Beese-Str. 5",
          "locality": "Augsburg",
          "region": "DE271",
          "postalCode": "86159",
          "countryName": "DEU"
        },
        "contactPoint": {
          "name": "Herr Christian Sturm",
          "email": "christian.cs.sturm@siemens.com",
          "telephone": "+49 (152) 22706977",
          "url": "http://siemens.de"
        }
      }
    ],
    "lots": [
      {
        "id": "LOT-0001",
        "title": "Optimierung/Dekarbonisierung der Kläranlage, Elektrotechnische Einbindung Rechengebäude mit PV und Gasspeicher",
        "description": "Weiterer Leistungsumfang: - Installation Niederspannungsschaltanlagen Rechengebäude und Faulgasspeicher - Installation von Mess-, Steuer-, Regel- und Elektrotechnik - Projektierung SPS-Automatisierungstechnik - Einbindung in das zentrale Prozessleitsystem - Erdungs- und Blitzschutzarbeiten - Errichtung von Kabeltrassen und Verlegesystemen - Installation von Beleuchtungs- und Gebäudeversorgungstechnik - Installation von Photovoltaikanlagen - Sicherheits- und Überwachungseinrichtungen für den Faulgasspeicher",
        "contractPeriod": {
          "startDate": "2026-08-03T00:00:00+02:00",
          "endDate": "2027-12-10T00:00:00+01:00"
        }
      }
    ]
  },
  "awards": [
    {
      "id": "LOT-0001",
      "title": "Elektrotechnische Einbindung Rechengebäude mit PV und Gasspeicher",
      "status": "active",
      "date": "2026-08-04T00:00:00+02:00",
      "value": {
        "amount": 771756.63,
        "currency": "EUR"
      },
      "relatedLots": [
        "LOT-0001"
      ]
    }
  ],
  "contracts": [
    {
      "id": "CON-0001",
      "awardID": "CON-0001",
      "title": "Elektrotechnische Einbindung Rechengebäude mit PV und Gasspeicher",
      "status": "active",
      "value": {
        "amount": 752591.15,
        "currency": "EUR"
      },
      "items": [
        {
          "id": "LOT-0001",
          "relatedLot": "LOT-0001"
        }
      ],
      "dateSigned": "2026-08-03T22:00:00.000Z"
    }
  ],
  "language": "DEU"
}
```
