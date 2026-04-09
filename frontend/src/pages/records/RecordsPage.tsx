import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { useResolvedMemberId } from '../../hooks/useFamily'
import type { Document, ProcessingStatus } from '../../types'

// ── Types ──────────────────────────────────────────────────────────────────

interface DocumentsResponse {
  items: Document[]
  total: number
  page: number
  page_size: number
}

// ── Helpers ────────────────────────────────────────────────────────────────


function getStatusBadge(status: ProcessingStatus): {
  label: string
  className: string
} {
  switch (status) {
    case 'COMPLETE':
      return {
        label: 'VERIFIED CLINICAL',
        className: 'bg-primary text-white',
      }
    case 'FAILED':
    case 'MANUAL_REVIEW':
      return {
        label: 'OBSERVATION REQUIRED',
        className: 'bg-tertiary-container text-tertiary',
      }
    case 'PROCESSING':
    case 'QUEUED':
    default:
      return {
        label: 'PROCESSING',
        className: 'bg-slate-100 text-slate-600 animate-pulse',
      }
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function getDocTypeLabel(type: Document['document_type']): string {
  switch (type) {
    case 'LAB_REPORT':
      return 'Lab Report'
    case 'PRESCRIPTION':
      return 'Prescription'
    case 'DISCHARGE':
      return 'Discharge Summary'
    case 'SCAN':
      return 'Imaging / Scan'
    default:
      return 'Document'
  }
}

// ── Sub-components ─────────────────────────────────────────────────────────

/** Decorative mini bar chart in teal. Static/decorative only. */
function MiniBarChart() {
  // Heights (in px) for 8 decorative bars
  const bars = [18, 28, 22, 35, 26, 40, 30, 38]
  return (
    <svg
      viewBox="0 0 80 44"
      className="w-20 h-11"
      aria-hidden="true"
    >
      {bars.map((h, i) => (
        <rect
          key={i}
          x={i * 10 + 1}
          y={44 - h}
          width={7}
          height={h}
          rx={2}
          fill="currentColor"
          className="text-primary-fixed"
        />
      ))}
    </svg>
  )
}

/** Icon that represents a document type inside a colored circle. */
function DocTypeIcon({ type }: { type: Document['document_type'] }) {
  const colorMap: Record<Document['document_type'], string> = {
    LAB_REPORT: 'bg-primary-fixed text-primary',
    PRESCRIPTION: 'bg-secondary-container text-secondary',
    DISCHARGE: 'bg-tertiary-container text-tertiary',
    SCAN: 'bg-surface-container-high text-on-surface-variant',
    OTHER: 'bg-surface-container-high text-on-surface-variant',
  }
  const cls = colorMap[type] ?? colorMap['OTHER']

  return (
    <div
      className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${cls}`}
      aria-hidden="true"
    >
      {type === 'LAB_REPORT' && (
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
          <path d="M9 3v11.5a3.5 3.5 0 0 0 7 0V3h-2v11.5a1.5 1.5 0 0 1-3 0V3H9zM7 2h10a1 1 0 0 1 1 1v12.5a5.5 5.5 0 0 1-11 0V3a1 1 0 0 1 1-1z" />
        </svg>
      )}
      {type === 'PRESCRIPTION' && (
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
          <path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zm-7 3a1 1 0 0 1 1 1v2h2a1 1 0 1 1 0 2h-2v2a1 1 0 1 1-2 0v-2H9a1 1 0 1 1 0-2h2V7a1 1 0 0 1 1-1zm-4 9h8a1 1 0 1 1 0 2H8a1 1 0 1 1 0-2z" />
        </svg>
      )}
      {type === 'DISCHARGE' && (
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6zm2-5h8v1.5H8V15zm0 2.5h5v1.5H8V17.5z" />
        </svg>
      )}
      {(type === 'SCAN' || type === 'OTHER') && (
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z" />
        </svg>
      )}
    </div>
  )
}

/** Single document card in the Recent Curations list. */
function DocumentCard({ doc }: { doc: Document }) {
  const badge = getStatusBadge(doc.processing_status)

  return (
    <div className="bg-surface-container-lowest rounded-xl p-4 shadow-sm shadow-teal-900/5 flex gap-3 items-start">
      {/* Icon */}
      <DocTypeIcon type={doc.document_type} />

      {/* Main content */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-sm font-bold text-on-surface truncate">
              {getDocTypeLabel(doc.document_type)}
            </p>
            <p className="text-xs text-on-surface-variant mt-0.5">
              {formatDate(doc.document_date ?? doc.uploaded_at)}
              {doc.facility_name ? ` · ${doc.facility_name}` : ''}
            </p>
          </div>
          {/* Status badge */}
          <span
            className={`text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full whitespace-nowrap ${badge.className}`}
          >
            {badge.label}
          </span>
        </div>

        {/* Analysis summary (placeholder text — real text comes from NLP in MV-026) */}
        <p className="text-xs text-on-surface-variant mt-2 line-clamp-2">
          {doc.processing_status === 'COMPLETE'
            ? 'Extraction complete. Key clinical markers identified and catalogued in your health profile.'
            : doc.processing_status === 'FAILED'
              ? 'Extraction failed. Manual review required to retrieve clinical data from this document.'
              : doc.processing_status === 'MANUAL_REVIEW'
                ? 'Low-confidence extraction flagged for manual review. Some markers may require verification.'
                : 'Document queued for extraction. Clinical markers will appear shortly.'}
        </p>

        {/* Footer row: key metrics + full analysis link */}
        <div className="flex items-center justify-between mt-2 gap-2">
          <span className="text-xs font-semibold text-on-surface-variant/70 font-mono">
            {doc.processing_status === 'COMPLETE'
              ? '— · —'
              : doc.processing_status === 'PROCESSING' || doc.processing_status === 'QUEUED'
                ? 'Pending...'
                : 'N/A'}
          </span>
          <button
            type="button"
            className="text-xs font-semibold text-primary hover:underline whitespace-nowrap min-h-[28px] flex items-center focus:outline-none focus:ring-2 focus:ring-primary/30 rounded"
            aria-label={`View full analysis for document ${doc.document_id}`}
          >
            Full Analysis →
          </button>
        </div>
      </div>
    </div>
  )
}

/** Skeleton placeholder card shown while loading. */
function SkeletonCard() {
  return (
    <div className="bg-surface-container-lowest rounded-xl p-4 shadow-sm shadow-teal-900/5 flex gap-3 items-start animate-pulse">
      <div className="w-10 h-10 rounded-full bg-surface-container flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-3.5 bg-surface-container rounded w-2/5" />
        <div className="h-2.5 bg-surface-container rounded w-1/3" />
        <div className="h-2.5 bg-surface-container rounded w-full mt-2" />
        <div className="h-2.5 bg-surface-container rounded w-4/5" />
        <div className="flex justify-between mt-2">
          <div className="h-2.5 bg-surface-container rounded w-16" />
          <div className="h-2.5 bg-surface-container rounded w-20" />
        </div>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────

export function RecordsPage() {
  const memberId = useResolvedMemberId()

  const fileInputRef = useRef<HTMLInputElement>(null)
  const [search, setSearch] = useState('')

  const { data, isLoading, isError } = useQuery<DocumentsResponse>({
    queryKey: ['documents', memberId],
    queryFn: async () => {
      const { data } = await api.get('/documents/', {
        params: { member_id: memberId, page: 1, page_size: 20 },
      })
      return data
    },
    enabled: !!memberId,
  })

  const documents = data?.items ?? []

  const filteredDocs = search.trim()
    ? documents.filter((doc) => {
        const q = search.toLowerCase()
        return (
          getDocTypeLabel(doc.document_type).toLowerCase().includes(q) ||
          (doc.facility_name ?? '').toLowerCase().includes(q) ||
          (doc.doctor_name ?? '').toLowerCase().includes(q)
        )
      })
    : documents

  function handleImportClick() {
    fileInputRef.current?.click()
  }

  return (
    <div className="space-y-6">
      {/* Hidden file input — upload flow wired in MV-025 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        aria-hidden="true"
        tabIndex={-1}
      />

      {/* ── Page header ───────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">
            Clinical Archive
          </h1>
          <p className="text-sm text-on-surface-variant mt-1">
            Your complete medical document library — extracted and indexed
          </p>
        </div>
        <button
          type="button"
          onClick={handleImportClick}
          className="bg-primary text-white font-semibold rounded-full px-5 py-2.5 hover:bg-primary/90 transition-colors shadow-sm shadow-teal-900/10 min-h-[44px] flex items-center gap-2 self-start whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-primary/40"
          aria-label="Import a new medical record"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4"
            aria-hidden="true"
          >
            <path d="M12 5v14M5 12l7-7 7 7" />
          </svg>
          Import Record
        </button>
      </div>

      {/* ── Banner row: Extraction accuracy + Active Markers ─────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Extraction accuracy panel */}
        <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm shadow-teal-900/5 flex flex-col justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant mb-1">
              Extraction Accuracy
            </p>
            <div className="flex items-end gap-3">
              <span className="text-5xl font-extrabold text-primary leading-none">
                99.4%
              </span>
              <MiniBarChart />
            </div>
          </div>
          <p className="text-xs text-on-surface-variant leading-relaxed">
            Parsed from{' '}
            <span className="font-semibold text-on-surface">142</span> historical
            documents using pdfminer.six + Med7 NLP pipeline.
          </p>
        </div>

        {/* Active Markers panel */}
        <div className="bg-primary rounded-xl p-5 shadow-sm shadow-teal-900/10 flex flex-col justify-between gap-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-primary-fixed">
            Active Markers
          </p>
          <div className="space-y-2.5">
            {/* Glucose / HbA1c */}
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-bold text-white">
                  Glucose HbA1c
                </p>
                <p className="text-xs text-primary-fixed/80">
                  Last checked 14 days ago
                </p>
              </div>
              <span className="text-[10px] font-semibold uppercase tracking-wide bg-primary-fixed text-primary px-2.5 py-1 rounded-full">
                Stable
              </span>
            </div>

            {/* Lipid Profile */}
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-bold text-white">Lipid Profile</p>
                <p className="text-xs text-primary-fixed/80">
                  Last checked 30 days ago
                </p>
              </div>
              <span className="text-[10px] font-semibold uppercase tracking-wide bg-tertiary-container text-tertiary px-2.5 py-1 rounded-full">
                Attention
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Recent Curations ──────────────────────────────────────────── */}
      <section aria-labelledby="curations-heading">
        {/* Section header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <h2
            id="curations-heading"
            className="text-lg font-extrabold text-on-surface tracking-tight"
          >
            Recent Curations
          </h2>

          {/* Search box */}
          <div className="relative w-full sm:w-64">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/50 pointer-events-none"
              aria-hidden="true"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
            <input
              type="search"
              placeholder="Search records…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm rounded-full bg-surface-container-lowest shadow-sm shadow-teal-900/5 text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-primary/30"
              aria-label="Search clinical records"
            />
          </div>
        </div>

        {/* Document list */}
        <div className="space-y-3">
          {/* Loading state: 3 skeletons */}
          {isLoading && (
            <>
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </>
          )}

          {/* Error state */}
          {isError && !isLoading && (
            <div className="bg-error-container rounded-xl p-5 text-center">
              <p className="text-sm font-semibold text-error">
                Failed to load documents. Please try again.
              </p>
            </div>
          )}

          {/* Empty state */}
          {!isLoading && !isError && filteredDocs.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center bg-surface-container-lowest rounded-xl shadow-sm shadow-teal-900/5">
              <div className="w-14 h-14 rounded-2xl bg-surface-container flex items-center justify-center mb-4">
                <svg
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="w-7 h-7 text-primary/40"
                  aria-hidden="true"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z" />
                </svg>
              </div>
              <p className="text-base font-bold text-on-surface">
                {search.trim() ? 'No matching records' : 'No records yet'}
              </p>
              <p className="text-sm text-on-surface-variant mt-1 max-w-xs">
                {search.trim()
                  ? 'Try a different search term or clear the filter.'
                  : 'Import a clinical record to get started. Supported format: PDF.'}
              </p>
              {!search.trim() && (
                <button
                  type="button"
                  onClick={handleImportClick}
                  className="mt-5 bg-primary text-white font-semibold rounded-full px-5 py-2.5 hover:bg-primary/90 transition-colors shadow-sm shadow-teal-900/10 min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/40"
                >
                  Import Record
                </button>
              )}
            </div>
          )}

          {/* Document cards */}
          {!isLoading &&
            !isError &&
            filteredDocs.map((doc) => (
              <DocumentCard key={doc.document_id} doc={doc} />
            ))}
        </div>
      </section>
    </div>
  )
}
