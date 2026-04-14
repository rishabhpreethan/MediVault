import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { Notification, PaginatedNotifications } from '../types'

const NOTIFICATIONS_KEY = ['notifications']
const UNREAD_COUNT_KEY = ['notifications', 'unread-count']

// ── Notifications list ─────────────────────────────────────────────────────

export function useNotifications(page = 1, limit = 20) {
  return useQuery<PaginatedNotifications>({
    queryKey: [...NOTIFICATIONS_KEY, { page, limit }],
    queryFn: async () => {
      const { data } = await api.get('/notifications', { params: { page, limit } })
      return data
    },
  })
}

// ── Unread count (polled every 30 s) ──────────────────────────────────────

export function useUnreadCount() {
  return useQuery<{ count: number }>({
    queryKey: UNREAD_COUNT_KEY,
    queryFn: async () => {
      const { data } = await api.get('/notifications/unread-count')
      return data
    },
    refetchInterval: 30_000,
  })
}

// ── Mark one notification read ─────────────────────────────────────────────

export function useMarkRead() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: async (notificationId) => {
      await api.patch(`/notifications/${notificationId}/read`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: NOTIFICATIONS_KEY })
      qc.invalidateQueries({ queryKey: UNREAD_COUNT_KEY })
    },
  })
}

// ── Mark all read ──────────────────────────────────────────────────────────

export function useMarkAllRead() {
  const qc = useQueryClient()
  return useMutation<void, Error, void>({
    mutationFn: async () => {
      await api.post('/notifications/read-all')
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: NOTIFICATIONS_KEY })
      qc.invalidateQueries({ queryKey: UNREAD_COUNT_KEY })
    },
  })
}

// ── Delete notification ────────────────────────────────────────────────────

export function useDeleteNotification() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: async (notificationId) => {
      await api.delete(`/notifications/${notificationId}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: NOTIFICATIONS_KEY })
      qc.invalidateQueries({ queryKey: UNREAD_COUNT_KEY })
    },
  })
}
