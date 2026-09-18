"use client"

import { useState } from "react"
import { CompanyProfileForm } from "@/components/company-profile-form"
import { TenderResults } from "@/components/tender-results"
import { TenderDetailSheet } from "@/components/tender-detail-sheet"
import { matchTendersRequest, ApiError } from "@/lib/api"
import type { CompanyProfile, TenderMatch } from "@/lib/tender-types"
import { HardHat } from "lucide-react"
import { toast } from "sonner"

const EMPTY_PROFILE: CompanyProfile = {
  does: "",
  placeOfPerformance: "",
  contractValueMin: "",
  contractValueMax: "",
  exclusions: "",
  specifications: "",
  revenue: 0,
  employees: 0,
}

export default function Page() {
  const [profile, setProfile] = useState<CompanyProfile>(EMPTY_PROFILE)
  const [matches, setMatches] = useState<TenderMatch[]>([])
  const [loading, setLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [viewingId, setViewingId] = useState<string | null>(null)

  const handleSubmit = async () => {
    const filledFields = Object.values(profile).filter((v) =>
      Array.isArray(v) ? v.length > 0 : typeof v === "string" ? v.trim() !== "" : v !== 0,
    ).length
    if (filledFields < 2) {
      toast.error("Please fill in at least a couple of fields to get a meaningful match.")
      return
    }

    setLoading(true)
    setHasSearched(true)
    setSelectedId(null)

    // The backend runs a genuinely slow, multi-stage pipeline (Gemini call,
    // then live tender fetching, then a second Gemini call to score/explain
    // matches) and streams progress the whole way -- surface it here so the
    // wait doesn't look frozen.
    const toastId = toast.loading("Starting your tender search...")

    try {
      const results = await matchTendersRequest(profile, (event) => {
        toast.loading(event.message, { id: toastId })
      })
      setMatches(results)
      toast.success(
        results.length > 0
          ? `Found your ${results.length} best-matched tender${results.length === 1 ? "" : "s"}.`
          : "No matching tenders found for this profile.",
        { id: toastId },
      )
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "Something went wrong while matching tenders. Please try again."
      toast.error(message, { id: toastId })
      setMatches([])
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setProfile(EMPTY_PROFILE)
    setMatches([])
    setHasSearched(false)
    setSelectedId(null)
    setViewingId(null)
  }

  const viewingMatch = matches.find((m) => m.tender.id === viewingId) ?? null

  return (
    <div className="min-h-screen bg-muted/20">
      <header className="border-b bg-background">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-4 sm:px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500 text-white">
            <HardHat className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold leading-tight">TenderMatch</h1>
            <p className="text-sm text-muted-foreground">AI tender finder for construction companies</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
          <div>
            <CompanyProfileForm
              profile={profile}
              onChange={setProfile}
              onSubmit={handleSubmit}
              onReset={handleReset}
              loading={loading}
            />
          </div>

          <section
            aria-label="Matched tenders"
            className="lg:sticky lg:top-6 lg:h-[calc(100vh-3rem)]"
          >
            <TenderResults
              matches={matches}
              loading={loading}
              hasSearched={hasSearched}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onViewDetails={setViewingId}
            />
          </section>
        </div>
      </main>

      <TenderDetailSheet
        match={viewingMatch}
        open={viewingId !== null}
        onOpenChange={(open) => { if (!open) setViewingId(null) }}
        isSelected={viewingMatch ? selectedId === viewingMatch.tender.id : false}
        onSelect={(id) => {
          setSelectedId(id)
          const t = matches.find((m) => m.tender.id === id)
          if (t) toast.success(selectedId === id ? "Tender kept as selected" : `Selected "${t.tender.title}"`)
        }}
      />
    </div>
  )
}