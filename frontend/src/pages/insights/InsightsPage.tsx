import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
  BarChart,
  Bar,
  Cell,
} from 'recharts'
import { api } from '../../lib/api'
import { useResolvedMemberId } from '../../hooks/useFamily'

// ── Types ─────────────────────────────────────────────────────────────────

interface LabDataPoint {
  date: string        // ISO date from backend
  value: number
  unit: string | null
  is_abnormal: boolean | null
  document_id: string | null
}

interface LabTrendSeries {
  test_name: string
  has_enough_data: boolean
  data_points: LabDataPoint[]
  unit: string | null
  reference_range: string | null
}

interface LabTrendResponse {
  series: LabTrendSeries[]
  member_id: string
}

interface AvailableTestsResponse {
  test_names: string[]
  member_id: string
}

// ── Vitals trend types (MV-073) ───────────────────────────────────────────

interface VitalDataPoint {
  recorded_at: string | null
  value: number
  unit: string | null
  vital_type: string
  systolic: number | null
  diastolic: number | null
}

interface VitalsTrendSeries {
  vital_type: string
  display_name: string
  unit: string | null
  data_points: VitalDataPoint[]
  has_enough_data: boolean
}

interface VitalsTrendResponse {
  series: VitalsTrendSeries[]
  member_id: string
}

// ── Medication timeline types (MV-072) ─────────────────────────────────────

interface MedicationBar {
  medication_id: string
  drug_name: string
  dosage: string | null
  is_active: boolean
  start_date: string | null
  end_date: string | null
  start_day: number
  duration_days: number | null
}

interface MedicationTimelineResponse {
  bars: MedicationBar[]
  member_id: string
  earliest_date: string | null
  today: string
}

// ── Reference range parser ────────────────────────────────────────────────
// Handles "70–100" (em dash), "70-100" (hyphen), "≥70", "≤100"

function parseReferenceRange(ref: string): { low: number | null; high: number | null } {
  // Try range patterns first: "70–100" or "70-100"
  const rangeMatch = ref.match(/^([\d.]+)\s*[–-]\s*([\d.]+)$/)
  if (rangeMatch) {
    return { low: parseFloat(rangeMatch[1]), high: parseFloat(rangeMatch[2]) }
  }
  const geMatch = ref.match(/^[≥>]([\d.]+)$/)
  if (geMatch) {
    return { low: parseFloat(geMatch[1]), high: null }
  }
  const leMatch = ref.match(/^[≤<]([\d.]+)$/)
  if (leMatch) {
    return { low: null, high: parseFloat(leMatch[1]) }
  }
  return { low: null, high: null }
}

// ── Date formatter ────────────────────────────────────────────────────────

function formatDateShort(isoDate: string): string {
  const d = new Date(isoDate)
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

// ── SVG Icons ─────────────────────────────────────────────────────────────

function IconUpload() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-8 h-8"
      aria-hidden="true"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  )
}

function IconChart() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-8 h-8"
      aria-hidden="true"
    >
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  )
}

// ── Skeleton ──────────────────────────────────────────────────────────────

