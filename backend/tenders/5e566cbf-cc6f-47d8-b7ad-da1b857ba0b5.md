# Lieferung einer meteorologischen Drohne zur Wetterbeobachtung

**Matched company:** company
**Buyer:** Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)
**Value (as matched):** 249,000.00 EUR
**CPV codes (as matched):** 34711200
**Region(s) (as matched):** DEA22, DEA23, DEE0C
**Published:** 2026-09-17T02:06:30Z
**Notice ID:** 5e566cbf-cc6f-47d8-b7ad-da1b857ba0b5
**OCID:** ocds-mnwr74-1f5cd467-a3ec-45fe-ab80-3b1295b68454

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
| `tender.lots` | Per-lot breakdown (value/CPV/region can differ from tender-level) | list of 1 item(s), first: `{"id": "LOT-0001", "title": "Lieferung einer meteorologischen Drohne zur Wetterbeobachtung", "description": "Der Standort Cochstedt des Deutschen Zentrums für Luft- und Raumfahrt (DLR) beabsichtigt die Beschaffung eines unbemannten Luftfahrtsystems zur Erfassung meteorologischer Messdaten in boden-n` |
| `tender.lotDetails` | Lot-bidding constraints (maximumLotsBidPerSupplier etc.) | _NOT PRESENT_ |
| `tender.additionalClassifications` | Secondary CPV/classification codes beyond the primary one | _NOT PRESENT_ |
| `tender.otherRequirements` | reservedParticipation, requiresStaffNamesAndQualifications, securityClearance, etc. | _NOT PRESENT_ |
| `tender.otherRequirements.reservedParticipation` | Sheltered-workshop / social-enterprise reservation codes | _NOT PRESENT_ |
| `tender.procurementMethod` | open / restricted / negotiated / etc. | open |
| `tender.procurementMethodDetails` | Free-text procedure detail | Open |
| `tender.tenderPeriod` | Submission deadline window | _NOT PRESENT_ |
| `tender.submissionMethodDetails` | How/where to submit a bid | _NOT PRESENT_ |
| `tender.value` | Tender-level estimated value | object with keys: `amount, currency` |
| `tender.items` | Item list (CPV classification lives here today) | list of 1 item(s), first: `{"id": "LOT-0001", "classification": {"scheme": "CPV", "id": "34711200", "description": "Non-piloted aircraft"}, "deliveryAddress": {"streetAddress": "Harzstraße 1", "locality": "Hecklingen", "region": "DEE0C", "postalCode": "39444", "countryName": "DEU"}, "relatedLot": "LOT-0001"}` |
| `parties` | All organizations involved, with roles[] per party | list of 2 item(s), first: `{"name": "Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)", "id": "ORG-0001", "identifier": {"id": "Leitweg-ID 992-03005-81", "legalName": "Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)"}, "address": {"streetAddress": "Linder Höhe", "locality": "Köln", "region": "DEA23", "postalCode": "5` |
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
  "ocid": "ocds-mnwr74-1f5cd467-a3ec-45fe-ab80-3b1295b68454",
  "id": "5e566cbf-cc6f-47d8-b7ad-da1b857ba0b5",
  "date": "2026-09-17T02:06:30Z",
  "tag": [
    "tender"
  ],
  "initiationType": "tender",
  "parties": [
    {
      "name": "Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)",
      "id": "ORG-0001",
      "identifier": {
        "id": "Leitweg-ID 992-03005-81",
        "legalName": "Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)"
      },
      "address": {
        "streetAddress": "Linder Höhe",
        "locality": "Köln",
        "region": "DEA23",
        "postalCode": "51147",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "evergabe@dlr.de",
        "telephone": "0 00",
        "url": "https://www.dlr.de"
      },
      "roles": [
        "buyer"
      ]
    },
    {
      "name": "Vergabekammer des Bundes",
      "id": "ORG-0002",
      "identifier": {
        "id": "991-02380-92",
        "legalName": "Vergabekammer des Bundes"
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
        "telephone": "+492289499578",
        "faxNumber": "+492289499163",
        "url": "http://www.bundeskartellamt.de"
      },
      "roles": [
        "reviewBody"
      ]
    }
  ],
  "buyer": {
    "name": "Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)",
    "id": "Leitweg-ID 992-03005-81",
    "identifier": {
      "id": "ORG-0001",
      "legalName": "Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)"
    },
    "address": {
      "streetAddress": "Linder Höhe",
      "locality": "Köln",
      "region": "DEA23",
      "postalCode": "51147",
      "countryName": "DEU"
    },
    "contactPoint": {
      "email": "evergabe@dlr.de",
      "telephone": "0 00",
      "url": "https://www.dlr.de"
    }
  },
  "tender": {
    "id": "1f5cd467-a3ec-45fe-ab80-3b1295b68454",
    "title": "Lieferung einer meteorologischen Drohne zur Wetterbeobachtung",
    "description": "Der Standort Cochstedt des Deutschen Zentrums für Luft- und Raumfahrt (DLR) beabsichtigt die Beschaffung eines unbemannten Luftfahrtsystems zur Erfassung meteorologischer Messdaten in boden-nahen und unteren Atmosphärenschichten. Das System soll für Forschungs-, Entwicklungs- und Erprobungszwecke eingesetzt werden und eine flexible, hochaufgelöste Erfassung von\nWetter- und Umweltdaten ermöglichen.",
    "procuringEntity": {
      "name": "Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)",
      "id": "Leitweg-ID 992-03005-81"
    },
    "items": [
      {
        "id": "LOT-0001",
        "classification": {
          "scheme": "CPV",
          "id": "34711200",
          "description": "Non-piloted aircraft"
        },
        "deliveryAddress": {
          "streetAddress": "Harzstraße 1",
          "locality": "Hecklingen",
          "region": "DEE0C",
          "postalCode": "39444",
          "countryName": "DEU"
        },
        "relatedLot": "LOT-0001"
      }
    ],
    "value": {
      "amount": 249000.0,
      "currency": "EUR"
    },
    "procurementMethod": "open",
    "procurementMethodDetails": "Open",
    "mainProcurementCategory": "goods",
    "numberOfTenderers": 0,
    "documents": [
      {
        "id": "DOC-0001",
        "url": "https://www.subreport.de/E26114163",
        "language": "DEU",
        "relatedLots": [
          "LOT-0001"
        ]
      }
    ],
    "lots": [
      {
        "id": "LOT-0001",
        "title": "Lieferung einer meteorologischen Drohne zur Wetterbeobachtung",
        "description": "Der Standort Cochstedt des Deutschen Zentrums für Luft- und Raumfahrt (DLR) beabsichtigt die Beschaffung eines unbemannten Luftfahrtsystems zur Erfassung meteorologischer Messdaten in boden-nahen und unteren Atmosphärenschichten. Das System soll für Forschungs-, Entwicklungs- und Erprobungszwecke eingesetzt werden und eine flexible, hochaufgelöste Erfassung von\nWetter- und Umweltdaten ermöglichen.",
        "value": {
          "amount": 249000.0,
          "currency": "EUR"
        }
      }
    ]
  },
  "language": "DEU"
}
```
