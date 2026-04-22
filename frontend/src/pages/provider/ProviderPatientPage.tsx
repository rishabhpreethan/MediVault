/**
 * Provider Patient View — MV-158
 *
 * Route: /provider/patient/:requestId  (PROVIDER role only)
 *
 * Shows:
 *   - Identity & Baseline panel (name, DOB, blood group, height/weight)
 *   - Encounter history feed
 *   - Log Encounter form
 */
import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'

interface PatientSummary {
  member_id: string
  full_name: string
  date_of_birth?: string
  blood_group?: string
  height_cm?: number
  weight_kg?: number
}

interface Encounter {
  encounter_id: string
  encounter_date: string
  chief_complaint?: string
  diagnosis_notes?: string
  prescriptions_note?: string
  follow_up_date?: string
  created_at: string
}

interface PatientData {
  request_id: string
  patient: PatientSummary
  encounters: Encounter[]
}

function calculateAge(dob: string): number {
  const today = new Date()
  const birth = new Date(dob)
  let age = today.getFullYear() - birth.getFullYear()
  const m = today.getMonth() - birth.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--
  return age
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

// ── Log Encounter Form ─────────────────────────────────────────────────────

interface DiagnosisEntry { condition_name: string; status: string }
interface MedicationEntry {
  drug_name: string
  dosage: string
  morning: boolean
  noon: boolean
  night: boolean
  food_timing: 'before' | 'after' | ''
  is_active: boolean
}

const emptyDx = (): DiagnosisEntry => ({ condition_name: '', status: 'ACTIVE' })
const emptyMed = (): MedicationEntry => ({
  drug_name: '', dosage: '',
  morning: false, noon: false, night: false,
  food_timing: '', is_active: true,
})

function formatMedFrequency(m: MedicationEntry): string | undefined {
  const times: string[] = []
  if (m.morning) times.push('Morning')
  if (m.noon) times.push('Noon')
  if (m.night) times.push('Night')
  if (times.length === 0) return undefined
  let freq = times.join('-')
  if (m.food_timing) freq += ` ${m.food_timing === 'before' ? 'Before food' : 'After food'}`
  return freq
}

interface LogFormProps {
  requestId: string
  onSuccess: () => void
}

function LogEncounterForm({ requestId, onSuccess }: LogFormProps) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    encounter_date: new Date().toISOString().split('T')[0],
    chief_complaint: '',
    diagnosis_notes: '',
    prescriptions_note: '',
    follow_up_date: '',
  })
  const [diagnoses, setDiagnoses] = useState<DiagnosisEntry[]>([emptyDx()])
  const [medications, setMedications] = useState<MedicationEntry[]>([emptyMed()])

  function resetForm() {
    setForm({
      encounter_date: new Date().toISOString().split('T')[0],
      chief_complaint: '',
      diagnosis_notes: '',
      prescriptions_note: '',
      follow_up_date: '',
    })
    setDiagnoses([emptyDx()])
    setMedications([emptyMed()])
  }

  const mutation = useMutation({
    mutationFn: (body: object) => api.post('/provider/encounters', body),
    onSuccess: () => {
      setOpen(false)
      resetForm()
      onSuccess()
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    mutation.mutate({
      ...form,
      request_id: requestId,
      follow_up_date: form.follow_up_date || undefined,
      diagnoses: diagnoses.filter((d) => d.condition_name.trim()),
      medications: medications
        .filter((m) => m.drug_name.trim())
        .map((m) => ({
          drug_name: m.drug_name,
          dosage: m.dosage || undefined,
          frequency: formatMedFrequency(m),
          is_active: m.is_active,
        })),
    })
  }

  function updateDx(i: number, patch: Partial<DiagnosisEntry>) {
    setDiagnoses((prev) => prev.map((d, idx) => (idx === i ? { ...d, ...patch } : d)))
  }

  function updateMed(i: number, patch: Partial<MedicationEntry>) {
    setMedications((prev) => prev.map((m, idx) => (idx === i ? { ...m, ...patch } : m)))
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 bg-primary text-white rounded-xl px-5 py-2.5 text-sm font-semibold hover:bg-teal-700 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        Log Encounter
      </button>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-teal-100 p-6 space-y-6">
      <h3 className="font-semibold text-slate-800 text-base">New Encounter</h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Encounter Date *</label>
          <input
            type="date"
            value={form.encounter_date}
            onChange={(e) => setForm({ ...form, encounter_date: e.target.value })}
            required
            className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Follow-up Date</label>
          <input
            type="date"
            value={form.follow_up_date}
            onChange={(e) => setForm({ ...form, follow_up_date: e.target.value })}
            className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-slate-600 mb-1">Chief Complaint</label>
        <input
          type="text"
          value={form.chief_complaint}
          onChange={(e) => setForm({ ...form, chief_complaint: e.target.value })}
          placeholder="e.g. Chest pain, persistent cough"
          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
      </div>

      {/* ── Diagnoses ────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide">Diagnoses</label>
          <button
            type="button"
            onClick={() => setDiagnoses((p) => [...p, emptyDx()])}
            className="text-xs text-primary font-medium hover:underline"
          >
            + Add another
          </button>
        </div>
        <div className="space-y-2">
          {diagnoses.map((d, i) => (
            <div key={i} className="flex gap-2 items-center">
              <input
                value={d.condition_name}
                onChange={(e) => updateDx(i, { condition_name: e.target.value })}
                placeholder="Condition name"
                className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
              <select
                value={d.status}
                onChange={(e) => updateDx(i, { status: e.target.value })}
                className="border border-slate-200 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-white"
              >
                <option value="ACTIVE">Active</option>
                <option value="CHRONIC">Chronic</option>
                <option value="RESOLVED">Resolved</option>
              </select>
              {diagnoses.length > 1 && (
                <button
                  type="button"
                  onClick={() => setDiagnoses((p) => p.filter((_, j) => j !== i))}
                  className="text-slate-300 hover:text-red-400 text-xl leading-none w-7 h-7 flex items-center justify-center"
                >
                  ×
                </button>
              )}
            </div>
          ))}
        </div>
        <textarea
          value={form.diagnosis_notes}
          onChange={(e) => setForm({ ...form, diagnosis_notes: e.target.value })}
          rows={2}
          placeholder="Additional clinical notes (optional)"
          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none mt-2"
        />
      </div>

      {/* ── Medications ──────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide">Medications Prescribed</label>
          <button
            type="button"
            onClick={() => setMedications((p) => [...p, emptyMed()])}
            className="text-xs text-primary font-medium hover:underline"
          >
            + Add another
          </button>
        </div>
        <div className="space-y-4">
          {medications.map((m, i) => (
            <div key={i} className="bg-slate-50 rounded-xl p-4 space-y-3 relative">
              {medications.length > 1 && (
                <button
                  type="button"
                  onClick={() => setMedications((p) => p.filter((_, j) => j !== i))}
                  className="absolute top-3 right-3 text-slate-300 hover:text-red-400 text-xl leading-none"
                >
                  ×
                </button>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Drug Name</label>
                  <input
                    value={m.drug_name}
                    onChange={(e) => updateMed(i, { drug_name: e.target.value })}
                    placeholder="e.g. Metformin"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary/30"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Dosage</label>
                  <input
                    value={m.dosage}
                    onChange={(e) => updateMed(i, { dosage: e.target.value })}
                    placeholder="e.g. 500mg"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary/30"
                  />
                </div>
              </div>

              {/* Timing: Morning / Noon / Night */}
              <div>
                <p className="text-xs text-slate-500 mb-1.5">Timing</p>
                <div className="flex gap-2 flex-wrap">
                  {(['morning', 'noon', 'night'] as const).map((slot) => (
                    <label
                      key={slot}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium cursor-pointer select-none transition-colors ${
                        m[slot]
                          ? 'bg-primary text-white border-primary'
                          : 'bg-white text-slate-600 border-slate-200 hover:border-primary/50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={m[slot]}
                        onChange={(e) => updateMed(i, { [slot]: e.target.checked } as Partial<MedicationEntry>)}
                        className="sr-only"
                      />
                      {slot.charAt(0).toUpperCase() + slot.slice(1)}
                    </label>
                  ))}
                </div>
              </div>

              {/* Food timing */}
              <div>
                <p className="text-xs text-slate-500 mb-1.5">With Food</p>
                <div className="flex gap-2">
                  {([
                    { val: 'before' as const, label: 'Before food' },
                    { val: 'after' as const, label: 'After food' },
                  ]).map(({ val, label }) => (
                    <label
                      key={val}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium cursor-pointer select-none transition-colors ${
                        m.food_timing === val
                          ? 'bg-teal-50 text-primary border-primary'
                          : 'bg-white text-slate-600 border-slate-200 hover:border-primary/50'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`food-timing-${i}`}
                        checked={m.food_timing === val}
                        onChange={() => updateMed(i, { food_timing: m.food_timing === val ? '' : val })}
                        className="sr-only"
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
        <textarea
          value={form.prescriptions_note}
          onChange={(e) => setForm({ ...form, prescriptions_note: e.target.value })}
          rows={2}
          placeholder="Additional prescription notes (optional)"
          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none mt-3"
        />
      </div>

      {mutation.isError && (
        <p className="text-sm text-red-500">Failed to save encounter. Please try again.</p>
      )}

      <div className="flex gap-3 justify-end">
        <button
          type="button"
          onClick={() => { setOpen(false); resetForm() }}
          className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={mutation.isPending}
          className="bg-primary text-white rounded-xl px-5 py-2 text-sm font-semibold hover:bg-teal-700 disabled:opacity-50"
        >
          {mutation.isPending ? 'Saving…' : 'Save Encounter'}
        </button>
      </div>
    </form>
  )
}

// ── Encounter Card ─────────────────────────────────────────────────────────

function EncounterCard({ encounter }: { encounter: Encounter }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-white rounded-2xl border border-slate-100 p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-semibold text-slate-800 text-sm">
            {formatDate(encounter.encounter_date)}
          </p>
          {encounter.chief_complaint && (
            <p className="text-slate-500 text-sm mt-0.5">{encounter.chief_complaint}</p>
          )}
        </div>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-xs text-primary hover:underline"
        >
          {expanded ? 'Less' : 'Details'}
        </button>
      </div>

      {expanded && (
        <div className="mt-4 space-y-3 border-t border-slate-50 pt-4">
          {encounter.diagnosis_notes && (
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Diagnosis</p>
              <p className="text-sm text-slate-700 whitespace-pre-wrap">{encounter.diagnosis_notes}</p>
            </div>
          )}
          {encounter.prescriptions_note && (
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Prescriptions</p>
              <p className="text-sm text-slate-700 whitespace-pre-wrap">{encounter.prescriptions_note}</p>
            </div>
          )}
          {encounter.follow_up_date && (
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Follow-up</p>
              <p className="text-sm text-slate-700">{formatDate(encounter.follow_up_date)}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────

export function ProviderPatientPage() {
  const { requestId } = useParams<{ requestId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data, isLoading, isError } = useQuery<PatientData>({
    queryKey: ['provider-patient', requestId],
    queryFn: async () => {
      const { data } = await api.get(`/provider/patient/${requestId}`)
      return data
    },
    enabled: !!requestId,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface px-4">
        <div className="bg-white rounded-2xl shadow-lg p-10 max-w-md w-full text-center">
          <p className="text-slate-700 font-medium mb-4">Unable to load patient data.</p>
          <button onClick={() => navigate('/provider')} className="text-sm text-primary hover:underline">
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  const { patient, encounters } = data

  return (
    <div className="min-h-screen bg-surface pb-16">
      {/* Header */}
      <div className="bg-white border-b border-slate-100 px-4 py-4 flex items-center gap-3 sticky top-0 z-10">
        <button
          onClick={() => navigate('/provider')}
          className="text-slate-400 hover:text-slate-600"
          aria-label="Back"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="font-semibold text-slate-800 font-manrope">{patient.full_name}</h1>
      </div>

      <div className="max-w-2xl mx-auto px-4 pt-6 space-y-5">
        {/* Identity & Baseline */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Identity & Baseline
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatBox
              label="Age"
              value={patient.date_of_birth ? `${calculateAge(patient.date_of_birth)} yrs` : '—'}
            />
            <StatBox label="Blood Group" value={patient.blood_group ?? '—'} />
            <StatBox
              label="Height"
              value={patient.height_cm ? `${patient.height_cm} cm` : '—'}
            />
            <StatBox
              label="Weight"
              value={patient.weight_kg ? `${patient.weight_kg} kg` : '—'}
            />
          </div>
        </div>

        {/* Encounters */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Encounters ({encounters.length})
            </h2>
            <LogEncounterForm
              requestId={requestId!}
              onSuccess={() => qc.invalidateQueries({ queryKey: ['provider-patient', requestId] })}
            />
          </div>

          {encounters.length === 0 ? (
            <div className="bg-white rounded-2xl border border-dashed border-slate-200 p-8 text-center text-slate-400 text-sm">
              No encounters logged yet.
            </div>
          ) : (
            encounters.map((enc) => <EncounterCard key={enc.encounter_id} encounter={enc} />)
          )}
        </div>
      </div>
    </div>
  )
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-teal-50/40 rounded-xl p-3 text-center">
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p className="text-base font-semibold text-slate-800">{value}</p>
    </div>
  )
}
