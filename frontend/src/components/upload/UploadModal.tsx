import { useEffect, useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'
import type { DocumentType } from '../../types'

// ── Types ──────────────────────────────────────────────────────────────────

export interface UploadModalProps {
  isOpen: boolean
  onClose: () => void
  memberId: string
}

type Step = 1 | 2 | 3 | 4

type UploadState =
  | { kind: 'idle' }
  | { kind: 'success' }
  | { kind: 'error'; message: string }

const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024 // 20 MB

// ── Pill options for document type ────────────────────────────────────────

interface DocTypeOption {
  value: DocumentType
  label: string
  icon: React.ReactNode
}

function LabIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5" aria-hidden="true">
      <path d="M9 3v11.5a3.5 3.5 0 0 0 7 0V3h-2v11.5a1.5 1.5 0 0 1-3 0V3H9zM7 2h10a1 1 0 0 1 1 1v12.5a5.5 5.5 0 0 1-11 0V3a1 1 0 0 1 1-1z" />
    </svg>
  )
}

function PrescriptionIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5" aria-hidden="true">
      <path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zm-7 3a1 1 0 0 1 1 1v2h2a1 1 0 1 1 0 2h-2v2a1 1 0 1 1-2 0v-2H9a1 1 0 1 1 0-2h2V7a1 1 0 0 1 1-1zm-4 9h8a1 1 0 1 1 0 2H8a1 1 0 1 1 0-2z" />
    </svg>
  )
}

function DischargeIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6zm2-5h8v1.5H8V15zm0 2.5h5v1.5H8V17.5z" />
    </svg>
  )
}

function OtherIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z" />
    </svg>
  )
}

const DOC_TYPE_OPTIONS: DocTypeOption[] = [
  { value: 'LAB_REPORT', label: 'Lab Report', icon: <LabIcon /> },
  { value: 'PRESCRIPTION', label: 'Prescription', icon: <PrescriptionIcon /> },
  { value: 'DISCHARGE', label: 'Discharge Summary', icon: <DischargeIcon /> },
  { value: 'OTHER', label: 'Other', icon: <OtherIcon /> },
]

// ── Step 1 — File Selection ────────────────────────────────────────────────

interface Step1Props {
  file: File | null
  fileError: string | null
  onFileChange: (file: File | null, error: string | null) => void
  onContinue: () => void
  onClose: () => void
}

function Step1FileSelection({ file, fileError, onFileChange, onContinue, onClose }: Step1Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  function validateAndSet(candidate: File) {
    if (candidate.type !== 'application/pdf' && !candidate.name.toLowerCase().endsWith('.pdf')) {
      onFileChange(null, 'Only PDF files are accepted.')
      return
    }
    if (candidate.size > MAX_FILE_SIZE_BYTES) {
      onFileChange(null, 'File exceeds the 20 MB limit.')
      return
    }
    onFileChange(candidate, null)
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0]
    if (picked) validateAndSet(picked)
    // Reset input so the same file can be re-selected after an error
    e.target.value = ''
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files?.[0]
    if (dropped) validateAndSet(dropped)
  }

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(true)
  }

  function handleDragLeave() {
    setIsDragging(false)
  }

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-xl font-extrabold text-on-surface tracking-tight">
            Import Record
          </h2>
          <p className="text-sm text-on-surface-variant mt-0.5">Step 1 of 2 — Select a file</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-surface-container transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30"
          aria-label="Close modal"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 text-on-surface-variant" aria-hidden="true">
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Click or drag a PDF here to select it"
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click() }}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          relative cursor-pointer rounded-2xl border-2 border-dashed p-8 flex flex-col items-center justify-center gap-3 transition-colors min-h-[200px]
          ${isDragging ? 'border-primary bg-primary/5' : 'border-outline-variant hover:border-primary/50 hover:bg-surface-container/40'}
          ${fileError ? 'border-error bg-error-container/20' : ''}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="sr-only"
          aria-hidden="true"
          tabIndex={-1}
          onChange={handleInputChange}
        />

        {file ? (
          /* File selected — show success state */
          <>
            <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-green-600" aria-hidden="true">
                <path d="M20 6 9 17l-5-5" />
              </svg>
            </div>
            <div className="text-center">
              <p className="text-sm font-bold text-on-surface truncate max-w-[260px]">{file.name}</p>
              <p className="text-xs text-on-surface-variant mt-0.5">{formatSize(file.size)}</p>
            </div>
            <p className="text-xs text-on-surface-variant/60">Click to choose a different file</p>
          </>
        ) : (
          /* No file yet */
          <>
            <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center flex-shrink-0">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-7 h-7 text-primary" aria-hidden="true">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="12" y1="18" x2="12" y2="12" />
                <line x1="9" y1="15" x2="15" y2="15" />
              </svg>
            </div>
            <div className="text-center">
              <p className="text-sm font-semibold text-on-surface">
                Drop your PDF here or{' '}
                <span className="text-primary underline underline-offset-2">click to browse</span>
              </p>
              <p className="text-xs text-on-surface-variant mt-1">PDF only · Max 20 MB</p>
            </div>
          </>
        )}
      </div>

      {/* Inline error */}
      {fileError && (
        <p className="mt-2 text-sm font-medium text-error flex items-center gap-1.5" role="alert">
          <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 flex-shrink-0" aria-hidden="true">
            <path d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 14.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2zm1-5a1 1 0 1 1-2 0V8a1 1 0 1 1 2 0v3.5z" />
          </svg>
          {fileError}
        </p>
      )}

      {/* Continue button */}
      <button
        type="button"
        onClick={onContinue}
        disabled={!file || !!fileError}
        className="mt-6 w-full bg-primary text-white font-semibold rounded-full py-3 hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-40 disabled:cursor-not-allowed min-h-[48px]"
      >
        Continue
      </button>
    </>
  )
}

