"use client"

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
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
  ChevronUp,
  ChevronDown,
} from "lucide-react"
import { toast } from "sonner"

type Props = {
  matches: TenderMatch[]
  loading: boolean
  hasSearched: boolean
  selectedId: string | null
  onSelect: (id: string) => void
}

/** Fixed geometry for the slot-machine reels. */
const CARD_H = 300
const ITEM_H = 340 // card + vertical gap; one "notch" of the reel
const REEL_H = 560

function scoreColor(score: number) {
  if (score >= 75) return "text-emerald-600 dark:text-emerald-400"
  if (score >= 55) return "text-amber-600 dark:text-amber-400"
  return "text-muted-foreground"
}

function rankLabel(index: number) {
  if (index === 0) return "#1 Best Match"
  if (index === 1) return "#2 Best Match"
  if (index === 2) return "#3 Best Match"
  return `#${index + 1}`
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
            Complete your company profile on the left and run the match. Then spin each reel to roll through every
            tender — whatever lands in the middle lane becomes your active pick.
          </p>
        </>
      )}
    </div>
  )
}

/** Presentational tender card. Always renders full detail; the reel dims/blurs it when off-center. */
function TenderCard({
  match,
  index,
  active,
  isSelected,
  onSelect,
}: {
  match: TenderMatch
  index: number
  active: boolean
  isSelected: boolean
  onSelect: (id: string) => void
}) {
  const { tender, score, reasons, considerations, summary } = match
  return (
    <div
      className={`flex h-[300px] w-full flex-col rounded-xl border bg-card shadow-lg transition-colors ${
        isSelected
          ? "border-amber-500 ring-2 ring-amber-500/50"
          : active
            ? "border-amber-400/80"
            : "border-border"
      }`}
    >
      <div className="flex items-start justify-between gap-3 border-b p-3">
        <div className="min-w-0 space-y-1">
          <Badge variant="secondary" className="rounded-md text-[10px]">
            {rankLabel(index)}
          </Badge>
          <h3 className="truncate text-sm font-semibold leading-snug">{tender.title}</h3>
          <p className="flex items-center gap-1 truncate text-xs text-muted-foreground">
            <Building2 className="h-3 w-3 shrink-0" />
            <span className="truncate">{tender.authority}</span>
          </p>
        </div>
        <div className="shrink-0 text-right">
          <div className={`text-xl font-bold ${scoreColor(score)}`}>{score}%</div>
          <div className="text-[9px] uppercase tracking-wide text-muted-foreground">match</div>
        </div>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        <Progress value={score} className="h-1.5" />

        <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Wallet className="h-3 w-3 shrink-0" />
            <span className="truncate text-foreground">{formatCurrency(tender.value, tender.currency)}</span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <MapPin className="h-3 w-3 shrink-0" />
            <span className="truncate text-foreground">{tender.location}</span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <CalendarClock className="h-3 w-3 shrink-0" />
            <span className="truncate text-foreground">{tender.deadline}</span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Users className="h-3 w-3 shrink-0" />
            <span className="truncate text-foreground">{tender.role}</span>
          </div>
        </div>

        <div className="rounded-lg border border-amber-200/70 bg-amber-50/60 p-2.5 dark:border-amber-500/20 dark:bg-amber-500/5">
          <div className="mb-1 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
            <Sparkles className="h-3 w-3" />
            AI analysis
          </div>
          <p className="text-xs leading-relaxed text-foreground/90">{summary}</p>
        </div>

        <div className="space-y-1">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400">
            Why it fits
          </p>
          <ul className="space-y-1">
            {reasons.length > 0 ? (
              reasons.slice(0, 3).map((r, i) => (
                <li key={i} className="flex gap-1.5 text-xs text-muted-foreground">
                  <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-emerald-500" />
                  <span>{r}</span>
                </li>
              ))
            ) : (
              <li className="text-xs text-muted-foreground">No strong positive signals detected.</li>
            )}
          </ul>
        </div>

        {considerations.length > 0 && (
          <div className="space-y-1">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
              Points to consider
            </p>
            <ul className="space-y-1">
              {considerations.slice(0, 2).map((c, i) => (
                <li key={i} className="flex gap-1.5 text-xs text-muted-foreground">
                  <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0 text-amber-500" />
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="border-t p-3">
        <Button
          variant={isSelected ? "default" : "outline"}
          size="sm"
          className="w-full"
          disabled={!active}
          onClick={() => {
            onSelect(tender.id)
            toast.success(isSelected ? "Tender kept as selected" : `Selected "${tender.title}"`)
          }}
        >
          {isSelected ? "Selected" : active ? "Choose this tender" : "Scroll into lane to choose"}
        </Button>
      </div>
    </div>
  )
}

/** One independent, scroll-snapping reel through every tender. */
function ReelColumn({
  matches,
  initialIndex,
  selectedId,
  onSelect,
}: {
  matches: TenderMatch[]
  initialIndex: number
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const itemRefs = useRef<(HTMLDivElement | null)[]>([])
  const rafRef = useRef<number | null>(null)
  const activeRef = useRef(initialIndex)
  const [active, setActive] = useState(initialIndex)

  const applyEffects = useCallback(() => {
    const container = scrollRef.current
    if (!container) return
    const cRect = container.getBoundingClientRect()
    const center = cRect.top + cRect.height / 2

    let best = 0
    let bestDist = Number.POSITIVE_INFINITY

    itemRefs.current.forEach((el, i) => {
      if (!el) return
      const r = el.getBoundingClientRect()
      const elCenter = r.top + r.height / 2
      const d = elCenter - center
      const dn = d / ITEM_H // notches from center
      const ad = Math.min(Math.abs(dn), 2.4)

      const scale = 1 - Math.min(ad, 1) * 0.16
      const opacity = Math.max(0.16, 1 - ad * 0.44)
      const blur = Math.min(ad * 2.6, 6)
      const rot = Math.max(Math.min(-dn * 20, 42), -42)

      el.style.transform = `rotateX(${rot}deg) scale(${scale})`
      el.style.opacity = String(opacity)
      el.style.filter = `blur(${blur}px)`
      el.style.zIndex = String(100 - Math.round(ad * 10))
      el.style.pointerEvents = ad < 0.5 ? "auto" : "none"

      const abs = Math.abs(d)
      if (abs < bestDist) {
        bestDist = abs
        best = i
      }
    })

    if (best !== activeRef.current) {
      activeRef.current = best
      setActive(best)
    }
  }, [])

  const onScroll = useCallback(() => {
    if (rafRef.current != null) return
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null
      applyEffects()
    })
  }, [applyEffects])

  // Center the reel on its initial tender, then compute effects.
  useLayoutEffect(() => {
    const container = scrollRef.current
    if (!container) return
    container.scrollTop = initialIndex * ITEM_H
    applyEffects()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    return () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  const nudge = (dir: 1 | -1) => {
    scrollRef.current?.scrollBy({ top: dir * ITEM_H, behavior: "smooth" })
  }

  const pad = (REEL_H - ITEM_H) / 2

  return (
    <div className="relative">
      <button
        type="button"
        aria-label="Scroll up"
        onClick={() => nudge(-1)}
        className="absolute -top-1 left-1/2 z-30 flex h-6 w-6 -translate-x-1/2 items-center justify-center rounded-full border border-border bg-background/90 text-muted-foreground shadow-sm transition hover:text-amber-600"
      >
        <ChevronUp className="h-4 w-4" />
      </button>

      <div
        ref={scrollRef}
        onScroll={onScroll}
        className="reel-scroll snap-y snap-mandatory overflow-y-auto overscroll-contain scroll-smooth [scrollbar-color:theme(colors.amber.400)_transparent] [scrollbar-width:thin] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-amber-400/70 [&::-webkit-scrollbar]:w-1.5"
        style={{ height: REEL_H, perspective: "1000px" }}
      >
        <div style={{ height: pad }} aria-hidden="true" />
        {matches.map((match, i) => (
          <div
            key={match.tender.id}
            ref={(el) => {
              itemRefs.current[i] = el
            }}
            className="flex snap-center items-center justify-center px-1 will-change-transform"
            style={{ height: ITEM_H, transformStyle: "preserve-3d" }}
          >
            <div style={{ height: CARD_H }} className="w-full">
              <TenderCard
                match={match}
                index={i}
                active={i === active}
                isSelected={selectedId === match.tender.id}
                onSelect={onSelect}
              />
            </div>
          </div>
        ))}
        <div style={{ height: pad }} aria-hidden="true" />
      </div>

      <button
        type="button"
        aria-label="Scroll down"
        onClick={() => nudge(1)}
        className="absolute -bottom-1 left-1/2 z-30 flex h-6 w-6 -translate-x-1/2 items-center justify-center rounded-full border border-border bg-background/90 text-muted-foreground shadow-sm transition hover:text-amber-600"
      >
        <ChevronDown className="h-4 w-4" />
      </button>
    </div>
  )
}

export function TenderResults({ matches, loading, hasSearched, selectedId, onSelect }: Props) {
  if (loading || !hasSearched) {
    return <EmptyState loading={loading} />
  }

  if (matches.length === 0) {
    return (
      <div className="flex h-full min-h-[300px] flex-col items-center justify-center rounded-xl border border-dashed p-10 text-center">
        <FileSearch className="mb-3 h-8 w-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">No tenders matched your profile. Try widening your criteria.</p>
      </div>
    )
  }

  // Each reel spins through the full sorted list; they start centered on the
  // 1st, 2nd and 3rd best matches respectively so the Top 3 are pre-loaded.
  const starts = [0, Math.min(1, matches.length - 1), Math.min(2, matches.length - 1)]

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-amber-500" />
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">{matches.length} tenders</span> ranked by suitability — spin
            any reel to browse them all.
          </p>
        </div>
        <span className="rounded-full border border-border/60 bg-muted/40 px-2.5 py-1 text-[11px] text-muted-foreground">
          Centered card = active pick
        </span>
      </div>

      <div className="relative overflow-hidden rounded-2xl border border-border/60 bg-gradient-to-b from-muted/40 via-background to-muted/40 p-4">
        {/* top / bottom fade masks to sell the drum curvature */}
        <div className="pointer-events-none absolute inset-x-0 top-0 z-20 h-20 bg-gradient-to-b from-background to-transparent" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 z-20 h-20 bg-gradient-to-t from-background to-transparent" />

        {/* active selector lane, centered on the reels */}
        <div className="pointer-events-none absolute inset-x-3 top-1/2 z-0 h-[312px] -translate-y-1/2 rounded-2xl border-y-2 border-amber-400/70 bg-amber-50/40 dark:border-amber-500/30 dark:bg-amber-500/5" />

        <div className="relative z-10 grid grid-cols-3 gap-3">
          {starts.map((start, col) => (
            <ReelColumn
              key={col}
              matches={matches}
              initialIndex={start}
              selectedId={selectedId}
              onSelect={onSelect}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
