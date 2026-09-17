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
  },
]

function parseNumber(value: string): number | null {
  const n = Number.parseFloat(value.replace(/[^0-9.]/g, ""))
  return Number.isFinite(n) ? n : null
}

function cpvFamily(code: string) {
  return code.replace(/[^0-9]/g, "").slice(0, 4)
}

function currency(value: number, code = "EUR") {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: code, maximumFractionDigits: 0 }).format(value)
}

/**
 * Mock "AI" matching engine. Scores each tender against the profile and
 * generates human-readable reasons and considerations. Replace with a real
 * backend call later — the shape of TenderMatch is what the UI consumes.
 */
export function matchTenders(profile: CompanyProfile): TenderMatch[] {
  const minValue = parseNumber(profile.contractValueMin)
  const maxValue = parseNumber(profile.contractValueMax)
  const insuranceLimit = parseNumber(profile.insuranceLimit)
  const deadline = profile.submissionDeadline ? new Date(profile.submissionDeadline) : null

  const matches = MOCK_TENDERS.map((tender): TenderMatch => {
    let score = 40
    const reasons: string[] = []
    const considerations: string[] = []

    // CPV / sector
    if (profile.cpvCode) {
      if (cpvFamily(tender.cpvCode) === cpvFamily(profile.cpvCode)) {
        score += 22
        reasons.push(`Same CPV family (${cpvFamily(profile.cpvCode)}xx) as your registered activity — a direct sector fit.`)
      } else if (tender.cpvCode.slice(0, 2) === profile.cpvCode.slice(0, 2)) {
        score += 10
        reasons.push(`Within the same broad construction division (45xx) as your CPV code.`)
      } else {
        considerations.push("CPV code differs from your primary registered activity.")
      }
    }

    // Contract nature
    if (profile.contractNature) {
      if (tender.contractNature === profile.contractNature) {
        score += 12
        reasons.push(`Contract nature is "${tender.contractNature}", matching your selected preference.`)
      } else {
        considerations.push(`Contract nature is "${tender.contractNature}" while you selected "${profile.contractNature}".`)
      }
    }

    // Place of performance
    if (profile.placeOfPerformance) {
      if (tender.location.toLowerCase().includes(profile.placeOfPerformance.toLowerCase().trim())) {
        score += 12
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
        score += 14
        reasons.push(`Contract value of ${currency(tender.value, tender.currency)} sits inside your target range.`)
      } else if (!belowMax) {
        considerations.push(`Value ${currency(tender.value, tender.currency)} exceeds your maximum — may require a consortium.`)
      } else {
        considerations.push(`Value ${currency(tender.value, tender.currency)} is below your minimum target.`)
      }
    }

    // Deadline
    if (deadline) {
      const tenderDeadline = new Date(tender.deadline)
      if (tenderDeadline >= deadline) {
        score += 6
        reasons.push(`Submission deadline (${tender.deadline}) gives you enough time to prepare a bid.`)
      } else {
        considerations.push(`Deadline ${tender.deadline} is earlier than your preferred cut-off.`)
      }
    }

    // Participation role
    if (profile.participationRole) {
      if (tender.role === profile.participationRole) {
        score += 8
        reasons.push(`Suited to your preferred role as "${tender.role}".`)
      } else {
        considerations.push(`Structured for a "${tender.role}" — differs from your preferred "${profile.participationRole}".`)
      }
    }

    // Insurance
    if (insuranceLimit !== null) {
      if (insuranceLimit >= tender.insuranceRequired) {
        score += 6
        reasons.push(`Your insurance limit covers the required ${currency(tender.insuranceRequired, tender.currency)}.`)
      } else {
        considerations.push(`Requires ${currency(tender.insuranceRequired, tender.currency)} insurance — above your current limit.`)
      }
    }

    // Guarantees
    if (profile.financialGuarantees && tender.guaranteeRequired === profile.financialGuarantees) {
      score += 4
      reasons.push(`Financial guarantee requirement (${tender.guaranteeRequired}) matches what you can provide.`)
    }

    // Certificates
    if (profile.certificates.length > 0) {
      const missing = tender.requiredCertificates.filter((c) => !profile.certificates.includes(c))
      const held = tender.requiredCertificates.filter((c) => profile.certificates.includes(c))
      if (held.length > 0) {
        score += Math.min(12, held.length * 4)
        reasons.push(`You already hold ${held.length} of ${tender.requiredCertificates.length} required certificates.`)
      }
      if (missing.length > 0) {
        considerations.push(`Missing certificate(s): ${missing.join(", ")}.`)
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

  return matches.sort((a, b) => b.score - a.score).slice(0, 3)
}

export function formatCurrency(value: number, code = "EUR") {
  return currency(value, code)
}
