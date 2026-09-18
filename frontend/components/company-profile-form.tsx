"use client"

import type React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { type CompanyProfile } from "@/lib/tender-types"
import { Loader2, Search, RotateCcw } from "lucide-react"

type Props = {
  profile: CompanyProfile
  onChange: (profile: CompanyProfile) => void
  onSubmit: () => void
  onReset: () => void
  loading: boolean
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-4">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</h3>
      {children}
    </div>
  )
}

export function CompanyProfileForm({ profile, onChange, onSubmit, onReset, loading }: Props) {
  const set = <K extends keyof CompanyProfile>(key: K, value: CompanyProfile[K]) =>
    onChange({ ...profile, [key]: value })

  return (
    <Card className="h-full border-border/60 shadow-sm">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg">Company Profile</CardTitle>
        <p className="text-sm text-muted-foreground">
          Fill in your details — no account needed. We&apos;ll match you to suitable tenders.
        </p>
      </CardHeader>
      <CardContent>
        <form
          className="space-y-8"
          onSubmit={(e) => {
            e.preventDefault()
            onSubmit()
          }}
        >
          <Section title="Scope & Nature">
            <div className="space-y-2">
              <Label htmlFor="does">What Your Company Does</Label>
              <Textarea
                id="does"
                placeholder="e.g. building construction, roofing, electrical installation…"
                value={profile.does}
                onChange={(e) => set("does", e.target.value)}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="place">Place of Performance</Label>
              <Input
                id="place"
                placeholder="e.g. North Region, Capital District"
                value={profile.placeOfPerformance}
                onChange={(e) => set("placeOfPerformance", e.target.value)}
              />
            </div>
          </Section>

          <Separator />

          <Section title="Contract Value">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="valMin">Contract Value — Min (EUR)</Label>
                <Input
                  id="valMin"
                  inputMode="numeric"
                  placeholder="500000"
                  value={profile.contractValueMin}
                  onChange={(e) => set("contractValueMin", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="valMax">Contract Value — Max (EUR)</Label>
                <Input
                  id="valMax"
                  inputMode="numeric"
                  placeholder="6000000"
                  value={profile.contractValueMax}
                  onChange={(e) => set("contractValueMax", e.target.value)}
                />
              </div>
            </div>
          </Section>

          <Separator />

          <Section title="Company Capacity">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="revenue">Annual Revenue (EUR)</Label>
                <Input
                  id="revenue"
                  type="number"
                  inputMode="numeric"
                  min={0}
                  placeholder="e.g. 5000000"
                  value={profile.revenue === 0 ? "" : profile.revenue}
                  onChange={(e) => set("revenue", e.target.value === "" ? 0 : Number(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="employees">Employees</Label>
                <Input
                  id="employees"
                  type="number"
                  inputMode="numeric"
                  min={0}
                  placeholder="e.g. 40"
                  value={profile.employees === 0 ? "" : profile.employees}
                  onChange={(e) => set("employees", e.target.value === "" ? 0 : Number(e.target.value))}
                />
              </div>
            </div>
          </Section>

          <Separator />

          <Section title="Specifications">
            <Textarea
              placeholder="e.g. turnkey delivery, MEP installations, 2-year maintenance…"
              value={profile.specifications}
              onChange={(e) => set("specifications", e.target.value)}
              rows={3}
            />
          </Section>

          <Separator />

          <Section title="Exclusions / Specific Limitations">
            <Textarea
              placeholder="e.g. no demolition, no offshore works, exclude asbestos removal…"
              value={profile.exclusions}
              onChange={(e) => set("exclusions", e.target.value)}
              rows={3}
            />
          </Section>

          <div className="flex gap-3 pt-2">
            <Button type="submit" className="flex-1" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing…
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Find matching tenders
                </>
              )}
            </Button>
            <Button type="button" variant="outline" onClick={onReset} disabled={loading}>
              <RotateCcw className="h-4 w-4" />
              <span className="sr-only">Reset form</span>
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
