import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import type {
  FamilyCircle,
  FamilyInvitation,
  FamilyMembership,
  VaultAccessGrant,
} from '../types'

// ── Family circle query ────────────────────────────────────────────────────

export function useFamilyCircle() {
  return useQuery<FamilyCircle>({
    queryKey: ['family-circle'],
    queryFn: async () => {
      const { data } = await api.get('/family/circle')
      return data
    },
  })
}

// ── Invitation mutations ───────────────────────────────────────────────────

interface SendInvitationPayload {
  email: string
  relationship: string
}

export function useSendInvitation() {
  const qc = useQueryClient()
  return useMutation<FamilyInvitation, Error, SendInvitationPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post('/family/invitations', payload)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['family-circle'] })
    },
  })
}

export function useCancelInvitation() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: async (invitationId) => {
      await api.delete(`/family/invitations/${invitationId}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['family-circle'] })
    },
  })
}

export function useResendInvitation() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: async (invitationId) => {
      await api.post(`/family/invitations/${invitationId}/resend`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['family-circle'] })
    },
  })
}

// ── Invite token mutations (public / accept flow) ──────────────────────────

export function useAcceptInvitation(token: string) {
  const qc = useQueryClient()
  return useMutation<FamilyMembership, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`/invite/${token}/accept`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['family-circle'] })
    },
  })
}

export function useDeclineInvitation(token: string) {
  return useMutation<void, Error, void>({
    mutationFn: async () => {
      await api.post(`/invite/${token}/decline`)
    },
  })
}

// ── Vault access grants ────────────────────────────────────────────────────

export function useVaultAccessGrants() {
  return useQuery<VaultAccessGrant[]>({
    queryKey: ['vault-access-grants'],
    queryFn: async () => {
      const { data } = await api.get('/family/access')
      return data
    },
  })
}

interface CreateGrantPayload {
  grantee_user_id: string
  target_user_id: string
}

export function useCreateGrant() {
  const qc = useQueryClient()
  return useMutation<VaultAccessGrant, Error, CreateGrantPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post('/family/access', payload)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['vault-access-grants'] })
    },
  })
}

export function useRevokeGrant() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: async (grantId) => {
      await api.delete(`/family/access/${grantId}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['vault-access-grants'] })
    },
  })
}

// ── Membership permissions ─────────────────────────────────────────────────

interface ToggleCanInvitePayload {
  membershipId: string
  can_invite: boolean
}

export function useToggleCanInvite() {
  const qc = useQueryClient()
  return useMutation<void, Error, ToggleCanInvitePayload>({
    mutationFn: async ({ membershipId, can_invite }) => {
      await api.patch(`/family/memberships/${membershipId}/can-invite`, { can_invite })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['family-circle'] })
    },
  })
}
