import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNotifications, useMarkRead, useMarkAllRead } from '../../hooks/useNotifications'
import { api } from '../../lib/api'
import type { Notification } from '../../types'

// ── Relative time helper ───────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString()
}

// ── Provider access request row (MV-163) ──────────────────────────────────

function ProviderAccessRow({ notification, onClose }: { notification: Notification; onClose: () => void }) {
  const qc = useQueryClient()
  const markRead = useMarkRead()
  const [responded, setResponded] = useState<'ACCEPTED' | 'DECLINED' | null>(null)

  const requestId = notification.metadata?.request_id as string | undefined

  const respond = useMutation({
    mutationFn: (action: 'accept' | 'decline') =>
      api.post(`/provider/access-requests/${requestId}/respond`, { action }),
    onSuccess: (_data, action) => {
      setResponded(action === 'accept' ? 'ACCEPTED' : 'DECLINED')
      markRead.mutate(notification.notification_id)
      qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  return (
    <div className="px-4 py-3 flex items-start gap-3 bg-teal-50/40 border-b border-teal-100 last:border-0">
      <span className="mt-1.5 shrink-0 w-2 h-2 rounded-full">
        {!notification.is_read && !responded && (
          <span className="block w-2 h-2 rounded-full bg-teal-500" aria-label="Unread" />
        )}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-slate-900">{notification.title}</p>
        <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{notification.body}</p>
        <p className="text-xs text-slate-400 mt-1">{relativeTime(notification.created_at)}</p>

        {responded ? (
          <p className={`text-xs font-medium mt-2 ${responded === 'ACCEPTED' ? 'text-teal-600' : 'text-slate-400'}`}>
            {responded === 'ACCEPTED' ? 'Access granted' : 'Access declined'}
          </p>
        ) : (
          <div className="flex gap-2 mt-2">
            <button
              onClick={() => respond.mutate('accept')}
              disabled={respond.isPending}
              className="bg-primary text-white text-xs font-medium rounded-lg px-3 py-1.5 hover:bg-teal-700 disabled:opacity-50"
            >
              Accept
            </button>
            <button
              onClick={() => respond.mutate('decline')}
              disabled={respond.isPending}
              className="border border-slate-200 text-slate-600 text-xs font-medium rounded-lg px-3 py-1.5 hover:bg-slate-50 disabled:opacity-50"
            >
              Decline
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Single notification row ────────────────────────────────────────────────

function NotificationRow({ notification, onClose }: { notification: Notification; onClose: () => void }) {
  const navigate = useNavigate()
  const markRead = useMarkRead()

  if (notification.type === 'PROVIDER_ACCESS_REQUEST') {
    return <ProviderAccessRow notification={notification} onClose={onClose} />
  }

  function handleClick() {
    if (!notification.is_read) {
      markRead.mutate(notification.notification_id)
    }
    if (notification.action_url) {
      navigate(notification.action_url)
      onClose()
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`w-full text-left px-4 py-3 flex items-start gap-3 hover:bg-slate-50 transition-colors min-h-[44px] ${
        notification.action_url ? 'cursor-pointer' : 'cursor-default'
      }`}
    >
      {/* Unread dot */}
      <span className="mt-1.5 shrink-0 w-2 h-2 rounded-full">
        {!notification.is_read && (
          <span className="block w-2 h-2 rounded-full bg-teal-500" aria-label="Unread" />
        )}
      </span>

      <div className="flex-1 min-w-0">
        <p className={`text-sm truncate ${notification.is_read ? 'font-normal text-slate-700' : 'font-semibold text-slate-900'}`}>
          {notification.title}
        </p>
        <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{notification.body}</p>
        <p className="text-xs text-slate-400 mt-1">{relativeTime(notification.created_at)}</p>
      </div>
    </button>
  )
}

// ── Skeleton loader ────────────────────────────────────────────────────────

function NotificationSkeleton() {
  return (
    <div className="px-4 py-3 flex items-start gap-3">
      <div className="mt-1.5 w-2 h-2 rounded-full bg-slate-200 shrink-0" />
      <div className="flex-1 space-y-1.5">
        <div className="h-3 bg-slate-200 rounded w-3/4 animate-pulse" />
        <div className="h-3 bg-slate-200 rounded w-full animate-pulse" />
        <div className="h-2.5 bg-slate-200 rounded w-1/3 animate-pulse" />
      </div>
    </div>
  )
}

// ── NotificationCentre panel ───────────────────────────────────────────────

interface NotificationCentreProps {
  onClose: () => void
}

export function NotificationCentre({ onClose }: NotificationCentreProps) {
  const panelRef = useRef<HTMLDivElement>(null)
  const { data, isLoading, isError } = useNotifications(1, 20)
  const markAllRead = useMarkAllRead()

  const notifications = data?.items ?? []
  const hasUnread = notifications.some((n) => !n.is_read)

  // Close on outside click
  useEffect(() => {
    function handlePointerDown(e: PointerEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('pointerdown', handlePointerDown)
    return () => document.removeEventListener('pointerdown', handlePointerDown)
  }, [onClose])

  return (
    <div
      ref={panelRef}
      className="absolute right-0 top-full mt-2 w-80 max-h-[480px] bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden flex flex-col z-50"
      role="dialog"
      aria-label="Notifications"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
        <h2 className="text-sm font-semibold text-slate-900">Notifications</h2>
        {hasUnread && (
          <button
            type="button"
            onClick={() => markAllRead.mutate()}
            disabled={markAllRead.isPending}
            className="text-xs text-teal-600 hover:text-teal-700 font-medium disabled:opacity-50 transition-colors"
          >
            {markAllRead.isPending ? 'Marking…' : 'Mark all read'}
          </button>
        )}
      </div>

      {/* Body */}
      <div className="overflow-y-auto flex-1">
        {isLoading && (
          <>
            <NotificationSkeleton />
            <NotificationSkeleton />
            <NotificationSkeleton />
          </>
        )}

        {isError && (
          <p className="px-4 py-6 text-sm text-slate-500 text-center">
            Failed to load notifications.
          </p>
        )}

        {!isLoading && !isError && notifications.length === 0 && (
          <p className="px-4 py-10 text-sm text-slate-400 text-center">
            No notifications
          </p>
        )}

        {!isLoading && !isError && notifications.map((n) => (
          <NotificationRow key={n.notification_id} notification={n} onClose={onClose} />
        ))}
      </div>
    </div>
  )
}
