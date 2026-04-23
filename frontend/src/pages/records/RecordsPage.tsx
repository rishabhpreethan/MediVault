import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../../lib/api'
import { useResolvedMemberId } from '../../hooks/useFamily'
import { TimelineTab } from './TimelineTab'

// ── Types ──────────────────────────────────────────────────────────────────

type DocType = 'LAB_REPORT' | 'PRESCRIPTION' | 'DISCHARGE_SUMMARY' | 'SCAN' | 'OTHER'
type ProcessingStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETE' | 'FAILED' | 'MANUAL_REVIEW'

interface DocumentItem {
  document_id: string
  document_type: DocType
  document_date: string | null
  processing_status: ProcessingStatus
  doctor_name: string | null
  facility_name: string | null
  uploaded_at: string
}

interface DocumentListResponse {
  items: DocumentItem[]
  total: number
}

// ── Helpers ────────────────────────────────────────────────────────────────

function docTypeLabel(t: DocType): string {
  switch (t) {
    case 'LAB_REPORT': return 'Lab Report'
    case 'PRESCRIPTION': return 'Prescription'
    case 'DISCHARGE_SUMMARY': return 'Discharge Summary'
    case 'SCAN': return 'Imaging'
    default: return 'Other'
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' })
}

// ── Status badge ───────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: ProcessingStatus }) {
  const styles: Record<ProcessingStatus, string> = {
    COMPLETE: 'bg-primary/10 text-primary',
    PROCESSING: 'bg-amber-100 text-amber-700',
    QUEUED: 'bg-amber-100 text-amber-700',
    FAILED: 'bg-error-container text-error',
    MANUAL_REVIEW: 'bg-surface-container text-on-surface-variant',
  }
  const labels: Record<ProcessingStatus, string> = {
    COMPLETE: 'Complete',
    PROCESSING: 'Processing',
    QUEUED: 'Queued',
    FAILED: 'Failed',
    MANUAL_REVIEW: 'Review',
  }
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${styles[status]}`}>
      {labels[status]}
    </span>
  )
}

// ── Documents tab ──────────────────────────────────────────────────────────

function DocumentsTab({ memberId }: { memberId: string }) {
  const { data, isLoading, isError } = useQuery<DocumentListResponse>({
    queryKey: ['documents', memberId],
    queryFn: async () => {
      const { data } = await api.get(`/documents/${memberId}`)
      return data
    },
    enabled: !!memberId,
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="bg-surface-container-lowest rounded-xl p-4 animate-pulse h-20" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-xl bg-error-container px-5 py-4 text-sm text-error font-medium">
        Failed to load documents. Please try again.
      </div>
    )
  }

  const docs = data?.items ?? []

  if (docs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-14 h-14 rounded-2xl bg-surface-container flex items-center justify-center mb-4">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-on-surface-variant" aria-hidden="true">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
        </div>
        <p className="text-base font-bold text-on-surface">No documents yet</p>
        <p className="text-sm text-on-surface-variant mt-1 max-w-xs">
          Document upload is coming soon. Your uploaded PDFs will appear here once the feature is live.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {docs.map((doc) => (
        <Link
          key={doc.document_id}
          to={`/records/${doc.document_id}`}
          className="block bg-surface-container-lowest rounded-xl px-5 py-4 shadow-sm shadow-teal-900/5 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-sm font-bold text-on-surface">{docTypeLabel(doc.document_type)}</p>
              <p className="text-xs text-on-surface-variant mt-0.5">
                {formatDate(doc.document_date ?? doc.uploaded_at)}
                {doc.doctor_name && ` · ${doc.doctor_name}`}
                {doc.facility_name && ` · ${doc.facility_name}`}
              </p>
            </div>
            <StatusBadge status={doc.processing_status} />
          </div>
        </Link>
      ))}
    </div>
  )
}

// ── Coming Soon modal ──────────────────────────────────────────────────────

function ComingSoonModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary flex-shrink-0">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          </div>
          <p className="text-base font-extrabold text-on-surface">Document Upload — Coming Soon</p>
        </div>
        <p className="text-sm text-on-surface-variant leading-relaxed">
          Upload your medical PDFs — prescriptions, lab reports, discharge summaries — and MediVault will automatically extract your medications, diagnoses, and test results into your health profile.
        </p>
        <button
          type="button"
          onClick={onClose}
          className="w-full min-h-[44px] rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors"
        >
          Got it
        </button>
      </div>
    </div>
  )
}

// ── RecordsPage ────────────────────────────────────────────────────────────

type Tab = 'timeline' | 'documents'

export function RecordsPage() {
  const memberId = useResolvedMemberId()
  const [activeTab, setActiveTab] = useState<Tab>('timeline')
  const [showComingSoon, setShowComingSoon] = useState(false)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">Records</h1>
          <p className="text-sm text-on-surface-variant mt-1">Your clinical history and uploaded documents</p>
        </div>
        <button
          type="button"
          onClick={() => setShowComingSoon(true)}
          className="shrink-0 inline-flex items-center gap-2 min-h-[40px] px-4 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4" aria-hidden="true">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Import
        </button>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 bg-surface-container rounded-xl p-1 w-fit">
        {(['timeline', 'documents'] as Tab[]).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold capitalize transition-colors min-h-[36px] ${
              activeTab === tab
                ? 'bg-white text-primary shadow-sm'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            {tab === 'timeline' ? 'Timeline' : 'Documents'}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'timeline' && <TimelineTab />}
      {activeTab === 'documents' && memberId && <DocumentsTab memberId={memberId} />}

      {/* Coming Soon modal */}
      {showComingSoon && <ComingSoonModal onClose={() => setShowComingSoon(false)} />}
    </div>
  )
}
