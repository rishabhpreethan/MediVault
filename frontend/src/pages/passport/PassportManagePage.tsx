import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { QRCodeSVG } from 'qrcode.react'
import { api } from '../../lib/api'
import { useActiveMemberDetails } from '../../hooks/useFamily'

// ── Types ──────────────────────────────────────────────────────────────────

interface PassportResponse {
  passport_id: string
  member_id: string
  share_token: string
  expires_at: string | null
  is_active: boolean
  show_medications: boolean
  show_labs: boolean
  show_diagnoses: boolean
  show_allergies: boolean
  created_at: string | null
  access_count: number
}

interface PassportListResponse {
  items: PassportResponse[]
  total: number
}

interface PassportCreate {
  member_id: string
  expires_in_days: number
  show_medications: boolean
  show_labs: boolean
  show_diagnoses: boolean
  show_allergies: boolean
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function shortToken(token: string): string {
  return token.slice(0, 8).toUpperCase()
}

function passportUrl(shareToken: string): string {
  return `${window.location.origin}/passport/${shareToken}`
}

// ── Generate Passport Modal ────────────────────────────────────────────────

interface GenerateModalProps {
  memberId: string
  onClose: () => void
  onGenerate: (payload: PassportCreate) => void
  isLoading: boolean
}

function GenerateModal({ memberId, onClose, onGenerate, isLoading }: GenerateModalProps) {
  const [showMedications, setShowMedications] = useState(true)
  const [showLabs, setShowLabs] = useState(true)
  const [showDiagnoses, setShowDiagnoses] = useState(true)
  const [showAllergies, setShowAllergies] = useState(true)
  const [expiryDays, setExpiryDays] = useState<30 | 60 | 90>(30)

  function handleSubmit() {
    onGenerate({
      member_id: memberId,
      expires_in_days: expiryDays,
      show_medications: showMedications,
      show_labs: showLabs,
      show_diagnoses: showDiagnoses,
      show_allergies: showAllergies,
    })
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 id="modal-title" className="text-lg font-bold text-on-surface">
            Generate Health Passport
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-surface-container transition-colors"
            aria-label="Close modal"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 text-on-surface-variant" aria-hidden="true">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Section toggles */}
        <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-3">
          Include Sections
        </p>
        <div className="space-y-3 mb-6">
          {[
            { label: 'Medications', value: showMedications, setter: setShowMedications },
            { label: 'Lab Results', value: showLabs, setter: setShowLabs },
            { label: 'Diagnoses', value: showDiagnoses, setter: setShowDiagnoses },
            { label: 'Allergies', value: showAllergies, setter: setShowAllergies },
          ].map(({ label, value, setter }) => (
            <label key={label} className="flex items-center justify-between cursor-pointer min-h-[44px] px-3 rounded-xl hover:bg-surface-container transition-colors">
              <span className="text-sm font-medium text-on-surface">{label}</span>
              <input
                type="checkbox"
                checked={value}
                onChange={(e) => setter(e.target.checked)}
                className="w-5 h-5 accent-primary rounded"
              />
            </label>
          ))}
        </div>

        {/* Expiry */}
        <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-3">
          Expiry
        </p>
        <div className="flex gap-3 mb-7">
          {([30, 60, 90] as const).map((days) => (
            <label
              key={days}
              className={`flex-1 flex items-center justify-center min-h-[44px] rounded-xl border-2 cursor-pointer text-sm font-semibold transition-colors ${
                expiryDays === days
                  ? 'border-primary bg-primary text-white'
                  : 'border-outline-variant text-on-surface-variant hover:border-primary/50'
              }`}
            >
              <input
                type="radio"
                name="expiry"
                value={days}
                checked={expiryDays === days}
                onChange={() => setExpiryDays(days)}
                className="sr-only"
              />
              {days} days
            </label>
          ))}
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 min-h-[44px] rounded-xl border-2 border-outline-variant text-on-surface-variant text-sm font-semibold hover:border-primary/50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isLoading}
            className="flex-1 min-h-[44px] rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors disabled:opacity-60"
          >
            {isLoading ? 'Generating…' : 'Generate'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── QR Access Module ───────────────────────────────────────────────────────

interface QRAccessModuleProps {
  passport: PassportResponse | null
  onGenerate: () => void
}

function QRAccessModule({ passport, onGenerate }: QRAccessModuleProps) {
  const [copied, setCopied] = useState(false)

  async function copyLink() {
    if (!passport) return
    await navigator.clipboard.writeText(passportUrl(passport.share_token))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm shadow-teal-900/5 p-5 flex flex-col items-center gap-4">
      <p className="text-xs font-semibold text-primary uppercase tracking-wide self-start">
        QR Access
      </p>

      {passport ? (
        <>
          <div className="p-3 bg-white rounded-xl shadow-[0_0_0_1px_rgba(0,107,95,0.12)]">
            <QRCodeSVG
              value={passportUrl(passport.share_token)}
              size={160}
              fgColor="#006b5f"
              bgColor="#ffffff"
              level="M"
            />
          </div>

          <button
            type="button"
            onClick={copyLink}
            className="inline-flex items-center gap-2 min-h-[44px] w-full justify-center rounded-xl bg-primary/10 text-primary text-sm font-semibold hover:bg-primary/20 transition-colors"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
              <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
              <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
            </svg>
            {copied ? 'Copied!' : 'Share Secure Link'}
          </button>

          <p className="text-xs text-on-surface-variant text-center">
            Expires {passport.expires_at ? formatDate(passport.expires_at) : 'never'}
          </p>
        </>
      ) : (
        <div className="flex flex-col items-center gap-4 py-6 text-center">
          <div className="w-24 h-24 rounded-xl bg-surface-container flex items-center justify-center">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-10 h-10 text-on-surface-variant/40" aria-hidden="true">
              <rect x="3" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="3" width="7" height="7" rx="1" />
              <rect x="3" y="14" width="7" height="7" rx="1" />
              <path d="M14 14h2v2h-2zM18 14h3M14 18h3M18 18h3M14 22h3M18 22h3" />
            </svg>
          </div>
          <p className="text-xs text-on-surface-variant">No active passport</p>
          <button
            type="button"
            onClick={onGenerate}
            className="min-h-[44px] px-5 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors"
          >
            Generate Passport
          </button>
        </div>
      )}
    </div>
  )
}

// ── Medical Identity Card ──────────────────────────────────────────────────

interface MedicalIdentityCardProps {
  memberName: string | undefined
  dob: string | null | undefined
  bloodGroup: string | null | undefined
  passport: PassportResponse | null
}

function MedicalIdentityCard({ memberName, dob, bloodGroup, passport }: MedicalIdentityCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm shadow-teal-900/5 p-5 col-span-2">
      <p className="text-xs font-semibold text-primary uppercase tracking-wide mb-4">
        Medical Identity
      </p>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-on-surface-variant font-medium uppercase tracking-wide">
            Name
          </p>
          <p className="text-base font-bold text-on-surface mt-1">
            {memberName ?? '—'}
          </p>
        </div>
        <div>
          <p className="text-xs text-on-surface-variant font-medium uppercase tracking-wide">
            Date of Birth
          </p>
          <p className="text-base font-bold text-on-surface mt-1">
            {formatDate(dob ?? null)}
          </p>
        </div>
        <div>
          <p className="text-xs text-on-surface-variant font-medium uppercase tracking-wide">
            Blood Group
          </p>
          {bloodGroup ? (
            <span className="inline-flex items-center mt-1 px-2.5 py-1 rounded-full text-sm font-bold bg-error-container text-error">
              {bloodGroup}
            </span>
          ) : (
            <p className="text-base font-bold text-on-surface mt-1">—</p>
          )}
        </div>
        <div>
          <p className="text-xs text-on-surface-variant font-medium uppercase tracking-wide">
            Passport ID
          </p>
          <p className="mt-1 font-mono text-sm font-bold text-on-surface tracking-wider">
            {passport ? shortToken(passport.share_token) : '—'}
          </p>
        </div>
      </div>

      {passport?.created_at && (
        <p className="mt-4 pt-4 border-t border-outline-variant/30 text-xs text-on-surface-variant">
          Last updated {formatDate(passport.created_at)}
        </p>
      )}
    </div>
  )
}

// ── Active Passports Table ─────────────────────────────────────────────────

interface ActivePassportsProps {
  passports: PassportResponse[]
  onGenerate: () => void
  onRevoke: (passportId: string) => void
  isRevoking: boolean
}

function ActivePassportsTable({ passports, onGenerate, onRevoke, isRevoking }: ActivePassportsProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm shadow-teal-900/5 p-5 col-span-3">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-bold text-on-surface">Active Passports</p>
        <button
          type="button"
          onClick={onGenerate}
          className="inline-flex items-center gap-2 min-h-[44px] px-4 rounded-full bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors shadow-sm shadow-teal-900/10"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Generate New
        </button>
      </div>

      {passports.length === 0 ? (
        <div className="py-10 text-center">
          <p className="text-sm text-on-surface-variant">No passports generated yet.</p>
        </div>
      ) : (
        <div className="overflow-x-auto -mx-5 px-5">
          <table className="w-full text-sm min-w-[560px]">
            <thead>
              <tr className="border-b border-outline-variant/40">
                <th className="text-left pb-3 text-xs font-semibold text-on-surface-variant uppercase tracking-wide">
                  Token
                </th>
                <th className="text-left pb-3 text-xs font-semibold text-on-surface-variant uppercase tracking-wide">
                  Created
                </th>
                <th className="text-left pb-3 text-xs font-semibold text-on-surface-variant uppercase tracking-wide">
                  Expires
                </th>
                <th className="text-right pb-3 text-xs font-semibold text-on-surface-variant uppercase tracking-wide">
                  Access Count
                </th>
                <th className="pb-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/20">
              {passports.map((p) => (
                <tr key={p.passport_id} className="hover:bg-surface-container-low/50 transition-colors">
                  <td className="py-3 pr-4">
                    <span className="font-mono font-bold text-on-surface tracking-wider">
                      {shortToken(p.share_token)}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-on-surface-variant">
                    {formatDate(p.created_at)}
                  </td>
                  <td className="py-3 pr-4 text-on-surface-variant">
                    {p.expires_at ? formatDate(p.expires_at) : 'Never'}
                  </td>
                  <td className="py-3 pr-4 text-right font-semibold text-on-surface">
                    {p.access_count}
                  </td>
                  <td className="py-3 text-right">
                    <button
                      type="button"
                      onClick={() => onRevoke(p.passport_id)}
                      disabled={isRevoking}
                      className="inline-flex items-center min-h-[36px] px-3 rounded-lg bg-error-container text-error text-xs font-semibold hover:bg-error/20 transition-colors disabled:opacity-50"
                    >
                      Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── Visibility Controls ────────────────────────────────────────────────────

interface VisibilityControlsProps {
  passport: PassportResponse | null
}

function VisibilityControls({ passport }: VisibilityControlsProps) {
  const sections: { key: keyof Pick<PassportResponse, 'show_medications' | 'show_labs' | 'show_diagnoses' | 'show_allergies'>; label: string }[] = [
    { key: 'show_medications', label: 'Medications' },
    { key: 'show_labs', label: 'Lab Results' },
    { key: 'show_diagnoses', label: 'Diagnoses' },
    { key: 'show_allergies', label: 'Allergies' },
  ]

  return (
    <div className="bg-white rounded-xl shadow-sm shadow-teal-900/5 p-5 col-span-2">
      <p className="text-sm font-bold text-on-surface mb-1">Passport Contents</p>
      <p className="text-xs text-on-surface-variant mb-4">
        {passport
          ? 'Sections included in this passport. Generate a new passport to change.'
          : 'Generate a passport to configure visible sections.'}
      </p>

      <div className="space-y-2">
        {sections.map(({ key, label }) => {
          const isEnabled = passport ? passport[key] : false
          return (
            <div
              key={key}
              className="flex items-center justify-between min-h-[44px] px-3 rounded-xl bg-surface-container-low"
            >
              <span className="text-sm font-medium text-on-surface">{label}</span>
              {passport ? (
                <div className={`w-5 h-5 rounded-full flex items-center justify-center ${isEnabled ? 'bg-primary' : 'bg-outline-variant/60'}`}>
                  {isEnabled && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3" aria-hidden="true">
                      <path d="M20 6 9 17l-5-5" />
                    </svg>
                  )}
                </div>
              ) : (
                <div className="w-5 h-5 rounded-full bg-outline-variant/40" />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Revoke / Share Panel ───────────────────────────────────────────────────

interface RevokeSharePanelProps {
  passport: PassportResponse | null
  onGenerate: () => void
  onRevoke: (passportId: string) => void
  isRevoking: boolean
}

function RevokeSharePanel({ passport, onGenerate, onRevoke, isRevoking }: RevokeSharePanelProps) {
  return (
    <div className="bg-on-surface rounded-xl p-5 col-span-1 flex flex-col gap-4">
      <p className="text-xs font-semibold text-white/60 uppercase tracking-wide">
        Access Control
      </p>

      {passport ? (
        <>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-white/60 font-medium uppercase tracking-wide">
                Total Accesses
              </p>
              <p className="text-2xl font-extrabold text-white mt-0.5">
                {passport.access_count}
              </p>
            </div>
            <div>
              <p className="text-xs text-white/60 font-medium uppercase tracking-wide">
                Status
              </p>
              <span className="inline-flex items-center mt-1 gap-1.5 px-2.5 py-1 rounded-full bg-primary/30 text-primary-container text-xs font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-primary-container" />
                Active
              </span>
            </div>
          </div>

          <div className="mt-auto">
            <button
              type="button"
              onClick={() => onRevoke(passport.passport_id)}
              disabled={isRevoking}
              className="w-full min-h-[44px] rounded-xl bg-error/20 text-red-300 text-sm font-semibold hover:bg-error/30 transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
                <path d="M18.36 6.64A9 9 0 0 1 20 12a9 9 0 1 1-3.95-7.36" />
                <path d="M9 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4" />
                <path d="m15 3 6 6-6 6" />
              </svg>
              {isRevoking ? 'Revoking…' : 'Revoke Access Now'}
            </button>
          </div>
        </>
      ) : (
        <div className="flex flex-col gap-3 py-4">
          <p className="text-sm text-white/60 leading-relaxed">
            No active passport. Generate one to share your clinical summary with healthcare providers.
          </p>
          <button
            type="button"
            onClick={onGenerate}
            className="w-full min-h-[44px] rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors mt-2"
          >
            Generate Passport
          </button>
        </div>
      )}
    </div>
  )
}

// ── PassportManagePage ─────────────────────────────────────────────────────

export function PassportManagePage() {
  const [showModal, setShowModal] = useState(false)
  const queryClient = useQueryClient()
  const { member } = useActiveMemberDetails()
  const memberId = member?.member_id

  // Fetch passports
  const { data: passportData, isLoading, isError } = useQuery<PassportListResponse>({
    queryKey: ['passports', memberId],
    queryFn: async () => {
      const { data } = await api.get('/passport/', { params: { member_id: memberId } })
      return data
    },
    enabled: !!memberId,
  })

  // Create mutation
  const createMutation = useMutation<PassportResponse, Error, PassportCreate>({
    mutationFn: async (payload) => {
      const { data } = await api.post('/passport/', payload)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['passports', memberId] })
      setShowModal(false)
    },
  })

  // Revoke mutation
  const revokeMutation = useMutation<void, Error, string>({
    mutationFn: async (passportId) => {
      await api.delete(`/passport/${passportId}`)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['passports', memberId] })
    },
  })

  const passports = passportData?.items ?? []
  // Primary active passport (most recently created active one)
  const activePassport = passports.find((p) => p.is_active) ?? null

  const isPassportActive = activePassport !== null

  function handleGenerate(payload: PassportCreate) {
    createMutation.mutate(payload)
  }

  function handleRevoke(passportId: string) {
    revokeMutation.mutate(passportId)
  }

  return (
    <>
      {showModal && memberId && (
        <GenerateModal
          memberId={memberId}
          onClose={() => setShowModal(false)}
          onGenerate={handleGenerate}
          isLoading={createMutation.isPending}
        />
      )}

      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        {/* Page Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">
              Health Passport
            </h1>
            <p className="text-sm text-on-surface-variant mt-1 max-w-xl">
              Your clinical summary and digital credentials, ready for immediate professional verification
            </p>
          </div>

          {/* Secure status badge */}
          <div
            className={`shrink-0 inline-flex items-center gap-2 px-3 py-2 rounded-full text-xs font-bold ${
              isPassportActive
                ? 'bg-primary/10 text-primary'
                : 'bg-surface-container text-on-surface-variant'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isPassportActive ? 'bg-primary animate-pulse' : 'bg-on-surface-variant/40'
              }`}
            />
            {isPassportActive ? 'Active Clinical Link' : 'No Active Passport'}
          </div>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className={`bg-white rounded-xl shadow-sm shadow-teal-900/5 h-48 animate-pulse ${i === 1 || i === 4 ? 'md:col-span-2' : ''}`}
              />
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="rounded-xl bg-error-container px-5 py-4 text-sm text-error font-medium">
            Failed to load passport data. Please try again.
          </div>
        )}

        {/* Mutation errors */}
        {createMutation.isError && (
          <div className="rounded-xl bg-error-container px-5 py-4 text-sm text-error font-medium">
            Failed to generate passport. Please try again.
          </div>
        )}
        {revokeMutation.isError && (
          <div className="rounded-xl bg-error-container px-5 py-4 text-sm text-error font-medium">
            Failed to revoke passport. Please try again.
          </div>
        )}

        {/* Bento Grid */}
        {!isLoading && !isError && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Row 1: QR (col-1) + Medical Identity (col-2) */}
            <QRAccessModule
              passport={activePassport}
              onGenerate={() => setShowModal(true)}
            />
            <MedicalIdentityCard
              memberName={member?.full_name}
              dob={member?.date_of_birth}
              bloodGroup={member?.blood_group}
              passport={activePassport}
            />

            {/* Row 2: Active Passports (col-3 full width) */}
            <ActivePassportsTable
              passports={passports}
              onGenerate={() => setShowModal(true)}
              onRevoke={handleRevoke}
              isRevoking={revokeMutation.isPending}
            />

            {/* Row 3: Visibility Controls (col-2) + Revoke Panel (col-1) */}
            <VisibilityControls passport={activePassport} />
            <RevokeSharePanel
              passport={activePassport}
              onGenerate={() => setShowModal(true)}
              onRevoke={handleRevoke}
              isRevoking={revokeMutation.isPending}
            />
          </div>
        )}
      </div>
    </>
  )
}
