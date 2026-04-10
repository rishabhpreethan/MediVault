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

// ── Main Page ─────────────────────────────────────────────────────────────

export function InsightsPage() {
  const memberId = useResolvedMemberId()
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
          Lab Trends
        </h1>
        <p className="text-sm text-on-surface-variant mt-0.5">
          Track your biomarkers over time
        </p>
      </div>

      {/* ── Loading skeleton (tests + chart area) ───────────────────────── */}
      {isLoadingTests && <ChartSkeleton />}

      {/* ── Error loading tests ──────────────────────────────────────────── */}
      {isErrorTests && (
        <div className="bg-error-container rounded-2xl p-5">
          <p className="text-sm font-bold text-error">Failed to load available tests</p>
          <p className="text-xs text-on-surface-variant mt-1">
            {testsError instanceof Error ? testsError.message : 'Please try again later'}
          </p>
        </div>
      )}

      {/* ── No tests available ───────────────────────────────────────────── */}
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

      {/* ── Tests loaded: pill selector + chart ─────────────────────────── */}
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
    </div>
  )
}
