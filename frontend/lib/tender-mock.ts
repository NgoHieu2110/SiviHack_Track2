import type { CompanyProfile, Tender, TenderMatch } from "./tender-types"

export const MOCK_TENDERS: Tender[] = [
  {
    id: "T-2026-0451",
    title: "Renovation of Municipal Secondary School Complex",
    authority: "City of Riverdale — Public Works Department",
    cpvCode: "45210000",
    cpvLabel: "Building construction work",
    contractNature: "Works",
    location: "Riverdale, North Region",
    value: 2_400_000,
    currency: "EUR",
    deadline: "2026-11-20",
    role: "Sole contractor",
    requiredCertificates: ["ISO 9001 (Quality)", "ISO 45001 (Health & Safety)", "Professional Register (Contractors)"],
    insuranceRequired: 3_000_000,
    guaranteeRequired: "Performance guarantee (5-10%)",
    startDate: "2027-01-15",
    description:
      "Full structural renovation and modernization of a 1970s school complex including facade, roofing and interior fit-out.",
    markdown: "",
  },
  {
    id: "T-2026-0478",
    title: "Construction of a District Health Centre",
    authority: "Regional Health Authority",
    cpvCode: "45215100",
    cpvLabel: "Buildings relating to health",
    contractNature: "Works",
    location: "North Region",
    value: 5_800_000,
    currency: "EUR",
    deadline: "2026-12-05",
    role: "Lead of a consortium",
    requiredCertificates: ["ISO 9001 (Quality)", "ISO 14001 (Environmental)", "ISO 45001 (Health & Safety)"],
    insuranceRequired: 6_000_000,
    guaranteeRequired: "Performance guarantee (5-10%)",
    startDate: "2027-03-01",
    description:
      "Turnkey construction of a new two-storey primary health centre with associated site works and MEP installations.",
    markdown: "",
  },
  {
    id: "T-2026-0492",
    title: "Resurfacing and Drainage of Regional Roads (Lot 3)",
    authority: "National Roads Agency",
    cpvCode: "45230000",
    cpvLabel: "Roads, railways, pipelines",
    contractNature: "Works",
    location: "North Region",
    value: 1_150_000,
    currency: "EUR",
    deadline: "2026-10-30",
    role: "Sole contractor",
    requiredCertificates: ["ISO 9001 (Quality)", "Professional Register (Contractors)"],
    insuranceRequired: 2_000_000,
    guaranteeRequired: "Bid bond (1-2%)",
    startDate: "2026-12-01",
    description:
      "Resurfacing of 12 km of regional road, replacement of drainage channels and installation of new road markings.",
    markdown: "",
  },
  {
    id: "T-2026-0510",
    title: "Electrical Upgrade of Public Administration Building",
    authority: "Ministry of Public Administration",
    cpvCode: "45310000",
    cpvLabel: "Electrical installation work",
    contractNature: "Works",
    location: "Capital District",
    value: 680_000,
    currency: "EUR",
    deadline: "2026-11-10",
    role: "Sole contractor",
    requiredCertificates: ["ISO 9001 (Quality)", "Electrical Works License"],
    insuranceRequired: 1_000_000,
    guaranteeRequired: "Performance guarantee (5-10%)",
    startDate: "2027-02-01",
    description:
      "Replacement of main distribution boards, rewiring and installation of a new emergency power system.",
    markdown: "",
  },
  {
    id: "T-2026-0523",
    title: "Facilities Maintenance Services for Government Campus",
    authority: "General Services Administration",
    cpvCode: "45450000",
    cpvLabel: "Other building completion work",
    contractNature: "Services",
    location: "Capital District",
    value: 920_000,
    currency: "EUR",
    deadline: "2026-12-18",
    role: "Consortium member",
    requiredCertificates: ["ISO 9001 (Quality)", "ISO 45001 (Health & Safety)"],
    insuranceRequired: 1_500_000,
    guaranteeRequired: "Advance payment guarantee",
    startDate: "2027-01-01",
    description:
      "Three-year multi-trade maintenance contract covering carpentry, plumbing, painting and minor building works.",
    markdown: "",
  },
  {
    id: "T-2026-0537",
    title: "New Water Treatment Pumping Station",
    authority: "Regional Water Utility",
    cpvCode: "45252100",
    cpvLabel: "Sewage-treatment plant construction work",
    contractNature: "Mixed (Works & Services)",
    location: "South Region",
    value: 8_900_000,
    currency: "EUR",
    deadline: "2027-01-25",
    role: "Lead of a consortium",
    requiredCertificates: ["ISO 9001 (Quality)", "ISO 14001 (Environmental)", "ISO 45001 (Health & Safety)", "SOA / Classification Certificate"],
    insuranceRequired: 10_000_000,
    guaranteeRequired: "Performance guarantee (5-10%)",
    startDate: "2027-05-01",
    description:
      "Design and construction of a new pumping station including civil works, mechanical equipment and 2-year operation.",
    markdown: "",
  },
]