// ── Step 2 — Document Details ──────────────────────────────────────────────

interface Step2Props {
  documentType: DocumentType
  documentDate: string
  onDocumentTypeChange: (t: DocumentType) => void
  onDocumentDateChange: (d: string) => void
  onUpload: () => void
  onBack: () => void
}

function Step2DocumentDetails({
  documentType,
  documentDate,
  onDocumentTypeChange,
  onDocumentDateChange,
  onUpload,
  onBack,
}: Step2Props) {
  return (
    <>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-xl font-extrabold text-on-surface tracking-tight">
          Document Details
        </h2>
        <p className="text-sm text-on-surface-variant mt-0.5">Step 2 of 2 — Describe your document</p>
      </div>

      {/* Document type pills */}
      <fieldset className="mb-6">
        <legend className="text-sm font-semibold text-on-surface mb-3">Document Type</legend>
        <div className="grid grid-cols-2 gap-2">
          {DOC_TYPE_OPTIONS.map((opt) => {
            const isSelected = documentType === opt.value
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => onDocumentTypeChange(opt.value)}
                className={`
                  flex items-center gap-2.5 px-4 py-3 rounded-full font-semibold text-sm transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/30
                  ${isSelected
                    ? 'bg-primary text-white shadow-sm shadow-primary/20'
                    : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                  }
                `}
                aria-pressed={isSelected}
              >
                {opt.icon}
                <span className="truncate">{opt.label}</span>
              </button>
            )
          })}
        </div>
      </fieldset>

      {/* Document date */}
      <div className="mb-6">
        <label htmlFor="document-date" className="block text-sm font-semibold text-on-surface mb-1.5">
          Document Date{' '}
          <span className="font-normal text-on-surface-variant">(optional)</span>
        </label>
        <input
          id="document-date"
          type="date"
          value={documentDate}
          onChange={(e) => onDocumentDateChange(e.target.value)}
          className="w-full rounded-xl bg-surface-container px-4 py-3 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 min-h-[44px]"
        />
      </div>

      {/* Action row */}
      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 bg-surface-container text-on-surface font-semibold rounded-full py-3 hover:bg-surface-container-high transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 min-h-[48px]"
        >
          Back
        </button>
        <button
          type="button"
          onClick={onUpload}
          className="flex-[2] bg-primary text-white font-semibold rounded-full py-3 hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40 min-h-[48px]"
        >
          Upload
        </button>
      </div>
    </>
  )
}

// ── Step 3 — Uploading ─────────────────────────────────────────────────────

function Step3Uploading() {
  return (
    <div className="flex flex-col items-center justify-center py-10 gap-5 text-center">
      {/* Spinner */}
      <div className="w-16 h-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin" aria-hidden="true" />
      <div>
        <p className="text-base font-bold text-on-surface">Uploading your document…</p>
        <p className="text-sm text-on-surface-variant mt-1">This may take a moment</p>
      </div>
    </div>
  )
}

// ── Step 4 — Success / Error ───────────────────────────────────────────────

interface Step4Props {
  uploadState: UploadState
  onDone: () => void
  onTryAgain: () => void
  onCancel: () => void
  onClose: () => void
}

