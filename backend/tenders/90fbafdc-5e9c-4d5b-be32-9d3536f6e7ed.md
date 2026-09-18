# Internet Relaunch des Bezirk Oberbayern

**Matched company:** company
**Buyer:** Bezirk Oberbayern
**Value (as matched):** 316,000.00 EUR
**CPV codes (as matched):** 72413000, 32412110
**Region(s) (as matched):** DE212, DEA23
**Published:** 2026-09-15T02:28:04Z
**Notice ID:** 90fbafdc-5e9c-4d5b-be32-9d3536f6e7ed
**OCID:** ocds-mnwr74-66aacb13-4fbe-473c-8083-4c83242f1b8f

_Matched against the filters.yaml profile (partial match (2/3 core criteria: nuts, value; missed: cpv)). Notes: Building construction (Hochbau) contractor based in Munich, handling contracts from roughly EUR 4.9k up to EUR 98m, with core focus on Oberbayern/Bayern and willingness to travel to adjacent German states. Explicitly excludes any offshore or marine work. [Generated at tolerance: cpv=0.50, nuts=0.50, value=0.50, exclude=0.50, role_hint=0.50]_

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
| `tender.lots` | Per-lot breakdown (value/CPV/region can differ from tender-level) | list of 1 item(s), first: `{"id": "LOT-0001", "title": "Internet Relaunch des Bezirk Oberbayern", "description": "Die bestehenden Webseiten des Bezirks Oberbayern und deren Einrichtungen erfüllen die aktuellen Anforderungen an Nutzerfreundlichkeit, Barrierefreiheit, technische Weiterentwicklungsfähigkeit sowie an eine zeitgem` |
| `tender.lotDetails` | Lot-bidding constraints (maximumLotsBidPerSupplier etc.) | _NOT PRESENT_ |
| `tender.additionalClassifications` | Secondary CPV/classification codes beyond the primary one | _NOT PRESENT_ |
| `tender.otherRequirements` | reservedParticipation, requiresStaffNamesAndQualifications, securityClearance, etc. | _NOT PRESENT_ |
| `tender.otherRequirements.reservedParticipation` | Sheltered-workshop / social-enterprise reservation codes | _NOT PRESENT_ |
| `tender.procurementMethod` | open / restricted / negotiated / etc. | _NOT PRESENT_ |
| `tender.procurementMethodDetails` | Free-text procedure detail | Negotiated with prior publication of a call for competition / competitive with negotiation |
| `tender.tenderPeriod` | Submission deadline window | _NOT PRESENT_ |
| `tender.submissionMethodDetails` | How/where to submit a bid | _NOT PRESENT_ |
| `tender.value` | Tender-level estimated value | object with keys: `amount, currency` |
| `tender.items` | Item list (CPV classification lives here today) | list of 1 item(s), first: `{"id": "LOT-0001", "classification": {"scheme": "CPV", "id": "72413000", "description": "World wide web (www) site design services"}, "additionalClassifications": [{"scheme": "CPV", "id": "32412110", "description": "Internet network"}], "deliveryAddress": {"locality": "München", "region": "DE212", "` |
| `parties` | All organizations involved, with roles[] per party | list of 4 item(s), first: `{"name": "Bezirk Oberbayern", "id": "ORG-0001", "identifier": {"id": "0420b596-8db7-4be9-b577-43cd83e0d9e6", "legalName": "Bezirk Oberbayern"}, "address": {"streetAddress": "Prinzregentenstr. 14", "locality": "München", "region": "DE212", "postalCode": "80538", "countryName": "DEU"}, "contactPoint":` |
| `buyer` | The buyer party reference | object with keys: `name, id, identifier, address, contactPoint` |
| `awards` | Award-stage data (not usually present on a pre-award notice) | list of 1 item(s), first: `{"id": "LOT-0001", "status": "active", "date": "2026-09-04T00:00:00+02:00", "value": {"amount": 762223.6, "currency": "EUR"}, "relatedLots": ["LOT-0001"]}` |
| `contracts` | Contract-stage data (not usually present on a pre-award notice) | list of 1 item(s), first: `{"id": "CON-0001", "awardID": "CON-0001", "status": "active", "value": {"amount": 390200, "currency": "EUR"}, "items": [{"id": "LOT-0001", "relatedLot": "LOT-0001"}], "dateSigned": "2026-09-03T22:00:00.000Z"}` |

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
  "ocid": "ocds-mnwr74-66aacb13-4fbe-473c-8083-4c83242f1b8f",
  "id": "90fbafdc-5e9c-4d5b-be32-9d3536f6e7ed",
  "date": "2026-09-15T02:28:04Z",
  "tag": [
    "award"
  ],
  "initiationType": "tender",
  "parties": [
    {
      "name": "Bezirk Oberbayern",
      "id": "ORG-0001",
      "identifier": {
        "id": "0420b596-8db7-4be9-b577-43cd83e0d9e6",
        "legalName": "Bezirk Oberbayern"
      },
      "address": {
        "streetAddress": "Prinzregentenstr. 14",
        "locality": "München",
        "region": "DE212",
        "postalCode": "80538",
        "countryName": "DEU"
      },
      "contactPoint": {
        "name": "Referat 11",
        "email": "vergabe@bezirk-oberbayern.de",
        "telephone": "+49 89219811300",
        "faxNumber": "+49 8921980511300",
        "url": "http://www.bezirk-oberbayern.de"
      },
      "roles": [
        "buyer"
      ]
    },
    {
      "name": "Vergabekammer Südbayern  - Regierung von Oberbayern",
      "id": "ORG-0002",
      "identifier": {
        "id": "4769482d-d217-40d7-baa7-427bc3469f46",
        "legalName": "Vergabekammer Südbayern  - Regierung von Oberbayern"
      },
      "address": {
        "streetAddress": "Maximilianstrasse 39",
        "locality": "München",
        "region": "DE212",
        "postalCode": "80538",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "poststelle@reg-ob.bayern.de",
        "telephone": "+49 8921760",
        "faxNumber": "+49 8921762914"
      },
      "roles": [
        "reviewContactPoint",
        "reviewBody"
      ]
    },
    {
      "name": "Bezirk Oberbayern ZVS",
      "id": "ORG-0003",
      "identifier": {
        "id": "1c44d1cc-b925-4568-896d-903a1a8bbd9c",
        "legalName": "Bezirk Oberbayern ZVS"
      },
      "address": {
        "streetAddress": "Prinzregentenstraße 14",
        "locality": "München",
        "region": "DE212",
        "postalCode": "80538",
        "countryName": "DEU"
      },
      "contactPoint": {
        "name": "Zentrale Vergabestelle",
        "email": "vergabe@bezirk-oberbayern.de",
        "telephone": "+49 89219811300",
        "url": "https://www.bezirk-oberbayern.de/"
      },
      "roles": [
        "processContactPoint"
      ]
    },
    {
      "name": "SUNZINET GmbH",
      "id": "ORG-0004",
      "identifier": {
        "id": "cd601b51-1b4b-4215-99d9-4eb781e2bf46",
        "legalName": "SUNZINET GmbH"
      },
      "address": {
        "locality": "Köln",
        "region": "DEA23",
        "postalCode": "51063",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "bid-management@sunzinet.com",
        "telephone": "02213550090"
      },
      "roles": [
        "tenderer",
        "supplier"
      ]
    }
  ],
  "buyer": {
    "name": "Bezirk Oberbayern",
    "id": "0420b596-8db7-4be9-b577-43cd83e0d9e6",
    "identifier": {
      "id": "ORG-0001",
      "legalName": "Bezirk Oberbayern"
    },
    "address": {
      "streetAddress": "Prinzregentenstr. 14",
      "locality": "München",
      "region": "DE212",
      "postalCode": "80538",
      "countryName": "DEU"
    },
    "contactPoint": {
      "name": "Referat 11",
      "email": "vergabe@bezirk-oberbayern.de",
      "telephone": "+49 89219811300",
      "faxNumber": "+49 8921980511300",
      "url": "http://www.bezirk-oberbayern.de"
    }
  },
  "tender": {
    "id": "66aacb13-4fbe-473c-8083-4c83242f1b8f",
    "title": "Internet Relaunch des Bezirk Oberbayern",
    "description": "Die bestehenden Webseiten des Bezirks Oberbayern und deren Einrichtungen erfüllen die aktuellen Anforderungen an Nutzerfreundlichkeit, Barrierefreiheit, technische Weiterentwicklungsfähigkeit sowie an eine zeitgemäße digitale Kommunikation nur noch eingeschränkt. Struktur, Inhalte und Nutzerführung sind nur teilweise an den Bedürfnissen der Nutzerinnen und Nutzer ausgerichtet. Zudem erschweren technische und strukturelle Einschränkungen die Weiterentwicklung der Website sowie die effiziente Pflege und Bereitstellung von Inhalten.\nVor diesem Hintergrund besteht der Bedarf, die Website des Bezirks Oberbayern konzeptionell, gestalterisch und technisch neu zu entwickeln. Ziel ist eine nutzerorientierte, barrierearme und zukunftsfähige Website, die den Zugang zu Informationen, Leistungen und Angeboten des Bezirks Oberbayern erleichtert und eine klare Orientierung für unterschiedliche Zielgruppen ermöglicht.\nDie zukünftige Website soll zudem die Marke des Bezirks Oberbayern im digitalen Raum angemessen abbilden und dessen Rolle als sozialer und kultureller Gestalter in der Region sichtbar machen.\nDie Website des Bezirks Oberbayern umfasst 892 Navigationspunkte mit Textseiten, 542 Meldungen mit ca. 1400 relevanten Textseiten. Insgesamt sind es 4043 Textseiten. Hinzu kommen 3700 Adressen (3100 in der Einrichtungssuche), die perspektivisch über eine Schnittstelle eingebunden werden können. Die Website zählt aktuell 6152 Medien.\n",
    "procuringEntity": {
      "name": "Bezirk Oberbayern",
      "id": "0420b596-8db7-4be9-b577-43cd83e0d9e6"
    },
    "items": [
      {
        "id": "LOT-0001",
        "classification": {
          "scheme": "CPV",
          "id": "72413000",
          "description": "World wide web (www) site design services"
        },
        "additionalClassifications": [
          {
            "scheme": "CPV",
            "id": "32412110",
            "description": "Internet network"
          }
        ],
        "deliveryAddress": {
          "locality": "München",
          "region": "DE212",
          "postalCode": "80538",
          "countryName": "DEU"
        },
        "relatedLot": "LOT-0001"
      }
    ],
    "value": {
      "amount": 316000.0,
      "currency": "EUR"
    },
    "procurementMethodDetails": "Negotiated with prior publication of a call for competition / competitive with negotiation",
    "mainProcurementCategory": "services",
    "awardPeriod": {
      "endDate": "2026-08-18T00:00:00+02:00"
    },
    "numberOfTenderers": 1,
    "tenderers": [
      {
        "name": "SUNZINET GmbH",
        "identifier": {
          "id": "ORG-0004",
          "legalName": "SUNZINET GmbH"
        },
        "address": {
          "locality": "Köln",
          "region": "DEA23",
          "postalCode": "51063",
          "countryName": "DEU"
        },
        "contactPoint": {
          "email": "bid-management@sunzinet.com",
          "telephone": "02213550090"
        }
      }
    ],
    "lots": [
      {
        "id": "LOT-0001",
        "title": "Internet Relaunch des Bezirk Oberbayern",
        "description": "Die bestehenden Webseiten des Bezirks Oberbayern und deren Einrichtungen erfüllen die aktuellen Anforderungen an Nutzerfreundlichkeit, Barrierefreiheit, technische Weiterentwicklungsfähigkeit sowie an eine zeitgemäße digitale Kommunikation nur noch eingeschränkt. Struktur, Inhalte und Nutzerführung sind nur teilweise an den Bedürfnissen der Nutzerinnen und Nutzer ausgerichtet. Zudem erschweren technische und strukturelle Einschränkungen die Weiterentwicklung der Website sowie die effiziente Pflege und Bereitstellung von Inhalten.\nVor diesem Hintergrund besteht der Bedarf, die Website des Bezirks Oberbayern konzeptionell, gestalterisch und technisch neu zu entwickeln. Ziel ist eine nutzerorientierte, barrierearme und zukunftsfähige Website, die den Zugang zu Informationen, Leistungen und Angeboten des Bezirks Oberbayern erleichtert und eine klare Orientierung für unterschiedliche Zielgruppen ermöglicht.\nDie zukünftige Website soll zudem die Marke des Bezirks Oberbayern im digitalen Raum angemessen abbilden und dessen Rolle als sozialer und kultureller Gestalter in der Region sichtbar machen.\nDie Website des Bezirks Oberbayern umfasst 892 Navigationspunkte mit Textseiten, 542 Meldungen mit ca. 1400 relevanten Textseiten. Insgesamt sind es 4043 Textseiten. Hinzu kommen 3700 Adressen (3100 in der Einrichtungssuche), die perspektivisch über eine Schnittstelle eingebunden werden können. Die Website zählt aktuell 6152 Medien.\n",
        "contractPeriod": {
          "startDate": "2026-10-01T00:00:00+02:00",
          "endDate": "2030-09-30T00:00:00+02:00"
        }
      }
    ]
  },
  "awards": [
    {
      "id": "LOT-0001",
      "status": "active",
      "date": "2026-09-04T00:00:00+02:00",
      "value": {
        "amount": 762223.6,
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
      "status": "active",
      "value": {
        "amount": 390200,
        "currency": "EUR"
      },
      "items": [
        {
          "id": "LOT-0001",
          "relatedLot": "LOT-0001"
        }
      ],
      "dateSigned": "2026-09-03T22:00:00.000Z"
    }
  ],
  "language": "DEU"
}
```
