export type CompanyProfile = {
  does: string
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
  /** Full raw tender .md content, as returned by the backend's
   * workflow_tools/7_select_from_raw_tenders.py. Required by
   * /tenders/remove and /tenders/refine to identify the notice server-side. */
  markdown: string
}

export type TenderMatch = {
  tender: Tender
  score: number
  reasons: string[]
  considerations: string[]
  summary: string
}
