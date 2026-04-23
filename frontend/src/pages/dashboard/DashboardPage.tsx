import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../../lib/api'
import { useResolvedMemberId } from '../../hooks/useFamily'
import type { HealthProfile, LabResult, Medication, Vital, LabFlag, Diagnosis } from '../../types/index'

// ── Inline SVG icons ───────────────────────────────────────────────────────

function IconEdit() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      className="w-4 h-4" aria-hidden="true">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  )
}

function IconBeaker() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      className="w-4 h-4" aria-hidden="true">
      <path d="M9 3H15M9 3v8l-4 6a2 2 0 0 0 1.697 3.05h10.606A2 2 0 0 0 19 17l-4-6V3" />
      <path d="M9 3h6" />
    </svg>
  )
}

function IconHeart() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      className="w-4 h-4" aria-hidden="true">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  )
}

function IconActivity() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      className="w-4 h-4" aria-hidden="true">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  )
}

function IconDroplet() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      className="w-4 h-4" aria-hidden="true">
      <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
    </svg>
  )
}

// ── Skeleton components ───────────────────────────────────────────────────

function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-surface-container rounded-lg ${className ?? ''}`} />
  )
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6" aria-label="Loading health profile">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <SkeletonBlock className="h-8 w-48" />
          <SkeletonBlock className="h-4 w-32" />
        </div>
        <div className="flex gap-3">
          <SkeletonBlock className="h-10 w-32 rounded-full" />
          <SkeletonBlock className="h-10 w-32 rounded-full" />
        </div>
      </div>
      {/* Vitals strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <SkeletonBlock className="h-32 rounded-xl" />
        <SkeletonBlock className="h-32 rounded-xl" />
      </div>
      {/* Main content */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="md:col-span-3 space-y-4">
          <SkeletonBlock className="h-48 rounded-xl" />
        </div>
        <div className="md:col-span-2 space-y-4">
          <SkeletonBlock className="h-48 rounded-xl" />
          <SkeletonBlock className="h-32 rounded-xl" />
        </div>
      </div>
    </div>
  )
}

// ── Lab flag badge ────────────────────────────────────────────────────────

function LabFlagBadge({ flag }: { flag: LabFlag }) {
  const styles: Record<LabFlag, string> = {
    NORMAL: 'bg-primary-fixed text-primary',
    HIGH: 'bg-error-container text-error',
    LOW: 'bg-tertiary-container text-tertiary',
    CRITICAL: 'bg-error-container text-error',
  }
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${styles[flag]}`}>
      {flag}
    </span>
  )
}

// ── Empty state component ─────────────────────────────────────────────────

function EmptyState({ icon, title, subtitle }: {
  icon: ReactNode
  title: string
  subtitle: string
}) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-center">
      <div className="w-12 h-12 rounded-2xl bg-surface-container flex items-center justify-center mb-3">
        <span className="text-primary/40">{icon}</span>
      </div>
      <p className="text-sm font-bold text-on-surface">{title}</p>
      <p className="text-xs text-on-surface-variant mt-1">{subtitle}</p>
    </div>
  )
}

// ── Helper: derive BP from vitals ─────────────────────────────────────────

function deriveBloodPressure(vitals: Vital[]): { systolic: number; diastolic: number } | null {
  const sys = vitals.find(v => v.vital_type.toLowerCase().includes('systolic') || v.vital_type === 'BLOOD_PRESSURE_SYSTOLIC')
  const dia = vitals.find(v => v.vital_type.toLowerCase().includes('diastolic') || v.vital_type === 'BLOOD_PRESSURE_DIASTOLIC')
  if (sys && dia) return { systolic: sys.value, diastolic: dia.value }
  return null
}

// ── Section: Vitals Strip ─────────────────────────────────────────────────

