# Fassadensanierung SVLFG Geschäftsstelle Landshut - Los 08 - Elektroarbeiten (PV-Anlage)

**Matched company:** Elektro Vogtland GmbH
**Buyer:** Sozialversicherung für Landwirtschaft, Forsten und Gartenbau (SVLFG)
**Value (as matched):** 316,526.16 EUR
**CPV codes (as matched):** 45215100, 45311000
**Region(s) (as matched):** DE221, DE731, DEA22, DEB1B
**Published:** 2026-08-22T15:08:05Z
**Notice ID:** fdedf43a-b975-4c01-bab0-6c30cae2f7be
**OCID:** ocds-mnwr74-5df3b5f2-039e-4e04-a19d-87d43d727958

_Matched against the `elektro_vogtland` profile in filters.yaml (match). Notes: Small electrical specialist, usually subcontractor. Saxony/Thuringia/east Bavaria, small contract sizes._

## Field inventory

What's actually populated on this release, beyond the handful of fields fetch_tenders.py currently filters on. Useful when deciding whether a field is reliable enough to add to filters.yaml as a real filter (see filters.yaml's own header for that workflow).

| Field (path) | What it would let you filter on | Status on this release |
|---|---|---|
| `tender.lots` | Per-lot breakdown (value/CPV/region can differ from tender-level) | list of 1 item(s), first: `{"id": "LOT-0001", "title": "Fassadensanierung SVLFG Geschäftsstelle Landshut - Los 08 - Elektroarbeiten (PV-Anlage)", "description": "Errichtung einer Photovoltaikanlage mit einer Leistung von ca. 210 kWp verteilt auf 4 gleichgroße Dachflächen inkl. Stromspeicher.", "value": {"amount": 316526.16, "` |
| `tender.lotDetails` | Lot-bidding constraints (maximumLotsBidPerSupplier etc.) | _NOT PRESENT_ |
| `tender.additionalClassifications` | Secondary CPV/classification codes beyond the primary one | _NOT PRESENT_ |
| `tender.otherRequirements` | reservedParticipation, requiresStaffNamesAndQualifications, securityClearance, etc. | _NOT PRESENT_ |
| `tender.otherRequirements.reservedParticipation` | Sheltered-workshop / social-enterprise reservation codes | _NOT PRESENT_ |
| `tender.procurementMethod` | open / restricted / negotiated / etc. | open |
| `tender.procurementMethodDetails` | Free-text procedure detail | Open |
| `tender.tenderPeriod` | Submission deadline window | _NOT PRESENT_ |
| `tender.submissionMethodDetails` | How/where to submit a bid | _NOT PRESENT_ |
| `tender.value` | Tender-level estimated value | object with keys: `amount, currency` |
| `tender.items` | Item list (CPV classification lives here today) | list of 1 item(s), first: `{"id": "LOT-0001", "classification": {"scheme": "CPV", "id": "45215100", "description": "Construction work for buildings relating to health"}, "additionalClassifications": [{"scheme": "CPV", "id": "45311000", "description": "Electrical wiring and fitting work"}], "deliveryAddress": {"streetAddress":` |
| `parties` | All organizations involved, with roles[] per party | list of 3 item(s), first: `{"name": "Sozialversicherung für Landwirtschaft, Forsten und Gartenbau (SVLFG)", "id": "ORG-0001", "identifier": {"id": "Leitweg-ID 9930176733", "legalName": "Sozialversicherung für Landwirtschaft, Forsten und Gartenbau (SVLFG)"}, "address": {"streetAddress": "Weißensteinstr. 70 -72", "locality": "K` |
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
  "ocid": "ocds-mnwr74-5df3b5f2-039e-4e04-a19d-87d43d727958",
  "id": "fdedf43a-b975-4c01-bab0-6c30cae2f7be",
  "date": "2026-08-22T15:08:05Z",
  "tag": [
    "tender"
  ],
  "initiationType": "tender",
  "parties": [
    {
      "name": "Sozialversicherung für Landwirtschaft, Forsten und Gartenbau (SVLFG)",
      "id": "ORG-0001",
      "identifier": {
        "id": "Leitweg-ID 9930176733",
        "legalName": "Sozialversicherung für Landwirtschaft, Forsten und Gartenbau (SVLFG)"
      },
      "address": {
        "streetAddress": "Weißensteinstr. 70 -72",
        "locality": "Kassel",
        "region": "DE731",
        "postalCode": "34131",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "ausschreibung@svlfg.de",
        "telephone": "+49 561785-0",
        "url": "http://www.svlfg.de"
      },
      "roles": [
        "buyer"
      ]
    },
    {
      "name": "VBS Vergabeberatungsstelle GmbH",
      "id": "ORG-0002",
      "identifier": {
        "id": "DE364668695",
        "legalName": "VBS Vergabeberatungsstelle GmbH"
      },
      "address": {
        "streetAddress": "Auf dem Kalk 5",
        "locality": "Montabaur",
        "region": "DEB1B",
        "postalCode": "56410",
        "countryName": "DEU"
      },
      "roles": [
        "procurementServiceProvider",
        "evaluationBody",
        "submissionReceiptBody"
      ]
    },
    {
      "name": "Vergabekammer des Bundes",
      "id": "ORG-0003",
      "identifier": {
        "id": "T:0022894990",
        "legalName": "Vergabekammer des Bundes"
      },
      "address": {
        "streetAddress": "Villemomblerstraße 76",
        "locality": "Bonn",
        "region": "DEA22",
        "postalCode": "53123",
        "countryName": "DEU"
      },
      "roles": [
        "reviewBody"
      ]
    }
  ],
  "buyer": {
    "name": "Sozialversicherung für Landwirtschaft, Forsten und Gartenbau (SVLFG)",
    "id": "Leitweg-ID 9930176733",
    "identifier": {
      "id": "ORG-0001",
      "legalName": "Sozialversicherung für Landwirtschaft, Forsten und Gartenbau (SVLFG)"
    },
    "address": {
      "streetAddress": "Weißensteinstr. 70 -72",
      "locality": "Kassel",
      "region": "DE731",
      "postalCode": "34131",
      "countryName": "DEU"
    },
    "contactPoint": {
      "email": "ausschreibung@svlfg.de",
      "telephone": "+49 561785-0",
      "url": "http://www.svlfg.de"
    }
  },
  "tender": {
    "id": "5df3b5f2-039e-4e04-a19d-87d43d727958",
    "title": "Fassadensanierung SVLFG Geschäftsstelle Landshut - Los 08 - Elektroarbeiten (PV-Anlage)",
    "description": "Los 08 - Elektroarbeiten (PV-Anlage)\n- Errichtung einer Photovoltaikanlage mit einer Leistung von ca. 210 kWp verteilt auf 4 gleichgroße Dachflächen inkl. Stromspeicher.",
    "procuringEntity": {
      "name": "Sozialversicherung für Landwirtschaft, Forsten und Gartenbau (SVLFG)",
      "id": "Leitweg-ID 9930176733"
    },
    "items": [
      {
        "id": "LOT-0001",
        "classification": {
          "scheme": "CPV",
          "id": "45215100",
          "description": "Construction work for buildings relating to health"
        },
        "additionalClassifications": [
          {
            "scheme": "CPV",
            "id": "45311000",
            "description": "Electrical wiring and fitting work"
          }
        ],
        "deliveryAddress": {
          "streetAddress": "Dr.-Georg-Heim-Allee 1",
          "locality": "Landshut",
          "region": "DE221",
          "postalCode": "84036",
          "countryName": "DEU"
        },
        "relatedLot": "LOT-0001"
      }
    ],
    "value": {
      "amount": 316526.16,
      "currency": "EUR"
    },
    "procurementMethod": "open",
    "procurementMethodDetails": "Open",
    "mainProcurementCategory": "works",
    "numberOfTenderers": 0,
    "documents": [
      {
        "id": "DOC-0001",
        "url": "https://www.subreport.de/E91655489",
        "language": "DEU",
        "relatedLots": [
          "LOT-0001"
        ]
      }
    ],
    "amendments": [
      {
        "date": "2026-08-22T15:08:05.757Z",
        "rationale": "Die Eignungskriterien werden um das Kriterium \"Referenzen zu bestimmten Arbeiten\" ergänzt.",
        "description": "Kriterium: Referenzen zu bestimmten Arbeiten\n\nAngaben, die mit dem Angebot vorzulegen sind: --- 1.) Eigenerklärung über die Ausführung vergleichbarer Leistungen in den letzten fünf Jahren --- 2.) Eigenerklärung über die Bereithaltung der für die Ausführung der Leistung erforderlichen Arbeitskräfte --- Für die vorgenannten Auskünfte (Eigenerklärungen) sind entsprechende Formblätter den Vergabeunterlagen beigefügt (Formblatt 124). Ebenso zugelassen ist die Vorlage\neiner Einheitlichen Europäischen Eigenerklärung (EEE) als vorläufiger Beleg der Eignung. Eigenerklärungen und Eignungsnachweise, die durch Präqualifizierung geführt werden, sind zugelassen. Die durch Präqualifizierung geführten Eigenerklärungen und Eignungsnachweise\nmüssen die gestellten auftragsbezogenen Mindestanforderungen nachweisen. ---- . Auf Verlangen der Vergabestelle sind durch den Bieter zum Beleg seiner Eigenerklärungen folgende Nachweise vorzulegen: Drei Referenzen, die mit der ausgeschriebenen Leistung vergleichbar sind, mit folgenden Angaben: Ansprechpartner; Art der ausgeführten Leistung; Auftragssumme; Ausführungszeitraum; stichwortartige Benennung des ausgeführten maßgeblichen Leistungsumfanges,  Angaben zu Arbeitskräften: Zahl der in den letzten 3 abgeschlossenen Geschäftsjahren\njahresdurchschnittlich beschäftigten Arbeitskräfte, gegliedert nach Lohngruppen mit extra ausgewiesenem Leitungspersonal. --- . Werden die Leistungen von einer Bietergemeinschaft angeboten, sind die Auskünfte/Nachweise für jedes Mitglied der Bietergemeinschaft zu erklären. Will sich der Bieter bei der Leistungserbringung eines Dritten (Nachunternehmer, Eignungsleihe) bedienen, sind die Auskünfte erforderlichenfalls auch von Dritten abzugeben. Die Vergabestelle behält sich vor, weitere Erklärungen oder Nachweise zur Eignung anzufordern.",
        "amendsReleaseID": "5e95bf1e-3505-4494-9f26-f05dff4acb87-01",
        "releaseID": "fdedf43a-b975-4c01-bab0-6c30cae2f7be-01"
      }
    ],
    "lots": [
      {
        "id": "LOT-0001",
        "title": "Fassadensanierung SVLFG Geschäftsstelle Landshut - Los 08 - Elektroarbeiten (PV-Anlage)",
        "description": "Errichtung einer Photovoltaikanlage mit einer Leistung von ca. 210 kWp verteilt auf 4 gleichgroße Dachflächen inkl. Stromspeicher.",
        "value": {
          "amount": 316526.16,
          "currency": "EUR"
        },
        "contractPeriod": {
          "startDate": "2026-11-30T00:00:00+01:00",
          "endDate": "2027-07-07T00:00:00+02:00"
        }
      }
    ]
  },
  "language": "DEU"
}
```
