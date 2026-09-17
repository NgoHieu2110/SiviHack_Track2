"use client"

import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { formatCurrency } from "@/lib/tender-mock"
import type { TenderMatch } from "@/lib/tender-types"
import {
  Sparkles,
  MapPin,
  CalendarClock,
  Wallet,
  Users,
  CheckCircle2,
  AlertTriangle,
  Building2,
  FileSearch,
  Loader2,
} from "lucide-react"
import { toast } from "sonner"

type Props = {
  matches: TenderMatch[]
  loading: boolean
  hasSearched: boolean
  selectedId: string | null
  onSelect: (id: string) => void
}

function scoreColor(score: number) {
  if (score >= 75) return "text-emerald-600 dark:text-emerald-400"
  if (score >= 55) return "text-amber-600 dark:text-amber-400"
  return "text-muted-foreground"
}

function EmptyState({ loading }: { loading: boolean }) {
  return (
    <div className="flex h-full min-h-[400px] flex-col items-center justify-center rounded-xl border border-dashed border-border/70 bg-muted/30 p-10 text-center">
      {loading ? (
        <>
          <Loader2 className="mb-4 h-10 w-10 animate-spin text-amber-500" />
          <h3 className="text-base font-semibold">Analyzing your profile…</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Matching your company against available public tenders and scoring each one.
          </p>
        </>
      ) : (
        <>
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-500/10">
            <FileSearch className="h-7 w-7 text-amber-600 dark:text-amber-400" />
          </div>
          <h3 className="text-base font-semibold">Your top tenders will appear here</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Complete your company profile on the left and run the match to see the 3 best tenders with an AI
            explanation of why they fit.
          </p>
        </>
      )}
    </div>
  )
}

export function TenderResults({ matches, loading, hasSearched, selectedId, onSelect }: Props) {
  if (loading || !hasSearched) {
    return <EmptyState loading={loading} />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-amber-500" />
        <p className="text-sm text-muted-foreground">
          <span className="font-medium text-foreground">{matches.length} best-matched tenders</span> based on your
          profile, ranked by suitability.
        </p>
      </div>

      {matches.map((match, index) => {
        const { tender, score, reasons, considerations, summary } = match
        const isSelected = selectedId === tender.id
        return (
          <Card
            key={tender.id}
            className={`overflow-hidden border transition-all ${
              isSelected ? "border-amber-500 ring-1 ring-amber-500/40" : "border-border/60 hover:border-border"
            }`}
          >
            <CardHeader className="gap-3 pb-3">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="rounded-md">
                      #{index + 1} Best match
                    </Badge>
                    <span className="text-xs text-muted-foreground">{tender.id}</span>
                  </div>
                  <h3 className="text-base font-semibold leading-snug">{tender.title}</h3>
                  <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <Building2 className="h-3.5 w-3.5" />
                    {tender.authority}
                  </p>
                </div>
                <div className="shrink-0 text-right">
                  <div className={`text-2xl font-bold ${scoreColor(score)}`}>{score}%</div>
                  <div className="text-[11px] uppercase tracking-wide text-muted-foreground">match</div>
                </div>
              </div>
              <Progress value={score} className="h-1.5" />
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-4">
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Wallet className="h-3.5 w-3.5" />
                  <span className="text-foreground">{formatCurrency(tender.value, tender.currency)}</span>
                </div>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <MapPin className="h-3.5 w-3.5" />
                  <span className="text-foreground">{tender.location}</span>
                </div>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <CalendarClock className="h-3.5 w-3.5" />
                  <span className="text-foreground">{tender.deadline}</span>
                </div>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Users className="h-3.5 w-3.5" />
                  <span className="text-foreground">{tender.role}</span>
                </div>
              </div>

              <div className="rounded-lg border border-amber-200/70 bg-amber-50/60 p-3 dark:border-amber-500/20 dark:bg-amber-500/5">
                <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
                  <Sparkles className="h-3.5 w-3.5" />
                  AI analysis
                </div>
                <p className="text-sm text-foreground/90">{summary}</p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400">
                    Why it fits
                  </p>
                  <ul className="space-y-1.5">
                    {reasons.length > 0 ? (
                      reasons.map((r, i) => (
                        <li key={i} className="flex gap-2 text-sm text-muted-foreground">
                          <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" />
                          <span>{r}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-sm text-muted-foreground">No strong positive signals detected.</li>
                    )}
                  </ul>
                </div>
                <div className="space-y-1.5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
                    Points to consider
                  </p>
                  <ul className="space-y-1.5">
                    {considerations.length > 0 ? (
                      considerations.map((c, i) => (
                        <li key={i} className="flex gap-2 text-sm text-muted-foreground">
                          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
                          <span>{c}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-sm text-muted-foreground">No blocking issues found.</li>
                    )}
                  </ul>
                </div>
              </div>

              <Separator />

              <div className="flex items-center justify-between gap-3">
                <p className="text-sm text-muted-foreground">{tender.description}</p>
                <Button
                  variant={isSelected ? "default" : "outline"}
                  size="sm"
                  className="shrink-0"
                  onClick={() => {
                    onSelect(tender.id)
                    toast.success(isSelected ? "Tender kept as selected" : `Selected "${tender.title}"`)
                  }}
                >
                  {isSelected ? "Selected" : "Choose this tender"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
