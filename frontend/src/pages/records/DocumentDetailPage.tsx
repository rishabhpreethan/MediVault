import { Link, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'
import type {
  Document,
  LabResult,
  Medication,
  Diagnosis,
  Allergy,
  ProcessingStatus,
  LabFlag,
  ConfidenceScore,
} from '../../types'

const API_BASE: string =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// ── Extended document type with extracted entities ─────────────────────────

interface DocumentDetail extends Document {
  lab_results?: LabResult[]
  medications?: Medication[]
  diagnoses?: Diagnosis[]
  allergies?: Allergy[]
  original_filename?: string
}

// ── Helpers ────────────────────────────────────────────────────────────────

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

function getDocTypePillClass(type: Document['document_type']): string {
  switch (type) {
    case 'LAB_REPORT':
      return 'bg-primary-fixed text-primary'
    case 'PRESCRIPTION':
      return 'bg-secondary-container text-secondary'
    case 'DISCHARGE':
      return 'bg-tertiary-container text-tertiary'
    default:
      return 'bg-surface-container-high text-on-surface-variant'
  }
}

function getStatusBadgeClass(status: ProcessingStatus): string {
  switch (status) {
    case 'COMPLETE':
      return 'bg-primary-fixed text-primary'
    case 'FAILED':
    case 'MANUAL_REVIEW':
      return 'bg-error-container text-error'
    case 'PROCESSING':
    case 'QUEUED':
    default:
      return 'bg-surface-container text-on-surface-variant animate-pulse'
  }
}

function getStatusLabel(status: ProcessingStatus): string {
  switch (status) {
    case 'COMPLETE':
      return 'Verified'
    case 'FAILED':
      return 'Failed'
    case 'MANUAL_REVIEW':
      return 'Manual Review'
    case 'PROCESSING':
      return 'Processing'
    case 'QUEUED':
      return 'Queued'
    default:
      return status
  }
}

function getLabFlagClass(flag: LabFlag): string {
  switch (flag) {
    case 'HIGH':
    case 'CRITICAL':
      return 'bg-error-container text-error'
    case 'LOW':
      return 'bg-tertiary-container text-tertiary'
    case 'NORMAL':
    default:
      return 'bg-primary-fixed text-primary'
  }
}

function getConfidenceBadgeClass(score: ConfidenceScore): string {
  switch (score) {
    case 'HIGH':
      return 'bg-primary-fixed text-primary'
    case 'MEDIUM':
      return 'bg-tertiary-container text-tertiary'
    case 'LOW':
    default:
      return 'bg-surface-container-high text-on-surface-variant'
  }
}

// ── Sub-components ─────────────────────────────────────────────────────────

function SkeletonDetailPage() {
  return (
    <div className="animate-pulse space-y-6">
      {/* Back link skeleton */}
      <div className="h-4 bg-surface-container rounded w-32" />

      <div className="grid grid-cols-1 md:grid-cols-[1fr_1.5fr] gap-6">
        {/* Left panel */}
        <div className="space-y-4">
          <div className="bg-surface-container-lowest rounded-2xl p-6 shadow-sm space-y-4">
            <div className="h-5 bg-surface-container rounded w-3/4" />
            <div className="h-4 bg-surface-container rounded w-1/3" />
            <div className="h-4 bg-surface-container rounded w-1/4" />
            <div className="h-4 bg-surface-container rounded w-2/5" />
          </div>
          <div className="bg-surface-container-lowest rounded-2xl shadow-sm min-h-[400px]" />
        </div>

        {/* Right panel */}
        <div className="space-y-4">
          <div className="h-4 bg-surface-container rounded w-40" />
          <div className="bg-surface-container-lowest rounded-2xl p-6 shadow-sm space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 bg-surface-container rounded" />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function LabResultsTable({ results }: { results: LabResult[] }) {
  if (results.length === 0) return null
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-3">
        Lab Results
      </h3>
      <div className="overflow-x-auto rounded-xl border border-outline-variant">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-container-low text-on-surface-variant text-xs uppercase tracking-wide">
              <th className="text-left px-4 py-2.5 font-semibold">Test</th>
              <th className="text-left px-4 py-2.5 font-semibold">Value</th>
              <th className="text-left px-4 py-2.5 font-semibold">Reference</th>
              <th className="text-left px-4 py-2.5 font-semibold">Flag</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr
                key={r.result_id}
                className="border-t border-outline-variant even:bg-surface-container-low/40"
              >
                <td className="px-4 py-3 font-medium text-on-surface">
                  {r.test_name}
                </td>
                <td className="px-4 py-3 text-on-surface-variant font-mono">
                  {r.value !== null ? `${r.value}` : r.value_text ?? '—'}
                  {r.unit ? ` ${r.unit}` : ''}
                </td>
                <td className="px-4 py-3 text-on-surface-variant font-mono text-xs">
                  {r.reference_low !== null && r.reference_high !== null
                    ? `${r.reference_low} – ${r.reference_high}`
                    : '—'}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full ${getLabFlagClass(r.flag)}`}
                  >
                    {r.flag}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function MedicationsList({ medications }: { medications: Medication[] }) {
  if (medications.length === 0) return null
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-3">
        Medications
      </h3>
      <ul className="space-y-2">
        {medications.map((m) => (
          <li
            key={m.medication_id}
            className="flex items-start gap-3 bg-surface-container-low rounded-xl px-4 py-3"
          >
            {/* Pill icon */}
            <div className="mt-0.5 flex-shrink-0">
              <svg
                viewBox="0 0 24 24"
                fill="currentColor"
                className="w-4 h-4 text-secondary"
                aria-hidden="true"
              >
                <path d="M4.22 11.29l6.07-6.07a5 5 0 0 1 7.07 7.07l-6.07 6.07a5 5 0 0 1-7.07-7.07zm1.41 1.42a3 3 0 0 0 4.24 4.24l2.83-2.83-4.24-4.24-2.83 2.83zm4.24-5.66L7.05 9.87l4.24 4.24 2.83-2.83L9.87 7.05z" />
              </svg>
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-on-surface">{m.drug_name}</p>
              <p className="text-xs text-on-surface-variant mt-0.5">
                {[m.dosage, m.frequency, m.route].filter(Boolean).join(' · ') || '—'}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function DiagnosesList({ diagnoses }: { diagnoses: Diagnosis[] }) {
  if (diagnoses.length === 0) return null
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-3">
        Diagnoses
      </h3>
      <ul className="space-y-2">
        {diagnoses.map((d) => (
          <li
            key={d.diagnosis_id}
            className="flex items-center justify-between gap-3 bg-surface-container-low rounded-xl px-4 py-3"
          >
            <div className="min-w-0">
              <p className="text-sm font-semibold text-on-surface truncate">
                {d.condition_name}
              </p>
              {d.icd10_code && (
                <p className="text-xs text-on-surface-variant font-mono mt-0.5">
                  ICD-10: {d.icd10_code}
                </p>
              )}
            </div>
            <span
              className={`text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full whitespace-nowrap flex-shrink-0 ${getConfidenceBadgeClass(d.confidence_score)}`}
            >
              {d.confidence_score}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function AllergiesList({ allergies }: { allergies: Allergy[] }) {
  if (allergies.length === 0) return null
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-3">
        Allergies
      </h3>
      <div className="flex flex-wrap gap-2">
        {allergies.map((a) => (
          <span
            key={a.allergy_id}
            className="bg-error-container text-error text-xs font-semibold px-3 py-1.5 rounded-full min-h-[28px] flex items-center"
          >
            {a.allergen_name}
            {a.severity !== 'UNKNOWN' && (
              <span className="ml-1.5 opacity-70">· {a.severity}</span>
            )}
          </span>
        ))}
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────

export function DocumentDetailPage() {
  const { documentId } = useParams<{ documentId: string }>()
  const queryClient = useQueryClient()

  const {
    data: doc,
    isLoading,
    isError,
  } = useQuery<DocumentDetail>({
    queryKey: ['document', documentId],
    queryFn: async () => {
      const { data } = await api.get(`/documents/${documentId}`)
      return data
    },
    enabled: !!documentId,
  })

  const retryMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/documents/${documentId}/retry`)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['document', documentId] })
      void queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  if (isLoading) {
    return (
      <div className="px-0">
        <SkeletonDetailPage />
      </div>
    )
  }

  if (isError || !doc) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-16 h-16 rounded-2xl bg-surface-container flex items-center justify-center mb-4">
          <svg
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-8 h-8 text-on-surface-variant/40"
            aria-hidden="true"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z" />
          </svg>
        </div>
        <p className="text-lg font-bold text-on-surface">Document not found</p>
        <p className="text-sm text-on-surface-variant mt-1">
          This document may have been deleted or you may not have access to it.
        </p>
        <Link
          to="/records"
          className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/30 rounded px-2"
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
            <path d="M19 12H5M12 5l-7 7 7 7" />
          </svg>
          Back to Records
        </Link>
      </div>
    )
  }

  const labResults = doc.lab_results ?? []
  const medications = doc.medications ?? []
  const diagnoses = doc.diagnoses ?? []
  const allergies = doc.allergies ?? []

  const hasAnyData =
    labResults.length > 0 ||
    medications.length > 0 ||
    diagnoses.length > 0 ||
    allergies.length > 0

  const displayName =
    doc.original_filename ?? getDocTypeLabel(doc.document_type)

  return (
    <div className="space-y-6">
      {/* ── Back link ──────────────────────────────────────────────────── */}
      <Link
        to="/records"
        className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/30 rounded px-1"
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
          <path d="M19 12H5M12 5l-7 7 7 7" />
        </svg>
        Back to Records
      </Link>

      {/* ── Two-column layout ──────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-[1fr_1.5fr] gap-6 items-start">
        {/* ── Left panel ─────────────────────────────────────────────── */}
        <div className="space-y-4">
          {/* Document header card */}
          <div className="bg-surface-container-lowest rounded-2xl p-6 shadow-sm shadow-teal-900/5">
            {/* Filename */}
            <p className="text-base font-bold text-on-surface leading-snug break-all">
              {displayName}
            </p>

            {/* Type + Status pills row */}
            <div className="flex flex-wrap gap-2 mt-3">
              <span
                className={`text-xs font-semibold uppercase tracking-wide px-2.5 py-1 rounded-full ${getDocTypePillClass(doc.document_type)}`}
              >
                {getDocTypeLabel(doc.document_type)}
              </span>
              <span
                className={`text-xs font-semibold uppercase tracking-wide px-2.5 py-1 rounded-full ${getStatusBadgeClass(doc.processing_status)}`}
              >
                {getStatusLabel(doc.processing_status)}
              </span>
            </div>

            {/* Meta fields */}
            <dl className="mt-4 space-y-2.5 text-sm">
              {doc.document_date && (
                <div className="flex items-center gap-2 text-on-surface-variant">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="w-4 h-4 flex-shrink-0"
                    aria-hidden="true"
                  >
                    <rect x="3" y="4" width="18" height="18" rx="2" />
                    <path d="M16 2v4M8 2v4M3 10h18" />
                  </svg>
                  <dt className="sr-only">Document date</dt>
                  <dd>{formatDate(doc.document_date)}</dd>
                </div>
              )}
              <div className="flex items-center gap-2 text-on-surface-variant">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-4 h-4 flex-shrink-0"
                  aria-hidden="true"
                >
                  <path d="M12 2v10l4 2" />
                  <circle cx="12" cy="12" r="10" />
                </svg>
                <dt className="sr-only">Uploaded on</dt>
                <dd>Uploaded {formatDate(doc.uploaded_at)}</dd>
              </div>
              {doc.facility_name && (
                <div className="flex items-center gap-2 text-on-surface-variant">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="w-4 h-4 flex-shrink-0"
                    aria-hidden="true"
                  >
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                    <polyline points="9 22 9 12 15 12 15 22" />
                  </svg>
                  <dt className="sr-only">Facility</dt>
                  <dd>{doc.facility_name}</dd>
                </div>
              )}
              {doc.doctor_name && (
                <div className="flex items-center gap-2 text-on-surface-variant">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="w-4 h-4 flex-shrink-0"
                    aria-hidden="true"
                  >
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                  <dt className="sr-only">Doctor</dt>
                  <dd>{doc.doctor_name}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* PDF viewer placeholder */}
          <div className="bg-surface-container-lowest rounded-2xl shadow-sm shadow-teal-900/5 min-h-[400px] flex flex-col items-center justify-center gap-4 p-6">
            <svg
              viewBox="0 0 64 64"
              fill="none"
              className="w-16 h-16 text-on-surface-variant/30"
              aria-hidden="true"
            >
              <rect
                x="8"
                y="4"
                width="36"
                height="48"
                rx="3"
                stroke="currentColor"
                strokeWidth="2.5"
              />
              <path
                d="M36 4v12h12"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M16 28h24M16 36h16"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <rect
                x="28"
                y="40"
                width="28"
                height="20"
                rx="3"
                fill="currentColor"
                opacity="0.15"
                stroke="currentColor"
                strokeWidth="2"
              />
              <path
                d="M33 46h18M33 50h12"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                opacity="0.5"
              />
            </svg>
            <p className="text-sm font-medium text-on-surface-variant text-center">
              PDF preview coming soon
            </p>
          </div>
        </div>

        {/* ── Right panel ────────────────────────────────────────────── */}
        <div className="space-y-6">
          {/* Section header */}
          <h2 className="text-xs font-semibold uppercase tracking-wider text-primary">
            Extracted Data
          </h2>

          {/* Extracted data content */}
          <div className="space-y-6">
            {/* FAILED state */}
            {(doc.processing_status === 'FAILED' ||
              doc.processing_status === 'MANUAL_REVIEW') && (
              <div className="bg-error-container rounded-2xl p-6">
                <div className="flex items-start gap-3">
                  <svg
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    className="w-5 h-5 text-error flex-shrink-0 mt-0.5"
                    aria-hidden="true"
                  >
                    <path d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 14a1 1 0 1 1 0-2 1 1 0 0 1 0 2zm1-4a1 1 0 1 1-2 0V8a1 1 0 1 1 2 0v4z" />
                  </svg>
                  <div>
                    <p className="text-sm font-semibold text-error">
                      Extraction failed
                    </p>
                    <p className="text-xs text-error/80 mt-1">
                      Extraction failed — you can retry or manually add data.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* PROCESSING / QUEUED state */}
            {(doc.processing_status === 'PROCESSING' ||
              doc.processing_status === 'QUEUED') && (
              <div className="bg-surface-container-low rounded-2xl p-6 flex flex-col items-center gap-4 min-h-[200px] justify-center">
                {/* Spinner */}
                <svg
                  className="w-8 h-8 text-primary animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden="true"
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeDasharray="60"
                    strokeDashoffset="20"
                    strokeLinecap="round"
                  />
                </svg>
                <div className="text-center">
                  <p className="text-sm font-semibold text-on-surface">
                    Extracting data from document…
                  </p>
                  <p className="text-xs text-on-surface-variant mt-1">
                    Clinical markers will appear here once complete.
                  </p>
                </div>
              </div>
            )}

            {/* COMPLETE with data */}
            {doc.processing_status === 'COMPLETE' && hasAnyData && (
              <div className="space-y-6">
                <LabResultsTable results={labResults} />
                <MedicationsList medications={medications} />
                <DiagnosesList diagnoses={diagnoses} />
                <AllergiesList allergies={allergies} />
              </div>
            )}

            {/* COMPLETE with no data yet (edge case) */}
            {doc.processing_status === 'COMPLETE' && !hasAnyData && (
              <div className="bg-surface-container-low rounded-2xl p-6 text-center">
                <p className="text-sm font-semibold text-on-surface">
                  Extraction complete
                </p>
                <p className="text-xs text-on-surface-variant mt-1">
                  No structured entities were extracted from this document.
                </p>
              </div>
            )}
          </div>

          {/* ── Action buttons ──────────────────────────────────────── */}
          <div className="flex flex-wrap gap-3 pt-2">
            {/* Download Original — always shown */}
            <a
              href={`${API_BASE}/documents/${documentId}/download`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 min-h-[44px] rounded-full border-2 border-primary text-primary text-sm font-semibold hover:bg-primary/5 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30"
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
                <path d="M12 5v14M5 12l7 7 7-7" />
                <path d="M3 19h18" />
              </svg>
              Download Original
            </a>

            {/* Retry Extraction — only shown on FAILED / MANUAL_REVIEW */}
            {(doc.processing_status === 'FAILED' ||
              doc.processing_status === 'MANUAL_REVIEW') && (
              <button
                type="button"
                onClick={() => retryMutation.mutate()}
                disabled={retryMutation.isPending}
                className="inline-flex items-center gap-2 px-5 py-2.5 min-h-[44px] rounded-full bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors shadow-sm shadow-teal-900/10 focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {retryMutation.isPending ? (
                  <>
                    <svg
                      className="w-4 h-4 animate-spin"
                      viewBox="0 0 24 24"
                      fill="none"
                      aria-hidden="true"
                    >
                      <circle
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="3"
                        strokeDasharray="60"
                        strokeDashoffset="20"
                        strokeLinecap="round"
                      />
                    </svg>
                    Retrying…
                  </>
                ) : (
                  <>
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
                      <path d="M1 4v6h6" />
                      <path d="M3.51 15a9 9 0 1 0 .49-4" />
                    </svg>
                    Retry Extraction
                  </>
                )}
              </button>
            )}
          </div>

          {/* Retry error feedback */}
          {retryMutation.isError && (
            <p className="text-xs text-error font-semibold">
              Retry request failed. Please try again.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