function parseNumber(value: string): number | null {
  const n = Number.parseFloat(value.replace(/[^0-9.]/g, ""))
  return Number.isFinite(n) ? n : null
}

function currency(value: number, code = "EUR") {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: code, maximumFractionDigits: 0 }).format(value)
}

function keywords(text: string): string[] {
  return Array.from(
    new Set(
      text
        .toLowerCase()
        .split(/[^a-z0-9]+/)
        .map((t) => t.trim())
        .filter((t) => t.length > 3),
    ),
  )
}

/**
 * Mock "AI" matching engine. Scores each tender against the profile and
 * generates human-readable reasons and considerations. Replace with a real
 * backend call later — the shape of TenderMatch is what the UI consumes.
 */
export function matchTenders(profile: CompanyProfile): TenderMatch[] {
  const minValue = parseNumber(profile.contractValueMin)
  const maxValue = parseNumber(profile.contractValueMax)

  const matches = MOCK_TENDERS.map((tender): TenderMatch => {
    let score = 40
    const reasons: string[] = []
    const considerations: string[] = []

    const tenderText =
      `${tender.title} ${tender.description} ${tender.cpvLabel} ${tender.contractNature}`.toLowerCase()

    // What the company does — activity / sector fit
    if (profile.does.trim()) {
      const hits = keywords(profile.does).filter((t) => tenderText.includes(t))
      if (hits.length > 0) {
        score += Math.min(24, hits.length * 8)
        reasons.push(`Your described activity matches this tender's scope (${hits.slice(0, 3).join(", ")}).`)
      } else {
        considerations.push("Tender scope does not clearly overlap with your described activity.")
      }
    }

    // Place of performance
    if (profile.placeOfPerformance.trim()) {
      if (tender.location.toLowerCase().includes(profile.placeOfPerformance.toLowerCase().trim())) {
        score += 14
        reasons.push(`Located in ${tender.location}, matching your area of operation.`)
      } else {
        considerations.push(`Place of performance is ${tender.location}, outside your stated area.`)
      }
    }

    // Contract value range
    if (minValue !== null || maxValue !== null) {
      const aboveMin = minValue === null || tender.value >= minValue
      const belowMax = maxValue === null || tender.value <= maxValue
      if (aboveMin && belowMax) {
        score += 16
        reasons.push(`Contract value of ${currency(tender.value, tender.currency)} sits inside your target range.`)
      } else if (!belowMax) {
        considerations.push(`Value ${currency(tender.value, tender.currency)} exceeds your maximum — may require a consortium.`)
      } else {
        considerations.push(`Value ${currency(tender.value, tender.currency)} is below your minimum target.`)
      }
    }

    // Specifications — capability fit
    if (profile.specifications.trim()) {
      const hits = keywords(profile.specifications).filter((t) => tenderText.includes(t))
      if (hits.length > 0) {
        score += Math.min(12, hits.length * 6)
        reasons.push(`Matches your stated specifications (${hits.slice(0, 3).join(", ")}).`)
      }
    }

    // Company capacity — annual revenue vs contract value
    if (profile.revenue > 0) {
      const ratio = tender.value / profile.revenue
      if (ratio <= 1) {
        score += 10
        reasons.push(`Contract value is within your annual revenue — a comfortable financial fit.`)
      } else if (ratio <= 2) {
        score += 4
        considerations.push(`Contract value is ${ratio.toFixed(1)}× your annual revenue — manageable but demanding.`)
      } else {
        score -= 6
        considerations.push(`Contract value is ${ratio.toFixed(1)}× your annual revenue — likely needs a consortium.`)
      }
    }

    // Company capacity — workforce vs contract scale
    if (profile.employees > 0) {
      const expected = Math.max(1, Math.ceil(tender.value / 250_000))
      if (profile.employees >= expected) {
        score += 6
        reasons.push(`Your team of ${profile.employees} is sized for a contract of this scale.`)
      } else {
        considerations.push(`A contract this size typically needs ~${expected} staff; you listed ${profile.employees}.`)
      }
    }

    // Exclusions
    if (profile.exclusions.trim()) {
      const terms = profile.exclusions
        .toLowerCase()
        .split(/[,;\n]/)
        .map((t) => t.trim())
        .filter(Boolean)
      const hit = terms.find(
        (t) => tender.title.toLowerCase().includes(t) || tender.description.toLowerCase().includes(t),
      )
      if (hit) {
        score -= 25
        considerations.push(`Matches one of your exclusion terms ("${hit}") — review carefully.`)
      }
    }

    score = Math.max(5, Math.min(99, Math.round(score)))

    const summary =
      reasons.length > 0
        ? `This tender scores ${score}% against your profile. ${reasons[0]} ${
            reasons[1] ?? ""
          }`.trim()
        : `This tender scores ${score}% — a limited match against the details you provided.`

    return { tender, score, reasons, considerations, summary }
  })

  // Return every scored tender, best first. The UI locks the top 3 into the
  // focus lane and dims the rest above/below as "others".
  return matches.sort((a, b) => b.score - a.score)
}

