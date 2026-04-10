import axios from 'axios'
import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Medication {
  drug_name: string
  dosage: string
  frequency?: string
}

interface PublicPassportData {
  passport_id: string
  member_name: string
  blood_group: string | null
  allergies: string[]
  medications: Medication[]
  diagnoses: string[]
  generated_at: string
  expires_at: string | null
  disclaimer: string
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function shortId(id: string): string {
  return id.slice(0, 8).toUpperCase()
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SkeletonCard({ rows = 3 }: { rows?: number }) {
  return (
    <div className="bg-white rounded-2xl shadow-[0_4px_24px_rgba(0,107,95,0.10)] p-6 space-y-3 animate-pulse">
      <div className="h-4 bg-surface-container rounded w-1/3" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-3 bg-surface-container rounded w-full" />
      ))}
    </div>
  )
}

function MinimalHeader() {
  return (
    <header className="sticky top-0 z-10 bg-white/70 backdrop-blur-md border-b border-teal-500/10">
      <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
        <span className="text-primary text-lg font-extrabold tracking-tighter">
          MediVault
        </span>
        <span className="text-xs font-semibold text-primary border border-primary/40 rounded-full px-3 py-1">
          Verified by MediVault
        </span>
      </div>
    </header>
  )
}

// Lock SVG for 410 state
function LockIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-12 h-12 text-primary mx-auto mb-4"
      aria-hidden="true"
    >
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Page states
// ---------------------------------------------------------------------------

function LoadingState() {
  return (
    <div className="min-h-screen bg-surface">
      <MinimalHeader />
      <main className="max-w-3xl mx-auto px-4 py-8 space-y-4">
        <SkeletonCard rows={4} />
        <SkeletonCard rows={3} />
        <SkeletonCard rows={3} />
      </main>
    </div>
  )
}

function NotFoundState() {
  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <MinimalHeader />
      <div className="flex-1 flex flex-col items-center justify-center px-4 text-center space-y-4">
        <p className="text-2xl font-bold text-on-surface">Passport not found</p>
        <p className="text-sm text-on-surface-variant">
          The passport you are looking for does not exist or has been removed.
        </p>
        <Link
          to="/"
          className="text-sm font-semibold text-primary underline underline-offset-2"
        >
          Go to home
        </Link>
      </div>
    </div>
  )
}