function ChartSkeleton() {
  return (
    <div className="animate-pulse space-y-4" aria-label="Loading chart">
      {/* Pill row skeleton */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {[120, 90, 110, 80, 140].map((w, i) => (
          <div
            key={i}
            className="h-9 rounded-full bg-surface-container flex-shrink-0"
            style={{ width: `${w}px` }}
          />
        ))}
      </div>
      {/* Chart card skeleton */}
      <div className="bg-surface-container-lowest rounded-2xl p-5 shadow-sm shadow-teal-900/5 space-y-4">
        <div className="h-5 w-40 bg-surface-container rounded-lg" />
        <div className="h-[300px] bg-surface-container rounded-xl" />
        {/* Stats strip skeleton */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="space-y-2">
              <div className="h-3 w-12 bg-surface-container rounded" />
              <div className="h-6 w-20 bg-surface-container rounded" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Custom Tooltip ────────────────────────────────────────────────────────

interface ChartPayloadEntry {
  payload: LabDataPoint & { formattedDate: string }
  value: number
}

interface LabTooltipProps {
  active?: boolean
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  payload?: any[]
  unit: string | null
  referenceRange: string | null
}

function LabTooltip({ active, payload, unit, referenceRange }: LabTooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  const entry = payload[0] as ChartPayloadEntry
  const point = entry.payload as LabDataPoint & { formattedDate: string }
  const isOutOfRange = point.is_abnormal === true

  return (
    <div className="bg-surface-container-lowest rounded-xl shadow-lg border border-outline-variant/30 p-3 text-xs min-w-[160px]">
      <p className="font-bold text-on-surface mb-2">{point.formattedDate}</p>
      <div className="flex items-baseline gap-1 mb-1">
        <span
          className={`text-base font-extrabold ${isOutOfRange ? 'text-error' : 'text-primary'}`}
        >
          {point.value}
        </span>
        {unit && <span className="text-on-surface-variant">{unit}</span>}
      </div>
      {referenceRange && (
        <p className="text-on-surface-variant">
          Reference: <span className="font-semibold">{referenceRange}</span>
        </p>
      )}
      {isOutOfRange && (
        <p className="mt-1.5 text-error font-semibold">Out of range</p>
      )}
    </div>
  )
}

// ── Custom Dot ────────────────────────────────────────────────────────────

function renderCustomDot(props: { cx?: number; cy?: number; payload?: LabDataPoint }): JSX.Element {
  const { cx, cy, payload } = props
  if (cx === undefined || cy === undefined || !payload) return <circle cx={0} cy={0} r={0} />
  const isOut = payload.is_abnormal === true
  return (
    <circle
      key={`dot-${cx}-${cy}`}
      cx={cx}
      cy={cy}
      r={isOut ? 6 : 4}
      fill={isOut ? '#ba1a1a' : '#006b5f'}
      stroke={isOut ? '#ffdad6' : '#62fae3'}
      strokeWidth={2}
    />
  )
}

// ── Stats strip ───────────────────────────────────────────────────────────

function StatsStrip({
  series,
}: {
  series: LabTrendSeries
}) {
  const { data_points, unit, reference_range } = series
  if (data_points.length === 0) return null

  const values = data_points.map((p) => p.value)
  const latest = data_points[data_points.length - 1]
  const min = Math.min(...values)
  const max = Math.max(...values)
  const avg = values.reduce((a, b) => a + b, 0) / values.length
  const isOutOfRange = latest.is_abnormal === true

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-outline-variant/20">
      {/* Latest */}
      <div>
        <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-1">
          Latest
        </p>
        <p
          className={`text-xl font-extrabold ${
            isOutOfRange ? 'text-error' : 'text-primary'
          }`}
        >
          {latest.value}
          {unit && (
            <span className="text-sm font-semibold text-on-surface-variant ml-1">
              {unit}
            </span>
          )}
        </p>
      </div>

      {/* Min */}
      <div>
        <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-1">
          Min
        </p>
        <p className="text-xl font-extrabold text-on-surface">
          {min}
          {unit && (
            <span className="text-sm font-semibold text-on-surface-variant ml-1">
              {unit}
            </span>
          )}
        </p>
      </div>

      {/* Max */}
      <div>
        <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-1">
          Max
        </p>
        <p className="text-xl font-extrabold text-on-surface">
          {max}
          {unit && (
            <span className="text-sm font-semibold text-on-surface-variant ml-1">
              {unit}
            </span>
          )}
        </p>
      </div>

      {/* Average */}
      <div>
        <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-1">
          Average
        </p>
        <p className="text-xl font-extrabold text-on-surface">
          {avg.toFixed(1)}
          {unit && (
            <span className="text-sm font-semibold text-on-surface-variant ml-1">
              {unit}
            </span>
          )}
        </p>
      </div>

      {/* Reference range full row */}
      {reference_range && (
        <div className="col-span-2 sm:col-span-4">
          <p className="text-xs text-on-surface-variant">
            Reference range:{' '}
            <span className="font-semibold text-on-surface">{reference_range}</span>
          </p>
        </div>
      )}
    </div>
  )
}

// ── Chart card ────────────────────────────────────────────────────────────

function LabChartCard({ series }: { series: LabTrendSeries }) {
  const { test_name, has_enough_data, data_points, unit, reference_range } = series

  if (!has_enough_data) {
    return (
      <div className="bg-surface-container-lowest rounded-2xl p-5 shadow-sm shadow-teal-900/5">
        <h2 className="text-base font-extrabold text-on-surface tracking-tight mb-4">
          {test_name}
        </h2>
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <div className="w-12 h-12 rounded-2xl bg-surface-container flex items-center justify-center mb-3 text-primary/40">
            <IconChart />
          </div>
          <p className="text-sm font-bold text-on-surface">Not enough data yet</p>
          <p className="text-xs text-on-surface-variant mt-1">
            Need at least 2 readings to display a trend
          </p>
        </div>
      </div>
    )
  }

  // Build chart data with formatted dates
  const chartData = data_points.map((p) => ({
    ...p,
    formattedDate: formatDateShort(p.date),
  }))

  // Parse reference range for the band
  const refBand =
    reference_range !== null ? parseReferenceRange(reference_range) : { low: null, high: null }
  const showBand =
    reference_range !== null &&
    refBand.low !== null &&
    refBand.high !== null

  // Y-axis domain padding
  const values = data_points.map((p) => p.value)
  const dataMin = Math.min(...values)
  const dataMax = Math.max(...values)
  const rangeLow = refBand.low ?? dataMin
  const rangeHigh = refBand.high ?? dataMax
  const domainMin = Math.floor(Math.min(dataMin, rangeLow) * 0.9)
  const domainMax = Math.ceil(Math.max(dataMax, rangeHigh) * 1.1)

  const yLabel = unit ? { value: unit, angle: -90, position: 'insideLeft' as const, offset: 10, style: { fontSize: 11, fill: '#3c4a46' } } : undefined

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-5 shadow-sm shadow-teal-900/5">
      <h2 className="text-base font-extrabold text-on-surface tracking-tight mb-4">
        {test_name}
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top: 8, right: 16, left: unit ? 8 : 0, bottom: 4 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#bacac5" strokeOpacity={0.4} />
          <XAxis
            dataKey="formattedDate"
            tick={{ fontSize: 11, fill: '#3c4a46' }}
            axisLine={{ stroke: '#bacac5' }}
            tickLine={false}
          />
          <YAxis
            domain={[domainMin, domainMax]}
            tick={{ fontSize: 11, fill: '#3c4a46' }}
            axisLine={false}
            tickLine={false}
            label={yLabel}
          />
          <Tooltip
            content={(props) => (
              <LabTooltip
                {...props}
                unit={unit}
                referenceRange={reference_range}
              />
            )}
          />
          {showBand && refBand.low !== null && refBand.high !== null && (
            <ReferenceArea
              y1={refBand.low}
              y2={refBand.high}
              fill="#006b5f"
              fillOpacity={0.08}
              stroke="none"
            />
          )}
          <Line
            type="monotone"
            dataKey="value"
            stroke="#006b5f"
            strokeWidth={2}
            dot={renderCustomDot}
            activeDot={{ r: 6, fill: '#006b5f' }}
            isAnimationActive={true}
          />
        </LineChart>
      </ResponsiveContainer>

      <StatsStrip series={series} />
    </div>
  )
}

// ── SVG Heartbeat icon (MV-073) ───────────────────────────────────────────

function IconHeartbeat() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-8 h-8"
      aria-hidden="true"
    >
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  )
}

