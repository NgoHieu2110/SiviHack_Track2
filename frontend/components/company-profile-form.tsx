"use client"

import type React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Separator } from "@/components/ui/separator"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  CPV_OPTIONS,
  CONTRACT_NATURE_OPTIONS,
  PARTICIPATION_ROLE_OPTIONS,
  GUARANTEE_OPTIONS,
  AVAILABILITY_OPTIONS,
  CERTIFICATE_OPTIONS,
  type CompanyProfile,
} from "@/lib/tender-types"
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

  const toggleCertificate = (cert: string, checked: boolean) => {
    set(
      "certificates",
      checked ? [...profile.certificates, cert] : profile.certificates.filter((c) => c !== cert),
    )
  }

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
              <Label htmlFor="cpv">Sector / CPV Code</Label>
              <Select value={profile.cpvCode} onValueChange={(v) => set("cpvCode", v)}>
                <SelectTrigger id="cpv">
                  <SelectValue placeholder="Select a CPV code" />
                </SelectTrigger>
                <SelectContent>
                  {CPV_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="nature">Contract Nature</Label>
              <Select value={profile.contractNature} onValueChange={(v) => set("contractNature", v)}>
                <SelectTrigger id="nature">
                  <SelectValue placeholder="Select contract nature" />
                </SelectTrigger>
                <SelectContent>
                  {CONTRACT_NATURE_OPTIONS.map((o) => (
                    <SelectItem key={o} value={o}>
                      {o}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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

          <Section title="Value & Timing">
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

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="deadline">Submission Deadline (from)</Label>
                <Input
                  id="deadline"
                  type="date"
                  value={profile.submissionDeadline}
                  onChange={(e) => set("submissionDeadline", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="availability">Availability Timeline</Label>
                <Select value={profile.availabilityTimeline} onValueChange={(v) => set("availabilityTimeline", v)}>
                  <SelectTrigger id="availability">
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    {AVAILABILITY_OPTIONS.map((o) => (
                      <SelectItem key={o} value={o}>
                        {o}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </Section>

          <Separator />

          <Section title="Role & Financials">
            <div className="space-y-2">
              <Label htmlFor="role">Participation Role</Label>
              <Select value={profile.participationRole} onValueChange={(v) => set("participationRole", v)}>
                <SelectTrigger id="role">
                  <SelectValue placeholder="Select participation role" />
                </SelectTrigger>
                <SelectContent>
                  {PARTICIPATION_ROLE_OPTIONS.map((o) => (
                    <SelectItem key={o} value={o}>
                      {o}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="guarantee">Financial Guarantees</Label>
              <Select value={profile.financialGuarantees} onValueChange={(v) => set("financialGuarantees", v)}>
                <SelectTrigger id="guarantee">
                  <SelectValue placeholder="Select what you can provide" />
                </SelectTrigger>
                <SelectContent>
                  {GUARANTEE_OPTIONS.map((o) => (
                    <SelectItem key={o} value={o}>
                      {o}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="insurance">Insurance Limit (EUR)</Label>
              <Input
                id="insurance"
                inputMode="numeric"
                placeholder="e.g. 5000000"
                value={profile.insuranceLimit}
                onChange={(e) => set("insuranceLimit", e.target.value)}
              />
            </div>
          </Section>

          <Separator />

          <Section title="Certificates & Professional Registers">
            <div className="grid gap-3">
              {CERTIFICATE_OPTIONS.map((cert) => (
                <label key={cert} className="flex items-center gap-3 text-sm cursor-pointer">
                  <Checkbox
                    checked={profile.certificates.includes(cert)}
                    onCheckedChange={(c) => toggleCertificate(cert, c === true)}
                  />
                  <span>{cert}</span>
                </label>
              ))}
            </div>
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
