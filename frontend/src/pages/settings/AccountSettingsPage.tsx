import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useAuth0 } from '@auth0/auth0-react'
import { api } from '../../lib/api'

// ── Types ──────────────────────────────────────────────────────────────────

interface ExportRequestResponse {
  job_id: string
  message: string
}

interface ExportStatusResponse {
  status: 'PENDING' | 'COMPLETE' | 'FAILED'
  download_url: string | null
}

// ── Inline SVG Icons ───────────────────────────────────────────────────────

function IconDownload() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-5 h-5"
      aria-hidden="true"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  )
}

function IconTrash() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-5 h-5"
      aria-hidden="true"
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6M14 11v6" />
      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
    </svg>
  )
}

function IconWarning() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-5 h-5"
      aria-hidden="true"
    >
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  )
}

function IconCheck() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-5 h-5"
      aria-hidden="true"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}

function IconSpinner() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-5 h-5 animate-spin"
      aria-hidden="true"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  )
}

// ── Delete Account Modal ───────────────────────────────────────────────────

interface DeleteAccountModalProps {
  onClose: () => void
  onConfirm: () => void
  isLoading: boolean
}

function DeleteAccountModal({ onClose, onConfirm, isLoading }: DeleteAccountModalProps) {
  const [confirmText, setConfirmText] = useState('')
  const isConfirmed = confirmText === 'DELETE'

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-modal-title"
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-red-100 flex items-center justify-center text-red-600">
              <IconWarning />
            </div>
            <h2 id="delete-modal-title" className="text-lg font-bold text-on-surface">
              Delete Account
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-surface-container transition-colors disabled:opacity-50"
            aria-label="Close modal"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 text-on-surface-variant" aria-hidden="true">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Warning body */}
        <div className="rounded-xl bg-red-50 border border-red-100 p-4 mb-5">
          <p className="text-sm text-red-800 font-medium leading-relaxed">
            This action is <strong>permanent and irreversible</strong>. Deleting your account will:
          </p>
          <ul className="mt-2 space-y-1 text-sm text-red-700 list-disc list-inside">
            <li>Remove all your medical records and documents</li>
            <li>Delete your health profile and timeline</li>
            <li>Revoke all active Health Passports</li>
            <li>Cancel any pending data exports</li>
          </ul>
        </div>

        {/* Confirmation input */}
        <div className="mb-6">
          <label htmlFor="delete-confirm-input" className="block text-sm font-semibold text-on-surface mb-2">
            Type <span className="font-mono font-bold text-red-600">DELETE</span> to confirm
          </label>
          <input
            id="delete-confirm-input"
            type="text"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder="DELETE"
            disabled={isLoading}
            className="w-full px-4 py-3 rounded-xl border border-outline-variant/30 text-sm font-mono font-semibold text-on-surface bg-white focus:outline-none focus:ring-2 focus:ring-red-500/40 focus:border-red-400 disabled:opacity-50 transition-colors"
            autoComplete="off"
          />
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 min-h-[44px] rounded-xl border-2 border-outline-variant text-on-surface-variant text-sm font-semibold hover:border-primary/50 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={!isConfirmed || isLoading}
            className="flex-1 min-h-[44px] px-5 py-3 rounded-xl bg-red-600 text-white text-sm font-semibold hover:bg-red-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <IconSpinner />
                Deleting…
              </>
            ) : (
              <>
                <IconTrash />
                Delete Account
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Data Export Card ───────────────────────────────────────────────────────

function DataExportCard() {
  const [jobId, setJobId] = useState<string | null>(null)
  const [requestError, setRequestError] = useState<string | null>(null)

  // Mutation: POST /export/request-all
  const requestExportMutation = useMutation<ExportRequestResponse, Error>({
    mutationFn: async () => {
      const { data } = await api.post<ExportRequestResponse>('/export/request-all')
      return data
    },
    onSuccess: (data) => {
      setJobId(data.job_id)
      setRequestError(null)
    },
    onError: () => {
      setRequestError('Failed to queue export. Please try again.')
    },
  })

  // Poll: GET /export/status/{job_id} — stops when COMPLETE or FAILED
  const { data: exportStatus } = useQuery<ExportStatusResponse>({
    queryKey: ['export-status', jobId],
    queryFn: async () => {
      const { data } = await api.get<ExportStatusResponse>(`/export/status/${jobId}`)
      return data
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'COMPLETE' || status === 'FAILED') return false
      return 3000
    },
  })

  const isPending = requestExportMutation.isPending
  const isQueued = !!jobId && exportStatus?.status === 'PENDING'
  const isComplete = exportStatus?.status === 'COMPLETE'
  const isFailed = exportStatus?.status === 'FAILED'

  function handleReset() {
    setJobId(null)
    setRequestError(null)
    requestExportMutation.reset()
  }

  return (
    <div className="bg-white rounded-2xl shadow-[0_4px_24px_rgba(0,107,95,0.10)] p-6">
      {/* Card header */}
      <div className="flex items-start gap-4 mb-4">
        <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary flex-shrink-0">
          <IconDownload />
        </div>
        <div>
          <h2 className="text-base font-bold text-on-surface">Export My Data</h2>
          <p className="text-sm text-on-surface-variant mt-0.5">
            Download a complete copy of your medical records, lab results, and health profile as a structured archive.
          </p>
        </div>
      </div>

      <div className="pt-4 border-t border-outline-variant/30">
        {/* Idle state */}
        {!jobId && !requestError && (
          <button
            type="button"
            onClick={() => requestExportMutation.mutate()}
            disabled={isPending}
            className="inline-flex items-center gap-2 min-h-[44px] px-5 py-3 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors disabled:opacity-60"
          >
            {isPending ? (
              <>
                <IconSpinner />
                Requesting…
              </>
            ) : (
              <>
                <IconDownload />
                Request Export
              </>
            )}
          </button>
        )}

        {/* Request error */}
        {requestError && (
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-red-50 border border-red-100 px-4 py-3 flex-1 text-sm text-red-700 font-medium">
              {requestError}
            </div>
            <button
              type="button"
              onClick={handleReset}
              className="min-h-[44px] px-4 rounded-xl border-2 border-outline-variant text-on-surface-variant text-sm font-semibold hover:border-primary/50 transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Queued / Polling state */}
        {isQueued && (
          <div className="flex items-center gap-3 rounded-xl bg-primary/5 border border-primary/20 px-4 py-3">
            <IconSpinner />
            <div>
              <p className="text-sm font-semibold text-primary">Export queued</p>
              <p className="text-xs text-on-surface-variant mt-0.5">
                Preparing your data archive… This may take a minute.
              </p>
            </div>
          </div>
        )}

        {/* Complete state */}
        {isComplete && exportStatus?.download_url && (
          <div className="space-y-3">
            <div className="flex items-center gap-3 rounded-xl bg-primary/5 border border-primary/20 px-4 py-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary flex-shrink-0">
                <IconCheck />
              </div>
              <div>
                <p className="text-sm font-semibold text-primary">Export ready</p>
                <p className="text-xs text-on-surface-variant mt-0.5">Your archive has been prepared.</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <a
                href={exportStatus.download_url}
                download
                className="inline-flex items-center gap-2 min-h-[44px] px-5 py-3 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors"
              >
                <IconDownload />
                Download Archive
              </a>
              <button
                type="button"
                onClick={handleReset}
                className="min-h-[44px] px-4 rounded-xl border-2 border-outline-variant text-on-surface-variant text-sm font-semibold hover:border-primary/50 transition-colors"
              >
                New Export
              </button>
            </div>
          </div>
        )}

        {/* Failed state */}
        {isFailed && (
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-red-50 border border-red-100 px-4 py-3 flex-1 text-sm text-red-700 font-medium">
              Export failed. Please try requesting a new export.
            </div>
            <button
              type="button"
              onClick={handleReset}
              className="min-h-[44px] px-4 rounded-xl border-2 border-outline-variant text-on-surface-variant text-sm font-semibold hover:border-primary/50 transition-colors"
            >
              Retry
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Danger Zone Card ───────────────────────────────────────────────────────

function DangerZoneCard() {
  const [showModal, setShowModal] = useState(false)
  const [deleted, setDeleted] = useState(false)
  const { logout } = useAuth0()

  const deleteMutation = useMutation<void, Error>({
    mutationFn: async () => {
      await api.delete('/auth/account')
    },
    onSuccess: () => {
      setShowModal(false)
      setDeleted(true)
      // Log out via Auth0 after 3 seconds
      setTimeout(() => {
        void logout({ logoutParams: { returnTo: window.location.origin } })
      }, 3000)
    },
  })

  return (
    <>
      {showModal && (
        <DeleteAccountModal
          onClose={() => setShowModal(false)}
          onConfirm={() => deleteMutation.mutate()}
          isLoading={deleteMutation.isPending}
        />
      )}

      <div className="bg-white rounded-2xl shadow-[0_4px_24px_rgba(0,107,95,0.10)] overflow-hidden">
        {/* Red-tinted card header */}
        <div className="bg-red-50 border-b border-red-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-red-100 flex items-center justify-center text-red-600 flex-shrink-0">
              <IconWarning />
            </div>
            <div>
              <h2 className="text-base font-bold text-red-900">Danger Zone</h2>
              <p className="text-xs text-red-600 font-medium mt-0.5">
                Actions here are permanent and cannot be undone.
              </p>
            </div>
          </div>
        </div>

        <div className="px-6 py-5">
          {deleted ? (
            /* Success state */
            <div className="flex items-center gap-3 rounded-xl bg-red-50 border border-red-100 px-4 py-3">
              <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 flex-shrink-0">
                <IconCheck />
              </div>
              <div>
                <p className="text-sm font-semibold text-red-900">
                  Your account has been scheduled for deletion
                </p>
                <p className="text-xs text-red-600 mt-0.5">
                  You will be logged out automatically in a moment.
                </p>
              </div>
            </div>
          ) : (
            /* Default state */
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-on-surface">Delete Account</p>
                <p className="text-xs text-on-surface-variant mt-0.5 max-w-sm">
                  Permanently delete your MediVault account and all associated medical records. This cannot be undone.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowModal(true)}
                disabled={deleteMutation.isPending}
                className="inline-flex items-center gap-2 min-h-[44px] px-5 py-3 rounded-xl bg-red-600 text-white text-sm font-semibold hover:bg-red-700 transition-colors disabled:opacity-60 shrink-0"
              >
                <IconTrash />
                Delete Account
              </button>
            </div>
          )}

          {deleteMutation.isError && !deleted && (
            <div className="mt-4 rounded-xl bg-red-50 border border-red-100 px-4 py-3 text-sm text-red-700 font-medium">
              Failed to delete account. Please try again or contact support.
            </div>
          )}
        </div>
      </div>
    </>
  )
}

// ── AccountSettingsPage ────────────────────────────────────────────────────

export function AccountSettingsPage() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">
          Account Settings
        </h1>
        <p className="text-sm text-on-surface-variant mt-1">
          Manage your account data and preferences.
        </p>
      </div>

      {/* Data Export card */}
      <DataExportCard />

      {/* Danger Zone card */}
      <DangerZoneCard />
    </div>
  )
}