// ── SVG Pill icon (MV-072) ────────────────────────────────────────────────

function IconPill() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-8 h-8"
      aria-hidden="true"
    >
      <path d="M10.5 20.5 3.5 13.5a5 5 0 0 1 7.07-7.07l7 7a5 5 0 0 1-7.07 7.07Z" />
      <line x1="8.5" y1="8.5" x2="15.5" y2="15.5" />
    </svg>
  )
}

// ── Medication Gantt skeleton (MV-072) ────────────────────────────────────

function GanttSkeleton() {
  return (
    <div className="animate-pulse space-y-3" aria-label="Loading medications">
      {[80, 120, 90, 140, 100].map((w, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="h-4 w-28 bg-surface-container rounded" />
          <div className="h-6 bg-surface-container rounded" style={{ width: `${w}px` }} />
        </div>
      ))}
    </div>
  )
}

// ── MedicationGanttChart component (MV-072) ───────────────────────────────

function MedicationGanttChart({ memberId }: { memberId: string }) {
  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery<MedicationTimelineResponse>({
    queryKey: ['medication-timeline', memberId],
    queryFn: async () => {
      const { data: responseData } = await api.get<MedicationTimelineResponse>(
        `/charts/medication-timeline?member_id=${memberId}`
      )
      return responseData
    },
    enabled: !!memberId,
  })

  if (isLoading) {
    return (
      <div className="bg-surface-container-lowest rounded-2xl p-5 shadow-sm shadow-teal-900/5">
        <GanttSkeleton />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="bg-error-container rounded-2xl p-5">
        <p className="text-sm font-bold text-error">Failed to load medication timeline</p>
        <p className="text-xs text-on-surface-variant mt-1">
          {error instanceof Error ? error.message : 'Please try again later'}
        </p>
      </div>
    )
  }

  if (!data || data.bars.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 rounded-2xl bg-surface-container flex items-center justify-center mb-4 text-primary/40">
          <IconPill />
        </div>
        <p className="text-base font-bold text-on-surface">No medication history yet</p>
        <p className="text-sm text-on-surface-variant mt-1 max-w-xs">
          Upload prescriptions or discharge summaries to track your medications
        </p>
      </div>
    )
  }

  // Compute today_day (days since earliest_date)
  const todayIso = data.today
  const earliestIso = data.earliest_date ?? todayIso

  function isoToDayOffset(iso: string): number {
    const earliest = new Date(earliestIso)
    const target = new Date(iso)
    return Math.round((target.getTime() - earliest.getTime()) / 86400000)
  }

  const todayDay = isoToDayOffset(todayIso)

  // Build chart rows: { name, offset, duration }
  const chartData = data.bars.map((bar) => ({
    name: bar.dosage ? `${bar.drug_name} ${bar.dosage}` : bar.drug_name,
    offset: bar.start_day,
    duration: bar.duration_days !== null ? bar.duration_days : Math.max(todayDay - bar.start_day, 1),
    is_active: bar.is_active,
  }))

  // Determine total axis domain
  const maxDay = Math.max(...chartData.map((d) => d.offset + d.duration), todayDay, 1)

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-5 shadow-sm shadow-teal-900/5">
      <h2 className="text-base font-extrabold text-on-surface tracking-tight mb-5">
        Medication Timeline
      </h2>
      <ResponsiveContainer width="100%" height={Math.max(chartData.length * 44, 120)}>
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ top: 0, right: 16, left: 0, bottom: 4 }}
          barSize={16}
        >
          <XAxis
            type="number"
            domain={[0, maxDay]}
            tick={{ fontSize: 11, fill: '#3c4a46' }}
            axisLine={{ stroke: '#bacac5' }}
            tickLine={false}
            tickFormatter={(v: number) => `Day ${v}`}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={140}
            tick={{ fontSize: 11, fill: '#3c4a46' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: 'transparent' }}
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null
              // Find the bar entry (duration bar is last in the stack)
              const entry = payload[payload.length - 1]
              const row = entry?.payload as typeof chartData[0] | undefined
              if (!row) return null
              return (
                <div className="bg-surface-container-lowest rounded-xl shadow-lg border border-outline-variant/30 p-3 text-xs min-w-[160px]">
                  <p className="font-bold text-on-surface mb-1">{row.name}</p>
                  <p className="text-on-surface-variant">
                    Start: Day {row.offset}
                  </p>
                  <p className="text-on-surface-variant">
                    Duration: {row.duration} day{row.duration !== 1 ? 's' : ''}
                  </p>
                  <p className={`mt-1 font-semibold ${row.is_active ? 'text-primary' : 'text-on-surface-variant'}`}>
                    {row.is_active ? 'Active' : 'Discontinued'}
                  </p>
                </div>
              )
            }}
          />
          {/* Invisible offset bar to push the visible bar to the right */}
          <Bar dataKey="offset" stackId="gantt" fill="transparent" isAnimationActive={false} />
          {/* Visible duration bar */}
          <Bar dataKey="duration" stackId="gantt" radius={4} isAnimationActive={true}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.is_active ? '#006b5f' : '#bacac5'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {/* Legend */}
      <div className="flex gap-4 mt-4 pt-3 border-t border-outline-variant/20">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-primary" />
          <span className="text-xs text-on-surface-variant">Active</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-outline-variant" />
          <span className="text-xs text-on-surface-variant">Discontinued</span>
        </div>
      </div>
    </div>
  )
}

