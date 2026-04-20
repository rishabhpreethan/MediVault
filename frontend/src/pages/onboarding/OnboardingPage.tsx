import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'

// ── Types ──────────────────────────────────────────────────────────────────

type Role = 'PATIENT' | 'PROVIDER'

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-', 'Unknown'] as const

interface OnboardingData {
  full_name: string
  date_of_birth: string
  height_cm: string
  weight_kg: string
  blood_group: string
  role: Role
  allergies: string[]
  licence_number: string
  registration_council: string
}

// ── Step progress indicator ────────────────────────────────────────────────

function StepDots({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={`rounded-full transition-all duration-300 ${
            i === current
              ? 'w-6 h-2 bg-primary'
              : i < current
              ? 'w-2 h-2 bg-primary/40'
              : 'w-2 h-2 bg-slate-200'
          }`}
        />
      ))}
    </div>
  )
}

// ── Step 1: Personal Info ──────────────────────────────────────────────────

function StepPersonalInfo({
  data,
  onChange,
  onNext,
  onSkip,
}: {
  data: Pick<OnboardingData, 'full_name' | 'date_of_birth' | 'height_cm' | 'weight_kg'>
  onChange: (field: keyof OnboardingData, value: string) => void
  onNext: () => void
  onSkip: () => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">Tell us about yourself</h1>
        <p className="text-sm text-on-surface-variant mt-1">We'll use this to set up your health profile.</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-semibold text-on-surface mb-1.5">Full name <span className="text-tertiary">*</span></label>
          <input
            type="text"
            placeholder="e.g. Neeraj Menon"
            value={data.full_name}
            onChange={(e) => onChange('full_name', e.target.value)}
            className="w-full rounded-xl border border-outline-variant bg-surface px-4 py-3 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-on-surface mb-1.5">Date of birth</label>
          <input
            type="date"
            value={data.date_of_birth}
            onChange={(e) => onChange('date_of_birth', e.target.value)}
            className="w-full rounded-xl border border-outline-variant bg-surface px-4 py-3 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-semibold text-on-surface mb-1.5">Height (cm)</label>
            <input
              type="number"
              placeholder="e.g. 170"
              value={data.height_cm}
              onChange={(e) => onChange('height_cm', e.target.value)}
              className="w-full rounded-xl border border-outline-variant bg-surface px-4 py-3 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-on-surface mb-1.5">Weight (kg)</label>
            <input
              type="number"
              placeholder="e.g. 65"
              value={data.weight_kg}
              onChange={(e) => onChange('weight_kg', e.target.value)}
              className="w-full rounded-xl border border-outline-variant bg-surface px-4 py-3 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
            />
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3 pt-2">
        <button
          type="button"
          onClick={onNext}
          className="w-full bg-primary text-white font-semibold rounded-full py-3 hover:bg-primary/90 transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/40"
        >
          Continue
        </button>
        <button type="button" onClick={onSkip} className="text-sm text-on-surface-variant hover:text-on-surface transition-colors min-h-[44px]">
          Skip for now
        </button>
      </div>
    </div>
  )
}

// ── Step 2: Blood Group ────────────────────────────────────────────────────

