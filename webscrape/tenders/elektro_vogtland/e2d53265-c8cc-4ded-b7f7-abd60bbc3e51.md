# Lieferung und Installation Bühnenbeleuchtung

**Matched company:** Elektro Vogtland GmbH
**Buyer:** Stadt Göttingen
**Value (as matched):** 778,168.00 EUR
**CPV codes (as matched):** 45237000, 45212320, 45311200, 45314320
**Region(s) (as matched):** DE91C, DE935, DEG0M
**Published:** 2026-07-13T22:00:00Z
**Notice ID:** e2d53265-c8cc-4ded-b7f7-abd60bbc3e51
**OCID:** ocds-mnwr74-c2dc85e7-ff3d-42d5-8d24-c86bd790b49a

_Matched against the `elektro_vogtland` profile in filters.yaml (match). Notes: Small electrical specialist, usually subcontractor. Saxony/Thuringia/east Bavaria, small contract sizes._

## Field inventory

What's actually populated on this release, beyond the handful of fields fetch_tenders.py currently filters on. Useful when deciding whether a field is reliable enough to add to filters.yaml as a real filter (see filters.yaml's own header for that workflow).

| Field (path) | What it would let you filter on | Status on this release |
|---|---|---|
| `tender.lots` | Per-lot breakdown (value/CPV/region can differ from tender-level) | list of 1 item(s), first: `{"id": "LOT-0000", "title": "Lieferung und Installation Bühnenbeleuchtung", "description": "##Lieferung und Installation der Bühnenbeleuchtung im Rahmen der Sanierung des Otfried-Müller-Hauses\n-Junge Theater- Hospitalstraße 6 / 37073 Göttingen\n\n##Das Bauvorhaben sieht die Sanierung des in Teilen ` |
| `tender.lotDetails` | Lot-bidding constraints (maximumLotsBidPerSupplier etc.) | _NOT PRESENT_ |
| `tender.additionalClassifications` | Secondary CPV/classification codes beyond the primary one | _NOT PRESENT_ |
| `tender.otherRequirements` | reservedParticipation, requiresStaffNamesAndQualifications, securityClearance, etc. | _NOT PRESENT_ |
| `tender.otherRequirements.reservedParticipation` | Sheltered-workshop / social-enterprise reservation codes | _NOT PRESENT_ |
| `tender.procurementMethod` | open / restricted / negotiated / etc. | open |
| `tender.procurementMethodDetails` | Free-text procedure detail | Open |
| `tender.tenderPeriod` | Submission deadline window | _NOT PRESENT_ |
| `tender.submissionMethodDetails` | How/where to submit a bid | _NOT PRESENT_ |
| `tender.value` | Tender-level estimated value | object with keys: `amount, currency` |
| `tender.items` | Item list (CPV classification lives here today) | list of 1 item(s), first: `{"id": "LOT-0000", "classification": {"scheme": "CPV", "id": "45237000", "description": "Stage construction works"}, "additionalClassifications": [{"scheme": "CPV", "id": "45212320", "description": "Construction work for buildings relating to artistic performances"}, {"scheme": "CPV", "id": "4531120` |
| `parties` | All organizations involved, with roles[] per party | list of 3 item(s), first: `{"name": "Stadt Göttingen", "id": "ORG-0001", "identifier": {"id": "031590016016-0-80", "legalName": "Stadt Göttingen"}, "address": {"streetAddress": "Hiroshimaplatz", "locality": "Göttingen", "region": "DE91C", "postalCode": "37083", "countryName": "DEU"}, "contactPoint": {"name": "Zentrale Vergabe` |
| `buyer` | The buyer party reference | object with keys: `name, id, identifier, address, contactPoint` |
| `awards` | Award-stage data (not usually present on a pre-award notice) | list of 1 item(s), first: `{"id": "LOT-0000", "title": "Lieferung und Installation Bühnenbeleuchtung", "status": "active", "date": "2026-07-14T00:00:00+02:00", "suppliers": [{"name": "LSS GmbH", "id": "DE150516887", "identifier": {"id": "ORG-9000", "legalName": "LSS GmbH"}, "address": {"streetAddress": "Sonnenstr. 5", "locali` |
| `contracts` | Contract-stage data (not usually present on a pre-award notice) | list of 1 item(s), first: `{"id": "CON-0001", "awardID": "CON-0001", "title": "Lieferung und Installation Bühnenbeleuchtung", "status": "active", "value": {"amount": 591786.88, "currency": "EUR"}, "items": [{"id": "LOT-0000", "relatedLot": "LOT-0000"}], "dateSigned": "2026-07-13T22:00:00.000Z"}` |

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
  "ocid": "ocds-mnwr74-c2dc85e7-ff3d-42d5-8d24-c86bd790b49a",
  "id": "e2d53265-c8cc-4ded-b7f7-abd60bbc3e51",
  "date": "2026-07-13T22:00:00Z",
  "tag": [
    "award"
  ],
  "initiationType": "tender",
  "parties": [
    {
      "name": "Stadt Göttingen",
      "id": "ORG-0001",
      "identifier": {
        "id": "031590016016-0-80",
        "legalName": "Stadt Göttingen"
      },
      "address": {
        "streetAddress": "Hiroshimaplatz",
        "locality": "Göttingen",
        "region": "DE91C",
        "postalCode": "37083",
        "countryName": "DEU"
      },
      "contactPoint": {
        "name": "Zentrale Vergabestelle",
        "email": "vergabestelle@goettingen.de",
        "telephone": "+49 551400-2310",
        "faxNumber": "+49 551400-3201",
        "url": "https://www.goettingen.de/"
      },
      "roles": [
        "buyer",
        "processContactPoint",
        "funder",
        "payer"
      ]
    },
    {
      "name": "Vergabekammer Niedersachsen",
      "id": "ORG-0002",
      "identifier": {
        "id": "t:04131153308",
        "legalName": "Vergabekammer Niedersachsen"
      },
      "address": {
        "streetAddress": "Auf der Hude",
        "locality": "Lüneburg",
        "region": "DE935",
        "postalCode": "21339",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "vergabekammer@mw.niedersachsen.de",
        "telephone": "+494131153308",
        "faxNumber": "+494131152943",
        "url": "https://www.mw.niedersachsen.de/startseite/themen/aufsicht_und_recht/vergabekammer_rechtslage_ab_18_04_2016/vergabekammer-niedersachsen-144803.html"
      },
      "roles": [
        "reviewContactPoint",
        "reviewBody"
      ]
    },
    {
      "name": "LSS GmbH",
      "id": "ORG-0003",
      "identifier": {
        "id": "DE150516887",
        "legalName": "LSS GmbH"
      },
      "address": {
        "streetAddress": "Sonnenstr. 5",
        "locality": "Altenburg",
        "region": "DEG0M",
        "postalCode": "04600",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "reisener@lss-lighting.de",
        "telephone": "+49 3447 83 550 0",
        "faxNumber": "+49 3447 86 177 9",
        "url": "https://lss-lighting.de/"
      },
      "roles": [
        "tenderer",
        "supplier"
      ]
    }
  ],
  "buyer": {
    "name": "Stadt Göttingen",
    "id": "031590016016-0-80",
    "identifier": {
      "id": "ORG-0001",
      "legalName": "Stadt Göttingen"
    },
    "address": {
      "streetAddress": "Hiroshimaplatz",
      "locality": "Göttingen",
      "region": "DE91C",
      "postalCode": "37083",
      "countryName": "DEU"
    },
    "contactPoint": {
      "name": "Zentrale Vergabestelle",
      "email": "vergabestelle@goettingen.de",
      "telephone": "+49 551400-2310",
      "faxNumber": "+49 551400-3201",
      "url": "https://www.goettingen.de/"
    }
  },
  "tender": {
    "id": "c2dc85e7-ff3d-42d5-8d24-c86bd790b49a",
    "title": "Lieferung und Installation Bühnenbeleuchtung",
    "description": "##Lieferung und Installation der Bühnenbeleuchtung im Rahmen der Sanierung des Otfried-Müller-Hauses\n-Junge Theater- Hospitalstraße 6 / 37073 Göttingen\nIm Rahmen der Sanierungsmaßnahmen am Otfried-Müller-Haus in Göttingen wird die Bühnenbeleuchtungsanlage des Jungen Theater svollständig erneuert, um einen flexiblen Proben- und Vorstellungsbetrieb sowie Gastspiele mit moderner Technik zu ermöglichen. \nDie Leistung umfasst eine Bühnenbeleuchtungsanlage mit Effektgeräten, dimmbarer LED-Saalbeleuchtung, Arbeits- und Blaulicht, ThruPower-Dimmermodulen für diverse Lasten sowie ein sternförmiges Lichtdatennetzwerk (DMX512 und Ethernet) mit Versatzkästen, Netzwerkknoten und Gateways.\nErgänzt werden Haupt- und Unterverteilungen, neue Lichtsteuerkonsolen sowie ein Kabel- und Leitungsnetz aus halogenfreien Energiekabeln und Cat7-Datenleitungen auf bühnentauglichen Verlegesystemen.\n\n##wesentliche Ausführungsarbeiten sind:\n#4 St. ELT-Verteiler; \n#1 St. Dimmeranlage mit 138 Dimmer- u. Schaltmodulen; \n#1 St. Lichtstellpult mit 2 St. Nebenpultsteuerungen;\n#2 St. Netzwerkschränke 42 HE mit aktiven u. passiven Komponenten; \n#59 St. Versatzkästen; \n#ca. 10000 m halogenfreie Kabel und Leitungen; \n#ca. 5500 m Datenkabel; \n#ca. 400 m Kabelrinne u. Kabelleiter; \n#ca. 280 m Stahlpanzerrohr; \n#39 St. Arbeits- u. Blaulichtleuchten;\n#34 St. Saallichtleuchten; \n#19 St. Bühnenscheinwerfer\n#div. Installationsmaterial, Bohrungen u. Brandschottungen\n\n## Erstellung der Werk- und Montageplanungen\n\n##Hinweis:\nDie Montagearbeiten auf der Baustelle sind -nach Freigabe der Werk- und Montageplanungen durch die AG- ab dem 18.12.2026 vorzusehen.",
    "procuringEntity": {
      "name": "Stadt Göttingen",
      "id": "031590016016-0-80"
    },
    "items": [
      {
        "id": "LOT-0000",
        "classification": {
          "scheme": "CPV",
          "id": "45237000",
          "description": "Stage construction works"
        },
        "additionalClassifications": [
          {
            "scheme": "CPV",
            "id": "45212320",
            "description": "Construction work for buildings relating to artistic performances"
          },
          {
            "scheme": "CPV",
            "id": "45311200",
            "description": "Electrical fitting work"
          },
          {
            "scheme": "CPV",
            "id": "45314320",
            "description": "Installation of computer cabling"
          }
        ],
        "deliveryAddress": {
          "streetAddress": "Hospitalstraße 6",
          "locality": "Göttingen",
          "region": "DE91C",
          "postalCode": "37079",
          "countryName": "DEU"
        },
        "relatedLot": "LOT-0000"
      }
    ],
    "value": {
      "amount": 778168.0,
      "currency": "EUR"
    },
    "procurementMethod": "open",
    "procurementMethodDetails": "Open",
    "mainProcurementCategory": "works",
    "additionalProcurementCategories": [
      "services"
    ],
    "awardPeriod": {
      "endDate": "2026-07-01T00:00:00+02:00"
    },
    "numberOfTenderers": 1,
    "tenderers": [
      {
        "name": "LSS GmbH",
        "identifier": {
          "id": "ORG-9000",
          "legalName": "LSS GmbH"
        },
        "address": {
          "streetAddress": "Sonnenstr. 5",
          "locality": "Altenburg",
          "region": "DEG0M",
          "postalCode": "04600",
          "countryName": "DEU"
        },
        "contactPoint": {
          "email": "reisener@lss-lighting.de",
          "telephone": "+49 3447 83 550 0",
          "faxNumber": "+49 3447 86 177 9",
          "url": "https://lss-lighting.de/"
        }
      }
    ],
    "lots": [
      {
        "id": "LOT-0000",
        "title": "Lieferung und Installation Bühnenbeleuchtung",
        "description": "##Lieferung und Installation der Bühnenbeleuchtung im Rahmen der Sanierung des Otfried-Müller-Hauses\n-Junge Theater- Hospitalstraße 6 / 37073 Göttingen\n\n##Das Bauvorhaben sieht die Sanierung des in Teilen denkmalgeschützten Otfried-Müller-Hauses und des ebenfalls in Teilen denkmalgeschützten Saalbaus vor. Der neuere, nicht geschützte Anbau wird abgerissen und durch einen neuen Anbau ersetzt. Das Gebäude steht seit Sommer 2019 leer, es ist nicht mehr in Betrieb und weist einen erheblichen Sanierungsbedarf auf. Der Bauteil Villa Otfried-Müller-Haus wurde in einer Mischung aus Mauerwerksbauweise (Keller- und Erdgeschoss) und Fachwerkbauweise (Ober- und Dachgeschoss) erstellt und weist eine Dachkonstruktion aus in der Mehrzahl bauzeitlichen Holzbalken auf. Die Decken über dem Kellergeschoss sind gemauerte Gewölbedecken und in kleinen Bereichen Holzbalkendecken. Der Saalbau besteht aus massiven Außenmauern mit einer Holzbalkendecke zum Dachraum. Die Dachkonstruktion ist eine Sprengwerkkonstruktion aus bauzeitlichen Holzbalken. Das Kellergeschoss unter dem Saal hat eine gemauerte Gewölbedecke. Die Villa besteht aus 2 Geschossen über dem Kellergeschoss und wird in der Mitte mit einem über die Geschosse durchgehenden Treppenhaus erschlossen. Der Saalbau besteht aus einem hohen Geschoss über dem Kellergeschoss, welches ungefähr die Höhe von 2 Geschossen der Villa aufweist. \n#Anbau: Der neue Anbau wird als Massivbau, hauptsächlich mit Spannbetonhohldielen als Deckenkonstruktion und mit einem üblichen Holzdachstuhl neu erstellt. Dieser Anbau wird aus einem Kellergeschoss und 2 Obergeschossen bestehen, erschlossen durch ein Treppenhaus, welches vom Keller bis in das 2. Obergeschoss reicht. Die Geschosshöhen in den Räumen des Gebäudes sind unterschiedlich. Die Höhen des Gebäudes sind den Vermesserplänen aus dem 3D-Laseraufmaß in der Anlage zu entnehmen. Die Beleuchtungs- und Heizungsanlagen des Gebäudes sind nicht mehr funktionsfähig.\n\n##Das Gebäude liegt in Ortskernlage der Stadt Göttingen, Hospitalstrasse 6, 37073 Göttingen. Vorgelagert zu dem Gebäude in östlicher und nördlicher Richtung befindet sich ein großer L-förmiger asphaltierter Platz „Am Wochenmarkt“. \n##Verkehrsverhältnisse auf der Baustelle, insbesondere Verkehrsbeschränkungen:\n#Das Halten auf dem Baustellengelände ist nur zum Aus- und Einladen zulässig. Parkplätze auf der Baustelle werden nicht gestellt. Es ist Sache jedes Unternehmers, für seine Parkplätze zu sorgen. Der Platz „Am Wochenmarkt“ darf ebenfalls nicht als Parkplatz genutzt werden, über den Platz „Am Wochenmarkt“ führt eine Feuerwehrzufahrt, die immer offengehalten werden muss. \n#Der Wochenmarkt ist in einer Belastungsklasse BK 1,0 gebaut worden. Dieses entspricht einer maximalen Achslast von 10to bei maximal 40to zulässigem Gesamtgewicht. Diese Grenzen sind in jedem Fall einzuhalten. \n\n##wichtiger Hinweis: \n#Die Nutzbarkeit von Transporteinrichtungen und Transportwegen in den Innenräumen des zu sanierenden Objekts sind eingeschränkt; diesbezüglich wird betreffend Art, Lage, Maße und  auf die Vorbemerkungen im Leistungsverzeichnis verwiesen.\n#Während des Ausführungszeitraums ist mit gewerkeübergreifenden Arbeiten im Gebäude zu rechnen\n\n\n##wesentliche Ausführungsarbeiten sind:\n#4 St. ELT-Verteiler; \n#1 St. Dimmeranlage mit 138 Dimmer- u. Schaltmodulen; \n#1 St. Lichtstellpult mit 2 St. Nebenpultsteuerungen;\n#2 St. Netzwerkschränke 42 HE mit aktiven u. passiven Komponenten; \n#59 St. Versatzkästen; \n#ca. 10000 m halogenfreie Kabel und Leitungen; \n#ca. 5500 m Datenkabel; \n#ca. 400 m Kabelrinne u. Kabelleiter; \n#ca. 280 m Stahlpanzerrohr; \n#39 St. Arbeits- u. Blaulichtleuchten;\n#34 St. Saallichtleuchten; \n#19 St. Bühnenscheinwerfer\n#div. Installationsmaterial, Bohrungen u. Brandschottungen\n\n## Erstellung der Werk- und Montageplanungen\n\nHinweis:\nDie Montagearbeiten auf der Bestelle sind nach Freigabe der Werk- und Montageplanungen durch die AG ab dem 18.12.2026 vorzusehen.",
        "value": {
          "amount": 778168.0,
          "currency": "EUR"
        },
        "contractPeriod": {
          "startDate": "2026-08-28T00:00:00+02:00",
          "endDate": "2027-10-21T00:00:00+02:00"
        }
      }
    ]
  },
  "awards": [
    {
      "id": "LOT-0000",
      "title": "Lieferung und Installation Bühnenbeleuchtung",
      "status": "active",
      "date": "2026-07-14T00:00:00+02:00",
      "suppliers": [
        {
          "name": "LSS GmbH",
          "id": "DE150516887",
          "identifier": {
            "id": "ORG-9000",
            "legalName": "LSS GmbH"
          },
          "address": {
            "streetAddress": "Sonnenstr. 5",
            "locality": "Altenburg",
            "region": "DEG0M",
            "postalCode": "04600",
            "countryName": "DEU"
          },
          "contactPoint": {
            "email": "reisener@lss-lighting.de",
            "telephone": "+49 3447 83 550 0",
            "faxNumber": "+49 3447 86 177 9",
            "url": "https://lss-lighting.de/"
          }
        }
      ],
      "relatedLots": [
        "LOT-0000"
      ]
    }
  ],
  "contracts": [
    {
      "id": "CON-0001",
      "awardID": "CON-0001",
      "title": "Lieferung und Installation Bühnenbeleuchtung",
      "status": "active",
      "value": {
        "amount": 591786.88,
        "currency": "EUR"
      },
      "items": [
        {
          "id": "LOT-0000",
          "relatedLot": "LOT-0000"
        }
      ],
      "dateSigned": "2026-07-13T22:00:00.000Z"
    }
  ],
  "language": "DEU",
  "relatedProcesses": [
    {
      "id": "298800-2026",
      "relationship": [
        "planning"
      ],
      "scheme": "ocid",
      "identifier": "298800-2026"
    }
  ]
}
```
