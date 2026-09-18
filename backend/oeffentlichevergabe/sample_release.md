# Sample OCDS release — 2026-09-16

- **Source day:** 2026-09-16
- **Source file in ZIP:** `0010ea9b-1249-49d6-afe2-6a10ac0d7b74-01.json`
- **Notice ID:** `0010ea9b-1249-49d6-afe2-6a10ac0d7b74`
- **OCID:** `ocds-mnwr74-f96533a2-d790-4874-8b0d-3dd88d695b15`
- **Title:** ARV Lieferung von Standardverkehrszeichen RB Ost, RB Süd und RB West 2027

This file is diagnostic output from `inspect_release.py`, generated to check which OCDS/eForms fields are actually populated on real Bekanntmachungsservice notices before deciding what to add to `filters.yaml` / `company_profiles.py`. It is not consumed by `fetch_tenders.py`.

## Field inventory (every field present on this release)

Full recursive walk of the release — every leaf field actually present, not just a hand-picked subset. A field missing here might still appear on other notices, so check a few more samples with different `--day` / `--notice-id` values before ruling anything out or building a filter around it.

| Field (path) | Value |
|---|---|
| `ocid` | ocds-mnwr74-f96533a2-d790-4874-8b0d-3dd88d695b15 |
| `id` | 0010ea9b-1249-49d6-afe2-6a10ac0d7b74 |
| `date` | 2026-09-16T02:06:28Z |
| `tag[0]` | tender |
| `initiationType` | tender |
| `parties[0].name` | Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten |
| `parties[0].id` | ORG-0001 |
| `parties[0].identifier.id` | 121000 |
| `parties[0].identifier.legalName` | Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten |
| `parties[0].address.streetAddress` | Lindenallee 51 |
| `parties[0].address.locality` | Hoppegarten |
| `parties[0].address.region` | DE409 |
| `parties[0].address.postalCode` | 15366 |
| `parties[0].address.countryName` | DEU |
| `parties[0].contactPoint.name` | Dezernat Vergabe und Vertragswesen |
| `parties[0].contactPoint.email` | LS-Vergabestelle@LS.Brandenburg.de |
| `parties[0].contactPoint.telephone` | +49 3342-249-1017 |
| `parties[0].contactPoint.faxNumber` | +49 3342-249-1193 |
| `parties[0].contactPoint.url` | http://www.ausschreibungen.ls.brandenburg.de |
| `parties[0].roles[0]` | buyer |
| `parties[0].roles[1]` | processContactPoint |
| `parties[0].roles[2]` | submissionReceiptBody |
| `parties[1].name` | Vergabekammer des Landes Brandenburg beim Ministerium für Wirtschaft, Energie, Klimaschutz und Europa |
| `parties[1].id` | ORG-0002 |
| `parties[1].identifier.id` | 12 |
| `parties[1].identifier.legalName` | Vergabekammer des Landes Brandenburg beim Ministerium für Wirtschaft, Energie, Klimaschutz und Europa |
| `parties[1].address.streetAddress` | Heinrich-Mann-Allee 107 |
| `parties[1].address.locality` | Potsdam |
| `parties[1].address.region` | DE404 |
| `parties[1].address.postalCode` | 14473 |
| `parties[1].address.countryName` | DEU |
| `parties[1].contactPoint.email` | Vergabekammer@MWEKE.Brandenburg.de |
| `parties[1].roles[0]` | reviewBody |
| `parties[2].name` | Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten |
| `parties[2].id` | ORG-0003 |
| `parties[2].identifier.id` | 121000 |
| `parties[2].identifier.legalName` | Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten |
| `parties[2].address.locality` | Hoppegarten |
| `parties[2].address.region` | DE409 |
| `parties[2].address.postalCode` | 15366 |
| `parties[2].address.countryName` | DEU |
| `parties[2].roles[0]` | reviewContactPoint |
| `parties[3].name` | Ministerium für Infrastruktur und Landesplanung, Abt. 4, Ref. 47 |
| `parties[3].id` | ORG-0004 |
| `parties[3].identifier.id` | 12 |
| `parties[3].identifier.legalName` | Ministerium für Infrastruktur und Landesplanung, Abt. 4, Ref. 47 |
| `parties[3].address.locality` | Potsdam |
| `parties[3].address.region` | DE404 |
| `parties[3].address.postalCode` | 14467 |
| `parties[3].address.countryName` | DEU |
| `parties[3].roles[0]` | mediationBody |
| `buyer.name` | Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten |
| `buyer.id` | 121000 |
| `buyer.identifier.id` | ORG-7001 |
| `buyer.identifier.legalName` | Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten |
| `buyer.address.streetAddress` | Lindenallee 51 |
| `buyer.address.locality` | Hoppegarten |
| `buyer.address.region` | DE409 |
| `buyer.address.postalCode` | 15366 |
| `buyer.address.countryName` | DEU |
| `buyer.contactPoint.name` | Dezernat Vergabe und Vertragswesen |
| `buyer.contactPoint.email` | LS-Vergabestelle@LS.Brandenburg.de |
| `buyer.contactPoint.telephone` | +49 3342-249-1017 |
| `buyer.contactPoint.faxNumber` | +49 3342-249-1193 |
| `buyer.contactPoint.url` | http://www.ausschreibungen.ls.brandenburg.de |
| `tender.id` | f96533a2-d790-4874-8b0d-3dd88d695b15 |
| `tender.title` | ARV Lieferung von Standardverkehrszeichen RB Ost, RB Süd und RB West 2027 |
| `tender.description` | Abrufvertrag - Lieferung von Standardverkehrszeichen im Regionalbereich Ost, Süd und West im Land Brandenburg - 2027 |
| `tender.procuringEntity.name` | Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten |
| `tender.procuringEntity.id` | 121000 |
| `tender.items[0].id` | LOT-0000 |
| `tender.items[0].classification.scheme` | CPV |
| `tender.items[0].classification.id` | 34992200 |
| `tender.items[0].classification.description` | Road signs |
| `tender.items[0].deliveryLocation.description` | 33 Straßenmeistereien im gesamten Land Brandenburg |
| `tender.items[0].deliveryAddress.streetAddress` | Landesbetrieb Straßenwesen Brandenburg, Betriebssitz Hoppegarten |
| `tender.items[0].deliveryAddress.locality` | Hoppegarten |
| `tender.items[0].deliveryAddress.region` | DE409 |
| `tender.items[0].deliveryAddress.postalCode` | 15366 |
| `tender.items[0].deliveryAddress.countryName` | DEU |
| `tender.items[0].relatedLot` | LOT-0000 |
| `tender.procurementMethod` | open |
| `tender.procurementMethodDetails` | Open |
| `tender.mainProcurementCategory` | goods |
| `tender.numberOfTenderers` | `0` |
| `tender.documents[0].id` | DOC-0001 |
| `tender.documents[0].url` | https://www.ausschreibungen.ls.brandenburg.de/NetServer/TenderingProcedureDetails?function=_Details&TenderOID=54321-Tender-1a08f33e534-740f1575de969945 |
| `tender.documents[0].language` | DEU |
| `tender.documents[0].relatedLots[0]` | LOT-0000 |
| `tender.lots[0].id` | LOT-0000 |
| `tender.lots[0].title` | ARV Lieferung von Standardverkehrszeichen RB Ost, RB Süd und RB West 2027 |
| `tender.lots[0].description` | ca. 1.445 St Verkehrszeichen-Gruppe 100 ca. 2.445 St Verkehrszeichen-Gruppe 200 ca. 885 St Verkehrszeichen-Gruppe 300 - 400 ca. 616 St Orts- und Hinweistafeln und Wegweiser ca. 25 St Verkehrszeichen-Gruppe 500 ca. 1.555 St Verkehrszeichen-Gruppe 600 ca. 2.070 St Zusatzzeichen |
| `tender.lots[0].contractPeriod.startDate` | 2027-01-01T00:00:00+01:00 |
| `tender.lots[0].contractPeriod.endDate` | 2027-12-31T00:00:00+01:00 |
| `language` | DEU |

