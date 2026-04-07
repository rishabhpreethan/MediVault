import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'

const RELATIONSHIPS = ['SELF', 'SPOUSE', 'PARENT', 'CHILD', 'SIBLING', 'OTHER'] as const
const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] as const

interface MemberPayload {
  name: string
  relationship: string
  date_of_birth?: string
  blood_group?: string
}

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
      {/* Teal info box */}
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

      {/* Illustration placeholder */}
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

// ── Form ──────────────────────────────────────────────────────────────────

export function AddFamilyMemberPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [name, setName] = useState('')
  const [relationship, setRelationship] = useState('')
  const [dob, setDob] = useState('')
  const [bloodGroup, setBloodGroup] = useState('')

  const mutation = useMutation({
    mutationFn: (payload: MemberPayload) => api.post('/family/members', payload),
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate({
      name,
      relationship,
      date_of_birth: dob || undefined,
      blood_group: bloodGroup || undefined,
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
    <div className="max-w-4xl mx-auto px-4 py-6">
      {/* Back link */}
      <button
        onClick={() => navigate('/passport')}
        className="flex items-center gap-1 text-sm text-on-surface-variant hover:text-primary mb-6 transition-colors"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back
      </button>

      <h1 className="text-2xl font-extrabold text-on-surface tracking-tight mb-6">Add Family Member</h1>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Left info panel — desktop only */}
        <div className="hidden md:flex flex-col gap-4 w-72 shrink-0">
          <div className="bg-primary/10 rounded-xl p-5">
            <p className="text-xs font-bold text-primary uppercase tracking-wider mb-2">Why This Matters</p>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              Connecting family members allows for automated hereditary risk mapping and emergency
              access synchronization. All health data is stored in one secure place.
            </p>
            <ul className="mt-4 space-y-2 text-sm text-on-surface-variant">
              {[
                "View each member's full medical history",
                'Track trends and check-up dates',
                'Share Health Passports during emergencies',
                'Get notified when records are processed',
              ].map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-primary mt-0.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl bg-surface-container h-40 flex items-center justify-center">
            <svg className="w-16 h-16 text-primary/20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
            </svg>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 space-y-6">
          {/* Member Identity */}
          <div className="bg-surface-container-lowest rounded-xl shadow-sm shadow-teal-900/5 p-6">
            <h2 className="text-base font-bold text-on-surface mb-4">Member Identity</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-1">
                  Full Legal Name <span className="text-error">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Jane Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full rounded-lg border border-outline-variant/30 bg-surface px-3 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-1">
                  Relationship
                </label>
                <select
                  value={relationship}
                  onChange={(e) => setRelationship(e.target.value)}
                  className="w-full rounded-lg border border-outline-variant/30 bg-surface px-3 py-2.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  <option value="">Select Relationship</option>
                  {RELATIONSHIPS.map((r) => (
                    <option key={r} value={r}>{r.charAt(0) + r.slice(1).toLowerCase()}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Clinical Profile */}
          <div className="bg-surface-container-lowest rounded-xl shadow-sm shadow-teal-900/5 p-6">
            <h2 className="text-base font-bold text-on-surface mb-4">Clinical Profile</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-1">
                  Date of Birth
                </label>
                <input
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  className="w-full rounded-lg border border-outline-variant/30 bg-surface px-3 py-2.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-2">
                  Blood Group
                </label>
                <div className="flex flex-wrap gap-2">
                  {BLOOD_GROUPS.map((bg) => (
                    <button
                      key={bg}
                      type="button"
                      onClick={() => setBloodGroup(bg === bloodGroup ? '' : bg)}
                      className={`px-4 py-2 rounded-full text-sm font-semibold transition-colors min-h-[44px] ${
                        bloodGroup === bg
                          ? 'bg-primary text-white shadow-sm'
                          : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                      }`}
                    >
                      {bg}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Error */}
          {mutation.isError && (
            <div className="rounded-lg bg-error-container px-4 py-3 text-sm text-error">
              Failed to register member. Please try again.
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate('/passport')}
              className="px-6 py-2.5 rounded-full text-sm font-semibold text-on-surface-variant hover:bg-surface-container transition-colors min-h-[44px]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim() || mutation.isPending}
              className="px-6 py-2.5 rounded-full text-sm font-semibold bg-primary text-white hover:bg-primary/90 transition-colors min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shadow-teal-900/10"
            >
              {mutation.isPending ? 'Registering…' : 'Register Member'}
            </button>
          </div>
        </form>
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
          {/* Form header */}
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
                {/* Full Legal Name */}
                <div>
                  <label
                    htmlFor="full-name"
                    className="block text-sm font-semibold text-on-surface mb-1.5"
                  >
                    Full Legal Name{' '}
                    <span className="text-error" aria-hidden="true">
                      *
                    </span>
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

                {/* Relationship */}
                <div>
                  <label
                    htmlFor="relationship"
                    className="block text-sm font-semibold text-on-surface mb-1.5"
                  >
                    Relationship{' '}
                    <span className="text-error" aria-hidden="true">
                      *
                    </span>
                  </label>
                  <select
                    id="relationship"
                    required
                    value={relationship}
                    onChange={(e) =>
                      setRelationship(e.target.value as Relationship)
                    }
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
                {/* Date of Birth */}
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

                {/* Blood Group */}
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
                        onClick={() =>
                          setBloodGroup((prev) => (prev === bg ? '' : bg))
                        }
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
                {mutation.error?.message ??
                  'Failed to register member. Please try again.'}
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