// ── Vitals stats strip (MV-073) ───────────────────────────────────────────

function VitalsStatsStrip({ series }: { series: VitalsTrendSeries }) {
  const { data_points, unit } = series
  if (data_points.length === 0) return null

  const values = data_points.map((p) => p.value)
  const latest = data_points[data_points.length - 1]
  const min = Math.min(...values)
  const max = Math.max(...values)

  const latestLabel =
    series.vital_type === 'blood_pressure' && latest.systolic !== null
      ? `${latest.systolic}`
      : `${latest.value}`

  return (
    <div className="grid grid-cols-3 gap-4 pt-4 border-t border-outline-variant/20">
      <div>
        <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-1">
          Latest
        </p>
        <p className="text-xl font-extrabold text-primary">
          {latestLabel}
          {unit && (
            <span className="text-sm font-semibold text-on-surface-variant ml-1">{unit}</span>
          )}
        </p>
      </div>
      <div>
        <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-1">
          Min
        </p>
        <p className="text-xl font-extrabold text-on-surface">
          {min}
          {unit && (
            <span className="text-sm font-semibold text-on-surface-variant ml-1">{unit}</span>
          )}
        </p>
      </div>
      <div>
        <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-1">
          Max
        </p>
        <p className="text-xl font-extrabold text-on-surface">
          {max}
          {unit && (
            <span className="text-sm font-semibold text-on-surface-variant ml-1">{unit}</span>
          )}
        </p>
      </div>
    </div>
  )
}