/**
 * The real backend's Tender fields (value, insuranceRequired, ...) are
 * Optional and can come back as null when the source notice didn't carry a
 * reliable value (see backend/models.py). Accept null/undefined here so
 * every caller doesn't need its own guard before calling this.
 */
export function formatCurrency(value: number | null | undefined, code = "EUR") {
  if (value === null || value === undefined) return "Not specified"
  return currency(value, code)
}

/**
 * The real backend appends everything from a tender's raw source .md that
 * doesn't fit the structured Tender fields onto the end of `description`,
 * after a "---\n\n## Additional details" marker, as "- **Label:** value"
 * lines plus an optional trailing italic notes paragraph (see
 * workflow_tools/7_select_from_raw_tenders.py's parse_raw_tender_md()).
 * Split that back out so callers can render it as its own clean section
 * instead of dumping raw markdown into a plain text block.
 */
const ADDITIONAL_DETAILS_MARKER = "\n\n---\n\n## Additional details\n"

export function splitDescription(description: string) {
  const markerIndex = description.indexOf(ADDITIONAL_DETAILS_MARKER)
  if (markerIndex === -1) {
    return { core: description, extra: [] as { label: string; value: string }[], notes: null as string | null }
  }

  const core = description.slice(0, markerIndex)
  let rest = description.slice(markerIndex + ADDITIONAL_DETAILS_MARKER.length)

  let notes: string | null = null
  const notesMarker = "\n\n_"
  const notesIndex = rest.indexOf(notesMarker)
  if (notesIndex !== -1) {
    notes = rest.slice(notesIndex + notesMarker.length).trim().replace(/_$/, "")
    rest = rest.slice(0, notesIndex)
  }

  const extra = rest
    .split("\n")
    .filter((line) => line.startsWith("- "))
    .map((line) => {
      const match = line.match(/^- \*\*(.+?):\*\*\s*(.*)$/)
      return match ? { label: match[1], value: match[2] } : { label: "", value: line.slice(2) }
    })

  return { core, extra, notes }
}