import { useEffect, useRef, useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'
import type { DocumentType } from '../../types'

// ── Constants ─────────────────────────────────────────────────────────────

const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024 // 20 MB
const MAX_FILES = 10

// ── Types ──────────────────────────────────────────────────────────────────

export interface UploadModalProps {
  isOpen: boolean
  onClose: () => void
  memberId: string
}

type FileUploadStatus = 'idle' | 'uploading' | 'done' | 'error'

interface FileEntry {
  id: string
  file: File
  documentType: DocumentType
  documentDate: string
  status: FileUploadStatus
  errorMessage: string | null
}

// ── Doc type options ───────────────────────────────────────────────────────

interface DocTypeOption {
  value: DocumentType
  label: string
}

const DOC_TYPE_OPTIONS: DocTypeOption[] = [
  { value: 'LAB_REPORT', label: 'Lab Report' },
  { value: 'PRESCRIPTION', label: 'Prescription' },
  { value: 'DISCHARGE', label: 'Discharge Summary' },
  { value: 'SCAN', label: 'Scan / Imaging' },
  { value: 'OTHER', label: 'Other' },
]

// ── Inline SVG Icons ───────────────────────────────────────────────────────

function CloseIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-5 h-5 text-on-surface-variant"
      aria-hidden="true"
    >
      <path d="M18 6 6 18M6 6l12 12" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4 text-green-600"
      aria-hidden="true"
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  )
}

function ErrorIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className="w-4 h-4 text-error flex-shrink-0"
      aria-hidden="true"
    >
      <path d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 14.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2zm1-5a1 1 0 1 1-2 0V8a1 1 0 1 1 2 0v3.5z" />
    </svg>
  )
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function newEntry(file: File): FileEntry {
  return {
    id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
    file,
    documentType: 'LAB_REPORT',
    documentDate: '',
    status: 'idle',
    errorMessage: null,
  }
}

// ── File row component ─────────────────────────────────────────────────────

interface FileRowProps {
  entry: FileEntry
  onTypeChange: (id: string, type: DocumentType) => void
  onDateChange: (id: string, date: string) => void
  onRemove: (id: string) => void
  isUploading: boolean
}

