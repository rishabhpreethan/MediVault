import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth0 } from '@auth0/auth0-react'
import { api } from '../../lib/api'
import { useAuthToken } from '../../hooks/useAuthToken'
import type { InviteTokenInfo } from '../../types'
import { useAcceptInvitation, useDeclineInvitation } from '../../hooks/useFamilyCircle'
import { AxiosError } from 'axios'

// ── Icons ──────────────────────────────────────────────────────────────────

function FamilyIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 64 64"
      className="w-16 h-16"
      fill="none"
      aria-hidden="true"
    >
      <circle cx="32" cy="32" r="30" fill="#006b5f" opacity="0.12" stroke="#006b5f" strokeWidth="2" />
      <path
        d="M40 35c2.21 0 3.98-1.79 3.98-4S42.21 27 40 27s-4 1.79-4 4 1.79 4 4 4zm-16 0c2.21 0 3.98-1.79 3.98-4S26.21 27 24 27s-4 1.79-4 4 1.79 4 4 4zm0 3c-3.11 0-9.33 1.56-9.33 4.67V45h18.67v-2.33C33.33 39.56 27.11 38 24 38zm16 0c-.39 0-.83.03-1.29.07 1.55 1.12 2.62 2.63 2.62 4.6V45h8V42.67C49.33 39.56 43.11 38 40 38z"
        fill="#006b5f"
      />
    </svg>
  )
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function InviteSkeleton() {
  return (
    <div className="w-full max-w-sm animate-pulse space-y-6">
      <div className="flex flex-col items-center gap-3">
        <div className="w-16 h-16 rounded-full bg-slate-200" />
        <div className="h-6 bg-slate-200 rounded w-40" />
        <div className="h-4 bg-slate-200 rounded w-32" />
      </div>
      <div className="rounded-2xl bg-white border border-slate-100 p-8 space-y-4">
        <div className="h-5 bg-slate-200 rounded w-full" />
        <div className="h-5 bg-slate-200 rounded w-3/4" />
        <div className="h-10 bg-slate-200 rounded-xl w-full" />
        <div className="h-10 bg-slate-200 rounded-xl w-full" />
      </div>
    </div>
  )
}

// ── Outcome card ───────────────────────────────────────────────────────────

interface OutcomeCardProps {
  icon: 'success' | 'info' | 'error'
  title: string
  message: string
  linkTo: string
  linkLabel: string
}

function OutcomeCard({ icon, title, message, linkTo, linkLabel }: OutcomeCardProps) {
  const colours = {
    success: { bg: 'bg-teal-100', text: 'text-teal-600' },
    info: { bg: 'bg-slate-100', text: 'text-slate-500' },
    error: { bg: 'bg-red-100', text: 'text-red-500' },
  }
  const { bg, text } = colours[icon]

  return (
    <div className="w-full max-w-sm">
      <div className="rounded-2xl bg-white shadow-sm border border-slate-100 p-8 space-y-4 text-center">
        <div className={`w-12 h-12 ${bg} ${text} rounded-full flex items-center justify-center mx-auto`}>
          {icon === 'success' && (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6" aria-hidden="true">
              <path d="M20 6L9 17l-5-5" />
            </svg>
          )}
          {icon === 'info' && (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
          )}
          {icon === 'error' && (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <path d="M15 9l-6 6M9 9l6 6" />
            </svg>
          )}
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900">{title}</p>
          <p className="text-sm text-slate-500 mt-1">{message}</p>
        </div>
        <Link
          to={linkTo}
          className="block w-full py-3 px-4 bg-teal-600 text-white rounded-xl font-medium min-h-[44px] hover:bg-teal-700 transition-colors text-sm"
        >
          {linkLabel}
        </Link>
      </div>
    </div>
  )
}

// ── InviteAcceptancePage ───────────────────────────────────────────────────