function Step4Result({ uploadState, onDone, onTryAgain, onCancel, onClose }: Step4Props) {
  const isSuccess = uploadState.kind === 'success'

  return (
    <>
      {/* Close button */}
      <div className="flex justify-end mb-2">
        <button
          type="button"
          onClick={onClose}
          className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-surface-container transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30"
          aria-label="Close modal"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 text-on-surface-variant" aria-hidden="true">
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="flex flex-col items-center justify-center py-6 gap-5 text-center">
        {/* Icon */}
        {isSuccess ? (
          <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8 text-green-600" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          </div>
        ) : (
          <div className="w-16 h-16 rounded-full bg-error-container flex items-center justify-center">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8 text-error" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <path d="M15 9l-6 6M9 9l6 6" />
            </svg>
          </div>
        )}

        {/* Text */}
        {isSuccess ? (
          <div>
            <p className="text-base font-bold text-on-surface">Document uploaded successfully!</p>
            <p className="text-sm text-on-surface-variant mt-1 max-w-xs mx-auto">
              Processing has started — we'll extract your health data shortly.
            </p>
          </div>
        ) : (
          <div>
            <p className="text-base font-bold text-on-surface">Upload failed</p>
            <p className="text-sm text-on-surface-variant mt-1 max-w-xs mx-auto">
              {uploadState.kind === 'error' ? uploadState.message : 'An unexpected error occurred.'}
            </p>
          </div>
        )}

        {/* Actions */}
        {isSuccess ? (
          <button
            type="button"
            onClick={onDone}
            className="bg-primary text-white font-semibold rounded-full px-8 py-3 hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40 min-h-[48px]"
          >
            Done
          </button>
        ) : (
          <div className="flex gap-3 w-full">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 bg-surface-container text-on-surface font-semibold rounded-full py-3 hover:bg-surface-container-high transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 min-h-[48px]"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={onTryAgain}
              className="flex-[2] bg-primary text-white font-semibold rounded-full py-3 hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40 min-h-[48px]"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </>
  )
}

// ── Main UploadModal ───────────────────────────────────────────────────────

export function UploadModal({ isOpen, onClose, memberId }: UploadModalProps) {
  const queryClient = useQueryClient()

  // Form state
  const [step, setStep] = useState<Step>(1)
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [documentType, setDocumentType] = useState<DocumentType>('LAB_REPORT')
  const [documentDate, setDocumentDate] = useState<string>('')
  const [uploadState, setUploadState] = useState<UploadState>({ kind: 'idle' })

  // Reset all state when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      // Delay reset so exit animation isn't jerky
      const t = setTimeout(() => {
        setStep(1)
        setFile(null)
        setFileError(null)
        setDocumentType('LAB_REPORT')
        setDocumentDate('')
        setUploadState({ kind: 'idle' })
      }, 200)
      return () => clearTimeout(t)
    }
  }, [isOpen])

  // Escape key handler — only on steps 1, 2, 4
  useEffect(() => {
    if (!isOpen) return
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && step !== 3) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, step, onClose])

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('No file selected')
      const formData = new FormData()
      formData.append('file', file)
      formData.append('member_id', memberId)
      formData.append('document_type', documentType)
      if (documentDate) formData.append('document_date', documentDate)
      await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setUploadState({ kind: 'success' })
      setStep(4)
    },
    onError: (err: unknown) => {
      let message = 'An unexpected error occurred. Please try again.'
      if (
        err &&
        typeof err === 'object' &&
        'response' in err &&
        err.response &&
        typeof err.response === 'object' &&
        'data' in err.response &&
        err.response.data &&
        typeof err.response.data === 'object' &&
        'message' in err.response.data &&
        typeof (err.response.data as { message: unknown }).message === 'string'
      ) {
        message = (err.response.data as { message: string }).message
      }
      setUploadState({ kind: 'error', message })
      setStep(4)
    },
  })

  function handleFileChange(f: File | null, error: string | null) {
    setFile(f)
    setFileError(error)
  }

  function handleContinue() {
    if (file && !fileError) setStep(2)
  }

  function handleUpload() {
    setStep(3)
    uploadMutation.mutate()
  }

  function handleDone() {
    onClose()
  }

  function handleTryAgain() {
    setUploadState({ kind: 'idle' })
    setStep(2)
  }

  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget && step !== 3) {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
        aria-hidden="true"
        onClick={handleBackdropClick}
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Upload medical document"
        className="fixed inset-x-4 top-1/2 -translate-y-1/2 max-w-lg mx-auto bg-white rounded-2xl shadow-2xl shadow-primary/10 z-50 p-6"
      >
        {step === 1 && (
          <Step1FileSelection
            file={file}
            fileError={fileError}
            onFileChange={handleFileChange}
            onContinue={handleContinue}
            onClose={onClose}
          />
        )}

        {step === 2 && (
          <Step2DocumentDetails
            documentType={documentType}
            documentDate={documentDate}
            onDocumentTypeChange={setDocumentType}
            onDocumentDateChange={setDocumentDate}
            onUpload={handleUpload}
            onBack={() => setStep(1)}
          />
        )}

        {step === 3 && <Step3Uploading />}

        {step === 4 && (
          <Step4Result
            uploadState={uploadState}
            onDone={handleDone}
            onTryAgain={handleTryAgain}
            onCancel={onClose}
            onClose={onClose}
          />
        )}
      </div>
    </>
  )
}