function StepBloodGroup({
  value,
  onChange,
  onNext,
  onSkip,
}: {
  value: string
  onChange: (v: string) => void
  onNext: () => void
  onSkip: () => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">Blood group</h1>
        <p className="text-sm text-on-surface-variant mt-1">Critical for emergencies. Select yours below.</p>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {BLOOD_GROUPS.map((bg) => (
          <button
            key={bg}
            type="button"
            onClick={() => onChange(bg)}
            className={`rounded-xl py-3 text-sm font-bold transition-all min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/40 ${
              value === bg
                ? 'bg-primary text-white shadow-md shadow-teal-900/20'
                : 'bg-surface-container-low text-on-surface hover:bg-surface-container'
            }`}
          >
            {bg}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-3 pt-2">
        <button
          type="button"
          onClick={onNext}
          className="w-full bg-primary text-white font-semibold rounded-full py-3 hover:bg-primary/90 transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/40"
        >
          Continue
        </button>
        <button type="button" onClick={onSkip} className="text-sm text-on-surface-variant hover:text-on-surface transition-colors min-h-[44px]">
          Skip for now
        </button>
      </div>
    </div>
  )
}

// ── Step 3: Allergies ──────────────────────────────────────────────────────

function StepAllergies({
  allergies,
  onAdd,
  onRemove,
  onNext,
  onSkip,
}: {
  allergies: string[]
  onAdd: (a: string) => void
  onRemove: (a: string) => void
  onNext: () => void
  onSkip: () => void
}) {
  const [input, setInput] = useState('')

  function handleAdd() {
    const val = input.trim()
    if (val && !allergies.includes(val)) {
      onAdd(val)
    }
    setInput('')
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">Known allergies</h1>
        <p className="text-sm text-on-surface-variant mt-1">Add any medications, foods, or substances you're allergic to.</p>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          placeholder="e.g. Penicillin, Pollen..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          className="flex-1 rounded-xl border border-outline-variant bg-surface px-4 py-3 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
        />
        <button
          type="button"
          onClick={handleAdd}
          className="rounded-xl bg-primary text-white px-4 py-3 font-semibold text-sm hover:bg-primary/90 transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/40"
        >
          Add
        </button>
      </div>

      {allergies.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {allergies.map((a) => (
            <span
              key={a}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-tertiary-container text-tertiary text-sm font-medium"
            >
              {a}
              <button
                type="button"
                onClick={() => onRemove(a)}
                className="w-4 h-4 rounded-full flex items-center justify-center hover:bg-tertiary/20 transition-colors"
                aria-label={`Remove ${a}`}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="flex flex-col gap-3 pt-2">
        <button
          type="button"
          onClick={onNext}
          className="w-full bg-primary text-white font-semibold rounded-full py-3 hover:bg-primary/90 transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/40"
        >
          Continue
        </button>
        <button type="button" onClick={onSkip} className="text-sm text-on-surface-variant hover:text-on-surface transition-colors min-h-[44px]">
          Skip for now
        </button>
      </div>
    </div>
  )
}

// ── Step 4: Role Selection ─────────────────────────────────────────────────

function StepRole({
  role,
  onChange,
  onNext,
}: {
  role: Role
  onChange: (r: Role) => void
  onNext: () => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">How will you use MediVault?</h1>
        <p className="text-sm text-on-surface-variant mt-1">This determines the features available to you.</p>
      </div>

      <div className="space-y-3">
        <button
          type="button"
          onClick={() => onChange('PATIENT')}
          className={`w-full text-left p-4 rounded-2xl border-2 transition-all min-h-[44px] focus:outline-none ${
            role === 'PATIENT'
              ? 'border-primary bg-primary/5 shadow-sm'
              : 'border-outline-variant bg-surface hover:border-primary/40'
          }`}
        >
          <div className="flex items-start gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${role === 'PATIENT' ? 'bg-primary text-white' : 'bg-surface-container-low text-on-surface-variant'}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-bold text-on-surface">I'm a Patient</p>
              <p className="text-xs text-on-surface-variant mt-0.5">Manage your personal health records and share them with your doctors.</p>
            </div>
          </div>
        </button>

        <button
          type="button"
          onClick={() => onChange('PROVIDER')}
          className={`w-full text-left p-4 rounded-2xl border-2 transition-all min-h-[44px] focus:outline-none ${
            role === 'PROVIDER'
              ? 'border-primary bg-primary/5 shadow-sm'
              : 'border-outline-variant bg-surface hover:border-primary/40'
          }`}
        >
          <div className="flex items-start gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${role === 'PROVIDER' ? 'bg-primary text-white' : 'bg-surface-container-low text-on-surface-variant'}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-bold text-on-surface">I'm a Healthcare Provider</p>
              <p className="text-xs text-on-surface-variant mt-0.5">Look up patients by passport ID and log medical encounters. Requires licence verification.</p>
            </div>
          </div>
        </button>
      </div>

      <button
        type="button"
        onClick={onNext}
        className="w-full bg-primary text-white font-semibold rounded-full py-3 hover:bg-primary/90 transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/40"
      >
        Continue
      </button>
    </div>
  )
}

// ── Step 5: Provider Licence ───────────────────────────────────────────────

function StepProviderLicence({
  data,
  onChange,
  onNext,
  onBack,
}: {
  data: Pick<OnboardingData, 'licence_number' | 'registration_council'>
  onChange: (field: keyof OnboardingData, value: string) => void
  onNext: () => void
  onBack: () => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">Medical licence</h1>
        <p className="text-sm text-on-surface-variant mt-1">Required to access patient lookup features.</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-semibold text-on-surface mb-1.5">Licence number <span className="text-tertiary">*</span></label>
          <input
            type="text"
            placeholder="e.g. MH-12345"
            value={data.licence_number}
            onChange={(e) => onChange('licence_number', e.target.value)}
            className="w-full rounded-xl border border-outline-variant bg-surface px-4 py-3 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-on-surface mb-1.5">Registration council</label>
          <input
            type="text"
            placeholder="e.g. Maharashtra Medical Council"
            value={data.registration_council}
            onChange={(e) => onChange('registration_council', e.target.value)}
            className="w-full rounded-xl border border-outline-variant bg-surface px-4 py-3 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
          />
        </div>
      </div>

      <div className="flex items-start gap-2.5 bg-primary/5 border border-primary/20 rounded-xl p-3">
        <svg viewBox="0 0 24 24" fill="none" stroke="#0f766e" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 mt-0.5 flex-shrink-0">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 8v4M12 16h.01" />
        </svg>
        <p className="text-xs text-primary leading-relaxed">
          Your licence will be verified against the NMC registry. You can use patient features while verification is pending.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <button
          type="button"
          onClick={onNext}
          disabled={!data.licence_number.trim()}
          className="w-full bg-primary text-white font-semibold rounded-full py-3 hover:bg-primary/90 transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Continue
        </button>
        <button type="button" onClick={onBack} className="text-sm text-on-surface-variant hover:text-on-surface transition-colors min-h-[44px]">
          Back
        </button>
      </div>
    </div>
  )
}

// ── Step 6: Complete ───────────────────────────────────────────────────────

function StepComplete({
  data,
  isLoading,
  error,
  onComplete,
}: {
  data: OnboardingData
  isLoading: boolean
  error: string | null
  onComplete: () => void
}) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center text-center gap-3">
        <div className="w-16 h-16 rounded-2xl bg-teal-50 flex items-center justify-center">
          <svg viewBox="0 0 24 24" fill="none" stroke="#0f766e" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">You're all set</h1>
          <p className="text-sm text-on-surface-variant mt-1">Here's a summary of your profile setup.</p>
        </div>
      </div>

      <div className="bg-surface-container-low rounded-2xl p-4 space-y-3">
        {data.full_name && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-on-surface-variant">Name</span>
            <span className="text-sm font-bold text-on-surface">{data.full_name}</span>
          </div>
        )}
        <div className="flex justify-between items-center">
          <span className="text-sm text-on-surface-variant">Role</span>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${data.role === 'PROVIDER' ? 'bg-primary/10 text-primary' : 'bg-secondary-container text-secondary'}`}>
            {data.role === 'PROVIDER' ? 'Healthcare Provider' : 'Patient'}
          </span>
        </div>

        {data.blood_group && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-on-surface-variant">Blood group</span>
            <span className="text-sm font-bold text-on-surface">{data.blood_group}</span>
          </div>
        )}

        {data.allergies.length > 0 && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-on-surface-variant">Allergies</span>
            <span className="text-sm font-semibold text-on-surface">{data.allergies.length} added</span>
          </div>
        )}

        {data.role === 'PROVIDER' && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-on-surface-variant">Licence verification</span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-100 text-amber-700">Pending</span>
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-tertiary bg-tertiary-container/30 rounded-xl px-4 py-3">{error}</p>
      )}

      <button
        type="button"
        onClick={onComplete}
        disabled={isLoading}
        className="w-full bg-primary text-white font-semibold rounded-full py-3 hover:bg-primary/90 transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-60"
      >
        {isLoading ? 'Saving…' : 'Go to my health passport'}
      </button>
    </div>
  )
}

// ── Main OnboardingPage ────────────────────────────────────────────────────

export function OnboardingPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [step, setStep] = useState(0)
  const [data, setData] = useState<OnboardingData>({
    full_name: '',
    date_of_birth: '',
    height_cm: '',
    weight_kg: '',
    blood_group: '',
    role: 'PATIENT',
    allergies: [],
    licence_number: '',
    registration_council: '',
  })

  function setField(field: keyof OnboardingData, value: string) {
    setData((prev) => ({ ...prev, [field]: value }))
  }

  const totalSteps = data.role === 'PROVIDER' ? 6 : 5

  const { mutate, isPending, error } = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        role: data.role,
        allergies: data.allergies,
      }
      if (data.full_name.trim()) payload.full_name = data.full_name.trim()
      if (data.date_of_birth) payload.date_of_birth = data.date_of_birth
      if (data.height_cm) payload.height_cm = parseFloat(data.height_cm)
      if (data.weight_kg) payload.weight_kg = parseFloat(data.weight_kg)
      if (data.blood_group) payload.blood_group = data.blood_group
      if (data.role === 'PROVIDER') {
        payload.licence_number = data.licence_number
        payload.registration_council = data.registration_council
      }
      await api.post('/auth/onboarding', payload)
    },
    onSuccess: () => {
      queryClient.setQueryData(['onboarding-status'], { onboarding_completed: true, role: data.role })
      navigate('/')
    },
  })

  const errorMessage = error
    ? ((error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? 'Something went wrong. Please try again.')
    : null

  // Determine which logical step maps to which step index
  // Steps for PATIENT: 0=personal, 1=blood, 2=allergies, 3=role, 4=complete
  // Steps for PROVIDER: 0=personal, 1=blood, 2=allergies, 3=role, 4=licence, 5=complete

  function nextStep() {
    setStep((s) => s + 1)
  }
  function prevStep() {
    setStep((s) => Math.max(0, s - 1))
  }

  function handleRoleNext() {
    if (data.role === 'PROVIDER') {
      setStep(4) // licence step
    } else {
      setStep(4) // complete step (no licence for PATIENT)
    }
  }

  const completeStepIndex = data.role === 'PROVIDER' ? 5 : 4
  const licenceStepIndex = 4

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Brand header */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
            <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <span className="text-lg font-extrabold text-on-surface tracking-tight">MediVault</span>
        </div>

        <div className="bg-white rounded-3xl shadow-xl shadow-teal-900/8 p-7">
          <StepDots current={step} total={totalSteps} />

          {step === 0 && (
            <StepPersonalInfo
              data={{ full_name: data.full_name, date_of_birth: data.date_of_birth, height_cm: data.height_cm, weight_kg: data.weight_kg }}
              onChange={setField}
              onNext={nextStep}
              onSkip={nextStep}
            />
          )}

          {step === 1 && (
            <StepBloodGroup
              value={data.blood_group}
              onChange={(v) => setField('blood_group', v)}
              onNext={nextStep}
              onSkip={nextStep}
            />
          )}

          {step === 2 && (
            <StepAllergies
              allergies={data.allergies}
              onAdd={(a) => setData((prev) => ({ ...prev, allergies: [...prev.allergies, a] }))}
              onRemove={(a) => setData((prev) => ({ ...prev, allergies: prev.allergies.filter((x) => x !== a) }))}
              onNext={nextStep}
              onSkip={nextStep}
            />
          )}

          {step === 3 && (
            <StepRole
              role={data.role}
              onChange={(r) => setField('role', r)}
              onNext={handleRoleNext}
            />
          )}

          {step === licenceStepIndex && data.role === 'PROVIDER' && (
            <StepProviderLicence
              data={data}
              onChange={setField}
              onNext={() => setStep(completeStepIndex)}
              onBack={prevStep}
            />
          )}

          {step === completeStepIndex && (
            <StepComplete
              data={data}
              isLoading={isPending}
              error={errorMessage}
              onComplete={() => mutate()}
            />
          )}
        </div>
      </div>
    </div>
  )
}
