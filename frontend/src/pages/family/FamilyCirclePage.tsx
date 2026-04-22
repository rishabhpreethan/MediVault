import { useState, useMemo } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import type {
  FamilyMember,
  FamilyMembership,
  FamilyInvitation,
  FamilyCircle,
} from '../../types'
import {
  useFamilyCircle,
  useFamilyCircleEvents,
  useSendInvitation,
  useCancelInvitation,
  useResendInvitation,
  useCreateManagedMember,
  useDeleteManagedMember,
  useDeleteMembership,
  useRequestVaultAccess,
  useVaultAccessGrants,
} from '../../hooks/useFamilyCircle'
import { useSetActiveMember } from '../../hooks/useFamily'
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

// ── Family tree (SVG layout + foreignObject HTML nodes) ────────────────────

const CW = 140   // card width
const CH = 116   // card height
const HG = 20    // horizontal gap between cards
const VG = 80    // vertical gap between levels
const PX = 48    // horizontal padding inside SVG
const PY = 32    // vertical padding inside SVG

function curve(x1: number, y1: number, x2: number, y2: number) {
  const my = (y1 + y2) / 2
  return `M ${x1} ${y1} C ${x1} ${my} ${x2} ${my} ${x2} ${y2}`
}

// ── Delete confirmation modal ──────────────────────────────────────────────

interface DeleteModalState {
  open: boolean
  type: 'managed' | 'linked' | 'pending'
  name: string
  onConfirm: () => void
}

