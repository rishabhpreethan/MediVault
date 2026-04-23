import { TimelineTab } from './TimelineTab'

export function RecordsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">
          Health Timeline
        </h1>
        <p className="text-sm text-on-surface-variant mt-1">
          Your clinical history in chronological order
        </p>
      </div>

      <TimelineTab />
    </div>
  )
}