function FileRow({ entry, onTypeChange, onDateChange, onRemove, isUploading }: FileRowProps) {
  const { id, file, documentType, documentDate, status, errorMessage } = entry
  const isActive = status === 'idle'

  return (
    <div
      className={`rounded-xl border p-3 transition-colors ${
        status === 'done'
          ? 'border-green-200 bg-green-50'
          : status === 'error'
            ? 'border-error/30 bg-error-container/20'
            : 'border-outline-variant bg-surface-container-lowest'
      }`}
    >
      {/* File name row */}
      <div className="flex items-start gap-2">
        {/* Status indicator */}
        <div className="w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">
          {status === 'uploading' && (
            <div
              className="w-4 h-4 rounded-full border-2 border-primary/20 border-t-primary animate-spin"
              aria-label="Uploading"
            />
          )}
          {status === 'done' && (
            <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
              <CheckIcon />
            </div>
          )}
          {status === 'error' && <ErrorIcon />}
          {status === 'idle' && (
            <svg
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-5 h-5 text-on-surface-variant/40"
              aria-hidden="true"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z" />
            </svg>
          )}
        </div>

        {/* Name + size */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-on-surface truncate" title={file.name}>
            {file.name}
          </p>
          <p className="text-xs text-on-surface-variant">{formatSize(file.size)}</p>
        </div>

        {/* Remove button — hidden while uploading/done */}
        {isActive && !isUploading && (
          <button
            type="button"
            onClick={() => onRemove(id)}
            className="w-7 h-7 flex items-center justify-center rounded-full hover:bg-surface-container-high transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 flex-shrink-0"
            aria-label={`Remove ${file.name}`}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-4 h-4 text-on-surface-variant"
              aria-hidden="true"
            >
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Per-file error */}
      {status === 'error' && errorMessage && (
        <p className="mt-1.5 text-xs font-medium text-error ml-8">{errorMessage}</p>
      )}

      {/* Type + date controls — only shown for idle files before upload starts */}
      {isActive && !isUploading && (
        <div className="mt-3 ml-8 space-y-2.5">
          {/* Document type pills — wrapped, compact */}
          <fieldset>
            <legend className="text-xs font-semibold text-on-surface-variant mb-1.5">
              Document Type
            </legend>
            <div className="flex flex-wrap gap-1.5">
              {DOC_TYPE_OPTIONS.map((opt) => {
                const selected = documentType === opt.value
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => onTypeChange(id, opt.value)}
                    aria-pressed={selected}
                    className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 ${
                      selected
                        ? 'bg-primary text-white'
                        : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                    }`}
                  >
                    {opt.label}
                  </button>
                )
              })}
            </div>
          </fieldset>

          {/* Date picker */}
          <div>
            <label
              htmlFor={`date-${id}`}
              className="text-xs font-semibold text-on-surface-variant block mb-1"
            >
              Document Date{' '}
              <span className="font-normal">(optional)</span>
            </label>
            <input
              id={`date-${id}`}
              type="date"
              value={documentDate}
              onChange={(e) => onDateChange(id, e.target.value)}
              className="rounded-lg bg-surface-container px-3 py-1.5 text-xs text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 min-h-[32px]"
            />
          </div>
        </div>
      )}
    </div>
  )
}

// ── Main UploadModal ───────────────────────────────────────────────────────

export function UploadModal({ isOpen, onClose, memberId }: UploadModalProps) {
  const queryClient = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [entries, setEntries] = useState<FileEntry[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [batchDone, setBatchDone] = useState(false)

  // Reset when modal closes
  useEffect(() => {
    if (!isOpen) {
      const t = setTimeout(() => {
        setEntries([])
        setIsUploading(false)
        setBatchDone(false)
        setIsDragging(false)
      }, 200)
      return () => clearTimeout(t)
    }
  }, [isOpen])

  // Escape key handler — blocked while uploading
  useEffect(() => {
    if (!isOpen) return
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && !isUploading) onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, isUploading, onClose])

  // ── File validation & adding ─────────────────────────────────────────────

  const addFiles = useCallback((incoming: FileList | File[]) => {
    const list = Array.from(incoming)
    const valid = list.filter(
      (f) =>
        (f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf')) &&
        f.size <= MAX_FILE_SIZE_BYTES,
    )
    setEntries((prev) => {
      const existing = new Set(prev.map((e) => `${e.file.name}:${e.file.size}`))
      const deduped = valid.filter((f) => !existing.has(`${f.name}:${f.size}`))
      const combined = [...prev, ...deduped.map(newEntry)]
      return combined.slice(0, MAX_FILES)
    })
  }, [])

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files) addFiles(e.target.files)
    e.target.value = ''
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files) addFiles(e.dataTransfer.files)
  }

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(true)
  }

  function handleDragLeave() {
    setIsDragging(false)
  }

  // ── Per-file metadata updates ────────────────────────────────────────────

  function handleTypeChange(id: string, type: DocumentType) {
    setEntries((prev) =>
      prev.map((e) => (e.id === id ? { ...e, documentType: type } : e)),
    )
  }

  function handleDateChange(id: string, date: string) {
    setEntries((prev) =>
      prev.map((e) => (e.id === id ? { ...e, documentDate: date } : e)),
    )
  }

  function handleRemove(id: string) {
    setEntries((prev) => prev.filter((e) => e.id !== id))
  }

  // ── Upload all ───────────────────────────────────────────────────────────

  async function handleUploadAll() {
    if (entries.length === 0 || isUploading) return
    setIsUploading(true)

    await Promise.all(
      entries.map(async (entry) => {
        // Mark as uploading
        setEntries((prev) =>
          prev.map((e) => (e.id === entry.id ? { ...e, status: 'uploading' } : e)),
        )

        try {
          const formData = new FormData()
          formData.append('file', entry.file)
          formData.append('member_id', memberId)
          formData.append('document_type', entry.documentType)
          if (entry.documentDate) formData.append('document_date', entry.documentDate)
          await api.post('/documents/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          })
          setEntries((prev) =>
            prev.map((e) => (e.id === entry.id ? { ...e, status: 'done' } : e)),
          )
        } catch (err: unknown) {
          let message = 'Upload failed. Please try again.'
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
          setEntries((prev) =>
            prev.map((e) =>
              e.id === entry.id ? { ...e, status: 'error', errorMessage: message } : e,
            ),
          )
        }
      }),
    )

    queryClient.invalidateQueries({ queryKey: ['documents'] })
    setIsUploading(false)
    setBatchDone(true)
  }

  // ── Backdrop click ───────────────────────────────────────────────────────

  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget && !isUploading) onClose()
  }

  if (!isOpen) return null

  const hasFiles = entries.length > 0
  const atMax = entries.length >= MAX_FILES
  const successCount = entries.filter((e) => e.status === 'done').length
  const errorCount = entries.filter((e) => e.status === 'error').length
  const allDone = hasFiles && entries.every((e) => e.status === 'done' || e.status === 'error')

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
        aria-label="Upload medical documents"
        className="fixed inset-x-4 top-1/2 -translate-y-1/2 max-w-lg mx-auto bg-white rounded-2xl shadow-2xl shadow-primary/10 z-50 flex flex-col max-h-[90dvh]"
      >
        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div className="flex items-start justify-between p-6 pb-4 flex-shrink-0">
          <div>
            <h2 className="text-xl font-extrabold text-on-surface tracking-tight">
              Import Records
            </h2>
            <p className="text-sm text-on-surface-variant mt-0.5">
              {batchDone
                ? `${successCount} uploaded${errorCount > 0 ? `, ${errorCount} failed` : ''}`
                : `Up to ${MAX_FILES} PDFs · Max 20 MB each`}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isUploading}
            className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-surface-container transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-40"
            aria-label="Close modal"
          >
            <CloseIcon />
          </button>
        </div>

        {/* ── Scrollable file list + drop zone ───────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-6 pb-2 space-y-2 min-h-0">
          {/* File rows */}
          {entries.map((entry) => (
            <FileRow
              key={entry.id}
              entry={entry}
              onTypeChange={handleTypeChange}
              onDateChange={handleDateChange}
              onRemove={handleRemove}
              isUploading={isUploading}
            />
          ))}

          {/* Drop zone — hidden once batch is done */}
          {!batchDone && !atMax && (
            <div
              role="button"
              tabIndex={isUploading ? -1 : 0}
              aria-label="Click or drag PDFs here to add them"
              onClick={() => !isUploading && inputRef.current?.click()}
              onKeyDown={(e) => {
                if (!isUploading && (e.key === 'Enter' || e.key === ' '))
                  inputRef.current?.click()
              }}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`
                cursor-pointer rounded-2xl border-2 border-dashed p-6 flex flex-col items-center justify-center gap-2 transition-colors min-h-[140px]
                ${isUploading ? 'opacity-40 cursor-not-allowed' : ''}
                ${isDragging ? 'border-primary bg-primary/5' : 'border-outline-variant hover:border-primary/50 hover:bg-surface-container/40'}
              `}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,application/pdf"
                multiple
                className="sr-only"
                aria-hidden="true"
                tabIndex={-1}
                onChange={handleInputChange}
              />
              <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-6 h-6 text-primary"
                  aria-hidden="true"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="12" y1="18" x2="12" y2="12" />
                  <line x1="9" y1="15" x2="15" y2="15" />
                </svg>
              </div>
              <div className="text-center">
                <p className="text-sm font-semibold text-on-surface">
                  {hasFiles ? 'Add more PDFs or ' : 'Drop PDFs here or '}
                  <span className="text-primary underline underline-offset-2">click to browse</span>
                </p>
                <p className="text-xs text-on-surface-variant mt-0.5">
                  PDF only · Max 20 MB · {MAX_FILES - entries.length} slot{MAX_FILES - entries.length !== 1 ? 's' : ''} remaining
                </p>
              </div>
            </div>
          )}

          {/* At-max notice */}
          {atMax && !batchDone && (
            <p className="text-xs text-center text-on-surface-variant py-2">
              Maximum of {MAX_FILES} files reached.
            </p>
          )}
        </div>

        {/* ── Footer actions ──────────────────────────────────────────────── */}
        <div className="p-6 pt-4 flex-shrink-0 border-t border-outline-variant/30">
          {batchDone && allDone ? (
            <button
              type="button"
              onClick={onClose}
              className="w-full bg-primary text-white font-semibold rounded-full py-3 hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40 min-h-[48px]"
            >
              Done
            </button>
          ) : (
            <button
              type="button"
              onClick={handleUploadAll}
              disabled={!hasFiles || isUploading}
              className="w-full bg-primary text-white font-semibold rounded-full py-3 hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-40 disabled:cursor-not-allowed min-h-[48px] flex items-center justify-center gap-2"
            >
              {isUploading ? (
                <>
                  <div
                    className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin"
                    aria-hidden="true"
                  />
                  Uploading…
                </>
              ) : (
                <>
                  {hasFiles
                    ? `Upload All (${entries.length} file${entries.length !== 1 ? 's' : ''})`
                    : 'Select files to upload'}
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </>
  )
}
