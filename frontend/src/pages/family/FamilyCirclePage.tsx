import { useState } from 'react'
import type { FormEvent } from 'react'
import type {
  FamilyMember,
  FamilyMembership,
  FamilyInvitation,
  FamilyCircle,
} from '../../types'
import {
  useFamilyCircle,
  useSendInvitation,
  useCancelInvitation,
  useResendInvitation,
} from '../../hooks/useFamilyCircle'
import { VaultAccessPanel } from './VaultAccessPanel'

// ── Helpers ────────────────────────────────────────────────────────────────

function getInitials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')
}

type Relationship = 'PARENT' | 'SPOUSE' | 'CHILD' | 'SIBLING' | 'OTHER'

const RELATIONSHIP_LABELS: Record<string, string> = {
  SELF: 'You',
  PARENT: 'Parent',
  SPOUSE: 'Spouse',
  CHILD: 'Child',
  SIBLING: 'Sibling',
  OTHER: 'Other',
}

// ── Member node card ───────────────────────────────────────────────────────

interface MemberCardProps {
  name: string
  relationship: string
  isSelf?: boolean
  isManaged?: boolean
  onManageAccess?: () => void
}

function MemberCard({ name, relationship, isSelf, isManaged, onManageAccess }: MemberCardProps) {
  const initials = getInitials(name)
  const relLabel = RELATIONSHIP_LABELS[relationship] ?? relationship

  return (
    <div
      className={`flex flex-col items-center gap-1.5 w-24 ${isSelf ? 'scale-110' : ''}`}
    >
      <div
        className={`w-14 h-14 rounded-full flex items-center justify-center text-base font-bold select-none ${
          isSelf
            ? 'bg-teal-600 text-white ring-4 ring-teal-200'
            : 'bg-slate-100 text-slate-600'
        }`}
      >
        {initials}
      </div>
      <p className="text-xs font-semibold text-slate-800 text-center leading-tight truncate w-full text-center">
        {name}
      </p>
      <span
        className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${
          isSelf
            ? 'bg-teal-100 text-teal-700'
            : isManaged
            ? 'bg-slate-100 text-slate-500'
            : 'bg-blue-50 text-blue-600'
        }`}
      >
        {isManaged ? 'Managed' : relLabel}
      </span>
      {onManageAccess && (
        <button
          type="button"
          onClick={onManageAccess}
          className="text-[10px] text-teal-600 hover:text-teal-800 font-medium transition-colors min-h-[44px] px-2 flex items-center"
        >
          Manage
        </button>
      )}
    </div>
  )
}

// ── Pending invitation card ────────────────────────────────────────────────

interface PendingCardProps {
  invitation: FamilyInvitation
}

function PendingCard({ invitation }: PendingCardProps) {
  const cancel = useCancelInvitation()
  const resend = useResendInvitation()
  const relLabel = RELATIONSHIP_LABELS[invitation.relationship] ?? invitation.relationship

  const truncatedEmail =
    invitation.invited_email.length > 20
      ? `${invitation.invited_email.slice(0, 18)}…`
      : invitation.invited_email

  return (
    <div className="flex flex-col items-center gap-1.5 w-28">
      <div className="w-14 h-14 rounded-full border-2 border-dashed border-slate-300 flex items-center justify-center bg-slate-50">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-slate-400" aria-hidden="true">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      </div>
      <p className="text-xs font-medium text-slate-500 text-center truncate w-full" title={invitation.invited_email}>
        {truncatedEmail}
      </p>
      <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-600">
        {relLabel} · Pending
      </span>
      <div className="flex gap-1 mt-0.5">
        <button
          type="button"
          onClick={() => resend.mutate(invitation.invitation_id)}
          disabled={resend.isPending}
          className="text-[10px] text-teal-600 hover:text-teal-800 font-medium transition-colors min-h-[44px] px-1 flex items-center disabled:opacity-50"
        >
          Resend
        </button>
        <button
          type="button"
          onClick={() => cancel.mutate(invitation.invitation_id)}
          disabled={cancel.isPending}
          className="text-[10px] text-red-500 hover:text-red-700 font-medium transition-colors min-h-[44px] px-1 flex items-center disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}

// ── Add member dashed button ───────────────────────────────────────────────

function AddMemberButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col items-center gap-1.5 w-24 min-h-[44px] group"
      aria-label="Invite a family member"
    >
      <div className="w-14 h-14 rounded-full border-2 border-dashed border-teal-300 flex items-center justify-center bg-teal-50 group-hover:bg-teal-100 transition-colors">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-teal-500" aria-hidden="true">
          <path d="M12 5v14M5 12h14" />
        </svg>
      </div>
      <span className="text-xs text-teal-600 font-medium group-hover:text-teal-800 transition-colors">
        Add member
      </span>
    </button>
  )
}

// ── Connector line between rows ────────────────────────────────────────────

function Connector() {
  return (
    <div className="flex justify-center">
      <div className="w-px h-8 bg-slate-200" aria-hidden="true" />
    </div>
  )
}

// ── Family tree visual ─────────────────────────────────────────────────────

interface FamilyTreeProps {
  circle: FamilyCircle
  selfMember: FamilyMember | undefined
  onInvite: () => void
  onManageAccess: (member: FamilyMember | FamilyMembership) => void
}

function FamilyTree({ circle, selfMember, onInvite, onManageAccess }: FamilyTreeProps) {
  const managed = circle.managed_profiles

  const parents = managed.filter((m) => m.relationship?.toUpperCase() === 'PARENT')
  const spouses = managed.filter((m) => m.relationship?.toUpperCase() === 'SPOUSE')
  const children = managed.filter((m) => m.relationship?.toUpperCase() === 'CHILD')
  const others = managed.filter(
    (m) =>
      !['SELF', 'PARENT', 'SPOUSE', 'CHILD'].includes(m.relationship?.toUpperCase() ?? ''),
  )

  const pendingInvitations = circle.pending_invitations_sent
  const linkedMembers = circle.memberships

  return (
    <div className="space-y-0">
      {/* Parents row */}
      {parents.length > 0 && (
        <>
          <div className="flex flex-wrap justify-center gap-6 py-4">
            {parents.map((p) => (
              <MemberCard
                key={p.member_id}
                name={p.full_name}
                relationship={p.relationship}
                onManageAccess={() => onManageAccess(p)}
              />
            ))}
          </div>
          <Connector />
        </>
      )}

      {/* Owner + Spouse row */}
      <div className="flex flex-wrap justify-center items-center gap-6 py-4">
        {spouses.filter((_, i) => i === 0).map((s) => (
          <MemberCard
            key={s.member_id}
            name={s.full_name}
            relationship={s.relationship}
            onManageAccess={() => onManageAccess(s)}
          />
        ))}

        {/* SELF node */}
        {selfMember ? (
          <MemberCard
            name={selfMember.full_name}
            relationship="SELF"
            isSelf
          />
        ) : (
          <div className="w-14 h-14 rounded-full bg-teal-600 ring-4 ring-teal-200 flex items-center justify-center text-white font-bold">
            Me
          </div>
        )}

        {spouses.filter((_, i) => i > 0).map((s) => (
          <MemberCard
            key={s.member_id}
            name={s.full_name}
            relationship={s.relationship}
            onManageAccess={() => onManageAccess(s)}
          />
        ))}

        {/* Add member button next to owner */}
        <AddMemberButton onClick={onInvite} />
      </div>

      {/* Children row */}
      {children.length > 0 && (
        <>
          <Connector />
          <div className="flex flex-wrap justify-center gap-6 py-4">
            {children.map((c) => (
              <MemberCard
                key={c.member_id}
                name={c.full_name}
                relationship={c.relationship}
                onManageAccess={() => onManageAccess(c)}
              />
            ))}
          </div>
        </>
      )}

      {/* Other managed profiles */}
      {others.length > 0 && (
        <div className="mt-6 pt-6 border-t border-slate-100">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 text-center">
            Other members
          </h3>
          <div className="flex flex-wrap justify-center gap-6">
            {others.map((m) => (
              <MemberCard
                key={m.member_id}
                name={m.full_name}
                relationship={m.relationship}
                isManaged
                onManageAccess={() => onManageAccess(m)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Linked (invited) members */}
      {linkedMembers.length > 0 && (
        <div className="mt-6 pt-6 border-t border-slate-100">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 text-center">
            Linked accounts
          </h3>
          <div className="flex flex-wrap justify-center gap-6">
            {linkedMembers.map((ms) => (
              <div key={ms.membership_id} className="flex flex-col items-center gap-1.5 w-24">
                <div className="w-14 h-14 rounded-full bg-indigo-50 flex items-center justify-center text-base font-bold text-indigo-600">
                  {ms.user_id.slice(0, 2).toUpperCase()}
                </div>
                <p className="text-xs font-semibold text-slate-800 text-center truncate w-full">
                  {ms.user_id.slice(0, 10)}…
                </p>
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-indigo-50 text-indigo-600">
                  {ms.role}
                </span>
                <button
                  type="button"
                  onClick={() => onManageAccess(ms)}
                  className="text-[10px] text-teal-600 hover:text-teal-800 font-medium transition-colors min-h-[44px] px-2 flex items-center"
                >
                  Manage
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pending invitations */}
      {pendingInvitations.length > 0 && (
        <div className="mt-6 pt-6 border-t border-slate-100">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 text-center">
            Pending invitations
          </h3>
          <div className="flex flex-wrap justify-center gap-6">
            {pendingInvitations.map((inv) => (
              <PendingCard key={inv.invitation_id} invitation={inv} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Invite modal ───────────────────────────────────────────────────────────

const RELATIONSHIPS: Relationship[] = ['PARENT', 'SPOUSE', 'CHILD', 'SIBLING', 'OTHER']

interface InviteModalProps {
  onClose: () => void
}

function InviteModal({ onClose }: InviteModalProps) {
  const [email, setEmail] = useState('')
  const [relationship, setRelationship] = useState<Relationship>('CHILD')
  const [sent, setSent] = useState(false)
  const sendInvitation = useSendInvitation()

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!email.trim()) return
    try {
      await sendInvitation.mutateAsync({ email: email.trim(), relationship })
      setSent(true)
    } catch {
      // error shown below
    }
  }

  const apiError = sendInvitation.error as (Error & { response?: { status?: number } }) | null
  const isConflict = apiError?.response?.status === 409
  const isSelfInvite = apiError?.response?.status === 400

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative w-full sm:max-w-md bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <h2 className="text-base font-semibold text-slate-900">Invite a family member</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Close"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5" aria-hidden="true">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-5 py-5">
          {sent ? (
            <div className="text-center py-6 space-y-3">
              <div className="w-12 h-12 rounded-full bg-teal-100 flex items-center justify-center mx-auto">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-teal-600" aria-hidden="true">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
              </div>
              <p className="text-sm font-semibold text-slate-900">Invitation sent!</p>
              <p className="text-xs text-slate-500">
                We sent an invite to <strong>{email}</strong>. They'll receive it shortly.
              </p>
              <button
                type="button"
                onClick={onClose}
                className="mt-2 w-full py-2.5 bg-teal-600 text-white rounded-xl font-medium text-sm hover:bg-teal-700 transition-colors min-h-[44px]"
              >
                Done
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
              <div>
                <label htmlFor="invite-email" className="block text-xs font-semibold text-slate-600 mb-1.5">
                  Email address
                </label>
                <input
                  id="invite-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="family@example.com"
                  required
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 min-h-[44px]"
                />
              </div>

              {/* Relationship */}
              <div>
                <p className="block text-xs font-semibold text-slate-600 mb-2">Relationship</p>
                <div className="flex flex-wrap gap-2">
                  {RELATIONSHIPS.map((rel) => (
                    <button
                      key={rel}
                      type="button"
                      onClick={() => setRelationship(rel)}
                      className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors min-h-[44px] ${
                        relationship === rel
                          ? 'bg-teal-600 text-white border-teal-600'
                          : 'border-slate-200 text-slate-600 hover:border-teal-400 hover:text-teal-600'
                      }`}
                    >
                      {RELATIONSHIP_LABELS[rel]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Errors */}
              {isConflict && (
                <p className="text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded-lg">
                  This person has already been invited or is already a member.
                </p>
              )}
              {isSelfInvite && (
                <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                  You can't invite yourself.
                </p>
              )}
              {apiError && !isConflict && !isSelfInvite && (
                <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                  Something went wrong. Please try again.
                </p>
              )}

              <button
                type="submit"
                disabled={sendInvitation.isPending || !email.trim()}
                className="w-full py-2.5 bg-teal-600 text-white rounded-xl font-semibold text-sm hover:bg-teal-700 transition-colors min-h-[44px] disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {sendInvitation.isPending ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Sending…
                  </>
                ) : (
                  'Send Invitation'
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Page skeleton ──────────────────────────────────────────────────────────

function PageSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-8 bg-slate-200 rounded w-48" />
        <div className="h-10 bg-slate-200 rounded-xl w-36" />
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 p-8 flex justify-center gap-8">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex flex-col items-center gap-2">
            <div className="w-14 h-14 rounded-full bg-slate-200" />
            <div className="h-3 bg-slate-200 rounded w-16" />
            <div className="h-2.5 bg-slate-200 rounded w-12" />
          </div>
        ))}
      </div>
    </div>
  )
}

