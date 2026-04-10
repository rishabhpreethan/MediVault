import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { useResolvedMemberId } from '../../hooks/useFamily'

// ── Types ──────────────────────────────────────────────────────────────────

type EventType =
  | 'MEDICATION'
  | 'LAB_RESULT'
  | 'DIAGNOSIS'
  | 'ALLERGY'
  | 'VITAL'
  | 'DOCUMENT'

interface TimelineEvent {
  event_id: string
  event_type: EventType
  event_date: string | null
  title: string
  subtitle: string | null
  source_document_id: string | null
  confidence_score: string | null
}

interface TimelineResponse {
  items: TimelineEvent[]
  total: number
  page: number
  page_size: number
  member_id: string
}

// ── Helpers ────────────────────────────────────────────────────────────────

const PLACEHOLDER_MEMBER_ID = '00000000-0000-0000-0000-000000000000'
const PAGE_SIZE = 20

/** Format an ISO date string into "MONTH YYYY" for grouping. */
function toMonthYear(isoDate: string): string {
  const d = new Date(isoDate)
  return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }).toUpperCase()
}

/** Format an ISO date string into "MMM YYYY" for display. */
function formatEventDate(isoDate: string | null): string {
  if (!isoDate) return '—'
  const d = new Date(isoDate)
  return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }).toUpperCase()
}

/** True if the event date corresponds to the current month. */
function isCurrentMonth(isoDate: string): boolean {
  const d = new Date(isoDate)
  const now = new Date()
  return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
}

/**
 * Returns a Tailwind border-left color class for each event type.
 * LAB_RESULT=teal, MEDICATION=blue, DIAGNOSIS=amber, ALLERGY=red, VITAL=green, DOCUMENT=slate.
 */
function eventBorderColor(type: EventType): string {
  switch (type) {
    case 'LAB_RESULT':
      return 'border-primary'
    case 'MEDICATION':
      return 'border-blue-400'
    case 'DIAGNOSIS':
      return 'border-amber-400'
    case 'ALLERGY':
      return 'border-red-400'
    case 'VITAL':
      return 'border-green-400'
    case 'DOCUMENT':
    default:
      return 'border-slate-300'
  }
}

/**
 * Map event_type to a human label and badge color for the metric chip.
 */
function eventTypeChip(type: EventType): { label: string; className: string } {
  switch (type) {
    case 'LAB_RESULT':
      return { label: 'Lab Result', className: 'bg-primary/10 text-primary' }
    case 'MEDICATION':
      return { label: 'Medication', className: 'bg-blue-50 text-blue-600' }
    case 'DIAGNOSIS':
      return { label: 'Diagnosis', className: 'bg-amber-50 text-amber-700' }
    case 'ALLERGY':
      return { label: 'Allergy', className: 'bg-red-50 text-red-600' }
    case 'VITAL':
      return { label: 'Vital', className: 'bg-green-50 text-green-700' }
    case 'DOCUMENT':
    default:
      return { label: 'Document', className: 'bg-slate-100 text-slate-600' }
  }
}

/**
 * Group a flat list of events by "MONTH YEAR" key, preserving insertion order.
 * Events without a date are grouped under "NO DATE".
 */
function groupByMonth(events: TimelineEvent[]): Map<string, TimelineEvent[]> {
  const map = new Map<string, TimelineEvent[]>()
  for (const ev of events) {
    const key = ev.event_date ? toMonthYear(ev.event_date) : 'NO DATE'
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(ev)
  }
  return map
}

// ── Sub-components ─────────────────────────────────────────────────────────

function SkeletonTimelineCard() {
  return (
    <div className="relative animate-pulse">
      {/* dot */}
      <div className="absolute -left-[2.75rem] top-1 w-5 h-5 rounded-full bg-surface-container border-4 border-white" />
      <div className="space-y-3">
        <div className="h-3 bg-surface-container rounded w-32" />
        <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm shadow-teal-900/5 space-y-3">
          <div className="h-4 bg-surface-container rounded w-3/5" />
          <div className="h-3 bg-surface-container rounded w-2/5" />
          <div className="h-3 bg-surface-container rounded w-full" />
          <div className="flex gap-2 mt-2">
            <div className="h-8 bg-surface-container rounded-lg w-28" />
            <div className="h-8 bg-surface-container rounded-lg w-16" />
          </div>
        </div>
      </div>
    </div>
  )
}

