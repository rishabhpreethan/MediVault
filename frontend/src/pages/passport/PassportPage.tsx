import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../../lib/api'
import type { FamilyMember } from '../../types'

function initials(name: string) {
// ── Helpers ────────────────────────────────────────────────────────────────

function getInitials(name: string): string {
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
function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function relationshipLabel(r: FamilyMember['relationship']): string {
  const map: Record<FamilyMember['relationship'], string> = {
    SELF: 'Self',
    SPOUSE: 'Spouse / Partner',
    PARENT: 'Parent',
    CHILD: 'Child',
    OTHER: 'Other',
  }
  return map[r] ?? r
}

// ── Avatar ─────────────────────────────────────────────────────────────────

interface AvatarProps {
  name: string
  size?: 'sm' | 'md' | 'lg'
}

function Avatar({ name, size = 'md' }: AvatarProps) {
  const sizeClasses = {
    sm: 'w-10 h-10 text-sm',
    md: 'w-14 h-14 text-base',
    lg: 'w-20 h-20 text-2xl',
  }
  return (
    <div
      className={`${sizeClasses[size]} rounded-full bg-primary flex items-center justify-center text-white font-bold select-none flex-shrink-0`}
      aria-hidden="true"
    >
      {getInitials(name)}
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
// ── Loading skeleton ───────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-[0_4px_24px_rgba(0,107,95,0.08)] animate-pulse">
      <div className="flex items-center gap-4 mb-4">
        <div className="w-14 h-14 rounded-full bg-surface-container" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-surface-container rounded w-3/4" />
          <div className="h-3 bg-surface-container rounded w-1/2" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-3 bg-surface-container rounded w-full" />
        <div className="h-3 bg-surface-container rounded w-4/5" />
      </div>
    </div>
  )
}

// ── Primary (self) member card ─────────────────────────────────────────────

interface PrimaryCardProps {
  member: FamilyMember
}

function PrimaryCard({ member }: PrimaryCardProps) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-[0_4px_24px_rgba(0,107,95,0.12)] border border-primary/10">
      <div className="flex items-start gap-5">
        <Avatar name={member.full_name} size="lg" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-xl font-bold text-on-surface truncate">
              {member.full_name}
            </h2>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-primary/10 text-primary tracking-wide">
              VERIFIED
            </span>
          </div>
          <p className="text-sm text-on-surface-variant mt-0.5">
            {relationshipLabel(member.relationship)}
          </p>

          {/* Stats row */}
          <div className="flex flex-wrap gap-6 mt-4">
            <div>
              <p className="text-xs text-on-surface-variant font-medium uppercase tracking-wide">
                Blood Group
              </p>
              <p className="text-base font-bold text-on-surface mt-0.5">
                {member.blood_group ?? '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-on-surface-variant font-medium uppercase tracking-wide">
                Date of Birth
              </p>
              <p className="text-base font-bold text-on-surface mt-0.5">
                {formatDate(member.date_of_birth)}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-5 pt-4 border-t border-outline-variant/40 flex gap-3">
        <Link
          to={`/records?member=${member.member_id}`}
          className="inline-flex items-center justify-center px-5 py-2.5 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors min-h-[44px]"
        >
          View Full Record
        </Link>
      </div>
    </div>
  )
}

// ── Family member card ─────────────────────────────────────────────────────

interface MemberCardProps {
  member: FamilyMember
}

function MemberCard({ member }: MemberCardProps) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-[0_4px_24px_rgba(0,107,95,0.08)] border border-outline-variant/30 flex flex-col gap-4 hover:shadow-[0_6px_28px_rgba(0,107,95,0.14)] transition-shadow">
      <div className="flex items-center gap-3">
        <Avatar name={member.full_name} size="sm" />
        <div className="min-w-0">
          <p className="font-bold text-on-surface text-sm truncate">
            {member.full_name}
          </p>
          <p className="text-xs text-on-surface-variant mt-0.5">
            {relationshipLabel(member.relationship)}
          </p>
        </div>
      </div>

      {/* Key metric pill */}
      <div className="flex flex-wrap gap-2">
        {member.blood_group && (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary">
            BLOOD: {member.blood_group}
          </span>
        )}
        {member.date_of_birth && (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-surface-container text-on-surface-variant">
            DOB: {formatDate(member.date_of_birth)}
          </span>
        )}
      </div>

      <Link
        to={`/records?member=${member.member_id}`}
        className="inline-flex items-center justify-center w-full px-4 py-2.5 rounded-xl border-2 border-primary text-primary text-sm font-semibold hover:bg-primary hover:text-white transition-colors min-h-[44px]"
      >
        Open Vault
      </Link>
    </div>
  )
}

// ── Add member card ────────────────────────────────────────────────────────

