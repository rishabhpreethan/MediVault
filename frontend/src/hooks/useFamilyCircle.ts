import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth0 } from '@auth0/auth0-react'
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

// ── SSE hook — real-time family circle updates ─────────────────────────────

export function useFamilyCircleEvents() {
  const queryClient = useQueryClient()
  const { getAccessTokenSilently } = useAuth0()

  useEffect(() => {
    const controller = new AbortController()
    let reconnectTimer: ReturnType<typeof setTimeout>

    async function connect() {
      try {
        const token = await getAccessTokenSilently()
        const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
        const res = await fetch(`${baseUrl}/family/circle/events`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        })
        if (!res.ok || !res.body) return

        const reader = res.body.getReader()
        const decoder = new TextDecoder()

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const text = decoder.decode(value, { stream: true })
          if (text.includes('family-updated')) {
            void queryClient.invalidateQueries({ queryKey: ['family-circle'] })
          }
        }
      } catch (err) {
        if ((err as Error).name === 'AbortError') return
        // Reconnect after 5 s on network error
        reconnectTimer = setTimeout(() => { void connect() }, 5_000)
      }
    }

    void connect()

    return () => {
      controller.abort()
      clearTimeout(reconnectTimer)
    }
  }, [getAccessTokenSilently, queryClient])
}

// ── Managed member (direct profile, no invite) ────────────────────────────

interface CreateManagedMemberPayload {
  name: string
  relationship: string
  date_of_birth?: string | null
}

export function useCreateManagedMember() {
  const qc = useQueryClient()
  return useMutation<void, Error, CreateManagedMemberPayload>({
    mutationFn: async (payload) => {
      await api.post('/family/members', payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['family-circle'] })
      qc.invalidateQueries({ queryKey: ['family-members'] })
    },
  })
}

export function useDeleteManagedMember() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: async (memberId) => {
      await api.delete(`/family/members/${memberId}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['family-circle'] })
      qc.invalidateQueries({ queryKey: ['family-members'] })
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

// ── Membership removal / leave ─────────────────────────────────────────────

export function useDeleteMembership() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: async (membershipId) => {
      await api.delete(`/family/memberships/${membershipId}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['family-circle'] })
      qc.invalidateQueries({ queryKey: ['family-members'] })
    },
  })
}

// ── Vault access requests ──────────────────────────────────────────────────

export function useRequestVaultAccess() {
  const qc = useQueryClient()
  return useMutation<{ notification_id: string; status: string }, Error, string>({
    mutationFn: async (targetUserId) => {
      const { data } = await api.post('/family/vault-access-requests', { target_user_id: targetUserId })
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}

export function useRespondVaultAccessRequest() {
  const qc = useQueryClient()
  return useMutation<void, Error, { notificationId: string; action: 'accept' | 'decline' }>({
    mutationFn: async ({ notificationId, action }) => {
      await api.post(`/family/vault-access-requests/${notificationId}/respond`, { action })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['vault-access-grants'] })
      qc.invalidateQueries({ queryKey: ['family-circle'] })
    },
  })
}
