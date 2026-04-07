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

export function AddFamilyMemberPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [name, setName] = useState('')
  const [relationship, setRelationship] = useState('')
  const [dob, setDob] = useState('')
  const [bloodGroup, setBloodGroup] = useState('')

  const mutation = useMutation({
    mutationFn: (payload: MemberPayload) => api.post('/family/members', payload),
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
      </div>
    </div>
  )
}