function VitalsStrip({ profile }: { profile: HealthProfile }) {
  const bpReading = deriveBloodPressure(profile.recent_vitals)
  const bloodGroup = profile.member.blood_group
  const allergies = profile.allergies

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {/* Blood Pressure card */}
      <div className="bg-surface-container-lowest rounded-xl p-4 shadow-sm shadow-teal-900/5">
        <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-2">
          Blood Pressure
        </p>
        {bpReading !== null ? (
          <>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-extrabold text-on-surface">
                {bpReading.systolic}
              </span>
              <span className="text-lg font-bold text-on-surface-variant">/</span>
              <span className="text-4xl font-extrabold text-on-surface">
                {bpReading.diastolic}
              </span>
              <span className="text-sm text-on-surface-variant">mmHg</span>
            </div>
            <p className="text-xs text-on-surface-variant/70 mt-2">From uploaded records</p>
          </>
        ) : (
          <div className="flex flex-col gap-1 mt-1">
            <span className="text-4xl font-extrabold text-on-surface">—</span>
            <p className="text-xs text-on-surface-variant/70">
              Upload a vitals record to see your BP
            </p>
          </div>
        )}
      </div>

      {/* Blood Type card */}
      <div className="bg-primary rounded-xl p-4 shadow-sm shadow-teal-900/10 text-white">
        <p className="text-xs font-semibold text-white/70 uppercase tracking-wide mb-2">
          Blood Type
        </p>
        <p className="text-3xl font-extrabold mb-3">
          {bloodGroup ?? 'Unknown'}
        </p>
        <div className="flex flex-wrap gap-1.5">
          {allergies.length === 0 ? (
            <span className="text-xs font-semibold bg-white/20 rounded-full px-2 py-0.5">
              No known allergies
            </span>
          ) : (
            allergies.slice(0, 3).map(a => (
              <span key={a.allergy_id} className="text-xs font-semibold bg-white/20 rounded-full px-2 py-0.5">
                {a.allergen_name}
              </span>
            ))
          )}
          {allergies.length > 3 && (
            <span className="text-xs font-semibold bg-white/20 rounded-full px-2 py-0.5">
              +{allergies.length - 3} more
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Section: Biochemical Metrics ──────────────────────────────────────────

function labIconForTest(testName: string) {
  const name = testName.toLowerCase()
  if (name.includes('cholesterol') || name.includes('lipid')) return <IconHeart />
  if (name.includes('vitamin') || name.includes('glucose') || name.includes('hba1c') || name.includes('a1c')) return <IconDroplet />
  return <IconBeaker />
}

function BiochemicalMetrics({ labs }: { labs: LabResult[] }) {
  const displayLabs = labs.slice(0, 5)

  return (
    <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm shadow-teal-900/5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-extrabold text-on-surface tracking-tight">
          Biochemical Metrics
        </h2>
        <button
          type="button"
          className="text-xs font-semibold text-primary hover:underline min-h-[44px] px-2 uppercase tracking-wide"
        >
          View Historical
        </button>
      </div>

      {displayLabs.length === 0 ? (
        <EmptyState
          icon={<IconBeaker />}
          title="No lab results yet"
          subtitle="Upload a lab report to see your biochemical metrics"
        />
      ) : (
        <div className="space-y-3">
          {displayLabs.map((lab) => {
            const displayValue = lab.value !== null
              ? `${lab.value}${lab.unit ? ` ${lab.unit}` : ''}`
              : lab.value_text ?? '—'
            return (
              <div
                key={lab.result_id}
                className="flex items-center gap-3 py-2"
              >
                <div className="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center flex-shrink-0 text-primary">
                  {labIconForTest(lab.test_name)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-on-surface truncate">
                    {lab.test_name_normalized ?? lab.test_name}
                  </p>
                  {lab.test_date && (
                    <p className="text-xs text-on-surface-variant/60">
                      {new Date(lab.test_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </p>
                  )}
                </div>
                <span className="text-sm font-bold text-on-surface mr-2 flex-shrink-0">
                  {displayValue}
                </span>
                <LabFlagBadge flag={lab.flag} />
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ── Section: Active Plan (Medications) ───────────────────────────────────

function ActivePlan({ medications, memberId }: { medications: Medication[]; memberId: string }) {
  const queryClient = useQueryClient()
  const [showDiscontinued, setShowDiscontinued] = useState(false)

  const discontinueMutation = useMutation({
    mutationFn: async (medId: string) => {
      await api.patch(`/profile/${memberId}/medications/${medId}/discontinue`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile', memberId] })
    },
  })

  const activeMeds = medications.filter(m => m.is_active).slice(0, 6)
  const discontinuedMeds = medications.filter(m => !m.is_active)
  const allActiveDiscontinued = activeMeds.length === 0

  const visibleMeds = showDiscontinued
    ? [...activeMeds, ...discontinuedMeds.slice(0, 6)]
    : activeMeds

  return (
    <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm shadow-teal-900/5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-extrabold text-on-surface tracking-tight">
          Active Plan
        </h2>
        <button
          type="button"
          aria-label="Edit active plan"
          className="text-on-surface-variant hover:text-primary transition-colors p-1.5 rounded-lg hover:bg-surface-container min-w-[44px] min-h-[44px] flex items-center justify-center"
        >
          <IconEdit />
        </button>
      </div>

      {allActiveDiscontinued && !showDiscontinued ? (
        <EmptyState
          icon={<IconActivity />}
          title="No active medications"
          subtitle="Upload a prescription to populate your medication plan"
        />
      ) : (
        <ul className="space-y-3 mb-4">
          {visibleMeds.map((med) => {
            const isDiscontinued = !med.is_active
            const isPending = discontinueMutation.isPending && discontinueMutation.variables === med.medication_id
            return (
              <li
                key={med.medication_id}
                className={`flex items-start gap-2 ${isDiscontinued ? 'opacity-50' : ''}`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 ${isDiscontinued ? 'bg-on-surface-variant' : 'bg-primary'}`}
                  aria-hidden="true"
                />
                <div className="min-w-0 flex-1">
                  <p className={`text-sm font-semibold text-on-surface leading-tight ${isDiscontinued ? 'line-through' : ''}`}>
                    {med.drug_name_normalized ?? med.drug_name}
                  </p>
                  <div className="flex items-center gap-2 flex-wrap">
                    {([med.dosage, med.frequency].filter((v): v is string => v !== null).length > 0) && (
                      <p className="text-xs text-on-surface-variant">
                        {[med.dosage, med.frequency].filter((v): v is string => v !== null).join(' · ')}
                      </p>
                    )}
                    {isDiscontinued && (
                      <span className="text-[10px] font-bold bg-surface-container text-on-surface-variant rounded px-2 py-0.5">
                        Discontinued
                      </span>
                    )}
                  </div>
                </div>
                {!isDiscontinued && (
                  <button
                    type="button"
                    aria-label={`Discontinue ${med.drug_name_normalized ?? med.drug_name}`}
                    disabled={isPending}
                    onClick={() => discontinueMutation.mutate(med.medication_id)}
                    className={`text-xs text-error hover:bg-error-container/30 rounded px-2 py-1 transition-colors flex-shrink-0 min-h-[44px] flex items-center ${isPending ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {isPending ? '…' : 'Discontinue'}
                  </button>
                )}
              </li>
            )
          })}
        </ul>
      )}

      {discontinuedMeds.length > 0 && (
        <button
          type="button"
          onClick={() => setShowDiscontinued(prev => !prev)}
          className="text-xs text-on-surface-variant hover:text-on-surface transition-colors mb-4 min-h-[44px] px-1 flex items-center gap-1"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            className={`w-3 h-3 transition-transform ${showDiscontinued ? 'rotate-180' : ''}`}
            aria-hidden="true">
            <polyline points="6 9 12 15 18 9" />
          </svg>
          {showDiscontinued ? 'Hide discontinued' : `Show ${discontinuedMeds.length} discontinued`}
        </button>
      )}

      <button
        type="button"
        className="w-full text-sm font-semibold text-primary border border-primary/30 rounded-full px-4 py-2.5 hover:bg-primary/5 transition-colors min-h-[44px] uppercase tracking-wide"
      >
        Manage Medications
      </button>
    </div>
  )
}

// ── Section: Known Conditions ─────────────────────────────────────────────

function IconCondition() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      className="w-4 h-4" aria-hidden="true">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  )
}

function KnownConditions({ diagnoses }: { diagnoses: Diagnosis[] }) {
  const statusColors: Record<string, string> = {
    ACTIVE: 'bg-error-container text-error',
    CHRONIC: 'bg-tertiary-container text-tertiary',
    RESOLVED: 'bg-primary-fixed text-primary',
    UNKNOWN: 'bg-surface-container text-on-surface-variant',
  }

  return (
    <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm shadow-teal-900/5">
      <h2 className="text-base font-extrabold text-on-surface tracking-tight mb-4">
        Known Conditions
      </h2>

      {diagnoses.length === 0 ? (
        <EmptyState
          icon={<IconCondition />}
          title="No conditions recorded"
          subtitle="Diagnoses extracted from uploaded documents will appear here"
        />
      ) : (
        <ul className="space-y-2">
          {diagnoses.slice(0, 5).map(d => (
            <li key={d.diagnosis_id} className="flex items-center gap-2">
              <span
                className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${d.status === 'ACTIVE' || d.status === 'CHRONIC' ? 'bg-error' : 'bg-primary'}`}
                aria-hidden="true"
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-on-surface truncate">
                  {d.condition_name}
                </p>
                {d.icd10_code && (
                  <p className="text-xs text-on-surface-variant/60">{d.icd10_code}</p>
                )}
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex-shrink-0 ${statusColors[d.status] ?? statusColors['UNKNOWN']}`}>
                {d.status}
              </span>
            </li>
          ))}
          {diagnoses.length > 5 && (
            <p className="text-xs text-on-surface-variant/60 pt-1">
              +{diagnoses.length - 5} more conditions
            </p>
          )}
        </ul>
      )}
    </div>
  )
}

// ── Section: Encounter History ────────────────────────────────────────────

interface EncounterItem {
  encounter_id: string
  encounter_date: string
  provider_name: string
  chief_complaint: string | null
  diagnosis_notes: string | null
  prescriptions_note: string | null
  follow_up_date: string | null
}

interface EncounterListResponse {
  items: EncounterItem[]
  total: number
}

function formatEncounterDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' })
}

function EncounterHistory({ memberId }: { memberId: string }) {
  const { data, isLoading } = useQuery<EncounterListResponse>({
    queryKey: ['encounters', memberId],
    queryFn: async () => {
      const { data } = await api.get(`/profile/${memberId}/encounters`)
      return data
    },
    enabled: !!memberId,
  })

  const encounters = data?.items ?? []

  return (
    <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm shadow-teal-900/5">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-6 h-6 flex items-center justify-center text-primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
        </div>
        <h2 className="text-base font-extrabold text-on-surface tracking-tight">Provider Encounters</h2>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[0, 1].map((i) => (
            <div key={i} className="h-16 rounded-lg bg-surface-container animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && encounters.length === 0 && (
        <p className="text-sm text-on-surface-variant text-center py-6">
          No provider encounters recorded yet. When a doctor views your profile and logs a visit, it will appear here.
        </p>
      )}

      {!isLoading && encounters.length > 0 && (
        <ul className="space-y-4">
          {encounters.map((enc) => (
            <li key={enc.encounter_id} className="border-l-2 border-primary/30 pl-4 space-y-1">
              <div className="flex items-baseline justify-between gap-2">
                <p className="text-sm font-bold text-on-surface">{enc.provider_name}</p>
                <p className="text-xs text-on-surface-variant shrink-0">{formatEncounterDate(enc.encounter_date)}</p>
              </div>
              {enc.chief_complaint && (
                <p className="text-xs text-on-surface-variant">{enc.chief_complaint}</p>
              )}
              {enc.diagnosis_notes && (
                <p className="text-sm text-on-surface">{enc.diagnosis_notes}</p>
              )}
              {enc.prescriptions_note && (
                <p className="text-xs text-on-surface-variant italic">{enc.prescriptions_note}</p>
              )}
              {enc.follow_up_date && (
                <p className="text-xs text-primary font-medium">
                  Follow up: {formatEncounterDate(enc.follow_up_date)}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ── Main Dashboard Page ───────────────────────────────────────────────────

export function DashboardPage() {
  const memberId = useResolvedMemberId()

  const { data: profile, isLoading, isError, error } = useQuery<HealthProfile>({
    queryKey: ['profile', memberId],
    queryFn: async () => {
      const { data } = await api.get<HealthProfile>(`/profile/?member_id=${memberId}`)
      return data
    },
    enabled: !!memberId,
  })

  if (isLoading) {
    return <DashboardSkeleton />
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-14 h-14 rounded-2xl bg-error-container flex items-center justify-center mb-4">
          <IconActivity />
        </div>
        <p className="text-base font-bold text-on-surface">Failed to load health profile</p>
        <p className="text-sm text-on-surface-variant mt-1">
          {error instanceof Error ? error.message : 'Please try again later'}
        </p>
      </div>
    )
  }

  if (!profile) return null

  const memberName = profile.member.full_name

  return (
    <div className="space-y-6">
      {/* ── Header Row ──────────────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">
          Health Profile
        </h1>
        {memberName && (
          <p className="text-sm text-on-surface-variant mt-0.5">{memberName}</p>
        )}
      </div>

      {/* ── Vitals Strip ────────────────────────────────────────────────── */}
      <VitalsStrip profile={profile} />

      {/* ── Two-column layout: metrics (left) + sidebar (right) ─────────── */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        {/* Left column: Biochemical Metrics */}
        <div className="md:col-span-3">
          <BiochemicalMetrics labs={profile.recent_labs} />
        </div>

        {/* Right column: Active Plan + Known Conditions */}
        <div className="md:col-span-2 space-y-4">
          <ActivePlan medications={profile.medications} memberId={memberId!} />
          <KnownConditions diagnoses={profile.diagnoses} />
        </div>
      </div>

      {/* ── Provider Encounters ─────────────────────────────────────────── */}
      <EncounterHistory memberId={memberId!} />

      {/* ── Trends: Coming Soon ──────────────────────────────────────────── */}
      <div className="bg-surface-container-lowest rounded-xl p-6 shadow-sm shadow-teal-900/5 flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary flex-shrink-0">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5" aria-hidden="true">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
        </div>
        <div>
          <p className="text-sm font-extrabold text-on-surface tracking-tight">Lab Trends & Medication Timeline</p>
          <p className="text-sm text-on-surface-variant mt-1">
            Track how your HbA1c, cholesterol, kidney function, and other values change over time. Medication timelines will show active and past prescriptions in a visual Gantt view. Available once document upload is enabled.
          </p>
          <span className="inline-block mt-3 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold tracking-wide">
            Coming Soon
          </span>
        </div>
      </div>
    </div>
  )
}
