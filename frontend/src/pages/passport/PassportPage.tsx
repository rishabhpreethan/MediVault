import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../../lib/api'
import type { FamilyMember } from '../../types'

function initials(name: string) {
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('')
}

function AvatarCircle({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' | 'lg' }) {
  const sz = size === 'lg' ? 'w-16 h-16 text-xl' : size === 'md' ? 'w-12 h-12 text-base' : 'w-9 h-9 text-sm'
  return (
    <div className={`${sz} rounded-full bg-primary-fixed text-primary font-extrabold flex items-center justify-center shrink-0`}>
      {initials(name)}
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="bg-surface-container-lowest rounded-xl shadow-sm shadow-teal-900/5 p-5 animate-pulse space-y-3">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-full bg-surface-container" />
        <div className="space-y-2 flex-1">
          <div className="h-4 w-32 bg-surface-container rounded" />
          <div className="h-3 w-20 bg-surface-container rounded" />
        </div>
      </div>
      <div className="h-8 bg-surface-container rounded-full" />
    </div>
  )
}

export function PassportPage() {
  const { data: members, isLoading, isError } = useQuery<FamilyMember[]>({
    queryKey: ['family-members'],
    queryFn: async () => {
      const { data } = await api.get('/family/members')
      return data
    },
  })

  const selfMember = members?.find((m) => m.relationship?.toUpperCase() === 'SELF') ?? members?.[0]
  const otherMembers = members?.filter((m) => m.member_id !== selfMember?.member_id) ?? []

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">Family Circle</h1>
          <p className="text-sm text-on-surface-variant mt-1">
            Manage and view health records for all connected family members.
          </p>
        </div>
        <Link
          to="/passport/add-member"
          className="shrink-0 flex items-center gap-2 bg-primary text-white text-sm font-semibold rounded-full px-4 py-2.5 min-h-[44px] hover:bg-primary/90 transition-colors shadow-sm shadow-teal-900/10"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 5v14M5 12h14" />
          </svg>
          Add Member
        </Link>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="rounded-xl bg-error-container px-5 py-4 text-sm text-error font-medium">
          Failed to load family members. Please try again.
        </div>
      )}

      {/* Empty */}
      {!isLoading && !isError && (!members || members.length === 0) && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-2xl bg-surface-container flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-primary/40" viewBox="0 0 24 24" fill="currentColor">
              <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
            </svg>
          </div>
          <p className="text-base font-bold text-on-surface">No family members yet</p>
          <p className="text-sm text-on-surface-variant mt-1 mb-6">
            Add yourself and your family to start managing everyone's health records in one place.
          </p>
          <Link
            to="/passport/add-member"
            className="bg-primary text-white text-sm font-semibold rounded-full px-6 py-2.5 min-h-[44px] hover:bg-primary/90 transition-colors"
          >
            Add First Member
          </Link>
        </div>
      )}

      {/* Primary member — featured card */}
      {selfMember && (
        <div className="bg-surface-container-lowest rounded-2xl shadow-sm shadow-teal-900/5 p-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <AvatarCircle name={selfMember.full_name} size="lg" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-xl font-extrabold text-on-surface truncate">{selfMember.full_name}</h2>
                <span className="text-xs font-bold bg-primary text-white rounded-full px-2 py-0.5">VERIFIED</span>
              </div>
              <p className="text-sm text-on-surface-variant mt-0.5">
                {selfMember.relationship ?? 'Primary Account'} · Blood Group: {selfMember.blood_group ?? '—'}
              </p>
            </div>
            <Link
              to={`/records?member=${selfMember.member_id}`}
              className="shrink-0 text-sm font-semibold text-primary border border-primary/30 rounded-full px-4 py-2 min-h-[44px] flex items-center hover:bg-primary/5 transition-colors"
            >
              View Full Record
            </Link>
          </div>
        </div>
      )}

      {/* Family member grid */}
      {members && members.length > 0 && (
        <div>
          <h3 className="text-base font-bold text-on-surface mb-4">Family Members</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {otherMembers.map((member) => (
              <div key={member.member_id} className="bg-surface-container-lowest rounded-xl shadow-sm shadow-teal-900/5 p-5 flex flex-col gap-4">
                <div className="flex items-center gap-3">
                  <AvatarCircle name={member.full_name} size="md" />
                  <div className="min-w-0">
                    <p className="font-bold text-on-surface truncate">{member.full_name}</p>
                    <p className="text-xs text-on-surface-variant">{member.relationship ?? '—'}</p>
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {member.blood_group && (
                    <span className="text-xs font-semibold bg-primary-fixed text-primary rounded-full px-2.5 py-0.5">
                      {member.blood_group}
                    </span>
                  )}
                  {member.date_of_birth && (
                    <span className="text-xs font-medium text-on-surface-variant bg-surface-container rounded-full px-2.5 py-0.5">
                      DOB: {member.date_of_birth}
                    </span>
                  )}
                </div>
                <Link
                  to={`/records?member=${member.member_id}`}
                  className="text-center text-sm font-semibold text-primary border border-primary/30 rounded-full py-2 min-h-[44px] flex items-center justify-center hover:bg-primary/5 transition-colors"
                >
                  Open Vault
                </Link>
              </div>
            ))}

            {/* Add member card */}
            <Link
              to="/passport/add-member"
              className="border-2 border-dashed border-primary/30 rounded-xl p-5 flex flex-col items-center justify-center gap-3 min-h-[160px] hover:border-primary/60 hover:bg-primary/5 transition-colors group"
            >
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                <svg className="w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 5v14M5 12h14" />
                </svg>
              </div>
              <div className="text-center">
                <p className="text-sm font-bold text-primary">Add Family Member</p>
                <p className="text-xs text-on-surface-variant mt-0.5">Connect another profile</p>
              </div>
            </Link>
          </div>
        </div>
      )}

      {/* Recent Activity — static placeholder */}
      {members && members.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-on-surface">Recent Activity</h3>
            <button className="text-sm font-semibold text-primary min-h-[44px] px-2 hover:underline">
              View All Logs
            </button>
          </div>
          <div className="bg-surface-container-lowest rounded-xl shadow-sm shadow-teal-900/5 divide-y divide-outline-variant/10">
            {[
              { icon: '🧪', text: 'Lab results uploaded', sub: 'Processed successfully', time: '2h ago' },
              { icon: '📋', text: 'Prescription scanned', sub: 'Extraction complete', time: '1d ago' },
              { icon: '🔔', text: 'Insurance verification required', sub: 'Action needed', time: '3d ago' },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3 px-5 py-3">
                <span className="text-xl">{item.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-on-surface">{item.text}</p>
                  <p className="text-xs text-on-surface-variant">{item.sub}</p>
                </div>
                <span className="text-xs text-on-surface-variant shrink-0">{item.time}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