## Fields fetch_tenders.py currently reads

For comparison — these are the only fields the current matching logic (`get_release_cpvs`, `get_release_regions`, `get_release_value`, `get_release_text_blob` in `fetch_tenders.py`) actually looks at:

- `tender.items[].classification.id` (CPV codes)
- `tender.items[].deliveryAddress.region`, `buyer.address.region`, `parties[].address.region` (NUTS codes)
- `tender.value.amount` / `tender.value.currency`, falling back to summed `tender.lots[].value`
- `tender.title`, `tender.description`, `tender.procurementMethodRationale`, `tender.lots[].title`, `tender.lots[].description` (as one lowercased text blob for keyword matching)

## Full raw release JSON

```json
{
  "ocid": "ocds-mnwr74-f96533a2-d790-4874-8b0d-3dd88d695b15",
  "id": "0010ea9b-1249-49d6-afe2-6a10ac0d7b74",
  "date": "2026-09-16T02:06:28Z",
  "tag": [
    "tender"
  ],
  "initiationType": "tender",
  "parties": [
    {
      "name": "Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten",
      "id": "ORG-0001",
      "identifier": {
        "id": "121000",
        "legalName": "Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten"
      },
      "address": {
        "streetAddress": "Lindenallee 51",
        "locality": "Hoppegarten",
        "region": "DE409",
        "postalCode": "15366",
        "countryName": "DEU"
      },
      "contactPoint": {
        "name": "Dezernat Vergabe und Vertragswesen",
        "email": "LS-Vergabestelle@LS.Brandenburg.de",
        "telephone": "+49 3342-249-1017",
        "faxNumber": "+49 3342-249-1193",
        "url": "http://www.ausschreibungen.ls.brandenburg.de"
      },
      "roles": [
        "buyer",
        "processContactPoint",
        "submissionReceiptBody"
      ]
    },
    {
      "name": "Vergabekammer des Landes Brandenburg beim Ministerium für Wirtschaft, Energie, Klimaschutz und Europa",
      "id": "ORG-0002",
      "identifier": {
        "id": "12",
        "legalName": "Vergabekammer des Landes Brandenburg beim Ministerium für Wirtschaft, Energie, Klimaschutz und Europa"
      },
      "address": {
        "streetAddress": "Heinrich-Mann-Allee 107",
        "locality": "Potsdam",
        "region": "DE404",
        "postalCode": "14473",
        "countryName": "DEU"
      },
      "contactPoint": {
        "email": "Vergabekammer@MWEKE.Brandenburg.de"
      },
      "roles": [
        "reviewBody"
      ]
    },
    {
      "name": "Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten",
      "id": "ORG-0003",
      "identifier": {
        "id": "121000",
        "legalName": "Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten"
      },
      "address": {
        "locality": "Hoppegarten",
        "region": "DE409",
        "postalCode": "15366",
        "countryName": "DEU"
      },
      "roles": [
        "reviewContactPoint"
      ]
    },
    {
      "name": "Ministerium für Infrastruktur und Landesplanung, Abt. 4, Ref. 47",
      "id": "ORG-0004",
      "identifier": {
        "id": "12",
        "legalName": "Ministerium für Infrastruktur und Landesplanung, Abt. 4, Ref. 47"
      },
      "address": {
        "locality": "Potsdam",
        "region": "DE404",
        "postalCode": "14467",
        "countryName": "DEU"
      },
      "roles": [
        "mediationBody"
      ]
    }
  ],
  "buyer": {
    "name": "Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten",
    "id": "121000",
    "identifier": {
      "id": "ORG-7001",
      "legalName": "Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten"
    },
    "address": {
      "streetAddress": "Lindenallee 51",
      "locality": "Hoppegarten",
      "region": "DE409",
      "postalCode": "15366",
      "countryName": "DEU"
    },
    "contactPoint": {
      "name": "Dezernat Vergabe und Vertragswesen",
      "email": "LS-Vergabestelle@LS.Brandenburg.de",
      "telephone": "+49 3342-249-1017",
      "faxNumber": "+49 3342-249-1193",
      "url": "http://www.ausschreibungen.ls.brandenburg.de"
    }
  },
  "tender": {
    "id": "f96533a2-d790-4874-8b0d-3dd88d695b15",
    "title": "ARV Lieferung von Standardverkehrszeichen RB Ost, RB Süd und RB West 2027",
    "description": "Abrufvertrag - Lieferung von Standardverkehrszeichen im Regionalbereich Ost, Süd und West im Land Brandenburg - 2027",
    "procuringEntity": {
      "name": "Landesbetrieb Straßenwesen Brandenburg Betriebssitz Hoppegarten",
      "id": "121000"
    },
    "items": [
      {
        "id": "LOT-0000",
        "classification": {
          "scheme": "CPV",
          "id": "34992200",
          "description": "Road signs"
        },
        "deliveryLocation": {
          "description": "33 Straßenmeistereien im gesamten Land Brandenburg"
        },
        "deliveryAddress": {
          "streetAddress": "Landesbetrieb Straßenwesen Brandenburg, Betriebssitz Hoppegarten",
          "locality": "Hoppegarten",
          "region": "DE409",
          "postalCode": "15366",
          "countryName": "DEU"
        },
        "relatedLot": "LOT-0000"
      }
    ],
    "procurementMethod": "open",
    "procurementMethodDetails": "Open",
    "mainProcurementCategory": "goods",
    "numberOfTenderers": 0,
    "documents": [
      {
        "id": "DOC-0001",
        "url": "https://www.ausschreibungen.ls.brandenburg.de/NetServer/TenderingProcedureDetails?function=_Details&TenderOID=54321-Tender-1a08f33e534-740f1575de969945",
        "language": "DEU",
        "relatedLots": [
          "LOT-0000"
        ]
      }
    ],
    "lots": [
      {
        "id": "LOT-0000",
        "title": "ARV Lieferung von Standardverkehrszeichen RB Ost, RB Süd und RB West 2027",
        "description": "ca. 1.445 St Verkehrszeichen-Gruppe 100\nca. 2.445 St Verkehrszeichen-Gruppe 200\nca. 885 St Verkehrszeichen-Gruppe 300 - 400\nca. 616 St Orts- und Hinweistafeln und Wegweiser\nca. 25 St Verkehrszeichen-Gruppe 500\nca. 1.555 St Verkehrszeichen-Gruppe 600\nca. 2.070 St Zusatzzeichen",
        "contractPeriod": {
          "startDate": "2027-01-01T00:00:00+01:00",
          "endDate": "2027-12-31T00:00:00+01:00"
        }
      }
    ]
  },
  "language": "DEU"
}
```
