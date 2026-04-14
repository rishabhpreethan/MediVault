import { useAuth0 } from '@auth0/auth0-react'
import type { FamilyMember, FamilyMembership } from '../../types'
import {
  useFamilyCircle,
  useVaultAccessGrants,
  useCreateGrant,
  useRevokeGrant,
  useToggleCanInvite,
} from '../../hooks/useFamilyCircle'

// ── Types ──────────────────────────────────────────────────────────────────

interface Props {
  targetMember: FamilyMember | FamilyMembership
  onClose: () => void
}

function isFamilyMember(m: FamilyMember | FamilyMembership): m is FamilyMember {
  return 'member_id' in m
}

function getMemberName(m: FamilyMember | FamilyMembership): string {
  if (isFamilyMember(m)) return m.full_name
  return `Member (${m.user_id.slice(0, 8)})`
}

function getMemberUserId(m: FamilyMember | FamilyMembership): string {
  if (isFamilyMember(m)) return m.user_id
  return m.user_id
}

// ── Toggle switch ──────────────────────────────────────────────────────────

interface ToggleProps {
  checked: boolean
  loading: boolean
  onChange: (val: boolean) => void
  label: string
}

function Toggle({ checked, loading, onChange, label }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={loading}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 min-w-[44px] min-h-[44px] ${
        checked ? 'bg-teal-600' : 'bg-slate-200'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
      {loading && (
        <span className="absolute inset-0 flex items-center justify-center">
          <span className="w-3 h-3 border-2 border-teal-600 border-t-transparent rounded-full animate-spin" />
        </span>
      )}
    </button>
  )
}

// ── VaultAccessPanel ───────────────────────────────────────────────────────

export function VaultAccessPanel({ targetMember, onClose }: Props) {
  const { user } = useAuth0()
  const { data: circle, isLoading: circleLoading } = useFamilyCircle()
  const { data: grants, isLoading: grantsLoading } = useVaultAccessGrants()
  const createGrant = useCreateGrant()
  const revokeGrant = useRevokeGrant()
  const toggleCanInvite = useToggleCanInvite()

  const targetName = getMemberName(targetMember)
  const targetUserId = getMemberUserId(targetMember)

  // Check if current user is the family admin
  const isAdmin = circle?.family?.created_by_user_id === user?.sub

  // Find the membership record for the target so we can toggle can_invite
  const targetMembership = circle?.memberships.find((m) => m.user_id === targetUserId)

  // All other family members (for the access matrix)
  const otherMembers: Array<{ userId: string; name: string }> = []
  if (circle) {
    circle.managed_profiles.forEach((mp) => {
      if (mp.user_id !== targetUserId) {
        otherMembers.push({ userId: mp.user_id, name: mp.full_name })
      }
    })
    circle.memberships.forEach((ms) => {
      if (ms.user_id !== targetUserId && !otherMembers.find((o) => o.userId === ms.user_id)) {
        otherMembers.push({ userId: ms.user_id, name: `Member (${ms.user_id.slice(0, 8)})` })
      }
    })
  }

  // Helpers to check/toggle grant state
  function hasGrant(granteeUserId: string, tgtUserId: string): boolean {
    return (grants ?? []).some(
      (g) => g.grantee_user_id === granteeUserId && g.target_user_id === tgtUserId,
    )
  }

  function findGrant(granteeUserId: string, tgtUserId: string) {
    return (grants ?? []).find(
      (g) => g.grantee_user_id === granteeUserId && g.target_user_id === tgtUserId,
    )
  }

  function handleToggleViewTarget(viewerUserId: string, currentlyGranted: boolean) {
    if (currentlyGranted) {
      const grant = findGrant(viewerUserId, targetUserId)
      if (grant) revokeGrant.mutate(grant.grant_id)
    } else {
      createGrant.mutate({ grantee_user_id: viewerUserId, target_user_id: targetUserId })
    }
  }

  function handleToggleViewOther(otherUserId: string, currentlyGranted: boolean) {
    if (currentlyGranted) {
      const grant = findGrant(targetUserId, otherUserId)
      if (grant) revokeGrant.mutate(grant.grant_id)
    } else {
      createGrant.mutate({ grantee_user_id: targetUserId, target_user_id: otherUserId })
    }
  }

  const isLoading = circleLoading || grantsLoading

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div className="relative w-full sm:max-w-lg bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl max-h-[85vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <h2 className="text-base font-semibold text-slate-900">
            Access settings for {targetName}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Close panel"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5" aria-hidden="true">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 px-5 py-4 space-y-6">
          {isLoading && (
            <div className="flex justify-center py-8">
              <div className="w-6 h-6 border-2 border-teal-600 border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {!isLoading && !isAdmin && (
            <p className="text-sm text-slate-500 text-center py-4">
              Only the family admin can manage access settings.
            </p>
          )}

          {!isLoading && isAdmin && (
            <>
              {/* Section: Who can view target's records */}
              <section>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  Who can view {targetName}'s records
                </h3>
                {otherMembers.length === 0 ? (
                  <p className="text-sm text-slate-400">No other members in the family.</p>
                ) : (
                  <ul className="space-y-3">
                    {otherMembers.map((om) => {
                      const granted = hasGrant(om.userId, targetUserId)
                      const isBusy =
                        (createGrant.isPending || revokeGrant.isPending)
                      return (
                        <li key={om.userId} className="flex items-center justify-between gap-3">
                          <span className="text-sm text-slate-700">{om.name}</span>
                          <Toggle
                            checked={granted}
                            loading={isBusy}
                            onChange={(val) => handleToggleViewTarget(om.userId, !val)}
                            label={`Allow ${om.name} to view ${targetName}'s records`}
                          />
                        </li>
                      )
                    })}
                  </ul>
                )}
              </section>

              {/* Section: What target can view */}
              <section>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  Can {targetName} view others' records
                </h3>
                {otherMembers.length === 0 ? (
                  <p className="text-sm text-slate-400">No other members in the family.</p>
                ) : (
                  <ul className="space-y-3">
                    {otherMembers.map((om) => {
                      const granted = hasGrant(targetUserId, om.userId)
                      const isBusy = createGrant.isPending || revokeGrant.isPending
                      return (
                        <li key={om.userId} className="flex items-center justify-between gap-3">
                          <span className="text-sm text-slate-700">{om.name}</span>
                          <Toggle
                            checked={granted}
                            loading={isBusy}
                            onChange={(val) => handleToggleViewOther(om.userId, !val)}
                            label={`Allow ${targetName} to view ${om.name}'s records`}
                          />
                        </li>
                      )
                    })}
                  </ul>
                )}
              </section>

              {/* Section: Invite permissions */}
              {targetMembership && (
                <section>
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    Invite permissions
                  </h3>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm text-slate-700">
                      Can {targetName} invite others to the family
                    </span>
                    <Toggle
                      checked={targetMembership.can_invite}
                      loading={toggleCanInvite.isPending}
                      onChange={(val) =>
                        toggleCanInvite.mutate({
                          membershipId: targetMembership.membership_id,
                          can_invite: val,
                        })
                      }
                      label={`Allow ${targetName} to invite others`}
                    />
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
