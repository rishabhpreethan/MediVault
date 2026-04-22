/**
 * Provider Dashboard — MV-159
 *
 * Route: /provider  (PROVIDER role only)
 *
 * States:
 *   idle       — passport UUID entry form
 *   waiting    — polled access request pending
 *   accepted   — redirect to patient view
 *   declined   — error state with retry
 *   expired    — error state with retry
 */
import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../lib/api'

type RequestState = 'idle' | 'waiting' | 'accepted' | 'declined' | 'expired' | 'error'

export function ProviderDashboardPage() {
  const [passportId, setPassportId] = useState('')
  const [requestId, setRequestId] = useState<string | null>(null)
  const [reqState, setReqState] = useState<RequestState>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const navigate = useNavigate()

  // ── Clean up poll on unmount ───────────────────────────────────────────────
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  // ── Poll while waiting ─────────────────────────────────────────────────────
  useEffect(() => {
    if (reqState !== 'waiting' || !requestId) return

    pollRef.current = setInterval(async () => {
      try {
        const { data } = await api.get(`/provider/access-requests/${requestId}/status`)
        if (data.status === 'ACCEPTED') {
          clearInterval(pollRef.current!)
          setReqState('accepted')
          navigate(`/provider/patient/${requestId}`)
        } else if (data.status === 'DECLINED') {
          clearInterval(pollRef.current!)
          setReqState('declined')
        } else if (data.status === 'EXPIRED') {
          clearInterval(pollRef.current!)
          setReqState('expired')
        }
      } catch {
        // ignore transient network errors during poll
      }
    }, 3000)

    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [reqState, requestId, navigate])

  // ── Submit passport lookup ─────────────────────────────────────────────────
  async function handleLookup(e: React.FormEvent) {
    e.preventDefault()
    if (!passportId.trim()) return

    setSubmitting(true)
    setErrorMsg('')
    try {
      const { data } = await api.post('/provider/patient-lookup', {
        passport_id: passportId.trim(),
      })
      setRequestId(data.request_id)
      setReqState('waiting')
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setErrorMsg(detail ?? 'Failed to look up passport. Please check the UUID and try again.')
      setReqState('error')
    } finally {
      setSubmitting(false)
    }
  }

  function handleRetry() {
    setReqState('idle')
    setRequestId(null)
    setErrorMsg('')
    setPassportId('')
  }

  // ── Waiting screen ─────────────────────────────────────────────────────────
  if (reqState === 'waiting') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface px-4">
        <div className="bg-white rounded-2xl shadow-lg p-10 max-w-md w-full text-center">
          <div className="w-16 h-16 rounded-full border-4 border-primary border-t-transparent animate-spin mx-auto mb-6" />
          <h2 className="text-xl font-semibold text-slate-800 mb-2 font-manrope">
            Waiting for patient approval
          </h2>
          <p className="text-slate-500 text-sm mb-6">
            The patient has been notified. They have 15 minutes to accept or decline your request.
          </p>
          <button
            onClick={handleRetry}
            className="text-sm text-slate-400 hover:text-slate-600 underline"
          >
            Cancel
          </button>
        </div>
      </div>
    )
  }

  // ── Declined screen ────────────────────────────────────────────────────────
  if (reqState === 'declined') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface px-4">
        <div className="bg-white rounded-2xl shadow-lg p-10 max-w-md w-full text-center">
          <div className="w-14 h-14 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-red-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-slate-800 mb-2 font-manrope">Request Declined</h2>
          <p className="text-slate-500 text-sm mb-6">The patient declined access to their records.</p>
          <button onClick={handleRetry} className="bg-primary text-white rounded-xl px-6 py-2.5 text-sm font-medium hover:bg-teal-700">
            Try Again
          </button>
        </div>
      </div>
    )
  }

  // ── Expired screen ─────────────────────────────────────────────────────────
  if (reqState === 'expired') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface px-4">
        <div className="bg-white rounded-2xl shadow-lg p-10 max-w-md w-full text-center">
          <div className="w-14 h-14 rounded-full bg-amber-50 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-amber-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" />
              <path strokeLinecap="round" d="M12 6v6l4 2" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-slate-800 mb-2 font-manrope">Request Expired</h2>
          <p className="text-slate-500 text-sm mb-6">The 15-minute window has passed without a response.</p>
          <button onClick={handleRetry} className="bg-primary text-white rounded-xl px-6 py-2.5 text-sm font-medium hover:bg-teal-700">
            Try Again
          </button>
        </div>
      </div>
    )
  }

  // ── Error screen ───────────────────────────────────────────────────────────
  if (reqState === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface px-4">
        <div className="bg-white rounded-2xl shadow-lg p-10 max-w-md w-full text-center">
          <div className="w-14 h-14 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-red-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-slate-800 mb-2 font-manrope">Lookup Failed</h2>
          <p className="text-slate-500 text-sm mb-6">{errorMsg}</p>
          <button onClick={handleRetry} className="bg-primary text-white rounded-xl px-6 py-2.5 text-sm font-medium hover:bg-teal-700">
            Try Again
          </button>
        </div>
      </div>
    )
  }

  // ── Idle — passport entry form ─────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-surface">
      {/* Minimal top nav for provider pages */}
      <header className="fixed top-0 w-full z-50 h-14 flex items-center justify-between px-6 bg-white/80 backdrop-blur-md border-b border-teal-500/10 shadow-sm">
        <span className="text-primary font-bold text-base tracking-tight select-none">MediVault</span>
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-teal-600 transition-colors"
        >
          <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4" aria-hidden="true">
            <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-9 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm6 12H5v-1c0-2 4-3.1 6-3.1s6 1.1 6 3.1v1zm3-1h-1v-1c0-1.3-.8-2.4-2-3.2.4-.1.7-.1 1-.1 1.7 0 3 1.3 3 3v1.3h-1z" />
          </svg>
          My Health Vault
        </Link>
      </header>
      <div className="flex items-center justify-center px-4 pt-14 min-h-screen">
      <div className="bg-white rounded-2xl shadow-lg p-10 max-w-md w-full">
        <div className="mb-8 text-center">
          <div className="w-14 h-14 rounded-2xl bg-teal-50 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-primary" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-slate-800 font-manrope">Patient Lookup</h1>
          <p className="text-slate-500 text-sm mt-1">
            Enter the patient's Health Passport UUID to request access to their records.
          </p>
        </div>

        <form onSubmit={handleLookup} className="space-y-4">
          <div>
            <label htmlFor="passport-id" className="block text-sm font-medium text-slate-700 mb-1.5">
              Health Passport UUID
            </label>
            <input
              id="passport-id"
              type="text"
              value={passportId}
              onChange={(e) => setPassportId(e.target.value)}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary font-mono"
              required
            />
            <p className="text-xs text-slate-400 mt-1">
              Ask the patient to share their QR code or paste the UUID from their Passport page.
            </p>
          </div>

          <button
            type="submit"
            disabled={submitting || !passportId.trim()}
            className="w-full bg-primary text-white rounded-xl py-3 text-sm font-semibold hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? 'Sending request…' : 'Request Access'}
          </button>
        </form>
      </div>
    </div>
    </div>
  )
}
