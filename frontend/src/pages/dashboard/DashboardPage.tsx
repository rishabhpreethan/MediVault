import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { api } from '../../lib/api'
import { useResolvedMemberId } from '../../hooks/useFamily'
import type { HealthProfile, LabResult, Medication, Vital, LabFlag } from '../../types/index'

// ── Inline SVG icons ───────────────────────────────────────────────────────

function IconShare() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      className="w-4 h-4" aria-hidden="true">
      <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
      <polyline points="16 6 12 2 8 6" />
      <line x1="12" y1="2" x2="12" y2="15" />
    </svg>
  )
}

function IconPlus() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
      className="w-4 h-4" aria-hidden="true">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  )
}

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

function IconCalendar() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      className="w-4 h-4" aria-hidden="true">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
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
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SkeletonBlock className="h-32 rounded-xl" />
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

// ── Static sparkline (no real data needed) ────────────────────────────────

function Sparkline() {
  // Static bar heights for visual decoration
  const bars = [6, 10, 8, 14, 10, 12, 9, 14, 11, 13]
  return (
    <div className="flex items-end gap-0.5 h-8" aria-hidden="true">
      {bars.map((h, i) => (
        <div
          key={i}
          className="w-1.5 rounded-sm bg-primary/20"
          style={{ height: `${h * 2}px` }}
        />
      ))}
    </div>
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

function deriveHeartRate(vitals: Vital[]): number | null {
  const hr = vitals.find(v =>
    v.vital_type === 'HEART_RATE' ||
    v.vital_type.toLowerCase().includes('pulse') ||
    v.vital_type.toLowerCase().includes('heart_rate')
  )
  return hr ? hr.value : null
}

// ── Section: Vitals Strip ─────────────────────────────────────────────────

function VitalsStrip({ profile }: { profile: HealthProfile }) {
  const bpReading = deriveBloodPressure(profile.recent_vitals)
  const heartRate = deriveHeartRate(profile.recent_vitals)
  const bloodGroup = profile.member.blood_group
  const hasAllergies = profile.allergies.length > 0

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {/* Pulse Rate card */}
      <div className="bg-surface-container-lowest rounded-xl p-4 shadow-sm shadow-teal-900/5">
        <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-2">
          Pulse Rate
        </p>
        {heartRate !== null ? (
          <>
            <div className="flex items-baseline gap-1 mb-2">
              <span className="text-4xl font-extrabold text-on-surface">{Math.round(heartRate)}</span>
              <span className="text-sm text-on-surface-variant">bpm</span>
              <span className="ml-auto text-xs font-semibold px-2 py-0.5 rounded-full bg-primary-fixed text-primary">
                STABLE
              </span>
            </div>
            <Sparkline />
          </>
        ) : (
          <div className="flex items-baseline gap-1 mb-2">
            <span className="text-4xl font-extrabold text-on-surface">—</span>
            <span className="text-xs text-on-surface-variant mt-1">No data yet</span>
          </div>
        )}
      </div>

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
            <p className="text-xs text-on-surface-variant/70 mt-2">Last checked recently</p>
          </>
        ) : (
          <>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-extrabold text-on-surface">118</span>
              <span className="text-lg font-bold text-on-surface-variant">/</span>
              <span className="text-4xl font-extrabold text-on-surface">76</span>
              <span className="text-sm text-on-surface-variant">mmHg</span>
            </div>
            <p className="text-xs text-on-surface-variant/70 mt-2">Last checked 2h ago</p>
          </>
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
          {hasAllergies ? (
            <span className="text-xs font-semibold bg-white/20 rounded-full px-2 py-0.5">
              {profile.allergies.length} {profile.allergies.length === 1 ? 'Allergy' : 'Allergies'}
            </span>
          ) : (
            <span className="text-xs font-semibold bg-white/20 rounded-full px-2 py-0.5">
              No Allergies
            </span>
          )}
          <span className="text-xs font-semibold bg-white/20 rounded-full px-2 py-0.5">
            Donor
          </span>
          <span className="text-xs font-semibold bg-white/20 rounded-full px-2 py-0.5">
            Insured
          </span>
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

function ActivePlan({ medications }: { medications: Medication[] }) {
  const activeMeds = medications.filter(m => m.is_active).slice(0, 6)

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

      {activeMeds.length === 0 ? (
        <EmptyState
          icon={<IconActivity />}
          title="No active medications"
          subtitle="Upload a prescription to populate your medication plan"
        />
      ) : (
        <ul className="space-y-3 mb-4">
          {activeMeds.map((med) => (
            <li key={med.medication_id} className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" aria-hidden="true" />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-on-surface leading-tight">
                  {med.drug_name_normalized ?? med.drug_name}
                </p>
                <p className="text-xs text-on-surface-variant">
                  {[med.dosage, med.frequency].filter((v): v is string => v !== null).join(' · ')}
                </p>
              </div>
            </li>
          ))}
        </ul>
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

// ── Section: Upcoming Consult ─────────────────────────────────────────────

function UpcomingConsult({ profile }: { profile: HealthProfile }) {
  // Find the most recent doctor visit from vitals metadata — we use a static placeholder
  // until MV-046 doctor extraction is surfaced in the profile API response
  const memberName = profile.member.full_name

  return (
    <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm shadow-teal-900/5">
      <h2 className="text-base font-extrabold text-on-surface tracking-tight mb-4">
        Upcoming Consult
      </h2>
      <div className="flex items-center gap-3">
        <div className="w-11 h-11 rounded-full bg-primary-fixed flex items-center justify-center flex-shrink-0">
          <span className="text-primary font-bold text-sm">DR</span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-on-surface">Dr. General Physician</p>
          <p className="text-xs text-on-surface-variant">Annual checkup</p>
        </div>
        <div className="flex items-center gap-1 text-xs text-on-surface-variant flex-shrink-0">
          <IconCalendar />
          <span>Schedule</span>
        </div>
      </div>
      {memberName && (
        <p className="text-xs text-on-surface-variant/60 mt-3">
          Profile: {memberName}
        </p>
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">
            Health Profile
          </h1>
          {memberName && (
            <p className="text-sm text-on-surface-variant mt-0.5">{memberName}</p>
          )}
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <button
            type="button"
            className="flex items-center gap-2 text-sm font-semibold text-primary border border-primary/30 rounded-full px-4 py-2.5 hover:bg-primary/5 transition-colors min-h-[44px]"
          >
            <IconShare />
            Share Vault
          </button>
          <button
            type="button"
            className="flex items-center gap-2 text-sm font-semibold text-white bg-primary rounded-full px-4 py-2.5 hover:bg-primary/90 transition-colors shadow-sm shadow-teal-900/10 min-h-[44px]"
          >
            <IconPlus />
            New Entry
          </button>
        </div>
      </div>

      {/* ── Vitals Strip ────────────────────────────────────────────────── */}
      <VitalsStrip profile={profile} />

      {/* ── Two-column layout: metrics (left) + sidebar (right) ─────────── */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        {/* Left column: Biochemical Metrics */}
        <div className="md:col-span-3">
          <BiochemicalMetrics labs={profile.recent_labs} />
        </div>

        {/* Right column: Active Plan + Upcoming Consult */}
        <div className="md:col-span-2 space-y-4">
          <ActivePlan medications={profile.medications} />
          <UpcomingConsult profile={profile} />
        </div>
      </div>
    </div>
  )
}