function RevokedState() {
  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <MinimalHeader />
      <div className="flex-1 flex flex-col items-center justify-center px-4 text-center space-y-4">
        <LockIcon />
        <p className="text-2xl font-bold text-on-surface">Passport expired or revoked</p>
        <p className="text-sm text-on-surface-variant max-w-xs">
          This passport has expired or been revoked by the account holder.
        </p>
        <Link
          to="/"
          className="text-sm font-semibold text-primary underline underline-offset-2"
        >
          Go to home
        </Link>
      </div>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <MinimalHeader />
      <div className="flex-1 flex flex-col items-center justify-center px-4 text-center space-y-4">
        <p className="text-2xl font-bold text-on-surface">Something went wrong</p>
        <p className="text-sm text-on-surface-variant max-w-xs">{message}</p>
        <Link
          to="/"
          className="text-sm font-semibold text-primary underline underline-offset-2"
        >
          Go to home
        </Link>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Passport content
// ---------------------------------------------------------------------------

function HeroCard({ data }: { data: PublicPassportData }) {
  return (
    <div className="bg-white rounded-2xl shadow-[0_4px_24px_rgba(0,107,95,0.10)] p-6 space-y-4">
      {/* Label */}
      <p className="text-xs font-semibold tracking-widest uppercase text-primary">
        Health Passport
      </p>

      {/* Name + blood group row */}
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold text-on-surface">{data.member_name}</h1>
        {data.blood_group ? (
          <span className="text-sm font-bold bg-error-container text-error px-3 py-0.5 rounded-full">
            {data.blood_group}
          </span>
        ) : (
          <span className="text-sm font-medium bg-surface-container text-on-surface-variant px-3 py-0.5 rounded-full">
            Blood group unknown
          </span>
        )}
      </div>

      {/* Passport ID */}
      <p className="font-mono text-xs text-on-surface-variant tracking-wider">
        ID: {shortId(data.passport_id)}
      </p>

      {/* Dates */}
      <div className="flex flex-wrap gap-4 text-xs text-on-surface-variant">
        <span>
          <span className="font-semibold text-on-surface">Generated:</span>{' '}
          {formatDate(data.generated_at)}
        </span>
        {data.expires_at ? (
          <span>
            <span className="font-semibold text-on-surface">Expires:</span>{' '}
            {formatDate(data.expires_at)}
          </span>
        ) : (
          <span>
            <span className="font-semibold text-on-surface">Expires:</span> Never
          </span>
        )}
      </div>
    </div>
  )
}

function AllergiesCard({ allergies }: { allergies: string[] }) {
  if (allergies.length === 0) return null
  return (
    <div className="bg-white rounded-2xl shadow-[0_4px_24px_rgba(0,107,95,0.10)] p-6 space-y-3">
      <h2 className="text-xs font-semibold tracking-widest uppercase text-primary">
        Allergies
      </h2>
      <div className="flex flex-wrap gap-2">
        {allergies.map((allergen) => (
          <span
            key={allergen}
            className="bg-error-container text-error text-xs font-semibold px-3 py-1 rounded-full"
          >
            {allergen}
          </span>
        ))}
      </div>
    </div>
  )
}

function MedicationsCard({ medications }: { medications: Medication[] }) {
  if (medications.length === 0) return null
  return (
    <div className="bg-white rounded-2xl shadow-[0_4px_24px_rgba(0,107,95,0.10)] p-6 space-y-3">
      <h2 className="text-xs font-semibold tracking-widest uppercase text-primary">
        Active Medications
      </h2>
      <ul className="space-y-2">
        {medications.map((med, idx) => (
          <li key={idx} className="flex items-start gap-2">
            <span className="mt-1.5 w-2 h-2 rounded-full bg-primary flex-shrink-0" aria-hidden="true" />
            <span className="text-sm">
              <span className="font-semibold text-on-surface">{med.drug_name}</span>
              {(med.dosage || med.frequency) && (
                <span className="text-on-surface-variant">
                  {' '}
                  &mdash;{' '}
                  {[med.dosage, med.frequency]
                    .filter((v): v is string => Boolean(v))
                    .join(', ')}
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function DiagnosesCard({ diagnoses }: { diagnoses: string[] }) {
  if (diagnoses.length === 0) return null
  return (
    <div className="bg-white rounded-2xl shadow-[0_4px_24px_rgba(0,107,95,0.10)] p-6 space-y-3">
      <h2 className="text-xs font-semibold tracking-widest uppercase text-primary">
        Diagnoses
      </h2>
      <ul className="space-y-2">
        {diagnoses.map((diagnosis, idx) => (
          <li key={idx} className="flex items-start gap-2">
            <span className="mt-1.5 w-2 h-2 rounded-full bg-yellow-400 flex-shrink-0" aria-hidden="true" />
            <span className="text-sm text-on-surface">{diagnosis}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function DisclaimerBar({ disclaimer }: { disclaimer: string }) {
  return (
    <p className="text-xs italic text-on-surface-variant text-center px-2">
      {disclaimer}
    </p>
  )
}

function PageFooter() {
  return (
    <footer className="text-xs text-on-surface-variant text-center py-8 px-4">
      This passport was generated by MediVault. Information is patient-reported and for
      reference only.
    </footer>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type PageState =
  | { kind: 'loading' }
  | { kind: 'not-found' }
  | { kind: 'revoked' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; data: PublicPassportData }

export function PublicPassportPage() {
  const { uuid } = useParams<{ uuid: string }>()
  const [state, setState] = useState<PageState>({ kind: 'loading' })

  useEffect(() => {
    if (!uuid) {
      setState({ kind: 'not-found' })
      return
    }

    let cancelled = false

    axios
      .get<PublicPassportData>(`${API_BASE}/passport/public/${uuid}`)
      .then((res) => {
        if (!cancelled) {
          setState({ kind: 'ready', data: res.data })
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (axios.isAxiosError(err)) {
          const status = err.response?.status
          if (status === 404) {
            setState({ kind: 'not-found' })
          } else if (status === 410) {
            setState({ kind: 'revoked' })
          } else {
            const responseData = err.response?.data as Record<string, unknown> | undefined
            const serverMessage =
              typeof responseData?.message === 'string' ? responseData.message : undefined
            setState({
              kind: 'error',
              message:
                serverMessage ?? 'Unable to load the passport. Please try again later.',
            })
          }
        } else {
          setState({
            kind: 'error',
            message: 'Unable to load the passport. Please try again later.',
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [uuid])

  if (state.kind === 'loading') return <LoadingState />
  if (state.kind === 'not-found') return <NotFoundState />
  if (state.kind === 'revoked') return <RevokedState />
  if (state.kind === 'error') return <ErrorState message={state.message} />

  const { data } = state

  return (
    <div className="min-h-screen bg-surface">
      <MinimalHeader />
      <main className="max-w-3xl mx-auto px-4 py-8 space-y-4">
        <HeroCard data={data} />

        {/* Section cards — shown only when data is present */}
        <AllergiesCard allergies={data.allergies} />
        <MedicationsCard medications={data.medications} />
        <DiagnosesCard diagnoses={data.diagnoses} />

        {/* Disclaimer */}
        <DisclaimerBar disclaimer={data.disclaimer} />
      </main>
      <PageFooter />
    </div>
  )
}
