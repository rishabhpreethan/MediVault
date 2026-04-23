import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { useResolvedMemberId } from '../../hooks/useFamily'
import type { HealthProfile, Medication, Diagnosis, LabResult, LabFlag } from '../../types'

// ── Helpers ────────────────────────────────────────────────────────────────

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function flagBadge(flag: LabFlag) {
  switch (flag) {
    case 'HIGH':
      return <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold bg-error-container text-error">HIGH</span>
    case 'LOW':
      return <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold bg-tertiary-container text-tertiary">LOW</span>
    case 'CRITICAL':
      return <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold bg-error text-on-error">CRITICAL</span>
    default:
      return <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary">NORMAL</span>
  }
}

function diagnosisStatusBadge(status: Diagnosis['status']) {
  const map: Record<Diagnosis['status'], string> = {
    ACTIVE: 'bg-error-container text-error',
    CHRONIC: 'bg-tertiary-container text-tertiary',
    RESOLVED: 'bg-primary/10 text-primary',
    UNKNOWN: 'bg-surface-container text-on-surface-variant',
  }
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${map[status]}`}>
      {status}
    </span>
  )
}

// Latest result per test name
function latestLabResults(labs: LabResult[]): LabResult[] {
  const map = new Map<string, LabResult>()
  for (const lab of labs) {
    const existing = map.get(lab.test_name)
    if (!existing) {
      map.set(lab.test_name, lab)
    } else {
      const existingDate = existing.test_date ?? ''
      const newDate = lab.test_date ?? ''
      if (newDate > existingDate) map.set(lab.test_name, lab)
    }
  }
  return [...map.values()].sort((a, b) => (b.test_date ?? '').localeCompare(a.test_date ?? ''))
}

// ── Section card ───────────────────────────────────────────────────────────

function SectionCard({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-surface-container-low overflow-hidden">
      <div className="flex items-center gap-3 px-5 py-4 border-b border-surface-container-low">
        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary flex-shrink-0">
          {icon}
        </div>
        <h2 className="text-sm font-extrabold text-on-surface uppercase tracking-wide">{title}</h2>
      </div>
      <div className="p-5">{children}</div>
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <p className="text-sm text-on-surface-variant text-center py-6">{message}</p>
  )
}

// ── Sub-sections ───────────────────────────────────────────────────────────

function ActiveMedications({ medications }: { medications: Medication[] }) {
  const active = medications.filter((m) => m.is_active)
  return (
    <SectionCard
      title="Active Medications"
      icon={
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
          <path d="M12 2a2 2 0 0 1 2 2v16a2 2 0 0 1-4 0V4a2 2 0 0 1 2-2z" />
          <path d="M6 8h12" />
        </svg>
      }
    >
      {active.length === 0 ? (
        <EmptyState message="No active medications on record" />
      ) : (
        <ul className="divide-y divide-surface-container-low">
          {active.map((med) => (
            <li key={med.medication_id} className="py-3 flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-on-surface truncate">
                  {med.drug_name_normalized ?? med.drug_name}
                </p>
                {(med.dosage || med.frequency) && (
                  <p className="text-xs text-on-surface-variant mt-0.5">
                    {[med.dosage, med.frequency].filter(Boolean).join(' · ')}
                  </p>
                )}
              </div>
              {med.start_date && (
                <p className="text-xs text-on-surface-variant whitespace-nowrap flex-shrink-0">
                  Since {formatDate(med.start_date)}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  )
}

function RecentDiagnoses({ diagnoses }: { diagnoses: Diagnosis[] }) {
  const recent = diagnoses.slice(0, 6)
  return (
    <SectionCard
      title="Diagnoses"
      icon={
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
          <path d="M9 12l2 2 4-4" />
          <path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
        </svg>
      }
    >
      {recent.length === 0 ? (
        <EmptyState message="No diagnoses on record" />
      ) : (
        <ul className="divide-y divide-surface-container-low">
          {recent.map((dx) => (
            <li key={dx.diagnosis_id} className="py-3 flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-on-surface truncate">{dx.condition_name}</p>
                {dx.icd10_code && (
                  <p className="text-xs text-on-surface-variant font-mono mt-0.5">{dx.icd10_code}</p>
                )}
              </div>
              <div className="flex flex-col items-end gap-1 flex-shrink-0">
                {diagnosisStatusBadge(dx.status)}
                {dx.diagnosed_date && (
                  <p className="text-[10px] text-on-surface-variant">{formatDate(dx.diagnosed_date)}</p>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  )
}

function LatestLabResults({ labs }: { labs: LabResult[] }) {
  const latest = latestLabResults(labs)
  return (
    <SectionCard
      title="Latest Lab Results"
      icon={
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
          <path d="M9 3v8l-4 6a2 2 0 0 0 1.697 3.05h10.606A2 2 0 0 0 19 17l-4-6V3" />
          <path d="M9 3h6" />
        </svg>
      }
    >
      {latest.length === 0 ? (
        <EmptyState message="No lab results on record" />
      ) : (
        <ul className="divide-y divide-surface-container-low">
          {latest.map((lab) => (
            <li key={lab.result_id} className="py-3 flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-on-surface truncate">{lab.test_name}</p>
                <p className="text-xs text-on-surface-variant mt-0.5">
                  {lab.value != null ? `${lab.value}${lab.unit ? ' ' + lab.unit : ''}` : (lab.value_text ?? '—')}
                  {lab.reference_low != null && lab.reference_high != null && (
                    <span className="ml-2 opacity-60">ref {lab.reference_low}–{lab.reference_high}</span>
                  )}
                </p>
              </div>
              <div className="flex flex-col items-end gap-1 flex-shrink-0">
                {flagBadge(lab.flag)}
                {lab.test_date && (
                  <p className="text-[10px] text-on-surface-variant">{formatDate(lab.test_date)}</p>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  )
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function SkeletonSection() {
  return (
    <div className="bg-white rounded-2xl border border-surface-container-low p-5 space-y-3 animate-pulse">
      <div className="h-4 bg-surface-container rounded w-40" />
      <div className="h-3 bg-surface-container rounded w-full" />
      <div className="h-3 bg-surface-container rounded w-3/4" />
      <div className="h-3 bg-surface-container rounded w-5/6" />
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────

export function InsightsPage() {
  const memberId = useResolvedMemberId()

  const { data: profile, isLoading, isError } = useQuery<HealthProfile>({
    queryKey: ['profile', memberId],
    queryFn: async () => {
      const { data } = await api.get(`/profile/${memberId}`)
      return data
    },
    enabled: !!memberId,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">Health Summary</h1>
        <p className="text-sm text-on-surface-variant mt-1">
          A snapshot of your current health — medications, diagnoses, and lab results
        </p>
      </div>

      {isError && (
        <div className="rounded-xl bg-error-container px-5 py-4 text-sm text-error font-medium">
          Failed to load health data. Please try again.
        </div>
      )}

      {isLoading && (
        <>
          <SkeletonSection />
          <SkeletonSection />
          <SkeletonSection />
        </>
      )}

      {profile && (
        <>
          <ActiveMedications medications={profile.medications} />
          <RecentDiagnoses diagnoses={profile.diagnoses} />
          <LatestLabResults labs={profile.recent_labs} />
        </>
      )}
    </div>
  )
}