function TimelineEventCard({
  event,
  isFirst,
}: {
  event: TimelineEvent
  isFirst: boolean
}) {
  const chip = eventTypeChip(event.event_type)
  const borderColor = eventBorderColor(event.event_type)
  const current = isFirst && event.event_date ? isCurrentMonth(event.event_date) : false

  const dateLabel = event.event_date
    ? current
      ? `CURRENT • ${formatEventDate(event.event_date)}`
      : formatEventDate(event.event_date)
    : null

  return (
    <div className="relative">
      {/* Timeline dot */}
      <div
        className={`absolute -left-[2.75rem] top-1 w-5 h-5 rounded-full z-10 border-4 border-white ${
          current ? 'bg-primary-container' : 'bg-white border-surface-container'
        }`}
        aria-hidden="true"
      />

      <div className="space-y-3">
        {/* Date label */}
        {dateLabel && (
          <span
            className={`text-xs font-bold tracking-widest uppercase ${
              current ? 'text-primary' : 'text-on-surface-variant'
            }`}
          >
            {dateLabel}
          </span>
        )}

        {/* Card */}
        <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm shadow-teal-900/5">
          {/* Header row */}
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="min-w-0">
              <h3 className="text-base font-bold text-on-surface leading-snug">
                {event.title}
              </h3>
              {event.subtitle && (
                <p className="text-xs text-on-surface-variant mt-0.5">{event.subtitle}</p>
              )}
            </div>
            <span
              className={`shrink-0 text-[10px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded ${chip.className}`}
            >
              {chip.label}
            </span>
          </div>

          {/* Metric chip row — shown only for LAB_RESULT when subtitle has a value */}
          {event.event_type === 'LAB_RESULT' && event.subtitle && (
            <div className="mb-4">
              <div
                className={`inline-block bg-surface-container-low p-2.5 rounded-lg border-l-4 ${borderColor}`}
              >
                <span className="block text-[10px] text-on-surface-variant font-bold uppercase tracking-wider">
                  {event.title}
                </span>
                <span className="text-sm font-bold text-on-surface">{event.subtitle}</span>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-2 mt-2">
            {event.source_document_id && (
              <button
                type="button"
                className="flex items-center gap-1.5 text-primary font-semibold text-xs px-3 py-2 bg-surface-container-low rounded-lg hover:bg-surface-container-high transition-all min-h-[36px]"
                aria-label={`View full report for ${event.title}`}
              >
                {/* Eye icon */}
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-3.5 h-3.5"
                  aria-hidden="true"
                >
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
                View Full Report
              </button>
            )}
            <button
              type="button"
              className="flex items-center gap-1.5 text-on-surface-variant font-semibold text-xs px-3 py-2 hover:bg-surface-container-low rounded-lg transition-all min-h-[36px]"
              aria-label={`Share ${event.title}`}
            >
              {/* Share icon */}
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-3.5 h-3.5"
                aria-hidden="true"
              >
                <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                <polyline points="16 6 12 2 8 6" />
                <line x1="12" y1="2" x2="12" y2="15" />
              </svg>
              Share
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Right sidebar ──────────────────────────────────────────────────────────

function ClinicalOverviewCard() {
  return (
    <div className="bg-surface-container-low rounded-xl p-5">
      <h4 className="font-bold text-on-surface mb-4 text-sm">Clinical Overview</h4>
      <div className="space-y-3">
        <div className="flex justify-between items-center pb-3 border-b border-outline-variant/20">
          <span className="text-xs text-on-surface-variant">Blood Type</span>
          <span className="text-sm font-bold text-on-surface">—</span>
        </div>
        <div className="flex justify-between items-center pb-3 border-b border-outline-variant/20">
          <span className="text-xs text-on-surface-variant">Primary Provider</span>
          <span className="text-sm font-bold text-on-surface">—</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-xs text-on-surface-variant">Next Review</span>
          <span className="text-sm font-bold text-primary">—</span>
        </div>
      </div>
    </div>
  )
}

function ActivePrescriptionsCard() {
  return (
    <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-surface-container-low">
      <h4 className="font-bold text-on-surface mb-4 text-sm">Active Prescriptions</h4>
      <p className="text-xs text-on-surface-variant leading-relaxed">
        Medications extracted from documents will appear here once processed.
      </p>
      <button
        type="button"
        className="w-full mt-5 py-3 border border-outline-variant rounded-lg text-xs font-bold uppercase tracking-widest hover:bg-surface-container-low transition-all min-h-[44px]"
      >
        Request Refill
      </button>
    </div>
  )
}

function ClinicalInsightsCard() {
  return (
    <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-primary to-secondary-container/70 p-5 min-h-[140px] flex flex-col justify-end">
      <h5 className="text-base font-extrabold leading-tight text-white mb-1">
        Clinical Insights
      </h5>
      <p className="text-xs text-primary-fixed/80 leading-relaxed">
        Upload more documents to unlock personalized health trend insights.
      </p>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────

export function TimelineTab() {
  const resolvedMemberId = useResolvedMemberId()
  const memberId = resolvedMemberId ?? PLACEHOLDER_MEMBER_ID

  const [page, setPage] = useState(1)

  const { data, isLoading, isError, isFetching } = useQuery<TimelineResponse>({
    queryKey: ['timeline', memberId, page],
    queryFn: async () => {
      const { data } = await api.get('/timeline/', {
        params: { member_id: memberId, page, page_size: PAGE_SIZE },
      })
      return data
    },
    enabled: !!resolvedMemberId,
  })

  const events = data?.items ?? []
  const total = data?.total ?? 0
  const hasMore = events.length > 0 && page * PAGE_SIZE < total

  // Group displayed events into month buckets
  const grouped = groupByMonth(events)

  // Flatten all event IDs in render order so we can check isFirst without mutation
  const allEventIds = Array.from(grouped.values()).flat().map((e) => e.event_id)

  return (
    <div className="flex flex-col md:flex-row gap-10">
      {/* ── Left column: timeline feed ──────────────────────────────── */}
      <div className="flex-1 min-w-0">
        {/* Section header */}
        <div className="mb-8">
          <h2 className="text-2xl font-extrabold text-on-surface tracking-tight">
            Health Timeline
          </h2>
          <p className="text-sm text-on-surface-variant mt-1 leading-relaxed">
            A longitudinal view of clinical events, diagnostics, and curative milestones.
          </p>
        </div>

        {/* Timeline feed */}
        <div
          className="relative pl-10 space-y-10"
          role="feed"
          aria-label="Health timeline events"
        >
          {/* Vertical line */}
          <div
            className="absolute left-6 top-0 bottom-0 w-0.5 bg-surface-container-low"
            aria-hidden="true"
          />

          {/* Loading: 3 skeleton cards */}
          {isLoading && (
            <>
              <SkeletonTimelineCard />
              <SkeletonTimelineCard />
              <SkeletonTimelineCard />
            </>
          )}

          {/* Error state */}
          {isError && !isLoading && (
            <div className="bg-error-container rounded-xl p-5 text-center">
              <p className="text-sm font-semibold text-error">
                Failed to load timeline events. Please try again.
              </p>
            </div>
          )}

          {/* Empty state */}
          {!isLoading && !isError && events.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center bg-surface-container-lowest rounded-xl shadow-sm shadow-teal-900/5">
              <div
                className="w-14 h-14 rounded-2xl bg-surface-container flex items-center justify-center mb-4"
                aria-hidden="true"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-7 h-7 text-primary/40"
                  aria-hidden="true"
                >
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                  <line x1="16" y1="2" x2="16" y2="6" />
                  <line x1="8" y1="2" x2="8" y2="6" />
                  <line x1="3" y1="10" x2="21" y2="10" />
                </svg>
              </div>
              <p className="text-base font-bold text-on-surface">No timeline events yet</p>
              <p className="text-sm text-on-surface-variant mt-1 max-w-xs">
                Upload a document to get started. Extracted clinical events will appear here
                automatically.
              </p>
            </div>
          )}

          {/* Grouped events */}
          {!isLoading &&
            !isError &&
            Array.from(grouped.entries()).map(([monthYear, monthEvents]) => (
              <div key={monthYear} className="space-y-8">
                {/* Month group header (shown above the first card in the group only
                    when there are multiple groups) */}
                {grouped.size > 1 && monthYear !== 'NO DATE' && (
                  <div className="relative -ml-10 pl-10">
                    <span className="text-[11px] font-bold tracking-widest text-on-surface-variant uppercase">
                      {monthYear}
                    </span>
                  </div>
                )}

                {monthEvents.map((event) => (
                  <TimelineEventCard
                    key={event.event_id}
                    event={event}
                    isFirst={allEventIds[0] === event.event_id}
                  />
                ))}
              </div>
            ))}

          {/* Load More button */}
          {!isLoading && !isError && hasMore && (
            <div className="flex justify-center pt-4">
              <button
                type="button"
                onClick={() => setPage((p) => p + 1)}
                disabled={isFetching}
                className="px-6 py-2.5 border border-outline-variant rounded-full text-sm font-semibold text-on-surface hover:bg-surface-container-low transition-all min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isFetching ? 'Loading…' : 'Load More'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── Right sidebar ────────────────────────────────────────────── */}
      <aside
        className="hidden md:block w-72 shrink-0 space-y-5"
        aria-label="Clinical overview sidebar"
      >
        <ClinicalOverviewCard />
        <ActivePrescriptionsCard />
        <ClinicalInsightsCard />
      </aside>
    </div>
  )
}
