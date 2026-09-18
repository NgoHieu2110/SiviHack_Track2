"use client"

import { useState } from "react"
import { CompanyProfileForm } from "@/components/company-profile-form"
import { TenderResults } from "@/components/tender-results"
import { TenderDetailSheet } from "@/components/tender-detail-sheet"
import { ApiError, matchTendersRequest } from "@/lib/api"
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
  const [detailId, setDetailId] = useState<string | null>(null)

  const detailMatch = matches.find((m) => m.tender.id === detailId) ?? null

  const handleSubmit = async () => {
    const filledFields = Object.values(profile).filter((v) => {
      if (Array.isArray(v)) return v.length > 0
      if (typeof v === "number") return v > 0
      if (typeof v === "string") return v.trim() !== ""
      return Boolean(v)
    }).length

    if (filledFields < 2) {
      toast.error("Please fill in at least a couple of fields to get a meaningful match.")
      return
    }

    setLoading(true)
    setHasSearched(true)
    setSelectedId(null)

    try {
      const results = await matchTendersRequest(profile, (event) => {
        toast.message(event.message)
      })
      setMatches(results)
      toast.success(`Found your ${results.length} best-matched tender(s).`)
    } catch (err) {
      setMatches([])
      toast.error(err instanceof ApiError ? err.message : "Could not reach the tender matching service.")
    } finally {
      setLoading(false)
    }
  }

  // A /tenders/refine call found a replacement for a dismissed slot --
  // append it to the pool so the reel can scroll onto it (the dismissed
  // tender stays in the list too; only the backend's tenders/ store drops
  // it, so it can still be seen if the user scrolls back to it here).
  const handleReplace = (replacement: TenderMatch) => {
    setMatches((prev) => [...prev, replacement])
  }

  const handleReset = () => {
    setProfile(EMPTY_PROFILE)
    setMatches([])
    setHasSearched(false)
    setSelectedId(null)
  }

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
              onViewDetails={setDetailId}
              onReplace={handleReplace}
            />
          </section>
        </div>
      </main>

      <TenderDetailSheet
        match={detailMatch}
        open={detailId !== null}
        onOpenChange={(open) => {
          if (!open) setDetailId(null)
        }}
        isSelected={detailMatch ? selectedId === detailMatch.tender.id : false}
        onSelect={(id) => {
          setSelectedId(id)
          toast.success("Noted as not a fit.")
        }}
      />
    </div>
  )
}
