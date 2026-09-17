webscrape/api_info_oeffentlichevergabe.md

Bekanntmachungsservice: OpenData API
 1.0.0 
OAS 3.1
/documentation/api/opendata
This documentation describes the Bekanntmachungsservice API for bulk downloads of notices.

This API is available as OpenAPI spec in YAML and JSON formats.

Servers

https://oeffentlichevergabe.de - Generated server url
opendata
Open Data API



GET
/api/notice-exports
Exports all notices in a given month or on a given day.

This interface retrieves all notice versions that had been published by the Bekanntmachungsservice in a given month or on a given day. All published notices processed before midnight on the previous day are available for retrieval.

The requested time frame can be specified with the pubMonth or pubDay parameters which are mutually exclusive. All notice versions are returned that are published

at or after 00:00:00 o'clock on the first day of the specified month (inclusive search) and before 00:00:00 o'clock at the first day of the next month (exclusive search), when specifying pubMonth
at or after 00:00:00 o'clock on the specified day (inclusive search) and before 00:00:00 o'clock of the following day (exclusive search), when specifying pubDay The times for these ranges are treated as times in the timezone Europe/Berlin.
Notices are provided as a ZIP file containing notices in the requested file format. Please note that the ZIP file may contain a different number of files depending on the selected format. All formats contain the same notices for the same time range just encoded differently. Some formats like eForms and OCDS provide one file per notice inside the ZIP files. Other formats like CSV provide a fixed amount of files inside the ZIP file where different parts of a notice are stored in different files and each file contains data for all requested notices.

A file format can be requested by specifying an Accept header according to the rules of HTTP Content Negotiation or by specifying a format query parameter. If an Accept header and a format query parameter are present in the same request, the format query parameter takes precedence. The following formats are supported.

format: eforms.zip, MIME type: application/vnd.bekanntmachungsservice.eforms.zip+zip The original eForms format of the notices as they were submitted to the Bekanntmachungsservice.
format: ocds.zip, MIME type: application/vnd.bekanntmachungsservice.ocds.zip+zip The notices in the Open Contracting Data Standard (OCDS) format.
format: csv.zip, MIME type: application/vnd.bekanntmachungsservice.csv.zip+zip The notices in form of multiple CSV tables in a ZIP file.
If no format is explicitely requested the eForms format with the MIME type application/vnd.bekanntmachungsservice.eforms.zip+zip will be returned.

eForms Format
The format eForms is a standard for publishing public procurement data. This is the original format that is used for notices submitted to the Bekanntmachungsservice by the procurement platforms. All other supported formats are converted based on this format.

The base eForms format is defined by the EU. It is referred to as eForms-EU in this documentation. Member states are encouraged to adapt this base format to their national needs. The format resulting from the national tailoring in Germany is referred to as eForms-DE in this documentation.

Documentation and SDKs for the different kinds of eForms can be found at the following locations.

Resource	Link
eForms-DE standard	https://xeinkauf.de/eforms-de/
eForms-DE SDK	https://gitlab.opencode.de/OC000008125155/SDK-eforms-de
eForms-EU standard	https://docs.ted.europa.eu/
eForms-EU SDK	https://github.com/OP-TED/eForms-SDK
There are different versions of the eForms standards. The Bekanntmachungsservice contains only eForms notices of a subset of the available versions. The Bekanntmachungsservice does only differentiate between major/minor versions but not between patch versions.

Kind	Version	eForms-EU base version
eForms-DE	2.1	1.14
eForms-DE	2.1	1.13
eForms-DE	2.0	1.12
eForms-DE	1.2	1.10
eForms-DE	1.1	1.7
eForms-DE	1.0	1.5
eForms-EU	1.14	1.14
eForms-EU	1.13	1.13
eForms-EU	1.12	1.12
eForms-EU	1.10	1.10
eForms-EU	1.0	1.0
eForms-EU	0.1	0.1
CSV Format
When requesting the CSV format, a ZIP file containing multiple tables will be returned. The main table is notice.csv. It contains one row for each requested notice. At this endpoint this file will contain only one row for the single notice that was requested. At other endpoints that export multiple notices at once like GET /api/notice-exports there can be multiple rows. Wherever there is an 1:n relation there is a new table in the ZIP file. E.g. lot.csv contains information about all lots of the requested notices.

The CSV files follow the standard defined in RFC 4180 . The table names, column names and column order for existing columns is considered stable. It is planed to not change these in future. It is possible that new columns are added at the end of existing tables at any time. It is also possible that new tables occur in the ZIP file. These type of changes are considered backwards compatible.

Each notice is identified by its noticeIdentifier and noticeVersion. These columns are used in other tables as foreign key. E.g. to find the contracts of a notice, the contract.csv table must be filtered for rows that have a given noticeIdentifier and noticeVersion. Some data like classification.csv can be defined at notice level and at lot level. Rows that have a value defined in the lotIdentifier column belong to the lot with the specified lotIdentifier of the notice. Rows that have no value defined in that column belong to the notice itself.

The table data structure is based on the business terms defined for the eForms standard. The documentation for the mapping of eForms business terms to CSV tables and columns can be found here .

OCDS Format
The Open Contracting Data Standard (OCDS) is a JSON based format for publishing documents at all stages of contracting processes. OCDS can be seen as an alternative format for eForms as it serves related purposes.

The OCDS format is documented at standard.open-contracting.org. The Bekanntmachungsservice supports OCDS version 1.1.

Parameters
Try it out
Name	Description
pubMonth
string
(query)
The month for which to retrieve the published notices. The format must be YYYY-MM, e.g. 2023-12. Cannot be specified along pubDay

pubMonth
pubDay
string
(query)
The day for which to retrieve the published notices. The format must be YYYY-MM-DD, e.g. 2023-12-24. Cannot be specified along pubMonth

pubDay
format
string
(query)
Allows to specifiy the return format of the notices within the ZIP via a query parameter instead of the Accept header.

Available values : eforms.zip, ocds.zip, csv.zip


--
Responses
Code	Description	Links
200	
When the notices could be retrieved as expected. Empty ZIP is provided if no notices were found in the requested month or on the requested day respectively.

Media type

application/vnd.bekanntmachungsservice.csv.zip+zip
Controls Accept header.
Example Value
Schema
{}
No links
400	
When the supplied pubMonth parameter is invalid. The format must be YYYY-MM, e.g. 2023-12.
When the supplied pubDay parameter is invalid. The format must be YYYY-MM-DD, e.g. 2023-12-24.
When neither pubMonth nor pubDay is present.
When pubMonth and pubDay are specified at the same time.
When pubMonth prior to 2022-12 is requested.
When a future pubMonth is requested.
When pubDay prior to 2022-12-01 is requested.
When a pubDay is requested that is today or in the future.
Media type

text/plain
No links
415	
When an unsupported format for the notices is requested.

Media type

text/plain
No links