function DeleteConfirmModal({ state, onClose }: { state: DeleteModalState; onClose: () => void }) {
  if (!state.open) return null

  const title =
    state.type === 'managed'
      ? `Delete ${state.name}'s profile?`
      : state.type === 'pending'
      ? `Cancel invitation to ${state.name}?`
      : `Remove ${state.name} from circle?`

  const body =
    state.type === 'managed'
      ? 'This will permanently delete their profile and all health records. This cannot be undone.'
      : state.type === 'pending'
      ? 'The invitation will be cancelled and they will not be able to join.'
      : 'They will be removed from your family circle. They keep their MediVault account.'

  const confirmLabel =
    state.type === 'managed'
      ? 'Delete profile + records'
      : state.type === 'pending'
      ? 'Cancel invitation'
      : 'Remove from circle'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
      <div className="relative w-full max-w-sm mx-4 bg-white rounded-2xl shadow-2xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        <p className="text-sm text-slate-500">{body}</p>
        <div className="flex gap-3 pt-1">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2.5 border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50 transition-colors min-h-[44px]"
          >
            Keep
          </button>
          <button
            type="button"
            onClick={() => { state.onConfirm(); onClose() }}
            className="flex-1 py-2.5 bg-red-500 text-white rounded-xl text-sm font-semibold hover:bg-red-600 transition-colors min-h-[44px]"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Member options sheet ───────────────────────────────────────────────────

type MemberOptionAction = {
  label: string
  variant: 'normal' | 'danger'
  onClick: () => void
}

interface MemberOptionsState {
  open: boolean
  name: string
  actions: MemberOptionAction[]
}

function MemberOptionsSheet({ state, onClose }: { state: MemberOptionsState; onClose: () => void }) {
  if (!state.open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
      <div className="relative w-full sm:max-w-sm sm:mx-4 bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden">
        <div className="px-5 pt-4 pb-3 border-b border-slate-100">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Options</p>
          <p className="text-sm font-semibold text-slate-900 mt-0.5">{state.name}</p>
        </div>
        <div className="divide-y divide-slate-100">
          {state.actions.map((action, i) => (
            <button
              key={i}
              type="button"
              onClick={() => { action.onClick(); onClose() }}
              className={`w-full px-5 py-4 text-sm font-medium text-left transition-colors min-h-[48px] ${
                action.variant === 'danger'
                  ? 'text-red-600 hover:bg-red-50'
                  : 'text-slate-700 hover:bg-slate-50'
              }`}
            >
              {action.label}
            </button>
          ))}
        </div>
        <div className="p-3 bg-slate-50">
          <button
            type="button"
            onClick={onClose}
            className="w-full py-3 bg-white border border-slate-200 text-slate-700 rounded-xl text-sm font-semibold hover:bg-slate-50 transition-colors min-h-[44px]"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

// Each node descriptor used for layout
interface NodeDesc {
  id: string
  type: 'self' | 'managed' | 'linked' | 'pending' | 'add'
  name: string
  sublabel: string
  onClick?: () => void
  onMenu?: () => void
}

// Rendered HTML card inside foreignObject
function NodeCard({ desc, w, h }: { desc: NodeDesc; w: number; h: number }) {
  function handleMenu(e: React.MouseEvent) {
    e.stopPropagation()
    desc.onMenu?.()
  }

  const initials = desc.name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0].toUpperCase())
    .join('')

  const menuBtn = desc.onMenu ? (
    <button
      type="button"
      onClick={handleMenu}
      title="Options"
      style={{ position: 'absolute', top: 4, right: 4 }}
      className="w-7 h-7 rounded-full flex items-center justify-center text-slate-300 hover:text-slate-500 hover:bg-slate-100 transition-colors"
    >
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5" aria-hidden="true">
        <circle cx="12" cy="5" r="2" />
        <circle cx="12" cy="12" r="2" />
        <circle cx="12" cy="19" r="2" />
      </svg>
    </button>
  ) : null

  if (desc.type === 'add') {
    return (
      <div
        onClick={desc.onClick}
        style={{ width: w, height: h, boxSizing: 'border-box' }}
        className="flex flex-col items-center justify-center gap-1.5 rounded-2xl border-2 border-dashed border-teal-300 bg-teal-50 cursor-pointer hover:bg-teal-100 hover:border-teal-400 transition-colors select-none"
      >
        <div className="w-10 h-10 rounded-full bg-teal-100 flex items-center justify-center">
          <svg viewBox="0 0 24 24" fill="none" stroke="#0f766e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
            <path d="M12 5v14M5 12h14" />
          </svg>
        </div>
        <span className="text-[11px] font-semibold text-teal-700 leading-tight text-center px-2">
          Add member
        </span>
      </div>
    )
  }

  if (desc.type === 'pending') {
    const [rel, ...rest] = desc.sublabel.split(' · ')
    const status = rest.join(' · ')
    return (
      <div
        style={{ width: w, height: h, boxSizing: 'border-box', position: 'relative' }}
        className="flex flex-col items-center justify-center gap-1.5 rounded-2xl border border-dashed border-amber-300 bg-white shadow-sm select-none px-2"
      >
        {menuBtn}
        <div className="w-10 h-10 rounded-full border-2 border-dashed border-slate-300 bg-slate-50 flex items-center justify-center">
          <span className="text-slate-400 text-base font-bold leading-none">?</span>
        </div>
        <p className="text-[11px] font-medium text-slate-600 text-center leading-tight truncate w-full text-center">
          {desc.name.length > 15 ? desc.name.slice(0, 14) + '…' : desc.name}
        </p>
        <div className="flex flex-col items-center gap-0.5">
          <span className="text-[9px] font-semibold text-slate-500">{rel}</span>
          {status && (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-700 text-[9px] font-semibold">
              {status}
            </span>
          )}
        </div>
      </div>
    )
  }

  if (desc.type === 'self') {
    return (
      <div
        style={{ width: w, height: h, boxSizing: 'border-box' }}
        className="flex flex-col items-center justify-center gap-1.5 rounded-2xl border-2 border-teal-600 bg-white shadow-md shadow-teal-100 select-none px-2"
      >
        <div className="w-11 h-11 rounded-full bg-teal-600 flex items-center justify-center ring-4 ring-teal-100">
          <span className="text-white text-sm font-bold leading-none">{initials}</span>
        </div>
        <p className="text-[12px] font-bold text-slate-900 text-center leading-tight truncate w-full text-center">
          {desc.name.length > 15 ? desc.name.slice(0, 14) + '…' : desc.name}
        </p>
        <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-teal-100 text-teal-700 text-[10px] font-semibold">
          You
        </span>
      </div>
    )
  }

  // type === 'linked'
  if (desc.type === 'linked') {
    return (
      <div
        style={{ width: w, height: h, boxSizing: 'border-box', position: 'relative' }}
        className="flex flex-col items-center justify-center gap-1 rounded-2xl border border-teal-200 bg-white shadow-sm select-none px-2"
      >
        {menuBtn}
        <div className="w-11 h-11 rounded-full bg-teal-50 flex items-center justify-center ring-2 ring-teal-200">
          <span className="text-teal-700 text-sm font-semibold leading-none">{initials}</span>
        </div>
        <p className="text-[12px] font-semibold text-slate-900 text-center leading-tight truncate w-full text-center">
          {desc.name.length > 15 ? desc.name.slice(0, 14) + '…' : desc.name}
        </p>
        <div className="flex flex-col items-center gap-0.5">
          <span className="text-[10px] text-slate-500 font-medium">{desc.sublabel}</span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-teal-100 text-teal-700 text-[9px] font-semibold">
            Linked
          </span>
        </div>
      </div>
    )
  }

  // type === 'managed'
  return (
    <div
      style={{ width: w, height: h, boxSizing: 'border-box', position: 'relative' }}
      className="flex flex-col items-center justify-center gap-1.5 rounded-2xl border border-slate-200 bg-white shadow-sm select-none px-2"
    >
      {menuBtn}
      <div className="w-11 h-11 rounded-full bg-slate-100 flex items-center justify-center">
        <span className="text-slate-600 text-sm font-semibold leading-none">{initials}</span>
      </div>
      <p className="text-[12px] font-semibold text-slate-900 text-center leading-tight truncate w-full text-center">
        {desc.name.length > 15 ? desc.name.slice(0, 14) + '…' : desc.name}
      </p>
      <div className="flex flex-col items-center gap-0.5">
        <span className="text-[10px] text-slate-500 font-medium">{desc.sublabel}</span>
        <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[9px] font-semibold">
          Managed
        </span>
      </div>
    </div>
  )
}

interface FamilyTreeProps {
  circle: FamilyCircle
  selfMember: FamilyMember | undefined
  isAdmin: boolean
  selfUserId: string
  onInvite: () => void
  onManageAccess: (member: FamilyMember | FamilyMembership) => void
  onDeleteMember: (memberId: string) => void
  onDeleteMembership: (membershipId: string) => void
  onCancelInvitation: (invitationId: string) => void
  onRequestVaultAccess: (userId: string, name: string) => void
  onViewVault: (memberId: string, name: string) => void
  grantedUserIds: Set<string>
  openDeleteModal: (type: 'managed' | 'linked' | 'pending', name: string, onConfirm: () => void) => void
  openMemberOptions: (name: string, actions: MemberOptionAction[]) => void
}

function FamilyTree({ circle, selfMember, isAdmin, selfUserId, onInvite, onManageAccess, onDeleteMember, onDeleteMembership, onCancelInvitation, onRequestVaultAccess, onViewVault, grantedUserIds, openDeleteModal, openMemberOptions }: FamilyTreeProps) {
  const managed = circle.managed_profiles
  const parents  = managed.filter((m) => m.relationship?.toUpperCase() === 'PARENT')
  const spouses  = managed.filter((m) => m.relationship?.toUpperCase() === 'SPOUSE')
  const children = managed.filter((m) => m.relationship?.toUpperCase() === 'CHILD')
  const others   = managed.filter(
    (m) => !['SELF', 'PARENT', 'SPOUSE', 'CHILD'].includes(m.relationship?.toUpperCase() ?? ''),
  )
  const pending = circle.pending_invitations_sent
  const joinedFamilies = circle.memberships
  const acceptedMembers = circle.family_members ?? []
  const acceptedParents   = acceptedMembers.filter((m) => m.relationship?.toUpperCase() === 'PARENT')
  const acceptedSpouses   = acceptedMembers.filter((m) => m.relationship?.toUpperCase() === 'SPOUSE')
  const acceptedChildren  = acceptedMembers.filter((m) => m.relationship?.toUpperCase() === 'CHILD')
  const acceptedOthers    = acceptedMembers.filter(
    (m) => !['PARENT', 'SPOUSE', 'CHILD'].includes(m.relationship?.toUpperCase() ?? ''),
  )

  function managedNode(m: FamilyMember, sublabel: string): NodeDesc {
    const actions: MemberOptionAction[] = [
      { label: 'View vault', variant: 'normal', onClick: () => onViewVault(m.member_id, m.full_name) },
    ]
    if (isAdmin) {
      actions.push({
        label: 'Delete member and account',
        variant: 'danger',
        onClick: () => openDeleteModal('managed', m.full_name, () => onDeleteMember(m.member_id)),
      })
    }
    return {
      id: m.member_id, type: 'managed' as const, name: m.full_name, sublabel,
      onMenu: () => openMemberOptions(m.full_name, actions),
    }
  }

  function linkedNode(ms: FamilyMembership, sublabel: string, canDelete: boolean): NodeDesc {
    const hasGrant = grantedUserIds.has(ms.user_id)
    const displayName = ms.family_owner_name ?? 'Member'
    const actions: MemberOptionAction[] = []
    if (hasGrant && ms.primary_member_id) {
      actions.push({ label: 'View vault', variant: 'normal', onClick: () => onViewVault(ms.primary_member_id!, displayName) })
    } else if (!hasGrant) {
      actions.push({ label: 'Request vault access', variant: 'normal', onClick: () => onRequestVaultAccess(ms.user_id, displayName) })
    }
    if (canDelete) {
      actions.push({
        label: 'Delete member from family',
        variant: 'danger',
        onClick: () => openDeleteModal('linked', displayName, () => onDeleteMembership(ms.membership_id)),
      })
    }
    return {
      id: ms.membership_id, type: 'linked' as const,
      name: displayName,
      sublabel,
      onMenu: actions.length > 0 ? () => openMemberOptions(displayName, actions) : undefined,
    }
  }

  // Build level arrays of NodeDesc
  const parentRow: NodeDesc[] = [
    ...parents.map((p) => managedNode(p, 'Parent')),
    ...acceptedParents.map((ms) => linkedNode(ms, RELATIONSHIP_LABELS['PARENT'], isAdmin)),
    ...joinedFamilies.map((ms) => linkedNode(
      ms,
      RELATIONSHIP_LABELS[ms.relationship ?? ''] ?? (ms.relationship ?? 'Member'),
      ms.user_id === selfUserId,
    )),
  ]

  const middleRow: NodeDesc[] = [
    ...spouses.map((s) => managedNode(s, 'Spouse')),
    ...acceptedSpouses.map((ms) => linkedNode(ms, RELATIONSHIP_LABELS['SPOUSE'], isAdmin)),
    { id: '__self', type: 'self' as const, name: selfMember?.full_name ?? 'Me', sublabel: 'You' },
    { id: '__add', type: 'add' as const, name: '', sublabel: '', onClick: onInvite },
  ]

  const childRow: NodeDesc[] = [
    ...children.map((c) => managedNode(c, 'Child')),
    ...acceptedChildren.map((ms) => linkedNode(ms, RELATIONSHIP_LABELS['CHILD'], isAdmin)),
  ]

  const bottomRow: NodeDesc[] = [
    ...others.map((o) => managedNode(o, RELATIONSHIP_LABELS[o.relationship] ?? 'Other')),
    ...acceptedOthers.map((ms) => linkedNode(
      ms,
      RELATIONSHIP_LABELS[ms.relationship ?? ''] ?? (ms.relationship ?? 'Member'),
      isAdmin,
    )),
    ...pending.map((inv) => {
      const invName = inv.invited_email.split('@')[0]
      const invActions: MemberOptionAction[] = isAdmin ? [
        {
          label: 'Cancel invitation',
          variant: 'danger',
          onClick: () => openDeleteModal('pending', invName, () => onCancelInvitation(inv.invitation_id)),
        },
      ] : []
      return {
        id: inv.invitation_id, type: 'pending' as const,
        name: invName,
        sublabel: `${RELATIONSHIP_LABELS[inv.relationship] ?? inv.relationship} · Pending`,
        onMenu: invActions.length > 0 ? () => openMemberOptions(invName, invActions) : undefined,
      }
    }),
  ]

  const levels: NodeDesc[][] = [
    ...(parentRow.length  > 0 ? [parentRow]  : []),
    middleRow,
    ...(childRow.length   > 0 ? [childRow]   : []),
    ...(bottomRow.length  > 0 ? [bottomRow]  : []),
  ]

  // SVG dimensions
  const maxCount    = Math.max(...levels.map((l) => l.length))
  const svgW        = Math.max(360, PX * 2 + maxCount * CW + (maxCount - 1) * HG)
  const svgH        = PY * 2 + levels.length * CH + (levels.length - 1) * VG

  function rowX(count: number, idx: number): number {
    const rowW   = count * CW + (count - 1) * HG
    const startX = (svgW - rowW) / 2
    return startX + idx * (CW + HG)
  }
  function rowY(li: number): number {
    return PY + li * (CH + VG)
  }

  // Self position (always in middleRow)
  const selfLi  = parentRow.length > 0 ? 1 : 0
  const selfNi  = middleRow.findIndex((n) => n.id === '__self')
  const selfCx  = rowX(middleRow.length, selfNi) + CW / 2
  const selfTopY = rowY(selfLi)
  const selfBotY = rowY(selfLi) + CH

  // Child level index (for edges)
  const childLi = selfLi + (childRow.length > 0 ? 1 : 0)
  const bottomLi = selfLi + (childRow.length > 0 ? 2 : 1)

  return (
    <div className="overflow-x-auto py-2">
      <svg
        width={svgW}
        height={svgH}
        style={{ display: 'block', margin: '0 auto', overflow: 'visible' }}
        aria-label="Family tree"
      >
        {/* ── Edges ── */}

        {/* Parents → Self */}
        {parentRow.map((_, pi) => (
          <path
            key={`ep${pi}`}
            d={curve(rowX(parentRow.length, pi) + CW / 2, rowY(0) + CH, selfCx, selfTopY)}
            fill="none" stroke="#cbd5e1" strokeWidth={1.5}
          />
        ))}

        {/* Self → Children */}
        {childRow.map((_, ci) => (
          <path
            key={`ec${ci}`}
            d={curve(selfCx, selfBotY, rowX(childRow.length, ci) + CW / 2, rowY(childLi))}
            fill="none" stroke="#cbd5e1" strokeWidth={1.5}
          />
        ))}

        {/* Self → Bottom row (pending / linked / others) — dashed */}
        {bottomRow.map((_, bi) => (
          <path
            key={`eb${bi}`}
            d={curve(selfCx, selfBotY, rowX(bottomRow.length, bi) + CW / 2, rowY(bottomLi))}
            fill="none" stroke="#e2e8f0" strokeWidth={1} strokeDasharray="5 3"
          />
        ))}

        {/* ── Nodes (foreignObject so we can use HTML/Tailwind) ── */}
        {levels.map((row, li) =>
          row.map((desc, ni) => (
            <foreignObject
              key={desc.id}
              x={rowX(row.length, ni)}
              y={rowY(li)}
              width={CW}
              height={CH}
            >
              {/* @ts-expect-error xmlns required for foreignObject children */}
              <div xmlns="http://www.w3.org/1999/xhtml">
                <NodeCard desc={desc} w={CW} h={CH} />
              </div>
            </foreignObject>
          ))
        )}
      </svg>
    </div>
  )
}

// ── Invite / add member modal ──────────────────────────────────────────────

const RELATIONSHIPS: Relationship[] = ['PARENT', 'SPOUSE', 'CHILD', 'SIBLING', 'OTHER']

function ageFromDob(dob: string): number | null {
  if (!dob) return null
  const birth = new Date(dob)
  if (isNaN(birth.getTime())) return null
  const today = new Date()
  let age = today.getFullYear() - birth.getFullYear()
  const m = today.getMonth() - birth.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--
  return age
}

interface InviteModalProps {
  onClose: () => void
}

function InviteModal({ onClose }: InviteModalProps) {
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [relationship, setRelationship] = useState<Relationship>('CHILD')
  const [dob, setDob] = useState('')
  const [done, setDone] = useState(false)
  const [doneMode, setDoneMode] = useState<'invite' | 'managed'>('invite')

  const sendInvitation = useSendInvitation()
  const createManaged = useCreateManagedMember()

  const isChild = relationship === 'CHILD'
  const age = isChild && dob ? ageFromDob(dob) : null
  const isMinorChild = isChild && age !== null && age < 12

  const isPending = sendInvitation.isPending || createManaged.isPending
  const apiError = (sendInvitation.error ?? createManaged.error) as (Error & { response?: { status?: number } }) | null
  const isConflict = apiError?.response?.status === 409
  const isSelfInvite = apiError?.response?.status === 400

  const canSubmit = isMinorChild
    ? name.trim().length > 0 && dob.length > 0
    : email.trim().length > 0

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    try {
      if (isMinorChild) {
        await createManaged.mutateAsync({ name: name.trim(), relationship, date_of_birth: dob || null })
        setDoneMode('managed')
      } else {
        await sendInvitation.mutateAsync({ email: email.trim(), relationship })
        setDoneMode('invite')
      }
      setDone(true)
    } catch {
      // error shown below
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />

      <div className="relative w-full sm:max-w-md bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <h2 className="text-base font-semibold text-slate-900">Add a family member</h2>
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
          {done ? (
            <div className="text-center py-6 space-y-3">
              <div className="w-12 h-12 rounded-full bg-teal-100 flex items-center justify-center mx-auto">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-teal-600" aria-hidden="true">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
              </div>
              {doneMode === 'managed' ? (
                <>
                  <p className="text-sm font-semibold text-slate-900">Child profile created!</p>
                  <p className="text-xs text-slate-500">
                    <strong>{name}</strong>'s health vault has been created and you have full access.
                  </p>
                </>
              ) : (
                <>
                  <p className="text-sm font-semibold text-slate-900">Invitation sent!</p>
                  <p className="text-xs text-slate-500">
                    We emailed an invite to <strong>{email}</strong>. They'll receive it shortly.
                  </p>
                </>
              )}
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
              {/* Relationship first */}
              <div>
                <p className="block text-xs font-semibold text-slate-600 mb-2">Relationship</p>
                <div className="flex flex-wrap gap-2">
                  {RELATIONSHIPS.map((rel) => (
                    <button
                      key={rel}
                      type="button"
                      onClick={() => { setRelationship(rel); setDob('') }}
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

              {/* Date of birth — only shown for CHILD */}
              {isChild && (
                <div>
                  <label htmlFor="invite-dob" className="block text-xs font-semibold text-slate-600 mb-1.5">
                    Child's date of birth
                  </label>
                  <input
                    id="invite-dob"
                    type="date"
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
                    max={new Date().toISOString().split('T')[0]}
                    className="w-full px-3 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 min-h-[44px]"
                  />
                </div>
              )}

              {/* Minor child notice */}
              {isMinorChild && (
                <div className="flex gap-2.5 bg-teal-50 border border-teal-100 rounded-xl px-3 py-3">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 text-teal-600 flex-shrink-0 mt-0.5" aria-hidden="true">
                    <circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" />
                  </svg>
                  <p className="text-xs text-teal-700">
                    Children under 12 are managed directly — no email needed. You'll have full access to their vault.
                  </p>
                </div>
              )}

              {/* Name — shown for minor children */}
              {isMinorChild && (
                <div>
                  <label htmlFor="invite-name" className="block text-xs font-semibold text-slate-600 mb-1.5">
                    Child's name
                  </label>
                  <input
                    id="invite-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Full name"
                    required
                    className="w-full px-3 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 min-h-[44px]"
                  />
                </div>
              )}

              {/* Email — shown for non-minor */}
              {!isMinorChild && (
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
              )}

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
                disabled={isPending || !canSubmit}
                className="w-full py-2.5 bg-teal-600 text-white rounded-xl font-semibold text-sm hover:bg-teal-700 transition-colors min-h-[44px] disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isPending ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    {isMinorChild ? 'Creating…' : 'Sending…'}
                  </>
                ) : isMinorChild ? (
                  'Create child profile'
                ) : (
                  'Send invitation'
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
  const [deleteModal, setDeleteModal] = useState<DeleteModalState>({
    open: false, type: 'managed', name: '', onConfirm: () => {},
  })
  const [memberOptions, setMemberOptions] = useState<MemberOptionsState>({
    open: false, name: '', actions: [],
  })
  const { user } = useAuth0()
  const navigate = useNavigate()
  const setActiveMember = useSetActiveMember()
  const { data: circle, isLoading, isError } = useFamilyCircle()
  const { data: grants } = useVaultAccessGrants()
  useFamilyCircleEvents()
  const deleteMember = useDeleteManagedMember()
  const deleteMembership = useDeleteMembership()
  const cancelInvitation = useCancelInvitation()
  const requestVaultAccess = useRequestVaultAccess()

  // Compare DB UUIDs — created_by_user_id is an internal UUID, not Auth0 sub
  const isAdmin = !!(
    circle?.family?.created_by_user_id &&
    circle?.self_member?.user_id &&
    circle.family.created_by_user_id === circle.self_member.user_id
  )
  const selfUserId = user?.sub ?? ''

  const grantedUserIds = useMemo(
    () => new Set((grants ?? []).map((g) => g.target_user_id)),
    [grants],
  )

  function handleViewVault(memberId: string, name: string) {
    setActiveMember(memberId, name)
    navigate('/')
  }

  function openDeleteModal(type: 'managed' | 'linked' | 'pending', name: string, onConfirm: () => void) {
    setDeleteModal({ open: true, type, name, onConfirm })
  }

  function openMemberOptions(name: string, actions: MemberOptionAction[]) {
    setMemberOptions({ open: true, name, actions })
  }

  function handleRequestVaultAccess(userId: string, name: string) {
    if (!window.confirm(`Send a vault access request to ${name}?`)) return
    requestVaultAccess.mutate(userId)
  }

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

  const selfMember = circle?.self_member ?? undefined
  const hasAnyMember =
    (circle?.managed_profiles.length ?? 0) > 0 ||
    (circle?.memberships.length ?? 0) > 0 ||
    (circle?.family_members?.length ?? 0) > 0 ||
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
                isAdmin={isAdmin}
                selfUserId={selfUserId}
                onInvite={() => setInviteOpen(true)}
                onManageAccess={(m) => setAccessTarget(m)}
                onDeleteMember={(id) => deleteMember.mutate(id)}
                onDeleteMembership={(id) => deleteMembership.mutate(id)}
                onCancelInvitation={(id) => cancelInvitation.mutate(id)}
                onRequestVaultAccess={handleRequestVaultAccess}
                onViewVault={handleViewVault}
                grantedUserIds={grantedUserIds}
                openDeleteModal={openDeleteModal}
                openMemberOptions={openMemberOptions}
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

      {/* Member options sheet */}
      <MemberOptionsSheet
        state={memberOptions}
        onClose={() => setMemberOptions((s) => ({ ...s, open: false }))}
      />

      {/* Delete confirmation modal */}
      <DeleteConfirmModal
        state={deleteModal}
        onClose={() => setDeleteModal((s) => ({ ...s, open: false }))}
      />

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
