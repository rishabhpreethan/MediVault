import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'
import type { FamilyMember } from '../../types'

// ── Types ─────────────────────────────────────────────────────────────────

type Relationship = FamilyMember['relationship']

interface AddMemberPayload {
  name: string
  relationship: Relationship
  date_of_birth: string
  blood_group: string
}

// ── Constants ─────────────────────────────────────────────────────────────

const RELATIONSHIPS: Array<{ value: Relationship; label: string }> = [
  { value: 'SELF', label: 'Self' },
  { value: 'SPOUSE', label: 'Spouse / Partner' },
  { value: 'PARENT', label: 'Parent' },
  { value: 'CHILD', label: 'Child' },
  { value: 'OTHER', label: 'Other' },
]

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

// ── Info panel ────────────────────────────────────────────────────────────

function InfoPanel() {
  return (
    <div className="hidden md:flex flex-col gap-6">
      <div className="bg-primary rounded-2xl p-6 text-white">
        <h2 className="text-lg font-bold mb-3">Why This Matters</h2>
        <p className="text-sm leading-relaxed text-white/90 mb-4">
          Connecting family members lets you manage everyone's health records in
          one secure place — from lab reports to prescriptions.
        </p>
        <ul className="space-y-3 text-sm">
          {[
            "View each member's full medical history",
            'Track trends and check-up dates',
            'Share Health Passports during emergencies',
            'Get notified when records are processed',
          ].map((item) => (
            <li key={item} className="flex items-start gap-2">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-4 h-4 flex-shrink-0 mt-0.5 text-primary-fixed"
                aria-hidden="true"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span className="text-white/90">{item}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex-1 bg-surface-container rounded-2xl flex items-center justify-center min-h-[200px]">
        <div className="flex flex-col items-center gap-3 text-on-surface-variant/60">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-16 h-16"
            aria-hidden="true"
          >
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <p className="text-xs font-medium">Family Health Ecosystem</p>
        </div>
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────

export function AddFamilyMemberPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [name, setName] = useState('')
  const [relationship, setRelationship] = useState<Relationship>('SELF')
  const [dateOfBirth, setDateOfBirth] = useState('')
  const [bloodGroup, setBloodGroup] = useState('')

  const mutation = useMutation<FamilyMember, Error, AddMemberPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post<FamilyMember>('/family/members', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['family-members'] })
      navigate('/passport')
    },
  })

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    mutation.mutate({
      name: name.trim(),
      relationship,
      date_of_birth: dateOfBirth,
      blood_group: bloodGroup,
    })
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Back link */}
      <Link
        to="/passport"
        className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:text-primary/80 transition-colors mb-6 min-h-[44px]"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-4 h-4"
          aria-hidden="true"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
        Back to Family Circle
      </Link>

      <div className="grid md:grid-cols-[1fr_1.6fr] gap-6 items-start">
        {/* Left info panel (desktop only) */}
        <InfoPanel />

        {/* Right form panel */}
        <div className="bg-white rounded-2xl shadow-[0_4px_24px_rgba(0,107,95,0.10)] overflow-hidden">
          <div className="px-6 py-5 border-b border-outline-variant/30">
            <h1 className="text-xl font-bold text-on-surface">
              Register Family Member
            </h1>
            <p className="text-sm text-on-surface-variant mt-1">
              Add a new member to your Family Circle
            </p>
          </div>

          <form onSubmit={handleSubmit} noValidate className="p-6 space-y-8">
            {/* Section: Member Identity */}
            <section aria-labelledby="identity-heading">
              <h2
                id="identity-heading"
                className="text-xs font-bold text-primary uppercase tracking-wider mb-4"
              >
                Member Identity
              </h2>

              <div className="space-y-4">
                <div>
                  <label
                    htmlFor="full-name"
                    className="block text-sm font-semibold text-on-surface mb-1.5"
                  >
                    Full Legal Name{' '}
                    <span className="text-error" aria-hidden="true">*</span>
                  </label>
                  <input
                    id="full-name"
                    type="text"
                    required
                    autoComplete="name"
                    placeholder="e.g. Priya Sharma"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-outline-variant bg-surface text-on-surface text-sm placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                  />
                </div>

                <div>
                  <label
                    htmlFor="relationship"
                    className="block text-sm font-semibold text-on-surface mb-1.5"
                  >
                    Relationship{' '}
                    <span className="text-error" aria-hidden="true">*</span>
                  </label>
                  <select
                    id="relationship"
                    required
                    value={relationship}
                    onChange={(e) => setRelationship(e.target.value as Relationship)}
                    className="w-full px-4 py-3 rounded-xl border border-outline-variant bg-surface text-on-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors appearance-none cursor-pointer"
                  >
                    {RELATIONSHIPS.map(({ value, label }) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </section>

            {/* Section: Clinical Profile */}
            <section aria-labelledby="clinical-heading">
              <h2
                id="clinical-heading"
                className="text-xs font-bold text-primary uppercase tracking-wider mb-4"
              >
                Clinical Profile
              </h2>

              <div className="space-y-5">
                <div>
                  <label
                    htmlFor="date-of-birth"
                    className="block text-sm font-semibold text-on-surface mb-1.5"
                  >
                    Date of Birth
                  </label>
                  <input
                    id="date-of-birth"
                    type="date"
                    value={dateOfBirth}
                    max={new Date().toISOString().split('T')[0]}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-outline-variant bg-surface text-on-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                  />
                </div>

                <div>
                  <p className="block text-sm font-semibold text-on-surface mb-2.5">
                    Blood Group
                  </p>
                  <div
                    className="flex flex-wrap gap-2"
                    role="group"
                    aria-label="Blood group selection"
                  >
                    {BLOOD_GROUPS.map((bg) => (
                      <button
                        key={bg}
                        type="button"
                        onClick={() => setBloodGroup((prev) => (prev === bg ? '' : bg))}
                        className={`px-4 py-2 rounded-full text-sm font-semibold transition-colors min-h-[44px] min-w-[52px] ${
                          bloodGroup === bg
                            ? 'bg-primary text-white'
                            : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                        }`}
                        aria-pressed={bloodGroup === bg}
                      >
                        {bg}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            {/* Inline error */}
            {mutation.isError && (
              <div
                role="alert"
                className="rounded-xl bg-error-container/50 border border-error/20 px-4 py-3 text-sm text-error font-medium"
              >
                {mutation.error?.message ?? 'Failed to register member. Please try again.'}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <Link
                to="/passport"
                className="flex-1 inline-flex items-center justify-center px-5 py-3 rounded-xl border-2 border-outline-variant text-on-surface text-sm font-semibold hover:bg-surface-container transition-colors min-h-[44px]"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={mutation.isPending || !name.trim()}
                className="flex-1 inline-flex items-center justify-center px-5 py-3 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors min-h-[44px]"
              >
                {mutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <svg
                      className="animate-spin w-4 h-4"
                      viewBox="0 0 24 24"
                      fill="none"
                      aria-hidden="true"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v8H4z"
                      />
                    </svg>
                    Registering…
                  </span>
                ) : (
                  'Register Member'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
