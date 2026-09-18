"use client"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { formatCurrency, splitDescription } from "@/lib/tender-mock"
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
  ShieldCheck,
  BadgeCheck,
  Landmark,
  ClipboardList,
  Info,
} from "lucide-react"

type Props = {
  match: TenderMatch | null
  open: boolean
  onOpenChange: (open: boolean) => void
  isSelected: boolean
  onSelect: (id: string) => void
}

function scoreColor(score: number | null) {
  if (score === null) return "text-muted-foreground"
  if (score >= 75) return "text-emerald-600 dark:text-emerald-400"
  if (score >= 55) return "text-amber-600 dark:text-amber-400"
  return "text-muted-foreground"
}

/** Backend fields (contractNature, startDate, guaranteeRequired, ...) can
 * legitimately come back as null when the source notice didn't carry a
 * reliable value (see backend/models.py's Tender). Fall back to a plain
 * "Not specified" instead of rendering blank or "null". */
function orNotSpecified(value: string | null | undefined) {
  return value && value.trim() !== "" ? value : "Not specified"
}

function Fact({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof MapPin
  label: string
  value: string
}) {
  return (
    <div className="flex items-start gap-2.5">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-muted">
        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
        <p className="text-sm font-medium text-foreground">{value}</p>
      </div>
    </div>
  )
}

export function TenderDetailSheet({ match, open, onOpenChange, isSelected, onSelect }: Props) {
  const tender = match?.tender
  const description = tender ? splitDescription(tender.description || "") : null

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex w-full flex-col gap-0 overflow-y-auto p-0 sm:max-w-xl">
        {match && tender ? (
          <>
            <SheetHeader className="space-y-3 border-b p-6 pr-12 text-left">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 space-y-2">
                  <Badge variant="secondary" className="rounded-md text-[10px]">
                    Tender details
                  </Badge>
                  <SheetTitle className="text-balance text-lg leading-snug">
                    {tender.title || "Untitled tender"}
                  </SheetTitle>
                  <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <Building2 className="h-3.5 w-3.5 shrink-0" />
                    <span className="truncate">{tender.authority || "Contracting authority not specified"}</span>
                  </p>
                </div>
                <div className="shrink-0 text-right">
                  <div className={`text-3xl font-bold ${scoreColor(match.score)}`}>
                    {match.score !== null ? `${match.score}%` : "—"}
                  </div>
                  <div className="text-[9px] uppercase tracking-wide text-muted-foreground">match</div>
                </div>
              </div>
              {match.score !== null && <Progress value={match.score} className="h-1.5" />}
            </SheetHeader>

            <div className="flex flex-1 flex-col gap-6 p-6">
              <div className="grid grid-cols-2 gap-4">
                <Fact icon={Wallet} label="Contract value" value={formatCurrency(tender.value, tender.currency ?? undefined)} />
                <Fact icon={MapPin} label="Location" value={orNotSpecified(tender.location)} />
                <Fact icon={CalendarClock} label="Deadline" value={orNotSpecified(tender.deadline)} />
                <Fact icon={Users} label="Role" value={orNotSpecified(tender.role)} />
                <Fact icon={ClipboardList} label="Contract nature" value={orNotSpecified(tender.contractNature)} />
                <Fact icon={CalendarClock} label="Start date" value={orNotSpecified(tender.startDate)} />
                <Fact icon={Landmark} label="CPV code" value={orNotSpecified(tender.cpvCode)} />
                <Fact icon={ShieldCheck} label="Guarantee" value={orNotSpecified(tender.guaranteeRequired)} />
              </div>

              <Separator />

              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">CPV category</p>
                <p className="text-sm text-foreground/90">{orNotSpecified(tender.cpvLabel)}</p>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Description</p>
                <p className="text-sm leading-relaxed text-foreground/90">
                  {description?.core.trim() || "No description provided."}
                </p>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Insurance required
                </p>
                <p className="text-sm text-foreground/90">
                  {formatCurrency(tender.insuranceRequired, tender.currency ?? undefined)}
                </p>
              </div>

              <div className="space-y-2">
                <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  <BadgeCheck className="h-3.5 w-3.5" />
                  Required certificates
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {tender.requiredCertificates.length > 0 ? (
                    tender.requiredCertificates.map((c) => (
                      <Badge key={c} variant="outline" className="rounded-md font-normal">
                        {c}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-sm text-muted-foreground">None specified</span>
                  )}
                </div>
              </div>

              <Separator />

              <div className="rounded-lg border border-amber-200/70 bg-amber-50/60 p-3 dark:border-amber-500/20 dark:bg-amber-500/5">
                <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
                  <Sparkles className="h-3.5 w-3.5" />
                  AI analysis
                </div>
                <p className="text-sm leading-relaxed text-foreground/90">{match.summary}</p>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400">
                  Why it fits
                </p>
                <ul className="space-y-1.5">
                  {match.reasons.length > 0 ? (
                    match.reasons.map((r, i) => (
                      <li key={i} className="flex gap-2 text-sm text-muted-foreground">
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                        <span>{r}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-muted-foreground">No strong positive signals detected.</li>
                  )}
                </ul>
              </div>

              {match.considerations.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
                    Points to consider
                  </p>
                  <ul className="space-y-1.5">
                    {match.considerations.map((c, i) => (
                      <li key={i} className="flex gap-2 text-sm text-muted-foreground">
                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {description && description.extra.length > 0 && (
                <>
                  <Separator />
                  <div className="space-y-2">
                    <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      <Info className="h-3.5 w-3.5" />
                      Additional details
                    </p>
                    <dl className="space-y-1.5 rounded-lg border bg-muted/30 p-3 text-sm">
                      {description.extra.map((item, i) =>
                        item.label ? (
                          <div key={i} className="flex flex-wrap gap-x-1.5">
                            <dt className="font-medium text-foreground">{item.label}:</dt>
                            <dd className="text-muted-foreground">{item.value}</dd>
                          </div>
                        ) : (
                          <div key={i} className="text-muted-foreground">
                            {item.value}
                          </div>
                        ),
                      )}
                    </dl>
                    {description.notes && (
                      <p className="text-xs italic text-muted-foreground">{description.notes}</p>
                    )}
                  </div>
                </>
              )}
            </div>

            <div className="sticky bottom-0 border-t bg-background/95 p-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
              <Button
                variant={isSelected ? "default" : "outline"}
                className="w-full"
                onClick={() => onSelect(tender.id)}
              >
                {isSelected ? "Selected tender" : "Choose this tender"}
              </Button>
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  )
}