function AddMemberCard() {
  return (
    <Link
      to="/passport/add-member"
      className="bg-white rounded-2xl p-5 border-2 border-dashed border-primary/40 flex flex-col items-center justify-center gap-3 hover:border-primary hover:shadow-[0_4px_20px_rgba(0,107,95,0.12)] transition-all min-h-[160px] group"
      aria-label="Add family member"
    >
      <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-6 h-6 text-primary"
          aria-hidden="true"
        >
          <path d="M12 5v14M5 12h14" />
        </svg>
      </div>
      <div className="text-center">
        <p className="text-sm font-bold text-primary">Add Family Member</p>
        <p className="text-xs text-on-surface-variant mt-0.5">
          Connect a new profile
        </p>
      </div>
    </Link>
  )
}

// ── Recent Activity section (static placeholder) ──────────────────────────

interface ActivityItem {
  id: string
  title: string
  description: string
  time: string
  type: 'lab' | 'prescription' | 'visit' | 'member'
}

const PLACEHOLDER_ACTIVITY: ActivityItem[] = [
  {
    id: '1',
    title: 'New lab report processed',
    description: 'CBC — Complete Blood Count extracted',
    time: 'Today, 10:32 AM',
    type: 'lab',
  },
  {
    id: '2',
    title: 'Prescription uploaded',
    description: 'Metformin 500 mg — 3 months',
    time: 'Yesterday, 3:15 PM',
    type: 'prescription',
  },
  {
    id: '3',
    title: 'Profile updated',
    description: 'Blood group and DOB added',
    time: '2 days ago',
    type: 'member',
  },
]

function activityIcon(type: ActivityItem['type']) {
  switch (type) {
    case 'lab':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
          <path d="M9 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8l-5-5z" />
          <polyline points="9 3 9 8 19 8" />
        </svg>
      )
    case 'prescription':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
          <circle cx="12" cy="12" r="10" />
          <path d="M8 12h8M12 8v8" />
        </svg>
      )
    case 'visit':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
      )
    default:
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      )
  }
}

function RecentActivity() {
  return (
    <section aria-labelledby="activity-heading" className="mt-8">
      <h2
        id="activity-heading"
        className="text-base font-bold text-on-surface mb-4"
      >
        Recent Activity
      </h2>
      <div className="bg-white rounded-2xl shadow-[0_4px_24px_rgba(0,107,95,0.08)] divide-y divide-outline-variant/30 overflow-hidden">
        {PLACEHOLDER_ACTIVITY.map((item) => (
          <div key={item.id} className="flex items-start gap-4 p-4">
            <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center text-primary flex-shrink-0 mt-0.5">
              {activityIcon(item.type)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-on-surface">{item.title}</p>
              <p className="text-xs text-on-surface-variant mt-0.5 truncate">
                {item.description}
              </p>
            </div>
            <p className="text-xs text-on-surface-variant whitespace-nowrap ml-2 mt-0.5">
              {item.time}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}

// ── Empty state ────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-5">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-10 h-10 text-primary"
          aria-hidden="true"
        >
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 1 0-3.87M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      </div>
      <h3 className="text-lg font-bold text-on-surface mb-2">
        No family members yet
      </h3>
      <p className="text-sm text-on-surface-variant max-w-xs mb-6">
        Add your first family member to start managing health records for your
        entire family in one place.
      </p>
      <Link
        to="/passport/add-member"
        className="inline-flex items-center justify-center px-6 py-3 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors min-h-[44px]"
      >
        Add Family Member
      </Link>
    </div>
  )
}

// ── PassportPage ───────────────────────────────────────────────────────────

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
  const selfMember = members?.find((m) => m.is_self) ?? members?.[0]
  const otherMembers = members?.filter((m) => m !== selfMember) ?? []

  return (
    <div className="space-y-0">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-on-surface">Family Circle</h1>
        <p className="text-sm text-on-surface-variant mt-1">
          Manage and view health records for all connected family members
        </p>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <SkeletonCard key={i} />)}
        <div className="space-y-4">
          <SkeletonCard />
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
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
        <div className="rounded-2xl bg-error-container/40 border border-error/20 p-5 text-sm text-error font-medium">
          Failed to load family members. Please try refreshing.
        </div>
      )}

      {/* Data */}
      {!isLoading && !isError && (
        <>
          {!members || members.length === 0 ? (
            <EmptyState />
          ) : (
            <>
              {/* Primary member card */}
              {selfMember && (
                <section aria-label="Primary member" className="mb-6">
                  <PrimaryCard member={selfMember} />
                </section>
              )}

              {/* Family member grid */}
              <section aria-label="Family members">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-bold text-on-surface">
                    Family Members
                  </h2>
                  <Link
                    to="/passport/add-member"
                    className="text-sm font-semibold text-primary hover:text-primary/80 transition-colors min-h-[44px] flex items-center"
                  >
                    + Add Member
                  </Link>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {otherMembers.map((member) => (
                    <MemberCard key={member.member_id} member={member} />
                  ))}
                  <AddMemberCard />
                </div>
              </section>

              {/* Recent Activity */}
              <RecentActivity />
            </>
          )}
        </>
      )}
    </div>
  )
}