// ── VitalsChartCard (MV-073) ──────────────────────────────────────────────

function VitalsChartCard({ series }: { series: VitalsTrendSeries }) {
  const { vital_type, display_name, has_enough_data, data_points, unit } = series

  if (!has_enough_data) {
    return (
      <div className="bg-surface-container-lowest rounded-2xl p-5 shadow-sm shadow-teal-900/5">
        <h2 className="text-base font-extrabold text-on-surface tracking-tight mb-4">
          {display_name}
        </h2>
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <div className="w-12 h-12 rounded-2xl bg-surface-container flex items-center justify-center mb-3 text-primary/40">
            <IconHeartbeat />
          </div>
          <p className="text-sm font-bold text-on-surface">Not enough data yet</p>
          <p className="text-xs text-on-surface-variant mt-1">
            Need at least 2 readings to display a trend
          </p>
        </div>
      </div>
    )
  }

  const chartData = data_points.map((p) => ({
    ...p,
    formattedDate: p.recorded_at ? formatDateShort(p.recorded_at) : '—',
  }))

  const values = data_points.map((p) => p.value)
  const dataMin = Math.min(...values)
  const dataMax = Math.max(...values)
  const domainMin = Math.floor(dataMin * 0.9)
  const domainMax = Math.ceil(dataMax * 1.1)

  const yLabel = unit
    ? { value: unit, angle: -90, position: 'insideLeft' as const, offset: 10, style: { fontSize: 11, fill: '#3c4a46' } }
    : undefined

  const isBP = vital_type === 'blood_pressure'

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-5 shadow-sm shadow-teal-900/5">
      <h2 className="text-base font-extrabold text-on-surface tracking-tight mb-4">
        {display_name}
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top: 8, right: 16, left: unit ? 8 : 0, bottom: 4 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#bacac5" strokeOpacity={0.4} />
          <XAxis
            dataKey="formattedDate"
            tick={{ fontSize: 11, fill: '#3c4a46' }}
            axisLine={{ stroke: '#bacac5' }}
            tickLine={false}
          />
          <YAxis
            domain={[domainMin, domainMax]}
            tick={{ fontSize: 11, fill: '#3c4a46' }}
            axisLine={false}
            tickLine={false}
            label={yLabel}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null
              const point = payload[0].payload as VitalDataPoint & { formattedDate: string }
              return (
                <div className="bg-surface-container-lowest rounded-xl shadow-lg border border-outline-variant/30 p-3 text-xs min-w-[140px]">
                  <p className="font-bold text-on-surface mb-2">{point.formattedDate}</p>
                  {isBP ? (
                    <div className="flex items-baseline gap-1">
                      <span className="text-base font-extrabold text-primary">{point.value}</span>
                      {unit && <span className="text-on-surface-variant">{unit}</span>}
                    </div>
                  ) : (
                    <div className="flex items-baseline gap-1">
                      <span className="text-base font-extrabold text-primary">{point.value}</span>
                      {unit && <span className="text-on-surface-variant">{unit}</span>}
                    </div>
                  )}
                </div>
              )
            }}
          />
          {/* Blood pressure: single line in teal; other vitals: same pattern */}
          <Line
            type="monotone"
            dataKey="value"
            stroke="#006b5f"
            strokeWidth={2}
            dot={{ r: 4, fill: '#006b5f', stroke: '#62fae3', strokeWidth: 2 }}
            activeDot={{ r: 6, fill: '#006b5f' }}
            isAnimationActive={true}
            name={isBP ? 'Systolic' : display_name}
          />
          {/* For BP, also render a second lighter line at diastolic if available */}
          {isBP && chartData.some((p) => p.diastolic !== null) && (
            <Line
              type="monotone"
              dataKey="diastolic"
              stroke="#2dd4bf"
              strokeWidth={2}
              dot={{ r: 4, fill: '#2dd4bf', stroke: '#62fae3', strokeWidth: 2 }}
              activeDot={{ r: 6, fill: '#2dd4bf' }}
              isAnimationActive={true}
              name="Diastolic"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
      <VitalsStatsStrip series={series} />
    </div>
  )
}

