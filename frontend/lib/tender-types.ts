export type CompanyProfile = {
  cpvCode: string
  contractNature: string
  placeOfPerformance: string
  contractValueMin: string
  contractValueMax: string
  submissionDeadline: string
  participationRole: string
  financialGuarantees: string
  insuranceLimit: string
  availabilityTimeline: string
  certificates: string[]
  exclusions: string
}

export type Tender = {
  id: string
  title: string
  authority: string
  cpvCode: string
  cpvLabel: string
  contractNature: string
  location: string
  value: number
  currency: string
  deadline: string
  role: string
  requiredCertificates: string[]
  insuranceRequired: number
  guaranteeRequired: string
  startDate: string
  description: string
}

export type TenderMatch = {
  tender: Tender
  score: number
  reasons: string[]
  considerations: string[]
  summary: string
}

export const CPV_OPTIONS = [
  { value: "45000000", label: "45000000 — Construction work" },
  { value: "45200000", label: "45200000 — Works for complete/part buildings & civil engineering" },
  { value: "45210000", label: "45210000 — Building construction work" },
  { value: "45220000", label: "45220000 — Engineering & construction works" },
  { value: "45230000", label: "45230000 — Roads, railways, pipelines, communication lines" },
  { value: "45260000", label: "45260000 — Roofing & other special trade works" },
  { value: "45310000", label: "45310000 — Electrical installation work" },
  { value: "45330000", label: "45330000 — Plumbing & sanitary works" },
  { value: "45400000", label: "45400000 — Building completion work" },
  { value: "45450000", label: "45450000 — Other building completion work" },
]

export const CONTRACT_NATURE_OPTIONS = ["Works", "Services", "Supplies", "Mixed (Works & Services)"]

export const PARTICIPATION_ROLE_OPTIONS = [
  "Sole contractor",
  "Lead of a consortium",
  "Consortium member",
  "Subcontractor",
]

export const GUARANTEE_OPTIONS = [
  "None required",
  "Bid bond (1-2%)",
  "Performance guarantee (5-10%)",
  "Advance payment guarantee",
]

export const AVAILABILITY_OPTIONS = [
  "Immediately",
  "Within 1 month",
  "Within 3 months",
  "Within 6 months",
]

export const CERTIFICATE_OPTIONS = [
  "ISO 9001 (Quality)",
  "ISO 14001 (Environmental)",
  "ISO 45001 (Health & Safety)",
  "Professional Register (Contractors)",
  "SOA / Classification Certificate",
  "Electrical Works License",
]
