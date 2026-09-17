export type CompanyProfile = {
  does: string
  contractNature: string
  placeOfPerformance: string
  contractValueMin: string
  contractValueMax: string
  exclusions: string
  specifications: string
  revenue: number
  employees: number
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

export const CONTRACT_NATURE_OPTIONS = ["Works", "Services", "Supplies", "Mixed (Works & Services)"]