// ── FamilyCirclePage ───────────────────────────────────────────────────────

export function FamilyCirclePage() {
  const [inviteOpen, setInviteOpen] = useState(false)
  const [accessTarget, setAccessTarget] = useState<FamilyMember | FamilyMembership | null>(null)
  const { data: circle, isLoading, isError } = useFamilyCircle()

  if (isLoading) return <PageSkeleton />

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <p className="text-sm text-slate-500">Failed to load your family circle.</p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-teal-600 text-white rounded-xl text-sm font-medium min-h-[44px] hover:bg-teal-700 transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  const selfMember = circle?.managed_profiles.find((m) => m.is_self)
  const hasAnyMember =
    (circle?.managed_profiles.length ?? 0) > 1 ||
    (circle?.memberships.length ?? 0) > 0 ||
    (circle?.pending_invitations_sent.length ?? 0) > 0

  return (
    <>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Family Circle</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Manage your family's health records and access.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setInviteOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-teal-600 text-white rounded-xl font-semibold text-sm hover:bg-teal-700 transition-colors min-h-[44px]"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Invite Member
          </button>
        </div>

        {/* Family tree card */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 md:p-8">
          {!hasAnyMember ? (
            /* Empty state */
            <div className="flex flex-col items-center justify-center py-12 gap-4 text-center">
              <div className="w-16 h-16 rounded-full bg-teal-50 flex items-center justify-center">
                <svg viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-teal-300" aria-hidden="true">
                  <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-700">Your family tree is empty.</p>
                <p className="text-xs text-slate-400 mt-1">
                  Invite a family member to get started.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setInviteOpen(true)}
                className="px-4 py-2.5 border-2 border-dashed border-teal-300 text-teal-600 rounded-xl text-sm font-medium hover:bg-teal-50 transition-colors min-h-[44px]"
              >
                Invite your first member
              </button>
            </div>
          ) : (
            circle && (
              <FamilyTree
                circle={circle}
                selfMember={selfMember}
                onInvite={() => setInviteOpen(true)}
                onManageAccess={(m) => setAccessTarget(m)}
              />
            )
          )}
        </div>

        {/* Received invitations */}
        {(circle?.pending_invitations_received.length ?? 0) > 0 && (
          <div className="bg-amber-50 rounded-2xl border border-amber-100 px-5 py-4">
            <h2 className="text-sm font-semibold text-amber-800 mb-3">
              Pending invitations for you
            </h2>
            <ul className="space-y-2">
              {circle!.pending_invitations_received.map((inv) => (
                <li key={inv.invitation_id} className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm text-slate-800">
                      Invited as <strong>{RELATIONSHIP_LABELS[inv.relationship] ?? inv.relationship}</strong> by{' '}
                      <span className="text-slate-500">{inv.invited_email}</span>
                    </p>
                    <p className="text-xs text-slate-400">
                      Expires {new Date(inv.expires_at).toLocaleDateString()}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Invite modal */}
      {inviteOpen && <InviteModal onClose={() => setInviteOpen(false)} />}

      {/* Vault access panel */}
      {accessTarget && (
        <VaultAccessPanel
          targetMember={accessTarget}
          onClose={() => setAccessTarget(null)}
        />
      )}
    </>
  )
}