// ── VitalsTrendChart component (MV-073) ───────────────────────────────────

function VitalsTrendChart({ memberId }: { memberId: string }) {
  const { data, isLoading, isError, error } = useQuery<VitalsTrendResponse>({
    queryKey: ['vitals-trends', memberId],
    queryFn: async () => {
      const { data: responseData } = await api.get<VitalsTrendResponse>(
        `/charts/vitals-trends?member_id=${memberId}`
      )
      return responseData
    },
    enabled: !!memberId,
  })

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4" aria-label="Loading vitals">
        <div className="bg-surface-container-lowest rounded-2xl p-5 shadow-sm shadow-teal-900/5 space-y-4">
          <div className="h-5 w-40 bg-surface-container rounded-lg" />
          <div className="h-[300px] bg-surface-container rounded-xl" />
          <div className="grid grid-cols-3 gap-4 pt-2">
            {[0, 1, 2].map((i) => (
              <div key={i} className="space-y-2">
                <div className="h-3 w-12 bg-surface-container rounded" />
                <div className="h-6 w-20 bg-surface-container rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="bg-error-container rounded-2xl p-5">
        <p className="text-sm font-bold text-error">Failed to load vitals data</p>
        <p className="text-xs text-on-surface-variant mt-1">
          {error instanceof Error ? error.message : 'Please try again later'}
        </p>
      </div>
    )
  }

  const seriesWithData = data?.series.filter((s) => s.has_enough_data) ?? []

  if (!data || seriesWithData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 rounded-2xl bg-surface-container flex items-center justify-center mb-4 text-primary/40">
          <IconHeartbeat />
        </div>
        <p className="text-base font-bold text-on-surface">No vitals data yet</p>
        <p className="text-sm text-on-surface-variant mt-1 max-w-xs">
          Upload documents containing vital measurements
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {seriesWithData.map((series) => (
        <VitalsChartCard key={series.vital_type} series={series} />
      ))}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────

type InsightsTab = 'lab-trends' | 'medications' | 'vitals'

export function InsightsPage() {
  const memberId = useResolvedMemberId()
  const [activeTab, setActiveTab] = useState<InsightsTab>('lab-trends')
  const [selectedTest, setSelectedTest] = useState<string | null>(null)

  // Fetch available test names
  const {
    data: availableTests,
    isLoading: isLoadingTests,
    isError: isErrorTests,
    error: testsError,
  } = useQuery<AvailableTestsResponse>({
    queryKey: ['available-tests', memberId],
    queryFn: async () => {
      const { data } = await api.get<AvailableTestsResponse>(
        `/charts/available-tests?member_id=${memberId}`
      )
      return data
    },
    enabled: !!memberId,
  })

  // Select the first test automatically when data loads
  useEffect(() => {
    if (availableTests && availableTests.test_names.length > 0 && selectedTest === null) {
      setSelectedTest(availableTests.test_names[0])
    }
  }, [availableTests, selectedTest])

  // Fetch chart data for the selected test
  const {
    data: trendData,
    isLoading: isLoadingTrend,
    isError: isErrorTrend,
    error: trendError,
  } = useQuery<LabTrendResponse>({
    queryKey: ['lab-trends', memberId, selectedTest],
    queryFn: async () => {
      const { data } = await api.get<LabTrendResponse>(
        `/charts/lab-trends?member_id=${memberId}&test_names=${encodeURIComponent(selectedTest ?? '')}`
      )
      return data
    },
    enabled: !!memberId && !!selectedTest,
  })

  const testNames = availableTests?.test_names ?? []
  const noTestsAvailable = !isLoadingTests && !isErrorTests && testNames.length === 0
  const activeSeries = trendData?.series.find(
    (s) => s.test_name.toLowerCase() === (selectedTest ?? '').toLowerCase()
  ) ?? trendData?.series[0] ?? null

  return (
    <div className="space-y-6">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">
          Insights
        </h1>
        <p className="text-sm text-on-surface-variant mt-0.5">
          Visualise your health data over time
        </p>
      </div>

      {/* ── Top-level tab switcher ───────────────────────────────────────── */}
      <div
        className="inline-flex gap-1 p-1 rounded-full bg-surface-container-low"
        role="tablist"
        aria-label="Insights sections"
      >
        {(
          [
            { id: 'lab-trends', label: 'Lab Trends' },
            { id: 'medications', label: 'Medications' },
            { id: 'vitals', label: 'Vitals' },
          ] as { id: InsightsTab; label: string }[]
        ).map(({ id, label }) => {
          const isActive = activeTab === id
          return (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => setActiveTab(id)}
              className={[
                'px-5 py-2 rounded-full text-sm font-semibold transition-all min-h-[44px] whitespace-nowrap',
                isActive
                  ? 'bg-white text-primary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface',
              ].join(' ')}
            >
              {label}
            </button>
          )
        })}
      </div>

      {/* ── Lab Trends tab ──────────────────────────────────────────────── */}
      {activeTab === 'lab-trends' && (
        <>
          {/* Loading skeleton (tests + chart area) */}
          {isLoadingTests && <ChartSkeleton />}

          {/* Error loading tests */}
          {isErrorTests && (
            <div className="bg-error-container rounded-2xl p-5">
              <p className="text-sm font-bold text-error">Failed to load available tests</p>
              <p className="text-xs text-on-surface-variant mt-1">
                {testsError instanceof Error ? testsError.message : 'Please try again later'}
              </p>
            </div>
          )}

          {/* No tests available */}
          {noTestsAvailable && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-16 h-16 rounded-2xl bg-surface-container flex items-center justify-center mb-4 text-primary/40">
                <IconUpload />
              </div>
              <p className="text-base font-bold text-on-surface">
                No lab data available yet
              </p>
              <p className="text-sm text-on-surface-variant mt-1 max-w-xs">
                Upload lab reports to start tracking your biomarkers
              </p>
            </div>
          )}

          {/* Tests loaded: pill selector + chart */}
          {!isLoadingTests && !isErrorTests && testNames.length > 0 && (
            <>
              {/* Pill selector */}
              <div
                className="flex gap-2 overflow-x-auto pb-1"
                role="tablist"
                aria-label="Select lab test"
              >
                {testNames.map((name) => {
                  const isSelected = selectedTest === name
                  return (
                    <button
                      key={name}
                      type="button"
                      role="tab"
                      aria-selected={isSelected}
                      onClick={() => setSelectedTest(name)}
                      className={[
                        'flex-shrink-0 px-4 py-2 rounded-full text-sm font-semibold transition-colors min-h-[44px] whitespace-nowrap',
                        isSelected
                          ? 'bg-primary text-white shadow-sm shadow-teal-900/10'
                          : 'bg-surface-container text-on-surface hover:bg-surface-container-high',
                      ].join(' ')}
                    >
                      {name}
                    </button>
                  )
                })}
              </div>

              {/* Chart area: loading skeleton while fetching trend */}
              {isLoadingTrend && (
                <div className="bg-surface-container-lowest rounded-2xl p-5 shadow-sm shadow-teal-900/5">
                  <div className="animate-pulse space-y-4">
                    <div className="h-5 w-36 bg-surface-container rounded-lg" />
                    <div className="h-[300px] bg-surface-container rounded-xl" />
                  </div>
                </div>
              )}

              {/* Chart area: error */}
              {isErrorTrend && !isLoadingTrend && (
                <div className="bg-error-container rounded-2xl p-5">
                  <p className="text-sm font-bold text-error">Failed to load chart data</p>
                  <p className="text-xs text-on-surface-variant mt-1">
                    {trendError instanceof Error ? trendError.message : 'Please try again later'}
                  </p>
                </div>
              )}

              {/* Chart area: data */}
              {!isLoadingTrend && !isErrorTrend && activeSeries && (
                <LabChartCard series={activeSeries} />
              )}

              {/* Edge case: no series returned for selected test */}
              {!isLoadingTrend && !isErrorTrend && trendData && !activeSeries && (
                <div className="bg-surface-container-lowest rounded-2xl p-8 shadow-sm shadow-teal-900/5 flex flex-col items-center text-center">
                  <div className="w-12 h-12 rounded-2xl bg-surface-container flex items-center justify-center mb-3 text-primary/40">
                    <IconChart />
                  </div>
                  <p className="text-sm font-bold text-on-surface">No data for this test</p>
                  <p className="text-xs text-on-surface-variant mt-1">
                    Select another test or upload more lab reports
                  </p>
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* ── Medications tab ─────────────────────────────────────────────── */}
      {activeTab === 'medications' && memberId && (
        <MedicationGanttChart memberId={memberId} />
      )}

      {/* Edge case: memberId not yet resolved while on medications tab */}
      {activeTab === 'medications' && !memberId && (
        <div className="bg-surface-container-lowest rounded-2xl p-5 shadow-sm shadow-teal-900/5">
          <GanttSkeleton />
        </div>
      )}

      {/* ── Vitals tab ──────────────────────────────────────────────────── */}
      {activeTab === 'vitals' && memberId && (
        <VitalsTrendChart memberId={memberId} />
      )}

      {/* Edge case: memberId not yet resolved while on vitals tab */}
      {activeTab === 'vitals' && !memberId && (
        <div className="animate-pulse space-y-4" aria-label="Loading vitals">
          <div className="bg-surface-container-lowest rounded-2xl p-5 shadow-sm shadow-teal-900/5 space-y-4">
            <div className="h-5 w-40 bg-surface-container rounded-lg" />
            <div className="h-[300px] bg-surface-container rounded-xl" />
          </div>
        </div>
      )}
    </div>
  )
}