export function InviteAcceptancePage() {
  const { token } = useParams<{ token: string }>()
  const { isAuthenticated, isLoading: authLoading, loginWithRedirect } = useAuth0()
  const navigate = useNavigate()
  useAuthToken()

  const [outcome, setOutcome] = useState<'accepted' | 'declined' | null>(null)
  const autoTriggered = useRef(false)

  const accept = useAcceptInvitation(token ?? '')
  const decline = useDeclineInvitation(token ?? '')

  const {
    data: inviteInfo,
    isLoading: inviteLoading,
    isError,
    error,
  } = useQuery<InviteTokenInfo, AxiosError>({
    queryKey: ['invite-token', token],
    queryFn: async () => {
      // This is a public endpoint — no auth header needed
      const { data } = await api.get(`/invite/${token}`, {
        headers: { Authorization: undefined },
      })
      return data
    },
    enabled: !!token,
    retry: false,
  })

  // Store action intent and redirect to OAuth when not authenticated
  function requireAuth(action: 'accept' | 'decline') {
    sessionStorage.setItem('pending_invite_action', action)
    sessionStorage.setItem('post_auth_return', `/invite/${token}`)
    loginWithRedirect({
      appState: { returnTo: `/invite/${token}` },
    }).catch(console.error)
  }

  // Auto-trigger stored action after OAuth return (avoids double-click)
  useEffect(() => {
    if (autoTriggered.current) return
    if (!isAuthenticated || !inviteInfo || inviteInfo.status !== 'PENDING' || outcome !== null) return
    const pendingAction = sessionStorage.getItem('pending_invite_action')
    if (!pendingAction) return
    autoTriggered.current = true
    sessionStorage.removeItem('pending_invite_action')
    if (pendingAction === 'accept') {
      accept.mutate(undefined, { onSuccess: () => void navigate('/') })
    } else if (pendingAction === 'decline') {
      decline.mutate(undefined, { onSuccess: () => setOutcome('declined') })
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, inviteInfo, outcome])

  async function handleAccept() {
    if (!isAuthenticated) { requireAuth('accept'); return }
    try {
      await accept.mutateAsync()
      navigate('/')
    } catch {
      // error shown via accept.isError
    }
  }

  async function handleDecline() {
    if (!isAuthenticated) { requireAuth('decline'); return }
    try {
      await decline.mutateAsync()
      setOutcome('declined')
    } catch {
      // error shown via decline.isError
    }
  }

  const isPageLoading = authLoading || inviteLoading
  const errorStatus = (error as AxiosError)?.response?.status
  const notFoundError = errorStatus === 404
  const inactiveError = errorStatus === 410

  const relLabel = inviteInfo
    ? (inviteInfo.relationship.charAt(0).toUpperCase() +
        inviteInfo.relationship.slice(1).toLowerCase())
    : ''

  return (
    <div className="min-h-screen bg-gradient-to-b from-teal-50 to-white flex flex-col items-center justify-center px-4 font-['Manrope',sans-serif]">
      {isPageLoading && <InviteSkeleton />}

      {!isPageLoading && notFoundError && (
        <OutcomeCard
          icon="error"
          title="Invalid invitation"
          message="This invitation link is invalid or doesn't exist."
          linkTo="/"
          linkLabel="Go to MediVault"
        />
      )}

      {!isPageLoading && isError && inactiveError && (
        <OutcomeCard
          icon="info"
          title="Invitation no longer active"
          message="This invitation has already been accepted, declined, or expired."
          linkTo="/"
          linkLabel="Go to MediVault"
        />
      )}

      {!isPageLoading && isError && !notFoundError && !inactiveError && (
        <OutcomeCard
          icon="error"
          title="Something went wrong"
          message="We couldn't load this invitation. Please try again later."
          linkTo="/"
          linkLabel="Go to MediVault"
        />
      )}

      {!isPageLoading && inviteInfo && inviteInfo.status === 'PENDING' && outcome === 'accepted' && (
        <OutcomeCard
          icon="success"
          title="Welcome to the family!"
          message="You've successfully joined the family circle."
          linkTo="/family"
          linkLabel="View Family Circle"
        />
      )}

      {!isPageLoading && inviteInfo && inviteInfo.status === 'PENDING' && outcome === 'declined' && (
        <OutcomeCard
          icon="info"
          title="Invitation declined"
          message="You've declined the invitation."
          linkTo="/"
          linkLabel="Go to MediVault"
        />
      )}

      {!isPageLoading && inviteInfo && inviteInfo.status === 'PENDING' && outcome === null && (
        <div className="w-full max-w-sm">
          {/* Logo area */}
          <div className="flex flex-col items-center mb-8 space-y-3">
            <FamilyIcon />
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Family Invitation</h1>
            <p className="text-sm text-slate-500 text-center">MediVault</p>
          </div>

          {/* Invitation card */}
          <div className="rounded-2xl bg-white shadow-sm border border-slate-100 p-8 space-y-5">
            <p className="text-sm text-slate-700 text-center leading-relaxed">
              <strong className="text-teal-700">{inviteInfo.inviter_name}</strong> has invited
              you to join their MediVault family as{' '}
              <strong className="text-slate-900">{relLabel}</strong>.
            </p>

            <div className="flex items-center gap-2 bg-slate-50 rounded-xl px-4 py-3 text-xs text-slate-500">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 shrink-0 text-slate-400" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
              Expires {new Date(inviteInfo.expires_at).toLocaleDateString()}
            </div>

            {/* Action errors */}
            {accept.isError && (
              <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg text-center">
                Failed to accept the invitation. Please try again.
              </p>
            )}
            {decline.isError && (
              <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg text-center">
                Failed to decline the invitation. Please try again.
              </p>
            )}

            {!isAuthenticated && (
              <p className="text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded-lg text-center">
                You'll need to sign in to accept or decline this invitation.
              </p>
            )}

            {/* Accept button */}
            <button
              type="button"
              onClick={handleAccept}
              disabled={accept.isPending || decline.isPending}
              className="w-full py-3 px-4 bg-teal-600 text-white rounded-xl font-medium min-h-[44px] hover:bg-teal-700 transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 flex items-center justify-center gap-2 text-sm"
            >
              {accept.isPending ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Accepting…
                </>
              ) : (
                'Accept Invitation'
              )}
            </button>

            {/* Decline button */}
            <button
              type="button"
              onClick={handleDecline}
              disabled={accept.isPending || decline.isPending}
              className="w-full py-3 px-4 border border-slate-200 text-slate-600 rounded-xl font-medium min-h-[44px] hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-2 disabled:opacity-50 text-sm"
            >
              {decline.isPending ? 'Declining…' : 'Decline'}
            </button>
          </div>

          {/* Trust signal */}
          <p className="mt-6 text-xs text-slate-400 text-center">
            Your health data stays private and secure.
          </p>
        </div>
      )}
    </div>
  )
}
